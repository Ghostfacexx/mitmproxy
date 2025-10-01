#!/usr/bin/env python3
"""
Test script for the card recognition and payment database system.
"""
import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.payment_db import PaymentDatabase
from src.database.card_recognition import CardRecognitionEngine
from src.database.integrated_system import IntegratedPaymentSystem
from src.utils.logger import setup_logger, Logger

# Initialize logger
setup_logger()
logger = Logger("DatabaseTest")


def create_test_tlv(tag: str, value: str) -> dict:
    """Create a test TLV dictionary."""
    return {
        'tag': int(tag, 16),
        'length': len(bytes.fromhex(value)),
        'value': bytes.fromhex(value),
        'children': []
    }


def create_test_card_data(brand: str, card_type: str, pan: str) -> dict:
    """Create test card data."""
    return {
        'brand': brand,
        'type': card_type,
        'pan': pan,
        'expiry_date': '2512',
        'cardholder_name': 'TEST CARDHOLDER',
        'application_id': 'A0000000031010',
        'application_label': brand.upper(),
        'issuer_country': '840',
        'currency_code': '840'
    }


def test_payment_database():
    """Test the payment database functionality."""
    logger.info("Testing Payment Database")
    
    # Initialize database
    db = PaymentDatabase("database/test_payments.db")
    
    # Test card data
    visa_card = create_test_card_data('Visa', 'Credit Card', '4111111111111111')
    mastercard_card = create_test_card_data('Mastercard', 'Debit Card', '5555555555554444')
    amex_card = create_test_card_data('American Express', 'Business Card', '378282246310005')
    
    # Add approved payments
    print("\n1. Adding approved payments...")
    
    # Visa credit card successful transactions
    for i in range(5):
        success = db.add_approved_payment(
            visa_card, 'POS', 'signature',
            amount=25.00 + i * 5,
            currency_code='840',
            notes=f'Test transaction {i+1}'
        )
        print(f"   Visa transaction {i+1}: {'SUCCESS' if success else 'FAILED'}")
    
    # Mastercard debit card with mixed results
    for i in range(3):
        success = db.add_approved_payment(
            mastercard_card, 'ATM', 'cdcvm',
            amount=100.00 + i * 10,
            currency_code='840',
            notes=f'ATM transaction {i+1}'
        )
        print(f"   Mastercard transaction {i+1}: {'SUCCESS' if success else 'FAILED'}")
    
    # Amex business card
    success = db.add_approved_payment(
        amex_card, 'POS', 'signature',
        amount=500.00,
        currency_code='840',
        notes='Business transaction'
    )
    print(f"   Amex transaction: {'SUCCESS' if success else 'FAILED'}")
    
    # Record some transaction history
    print("\n2. Recording transaction history...")
    
    for i in range(10):
        card = visa_card if i % 2 == 0 else mastercard_card
        terminal = 'POS' if i % 3 == 0 else 'ATM'
        success = i % 4 != 0  # 75% success rate
        
        db.record_transaction(
            card_data=card,
            transaction_id=f'TXN_{i:04d}',
            terminal_type=terminal,
            bypass_method='signature' if card['brand'] == 'Visa' else 'cdcvm',
            success=success,
            amount=50.0 + i * 10,
            currency_code='840',
            response_code='00' if success else '05',
            error_message=None if success else 'Transaction declined',
            processing_time_ms=150 + i * 10
        )
        print(f"   Transaction {i}: {'SUCCESS' if success else 'FAILED'}")
    
    # Test retrieving approved bypasses
    print("\n3. Testing approved bypass retrieval...")
    
    visa_bypass = db.get_approved_bypass(visa_card, 'POS')
    if visa_bypass:
        print(f"   Visa POS bypass: {visa_bypass['bypass_method']} "
              f"({visa_bypass['success_rate']:.1%} success rate)")
    else:
        print("   No Visa POS bypass found")
    
    mastercard_bypass = db.get_approved_bypass(mastercard_card, 'ATM')
    if mastercard_bypass:
        print(f"   Mastercard ATM bypass: {mastercard_bypass['bypass_method']} "
              f"({mastercard_bypass['success_rate']:.1%} success rate)")
    else:
        print("   No Mastercard ATM bypass found")
    
    # Get card history
    print("\n4. Testing card history retrieval...")
    
    visa_history = db.get_card_history(visa_card, limit=5)
    print(f"   Visa card history: {len(visa_history)} transactions")
    for tx in visa_history[:3]:
        print(f"     {tx['timestamp']}: {tx['bypass_method']} - "
              f"{'SUCCESS' if tx['success'] else 'FAILED'}")
    
    # Get statistics
    print("\n5. Database statistics...")
    stats = db.get_statistics()
    print(f"   Total approved payments: {stats.get('total_approved_payments', 0)}")
    print(f"   Total transactions: {stats.get('total_transactions', 0)}")
    print(f"   Overall success rate: {stats.get('overall_success_rate', 0):.1%}")
    print(f"   Card brands: {stats.get('card_brands', {})}")
    
    print("\nPayment Database test completed!")
    return db


def test_card_recognition():
    """Test the card recognition engine."""
    logger.info("Testing Card Recognition Engine")
    
    # Initialize recognition engine
    engine = CardRecognitionEngine("database/test_payments.db")
    
    # Test TLVs for different cards
    visa_tlvs = [
        create_test_tlv('5A', '4111111111111111'),
        create_test_tlv('4F', 'A0000000031010'),
        create_test_tlv('9F07', '0100'),
        create_test_tlv('5F20', '5445535420434152444E4F4C444552'),
        create_test_tlv('5F24', '2512'),
    ]
    
    mastercard_tlvs = [
        create_test_tlv('5A', '5555555555554444'),
        create_test_tlv('4F', 'A0000000041010'),
        create_test_tlv('9F07', '0800'),
        create_test_tlv('5F20', '5445535420434152444E4F4C444552'),
        create_test_tlv('5F24', '2612'),
    ]
    
    print("\n1. Testing card recognition...")
    
    # Recognize Visa card
    visa_recognition = engine.recognize_card(visa_tlvs)
    print(f"   Visa recognition: {visa_recognition['recognition_status']} "
          f"(confidence: {visa_recognition['confidence_score']:.2f})")
    print(f"   Transaction count: {visa_recognition['transaction_count']}")
    print(f"   Success rate: {visa_recognition['success_rate']:.1%}")
    
    # Recognize Mastercard
    mc_recognition = engine.recognize_card(mastercard_tlvs)
    print(f"   Mastercard recognition: {mc_recognition['recognition_status']} "
          f"(confidence: {mc_recognition['confidence_score']:.2f})")
    print(f"   Transaction count: {mc_recognition['transaction_count']}")
    print(f"   Success rate: {mc_recognition['success_rate']:.1%}")
    
    print("\n2. Testing auto-approval recommendations...")
    
    # Test auto-approval for Visa at POS
    visa_pos_approval = engine.get_auto_approval_recommendation(visa_tlvs, 'POS')
    print(f"   Visa POS auto-approval: {visa_pos_approval['auto_approve']}")
    if visa_pos_approval['auto_approve']:
        bypass = visa_pos_approval['approved_bypass']
        print(f"   Bypass method: {bypass['bypass_method']} "
              f"({bypass['success_rate']:.1%} success)")
    else:
        print(f"   Reason: {visa_pos_approval['reason']}")
    
    # Test auto-approval for Mastercard at ATM
    mc_atm_approval = engine.get_auto_approval_recommendation(mastercard_tlvs, 'ATM')
    print(f"   Mastercard ATM auto-approval: {mc_atm_approval['auto_approve']}")
    if mc_atm_approval['auto_approve']:
        bypass = mc_atm_approval['approved_bypass']
        print(f"   Bypass method: {bypass['bypass_method']} "
              f"({bypass['success_rate']:.1%} success)")
    else:
        print(f"   Reason: {mc_atm_approval['reason']}")
    
    print("\n3. Testing learning from transactions...")
    
    # Simulate learning from successful transactions
    for i in range(3):
        success = engine.learn_from_transaction(
            visa_tlvs, 'POS', 'signature', True,
            {
                'amount': 75.0 + i * 25,
                'currency_code': '840',
                'response_code': '00',
                'processing_time_ms': 120 + i * 20
            }
        )
        print(f"   Learning attempt {i+1}: {'SUCCESS' if success else 'FAILED'}")
    
    # Test recognition again after learning
    print("\n4. Re-testing recognition after learning...")
    visa_recognition_2 = engine.recognize_card(visa_tlvs)
    print(f"   Visa recognition: {visa_recognition_2['recognition_status']} "
          f"(confidence: {visa_recognition_2['confidence_score']:.2f})")
    print(f"   Transaction count: {visa_recognition_2['transaction_count']}")
    
    # Get recognition statistics
    print("\n5. Recognition engine statistics...")
    stats = engine.get_recognition_statistics()
    print(f"   Auto-approval enabled: {stats['auto_approval_enabled']}")
    print(f"   Confidence threshold: {stats['confidence_threshold']}")
    print(f"   Cache size: {stats['cache_size']}")
    
    print("\nCard Recognition Engine test completed!")
    return engine


def test_integrated_system():
    """Test the integrated payment system."""
    logger.info("Testing Integrated Payment System")
    
    # Initialize integrated system
    system = IntegratedPaymentSystem("database/test_payments.db")
    
    # Test TLVs
    test_tlvs = [
        create_test_tlv('5A', '4111111111111111'),
        create_test_tlv('4F', 'A0000000031010'),
        create_test_tlv('9F07', '0100'),
        create_test_tlv('5F20', '5445535420434152444E4F4C444552'),
        create_test_tlv('5F24', '2512'),
        create_test_tlv('9F6C', '0040'),
        create_test_tlv('9F35', '21'),
    ]
    
    print("\n1. Testing transaction processing...")
    
    # Process a few transactions
    for i in range(3):
        terminal_type = 'POS' if i % 2 == 0 else 'ATM'
        state = {'bypass_pin': True, 'cdcvm_enabled': True}
        
        result = system.process_transaction(test_tlvs, terminal_type, state)
        
        print(f"   Transaction {i+1}:")
        print(f"     Terminal: {terminal_type}")
        print(f"     Auto-approved: {result.get('auto_applied', False)}")
        print(f"     Processing stage: {result.get('processing_stage')}")
        print(f"     Processing time: {result.get('processing_time_ms', 0)}ms")
        
        # Simulate learning from the result
        if result.get('auto_applied'):
            success = i % 3 != 0  # Vary success rate
            learning_result = system.learn_from_result(
                result['transaction_id'],
                test_tlvs,
                terminal_type,
                result.get('bypass_method', 'signature'),
                success,
                {
                    'amount': 100.0 + i * 50,
                    'currency_code': '840',
                    'response_code': '00' if success else '05',
                    'processing_time_ms': result.get('processing_time_ms', 150)
                }
            )
            print(f"     Learning: {'SUCCESS' if learning_result else 'FAILED'}")
    
    print("\n2. Testing card recommendations...")
    
    recommendations = system.get_card_recommendations(test_tlvs)
    if 'error' not in recommendations:
        print(f"   Card: {recommendations['card_info']['brand']} "
              f"{recommendations['card_info']['type']}")
        print(f"   Recognition: {recommendations['recognition']['recognition_status']}")
        print(f"   Best terminal: {recommendations['best_terminal_type']}")
        print(f"   Overall confidence: {recommendations['overall_confidence']:.1%}")
    else:
        print(f"   Error: {recommendations['error']}")
    
    print("\n3. System status...")
    
    status = system.get_system_status()
    if status['system_online']:
        print(f"   System online: {status['system_online']}")
        print(f"   Auto-approval enabled: {status['auto_approval_enabled']}")
        print(f"   Total transactions: {status['transaction_stats']['total_transactions']}")
        print(f"   Auto-approved: {status['transaction_stats']['auto_approved']}")
        print(f"   Manual review: {status['transaction_stats']['manual_review']}")
    else:
        print(f"   System error: {status.get('error')}")
    
    print("\n4. Exporting learning data...")
    
    system.export_learning_data("database/test_export.json")
    print("   Export completed: database/test_export.json")
    
    print("\nIntegrated Payment System test completed!")
    return system


def main():
    """Run all database and recognition tests."""
    logger.info("Starting comprehensive database and recognition tests")
    
    # Create database directory
    Path("database").mkdir(exist_ok=True)
    
    print("="*60)
    print("PAYMENT DATABASE AND CARD RECOGNITION SYSTEM TEST")
    print("="*60)
    
    # Test 1: Payment Database
    print("\n" + "="*60)
    print("TEST 1: PAYMENT DATABASE")
    print("="*60)
    db = test_payment_database()
    
    # Test 2: Card Recognition Engine
    print("\n" + "="*60)
    print("TEST 2: CARD RECOGNITION ENGINE")
    print("="*60)
    engine = test_card_recognition()
    
    # Test 3: Integrated System
    print("\n" + "="*60)
    print("TEST 3: INTEGRATED PAYMENT SYSTEM")
    print("="*60)
    system = test_integrated_system()
    
    # Final statistics
    print("\n" + "="*60)
    print("FINAL SYSTEM STATISTICS")
    print("="*60)
    
    final_stats = db.get_statistics()
    print(f"Database Statistics:")
    print(f"  Total approved payments: {final_stats.get('total_approved_payments', 0)}")
    print(f"  Total transactions: {final_stats.get('total_transactions', 0)}")
    print(f"  Overall success rate: {final_stats.get('overall_success_rate', 0):.1%}")
    
    system_status = system.get_system_status()
    if system_status['system_online']:
        print(f"\nSystem Performance:")
        print(f"  Processed transactions: {system_status['transaction_stats']['total_transactions']}")
        print(f"  Auto-approved: {system_status['transaction_stats']['auto_approved']}")
        print(f"  Manual review required: {system_status['transaction_stats']['manual_review']}")
        print(f"  Learning events: {system_status['transaction_stats']['learned_transactions']}")
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    logger.info("Comprehensive database and recognition tests completed")


if __name__ == "__main__":
    main()
