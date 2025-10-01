"""
Integration script for card recognition and auto-approval with the main system.
"""
import os
import sys
import time
import json
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.card_recognition import CardRecognitionEngine
from src.database.payment_db import PaymentDatabase
from src.mitm.bypass_engine import get_comprehensive_card_info
from src.utils.logger import setup_logger, Logger

# Initialize logger
setup_logger()
logger = Logger("IntegratedSystem")


class IntegratedPaymentSystem:
    """Integrated system combining bypass engine with card recognition and learning."""
    
    def __init__(self, db_path: str = "database/payments.db"):
        """
        Initialize the integrated payment system.
        
        Args:
            db_path: Path to the payment database
        """
        self.db = PaymentDatabase(db_path)
        self.recognition_engine = CardRecognitionEngine(db_path)
        self.stats = {
            'total_transactions': 0,
            'auto_approved': 0,
            'manual_review': 0,
            'learned_transactions': 0
        }
        
        logger.info("Integrated payment system initialized")
    
    def process_transaction(self, tlvs: List[Dict[str, Any]], terminal_type: str,
                          state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a complete transaction with recognition and auto-approval.
        
        Args:
            tlvs: TLV data from card
            terminal_type: Terminal type (POS/ATM)
            state: Current MITM state
            
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        transaction_id = self._generate_transaction_id()
        
        try:
            logger.info(f"Processing transaction {transaction_id}")
            
            # Step 1: Recognize the card
            recognition_result = self.recognition_engine.recognize_card(tlvs)
            card_info = recognition_result['card_info']
            
            logger.info(f"Card recognized: {card_info['brand']} {card_info['type']} "
                       f"(confidence: {recognition_result['confidence_score']:.2f})")
            
            # Step 2: Check for auto-approval
            auto_approval = self.recognition_engine.get_auto_approval_recommendation(tlvs, terminal_type)
            
            result = {
                'transaction_id': transaction_id,
                'timestamp': time.time(),
                'card_recognition': recognition_result,
                'auto_approval_recommendation': auto_approval,
                'processing_stage': 'recognition_complete'
            }
            
            # Step 3: Apply auto-approval if recommended
            if auto_approval['auto_approve']:
                modified_tlvs, approval_result = self.recognition_engine.apply_auto_approval(
                    tlvs, terminal_type, state
                )
                
                result.update({
                    'auto_applied': True,
                    'modified_tlvs': modified_tlvs,
                    'approval_result': approval_result,
                    'bypass_method': approval_result.get('bypass_method'),
                    'processing_stage': 'auto_approved'
                })
                
                self.stats['auto_approved'] += 1
                logger.info(f"Transaction {transaction_id} auto-approved using {approval_result.get('bypass_method')}")
                
            else:
                result.update({
                    'auto_applied': False,
                    'manual_review_required': True,
                    'reason': auto_approval.get('reason'),
                    'processing_stage': 'manual_review_required'
                })
                
                self.stats['manual_review'] += 1
                logger.info(f"Transaction {transaction_id} requires manual review: {auto_approval.get('reason')}")
            
            # Step 4: Update statistics
            self.stats['total_transactions'] += 1
            result['processing_time_ms'] = int((time.time() - start_time) * 1000)
            result['system_stats'] = self.stats.copy()
            
            return result
            
        except Exception as e:
            logger.error(f"Transaction processing failed: {e}")
            return {
                'transaction_id': transaction_id,
                'error': str(e),
                'processing_stage': 'error',
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
    
    def learn_from_result(self, transaction_id: str, tlvs: List[Dict[str, Any]], 
                         terminal_type: str, bypass_method: str, success: bool,
                         response_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Learn from a transaction result.
        
        Args:
            transaction_id: Transaction identifier
            tlvs: TLV data
            terminal_type: Terminal type
            bypass_method: Bypass method used
            success: Whether transaction succeeded
            response_data: Additional response data
            
        Returns:
            True if learning was successful
        """
        try:
            # Learn from the transaction
            learned = self.recognition_engine.learn_from_transaction(
                tlvs, terminal_type, bypass_method, success, response_data or {}
            )
            
            if learned:
                self.stats['learned_transactions'] += 1
                logger.info(f"Learned from transaction {transaction_id}: "
                           f"{'SUCCESS' if success else 'FAILURE'}")
            
            return learned
            
        except Exception as e:
            logger.error(f"Learning from transaction {transaction_id} failed: {e}")
            return False
    
    def get_card_recommendations(self, tlvs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get comprehensive recommendations for a card.
        
        Args:
            tlvs: TLV data from card
            
        Returns:
            Dictionary with recommendations
        """
        try:
            # Get card recognition
            recognition = self.recognition_engine.recognize_card(tlvs)
            card_info = recognition['card_info']
            
            # Get recommendations for both terminal types
            pos_recommendation = self.recognition_engine.get_auto_approval_recommendation(tlvs, 'POS')
            atm_recommendation = self.recognition_engine.get_auto_approval_recommendation(tlvs, 'ATM')
            
            # Get transaction history
            history = self.db.get_card_history(card_info, limit=10)
            
            return {
                'card_info': card_info,
                'recognition': recognition,
                'recommendations': {
                    'POS': pos_recommendation,
                    'ATM': atm_recommendation
                },
                'transaction_history': history,
                'best_terminal_type': 'POS' if pos_recommendation.get('auto_approve') else 'ATM' if atm_recommendation.get('auto_approve') else 'manual',
                'overall_confidence': max(
                    pos_recommendation.get('approved_bypass', {}).get('success_rate', 0),
                    atm_recommendation.get('approved_bypass', {}).get('success_rate', 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get card recommendations: {e}")
            return {'error': str(e)}
    
    def export_learning_data(self, output_file: str = "learning_export.json"):
        """
        Export learning data for analysis.
        
        Args:
            output_file: Output file path
        """
        try:
            # Get database statistics
            db_stats = self.db.get_statistics()
            recognition_stats = self.recognition_engine.get_recognition_statistics()
            
            export_data = {
                'export_timestamp': time.time(),
                'system_stats': self.stats,
                'database_stats': db_stats,
                'recognition_stats': recognition_stats,
                'version': '1.0.0'
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Learning data exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export learning data: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dictionary with system status
        """
        try:
            db_stats = self.db.get_statistics()
            recognition_stats = self.recognition_engine.get_recognition_statistics()
            
            return {
                'system_online': True,
                'auto_approval_enabled': self.recognition_engine.auto_approval_enabled,
                'confidence_threshold': self.recognition_engine.confidence_threshold,
                'transaction_stats': self.stats,
                'database_stats': db_stats,
                'recognition_stats': recognition_stats,
                'cache_size': len(self.recognition_engine.recognition_cache)
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'system_online': False, 'error': str(e)}
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        import uuid
        return f"TXN_{int(time.time())}_{str(uuid.uuid4())[:8]}"


def main():
    """Main function for testing the integrated system."""
    logger.info("Starting integrated payment system test")
    
    # Initialize system
    system = IntegratedPaymentSystem()
    
    # Test card data (example TLVs)
    test_tlvs = [
        {
            'tag': 0x5A,
            'length': 8,
            'value': bytes.fromhex('4111111111111111'),
            'children': []
        },
        {
            'tag': 0x4F,
            'length': 7,
            'value': bytes.fromhex('A0000000031010'),
            'children': []
        },
        {
            'tag': 0x9F07,
            'length': 2,
            'value': bytes.fromhex('0100'),
            'children': []
        }
    ]
    
    # Test processing
    result = system.process_transaction(test_tlvs, 'POS', {'bypass_pin': True})
    print(f"Processing result: {json.dumps(result, indent=2, default=str)}")
    
    # Test learning (simulate successful transaction)
    if result.get('auto_applied'):
        learning_result = system.learn_from_result(
            result['transaction_id'], 
            test_tlvs, 
            'POS', 
            result.get('bypass_method', 'signature'),
            True,
            {'amount': 25.00, 'currency_code': '840', 'response_code': '00'}
        )
        print(f"Learning result: {learning_result}")
    
    # Get system status
    status = system.get_system_status()
    print(f"System status: {json.dumps(status, indent=2, default=str)}")
    
    # Export data
    system.export_learning_data("test_export.json")
    
    logger.info("Integrated payment system test completed")


if __name__ == "__main__":
    main()
