#!/usr/bin/env python3
"""
🏦 Comprehensive Credit Card Structures
Complete implementation of credit card data structures, EMV standards, and TLV data
"""

import random
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json

class CreditCardTypes:
    """Comprehensive credit card type definitions with industry standards"""
    
    CARD_TYPES = {
        'Visa': {
            'bin_ranges': [
                '4000', '4111', '4444', '4567', '4712', '4999',
                '4001', '4003', '4005', '4007', '4009', '4011'
            ],
            'aid': 'A0000000031010',
            'application_label': 'VISA',
            'application_preferred_name': 'VISA CREDIT',
            'kernel_id': '01',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '01',
            'application_version': '0008',
            'pan_length': 16,
            'cvv_length': 3,
            'supported_features': ['contactless', 'chip', 'magstripe', 'online', 'offline'],
            'verification_methods': ['PIN', 'Signature', 'No CVM', 'CDCVM'],
            'transaction_limits': {
                'contactless_limit': 10000,  # $100.00 in cents
                'offline_limit': 5000,       # $50.00 in cents
                'floor_limit': 0
            }
        },
        'Mastercard': {
            'bin_ranges': [
                '5100', '5200', '5300', '5400', '5500', '2720',
                '5101', '5102', '5103', '5104', '5105', '2721'
            ],
            'aid': 'A0000000041010',
            'application_label': 'MASTERCARD',
            'application_preferred_name': 'MASTERCARD CREDIT',
            'kernel_id': '02',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '02',
            'application_version': '0002',
            'pan_length': 16,
            'cvv_length': 3,
            'supported_features': ['contactless', 'chip', 'magstripe', 'online', 'offline'],
            'verification_methods': ['PIN', 'Signature', 'No CVM', 'CDCVM'],
            'transaction_limits': {
                'contactless_limit': 10000,  # $100.00 in cents
                'offline_limit': 5000,       # $50.00 in cents
                'floor_limit': 0
            }
        },
        'American Express': {
            'bin_ranges': [
                '3400', '3700', '3780', '3701', '3702', '3703'
            ],
            'aid': 'A000000025010801',
            'application_label': 'AMERICAN EXPRESS',
            'application_preferred_name': 'AMEX CREDIT',
            'kernel_id': '03',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '03',
            'application_version': '0001',
            'pan_length': 15,
            'cvv_length': 4,
            'supported_features': ['contactless', 'chip', 'magstripe', 'online'],
            'verification_methods': ['PIN', 'Signature', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 20000,  # $200.00 in cents
                'offline_limit': 10000,      # $100.00 in cents
                'floor_limit': 0
            }
        },
        'Discover': {
            'bin_ranges': [
                '6011', '6500', '6550', '6012', '6013', '6501'
            ],
            'aid': 'A0000001523010',
            'application_label': 'DISCOVER',
            'application_preferred_name': 'DISCOVER CREDIT',
            'kernel_id': '04',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '04',
            'application_version': '0001',
            'pan_length': 16,
            'cvv_length': 3,
            'supported_features': ['contactless', 'chip', 'magstripe', 'online', 'offline'],
            'verification_methods': ['PIN', 'Signature', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 10000,  # $100.00 in cents
                'offline_limit': 5000,       # $50.00 in cents
                'floor_limit': 0
            }
        },
        'JCB': {
            'bin_ranges': [
                '3528', '3589', '3529', '3530', '3531', '3532'
            ],
            'aid': 'A0000000651010',
            'application_label': 'JCB',
            'application_preferred_name': 'JCB CREDIT',
            'kernel_id': '05',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0392',  # JPY
            'country_code': '0392',
            'issuer_code_table_index': '05',
            'application_version': '0001',
            'pan_length': 16,
            'cvv_length': 3,
            'supported_features': ['contactless', 'chip', 'magstripe', 'online'],
            'verification_methods': ['PIN', 'Signature', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 10000,  # ¥10,000 in yen
                'offline_limit': 5000,       # ¥5,000 in yen
                'floor_limit': 0
            }
        },
        'UnionPay': {
            'bin_ranges': [
                '6200', '6220', '6240', '6201', '6202', '6221'
            ],
            'aid': 'A000000333010101',
            'application_label': 'UNIONPAY',
            'application_preferred_name': 'UNIONPAY CREDIT',
            'kernel_id': '06',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0156',  # CNY
            'country_code': '0156',
            'issuer_code_table_index': '06',
            'application_version': '0001',
            'pan_length': 16,
            'cvv_length': 3,
            'supported_features': ['contactless', 'chip', 'magstripe', 'online'],
            'verification_methods': ['PIN', 'Signature', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 30000,  # ¥300 in yuan
                'offline_limit': 15000,      # ¥150 in yuan
                'floor_limit': 0
            }
        },
        'Diners Club': {
            'bin_ranges': [
                '3000', '3010', '3020', '3001', '3002', '3011'
            ],
            'aid': 'A0000001523010',
            'application_label': 'DINERS CLUB',
            'application_preferred_name': 'DINERS CREDIT',
            'kernel_id': '07',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '07',
            'application_version': '0001',
            'pan_length': 14,
            'cvv_length': 3,
            'supported_features': ['chip', 'magstripe', 'online'],
            'verification_methods': ['PIN', 'Signature'],
            'transaction_limits': {
                'contactless_limit': 0,      # Not supported
                'offline_limit': 10000,      # $100.00 in cents
                'floor_limit': 0
            }
        },
        'Maestro': {
            'bin_ranges': [
                '5018', '5020', '5038', '5893', '6304', '6759'
            ],
            'aid': 'A0000000043060',
            'application_label': 'MAESTRO',
            'application_preferred_name': 'MAESTRO DEBIT',
            'kernel_id': '08',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0978',  # EUR
            'country_code': '0276',
            'issuer_code_table_index': '08',
            'application_version': '0001',
            'pan_length': 16,
            'cvv_length': 3,
            'card_category': 'debit',
            'supported_features': ['contactless', 'chip', 'magstripe', 'online'],
            'verification_methods': ['PIN', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 5000,   # €50.00 in cents
                'offline_limit': 2500,       # €25.00 in cents
                'floor_limit': 0
            }
        },
        
        # DEBIT CARD TYPES
        'Visa Debit': {
            'bin_ranges': [
                '4000', '4111', '4567', '4571', '4631', '4988'
            ],
            'aid': 'A0000000032010',
            'application_label': 'VISA DEBIT',
            'application_preferred_name': 'VISA DEBIT',
            'kernel_id': '01',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '01',
            'application_version': '0008',
            'pan_length': 16,
            'cvv_length': 3,
            'card_category': 'debit',
            'supported_features': ['contactless', 'chip', 'magstripe', 'online', 'pin_required'],
            'verification_methods': ['PIN', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 5000,   # $50.00 in cents
                'offline_limit': 0,          # No offline for debit
                'floor_limit': 0,
                'daily_limit': 50000,        # $500.00 daily limit
                'pin_required_above': 2500   # $25.00
            }
        },
        'Mastercard Debit': {
            'bin_ranges': [
                '5101', '5200', '5300', '5555', '5434', '2223'
            ],
            'aid': 'A0000000043060',
            'application_label': 'MASTERCARD DEBIT',
            'application_preferred_name': 'MASTERCARD DEBIT',
            'kernel_id': '02',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '02',
            'application_version': '0002',
            'pan_length': 16,
            'cvv_length': 3,
            'card_category': 'debit',
            'supported_features': ['contactless', 'chip', 'magstripe', 'online', 'pin_required'],
            'verification_methods': ['PIN', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 5000,   # $50.00 in cents
                'offline_limit': 0,          # No offline for debit
                'floor_limit': 0,
                'daily_limit': 50000,        # $500.00 daily limit
                'pin_required_above': 2500   # $25.00
            }
        },
        
        # PREPAID CARD TYPES
        'Visa Prepaid': {
            'bin_ranges': [
                '4003', '4571', '4744', '4847', '4917', '4929'
            ],
            'aid': 'A0000000031010',
            'application_label': 'VISA PREPAID',
            'application_preferred_name': 'VISA PREPAID',
            'kernel_id': '01',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '01',
            'application_version': '0008',
            'pan_length': 16,
            'cvv_length': 3,
            'card_category': 'prepaid',
            'supported_features': ['contactless', 'chip', 'magstripe', 'online', 'balance_inquiry'],
            'verification_methods': ['PIN', 'Signature', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 10000,  # $100.00 in cents
                'offline_limit': 2500,       # $25.00 in cents
                'floor_limit': 0,
                'max_balance': 500000,       # $5000.00 maximum balance
                'reload_limit': 200000       # $2000.00 per reload
            }
        },
        'Mastercard Prepaid': {
            'bin_ranges': [
                '5555', '5103', '5204', '5301', '5431', '2221'
            ],
            'aid': 'A0000000041010',
            'application_label': 'MASTERCARD PREPAID',
            'application_preferred_name': 'MASTERCARD PREPAID',
            'kernel_id': '02',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '02',
            'application_version': '0002',
            'pan_length': 16,
            'cvv_length': 3,
            'card_category': 'prepaid',
            'supported_features': ['contactless', 'chip', 'magstripe', 'online', 'balance_inquiry'],
            'verification_methods': ['PIN', 'Signature', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 10000,  # $100.00 in cents
                'offline_limit': 2500,       # $25.00 in cents
                'floor_limit': 0,
                'max_balance': 500000,       # $5000.00 maximum balance
                'reload_limit': 200000       # $2000.00 per reload
            }
        },
        'American Express Prepaid': {
            'bin_ranges': [
                '3782', '3787', '3797', '3716', '3714', '3717'
            ],
            'aid': 'A000000025010801',
            'application_label': 'AMERICAN EXPRESS PREPAID',
            'application_preferred_name': 'AMEX PREPAID',
            'kernel_id': '03',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '03',
            'application_version': '0001',
            'pan_length': 15,
            'cvv_length': 4,
            'card_category': 'prepaid',
            'supported_features': ['contactless', 'chip', 'magstripe', 'online', 'balance_inquiry'],
            'verification_methods': ['PIN', 'Signature', 'No CVM'],
            'transaction_limits': {
                'contactless_limit': 15000,  # $150.00 in cents
                'offline_limit': 5000,       # $50.00 in cents
                'floor_limit': 0,
                'max_balance': 1000000,      # $10000.00 maximum balance
                'reload_limit': 300000       # $3000.00 per reload
            }
        },
        'Gift Card Prepaid': {
            'bin_ranges': [
                '6040', '6042', '6043', '6044', '6045', '6046'
            ],
            'aid': 'A0000001523010',
            'application_label': 'GIFT CARD',
            'application_preferred_name': 'GIFT CARD',
            'kernel_id': '04',
            'terminal_type': '22',
            'capabilities': 'E0F8C8',
            'currency_code': '0840',  # USD
            'country_code': '0840',
            'issuer_code_table_index': '04',
            'application_version': '0001',
            'pan_length': 16,
            'cvv_length': 3,
            'card_category': 'prepaid',
            'supported_features': ['contactless', 'chip', 'magstripe', 'online', 'balance_inquiry'],
            'verification_methods': ['No CVM'],
            'transaction_limits': {
                'contactless_limit': 50000,  # $500.00 in cents
                'offline_limit': 10000,      # $100.00 in cents
                'floor_limit': 0,
                'max_balance': 100000,       # $1000.00 maximum balance
                'reload_limit': 0            # No reload for gift cards
            }
        }
    }

class EMVTags:
    """Comprehensive EMV tag definitions"""
    
    TAGS = {
        # Application Selection Tags
        '4F': 'Application Identifier (AID)',
        '50': 'Application Label',
        '84': 'Dedicated File (DF) Name',
        '87': 'Application Priority Indicator',
        '88': 'Short File Identifier (SFI)',
        
        # Cardholder Data Tags
        '5A': 'Application Primary Account Number (PAN)',
        '5F20': 'Cardholder Name',
        '5F24': 'Application Expiration Date',
        '5F25': 'Application Effective Date',
        '5F30': 'Service Code',
        '5F34': 'Application PAN Sequence Number',
        
        # Issuer Data Tags
        '5F28': 'Issuer Country Code',
        '5F50': 'Issuer URL',
        '5F53': 'International Bank Account Number (IBAN)',
        '5F54': 'Bank Identifier Code (BIC)',
        
        # Application Data Tags
        '82': 'Application Interchange Profile',
        '8C': 'Card Risk Management Data Object List 1 (CDOL1)',
        '8D': 'Card Risk Management Data Object List 2 (CDOL2)',
        '8E': 'Cardholder Verification Method (CVM) List',
        '8F': 'Certification Authority Public Key Index',
        
        # Cryptographic Tags
        '90': 'Issuer Public Key Certificate',
        '92': 'Issuer Public Key Remainder',
        '93': 'Signed Static Application Data',
        '9F46': 'ICC Public Key Certificate',
        '9F47': 'ICC Public Key Exponent',
        '9F48': 'ICC Public Key Remainder',
        '9F4B': 'Signed Dynamic Application Data',
        
        # Transaction Data Tags
        '5F2A': 'Transaction Currency Code',
        '9A': 'Transaction Date',
        '9C': 'Transaction Type',
        '9F02': 'Amount, Authorized (Numeric)',
        '9F03': 'Amount, Other (Numeric)',
        '9F21': 'Transaction Time',
        '9F37': 'Unpredictable Number',
        '9F41': 'Transaction Sequence Counter',
        
        # Terminal Data Tags
        '9F01': 'Acquirer Country Code',
        '9F1A': 'Terminal Country Code',
        '9F1C': 'Terminal Identification',
        '9F1E': 'Interface Device (IFD) Serial Number',
        '9F33': 'Terminal Capabilities',
        '9F35': 'Terminal Type',
        '9F40': 'Additional Terminal Capabilities',
        
        # Application Control Tags
        '9F06': 'Application Identifier (AID) - terminal',
        '9F07': 'Application Usage Control',
        '9F08': 'Application Version Number',
        '9F09': 'Application Version Number (Terminal)',
        '9F0D': 'Issuer Action Code - Default',
        '9F0E': 'Issuer Action Code - Denial',
        '9F0F': 'Issuer Action Code - Online',
        
        # Cryptogram and Authentication Tags
        '9F26': 'Application Cryptogram',
        '9F27': 'Cryptogram Information Data',
        '9F36': 'Application Transaction Counter (ATC)',
        '9F4C': 'ICC Dynamic Number',
        
        # Custom/Proprietary Tags
        'DF01': 'Application PAN Suffix',
        'DF02': 'Transaction Timestamp',
        'DF03': 'Device ID',
        'DF04': 'Card UID',
        'DF05': 'Card Brand',
        'DF06': 'Card Sequence Number',
        'DF07': 'Issuer Script Template',
        'DF08': 'Application Cryptogram Type',
        'DF09': 'Terminal Risk Management Data',
        'DF0A': 'Card Authentication Data'
    }

class CreditCardGenerator:
    """Comprehensive credit card data generator"""
    
    @staticmethod
    def luhn_checksum(card_num: str) -> int:
        """Calculate Luhn checksum for card number validation"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10
    
    @staticmethod
    def generate_pan(card_type: str) -> str:
        """Generate a valid PAN with Luhn checksum"""
        if card_type not in CreditCardTypes.CARD_TYPES:
            raise ValueError(f"Unsupported card type: {card_type}")
        
        config = CreditCardTypes.CARD_TYPES[card_type]
        bin_range = random.choice(config['bin_ranges'])
        pan_length = config['pan_length']
        
        # Generate remaining digits (excluding checksum)
        remaining_digits = pan_length - len(bin_range) - 1
        pan_digits = bin_range + ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
        
        # Calculate and append Luhn checksum
        checksum = (10 - CreditCardGenerator.luhn_checksum(pan_digits)) % 10
        return pan_digits + str(checksum)
    
    @staticmethod
    def generate_expiry_date() -> str:
        """Generate a realistic expiry date (MMYY format)"""
        current_date = datetime.now()
        future_date = current_date + timedelta(days=random.randint(365, 1825))  # 1-5 years
        return future_date.strftime('%m%y')
    
    @staticmethod
    def generate_service_code() -> str:
        """Generate a realistic service code"""
        # First digit: Interchange and technology
        first_digit = random.choice(['1', '2', '5', '6', '7'])  # Common service codes
        
        # Second digit: Authorization processing
        second_digit = random.choice(['0', '2', '4'])
        
        # Third digit: Allowed services
        third_digit = random.choice(['0', '1', '3', '5', '7'])
        
        return first_digit + second_digit + third_digit
    
    @staticmethod
    def generate_cvv(card_type: str) -> str:
        """Generate CVV based on card type"""
        config = CreditCardTypes.CARD_TYPES[card_type]
        cvv_length = config['cvv_length']
        return ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])
    
    @staticmethod
    def generate_comprehensive_tlv_data(card_data: Dict[str, Any], card_config: Dict[str, Any]) -> str:
        """Generate comprehensive TLV data for EMV compliance"""
        pan = card_data['pan']
        card_type = card_data['card_type']
        
        tlv_tags = [
            # Application Selection
            ('4F', card_config['aid']),
            ('50', card_config['application_label']),
            ('84', card_config['aid']),
            ('87', '01'),  # Application Priority Indicator
            ('88', '01'),  # Short File Identifier
            
            # Cardholder Data
            ('5A', pan),
            ('5F20', f"{card_type} CARDHOLDER"),
            ('5F24', card_data['expiry_date']),
            ('5F25', card_data['expiry_date'][:2]),
            ('5F30', card_data['service_code']),
            ('5F34', pan[-4:]),
            
            # Issuer Data
            ('5F28', card_config['country_code']),
            
            # Application Data
            ('82', '5800'),  # Application Interchange Profile
            ('8C', '9F02069F03069F1A0295055F2A029A039C019F37049F35019F45029F4C089F34038D0C910A8A0295059F37049F4C08'),
            ('8D', '910A8A0295059F37049F4C08'),
            ('8E', '000000000000000042031E031F00'),
            ('8F', '01'),
            
            # Cryptographic Data
            ('90', ''.join([f"{random.randint(0, 255):02X}" for _ in range(64)])),
            ('92', ''.join([f"{random.randint(0, 255):02X}" for _ in range(32)])),
            ('93', ''.join([f"{random.randint(0, 255):02X}" for _ in range(64)])),
            ('9F46', ''.join([f"{random.randint(0, 255):02X}" for _ in range(64)])),
            ('9F47', '03'),
            ('9F48', ''.join([f"{random.randint(0, 255):02X}" for _ in range(32)])),
            ('9F4B', ''.join([f"{random.randint(0, 255):02X}" for _ in range(32)])),
            
            # Transaction Data
            ('5F2A', card_config['currency_code']),
            ('9A', datetime.now().strftime('%y%m%d')),
            ('9C', '00'),  # Transaction Type (Purchase)
            ('9F02', '000000001000'),  # Amount Authorized
            ('9F03', '000000000000'),  # Amount Other
            ('9F21', datetime.now().strftime('%H%M%S')),
            ('9F37', ''.join([f"{random.randint(0, 255):02X}" for _ in range(4)])),
            ('9F41', f"{random.randint(1, 9999):04d}"),
            
            # Terminal Data
            ('9F01', card_config['country_code']),
            ('9F1A', card_config['country_code']),
            ('9F1C', '00000000'),
            ('9F1E', '0000000000000000'),
            ('9F33', card_config['capabilities']),
            ('9F35', card_config['terminal_type']),
            ('9F40', 'F000F0A001'),
            
            # Application Control
            ('9F06', card_config['aid']),
            ('9F07', 'FF00'),
            ('9F08', card_config['application_version']),
            ('9F09', '008C'),
            ('9F0D', 'F040AC8000'),
            ('9F0E', '0000000000'),
            ('9F0F', 'F040ACA000'),
            
            # Cryptogram and Authentication
            ('9F26', ''.join([f"{random.randint(0, 255):02X}" for _ in range(8)])),
            ('9F27', '80'),
            ('9F36', ''.join([f"{random.randint(0, 255):02X}" for _ in range(2)])),
            ('9F4C', ''.join([f"{random.randint(0, 255):02X}" for _ in range(8)])),
            
            # Custom Tags
            ('DF01', pan[-4:]),
            ('DF02', datetime.now().strftime('%Y%m%d%H%M%S')),
            ('DF03', card_data.get('device_id', 'UNKNOWN')),
            ('DF04', card_data['uid']),
            ('DF05', card_type),
            ('DF06', f"{random.randint(1, 999):03d}"),
            ('DF07', ''),  # Issuer Script Template (empty)
            ('DF08', 'TC'),  # Transaction Certificate
            ('DF09', '00000000'),  # Terminal Risk Management Data
            ('DF0A', ''.join([f"{random.randint(0, 255):02X}" for _ in range(16)])),  # Card Authentication Data
        ]
        
        return '|'.join([f"{tag}:{value}" for tag, value in tlv_tags if value])
    
    @staticmethod
    def generate_track_data(pan: str, card_type: str, expiry_date: str, service_code: str) -> Tuple[str, str]:
        """Generate Track 1 and Track 2 data"""
        cardholder_name = f"{card_type} CARDHOLDER"
        
        # Track 1 Format: %B<PAN>^<Name>^<Expiry><Service Code><Discretionary Data>?
        track1 = f"%B{pan}^{cardholder_name}^{expiry_date}{service_code}00000000000000000000?"
        
        # Track 2 Format: ;<PAN>=<Expiry><Service Code><Discretionary Data>?
        track2 = f";{pan}={expiry_date}{service_code}00000000000000000000?"
        
        return track1, track2
    
    @staticmethod
    def create_comprehensive_card(card_type: Optional[str] = None, custom_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a comprehensive credit card with all data structures"""
        # Select random card type if not specified
        if not card_type or card_type not in CreditCardTypes.CARD_TYPES:
            card_type = random.choice(list(CreditCardTypes.CARD_TYPES.keys()))
        
        card_config = CreditCardTypes.CARD_TYPES[card_type]
        
        # Generate basic card data
        pan = CreditCardGenerator.generate_pan(card_type)
        expiry_date = CreditCardGenerator.generate_expiry_date()
        service_code = CreditCardGenerator.generate_service_code()
        cvv = CreditCardGenerator.generate_cvv(card_type)
        
        # Create comprehensive card data structure
        card_data = {
            # Basic Card Information
            'uid': ''.join([f"{random.randint(0, 255):02X}" for _ in range(7)]),
            'atqa': f"{random.randint(0x0001, 0xFFFF):04X}",
            'sak': f"{random.randint(0x08, 0x28):02X}",
            'protocol': 'ISO14443A',
            'card_type': card_type,
            'pan': pan,
            'masked_pan': pan[:6] + '*' * (len(pan) - 10) + pan[-4:],
            'expiry_date': expiry_date,
            'service_code': service_code,
            'cvv': cvv,
            'cvv2': cvv,
            'icvv': CreditCardGenerator.generate_cvv(card_type),
            
            # Timestamps
            'timestamp': datetime.now().isoformat(),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'expires_at': datetime.strptime(expiry_date, '%m%y').strftime('%Y-%m-%d'),
            
            # Card Configuration
            'card_config': card_config,
            'supported_features': card_config['supported_features'],
            'verification_methods': card_config['verification_methods'],
            'transaction_limits': card_config['transaction_limits'],
            
            # Device Information
            'device_id': custom_data.get('device_id') if custom_data else f"device_{random.randint(1000, 9999)}",
            'session_id': str(uuid.uuid4())[:8],
            'reader_type': custom_data.get('reader_type') if custom_data else 'nfc_reader',
        }
        
        # Add custom data if provided
        if custom_data:
            card_data.update(custom_data)
        
        # Generate comprehensive TLV data
        card_data['tlv_data'] = CreditCardGenerator.generate_comprehensive_tlv_data(card_data, card_config)
        
        # Generate track data
        track1, track2 = CreditCardGenerator.generate_track_data(pan, card_type, expiry_date, service_code)
        card_data['track1'] = track1
        card_data['track2'] = track2
        
        # Add EMV application data
        card_data['emv_data'] = {
            'aid': card_config['aid'],
            'application_label': card_config['application_label'],
            'application_preferred_name': card_config['application_preferred_name'],
            'kernel_id': card_config['kernel_id'],
            'priority': '01',
            'application_version': card_config['application_version'],
            'terminal_capabilities': card_config['capabilities'],
            'additional_terminal_capabilities': 'F000F0A001',
            'terminal_type': card_config['terminal_type'],
            'terminal_country_code': card_config['country_code'],
            'transaction_currency_code': card_config['currency_code'],
            'acquirer_country_code': card_config['country_code'],
            'issuer_code_table_index': card_config['issuer_code_table_index']
        }
        
        # Add security features
        card_data['security_features'] = {
            'cvv': cvv,
            'cvv2': cvv,
            'icvv': card_data['icvv'],
            'pin_verification_method': random.choice(['online', 'offline', 'both']),
            'cvm_list': card_config['verification_methods'],
            'offline_auth_supported': 'offline' in card_config['supported_features'],
            'online_auth_supported': 'online' in card_config['supported_features'],
            'contactless_supported': 'contactless' in card_config['supported_features'],
            'chip_supported': 'chip' in card_config['supported_features'],
            'magstripe_supported': 'magstripe' in card_config['supported_features'],
            'dda_supported': True,  # Dynamic Data Authentication
            'sda_supported': True,  # Static Data Authentication
            'cda_supported': True   # Combined Data Authentication
        }
        
        # Add transaction data
        card_data['transaction_data'] = {
            'last_transaction_date': datetime.now().strftime('%Y%m%d'),
            'last_transaction_time': datetime.now().strftime('%H%M%S'),
            'transaction_counter': random.randint(1, 65535),
            'last_online_atc': random.randint(1, 65535),
            'pin_try_counter': 3,
            'offline_spending_amount': 0,
            'consecutive_offline_transactions': 0
        }
        
        # Add issuer data
        card_data['issuer_data'] = {
            'issuer_country_code': card_config['country_code'],
            'issuer_identification_number': pan[:6],
            'bank_name': f"{card_type} Bank",
            'product_type': 'CREDIT',
            'card_program': card_config['application_preferred_name'],
            'issuer_url': f"https://www.{card_type.lower().replace(' ', '')}.com",
            'customer_service_phone': '+1-800-555-0199'
        }
        
        return card_data

class DebitCardManager:
    """Specialized debit card management and validation"""
    
    @staticmethod
    def validate_pin_requirements(card_data: Dict[str, Any], transaction_amount: int) -> Dict[str, Any]:
        """Validate PIN requirements for debit transactions"""
        card_config = card_data.get('card_config', {})
        pin_required_above = card_config.get('transaction_limits', {}).get('pin_required_above', 0)
        
        return {
            'pin_required': transaction_amount > pin_required_above,
            'pin_required_above': pin_required_above,
            'verification_method': 'PIN' if transaction_amount > pin_required_above else 'No CVM',
            'offline_allowed': False,  # Debit cards require online authorization
            'daily_limit_check': True
        }
    
    @staticmethod
    def check_daily_limits(card_data: Dict[str, Any], transaction_amount: int, daily_spent: int = 0) -> Dict[str, Any]:
        """Check daily transaction limits for debit cards"""
        card_config = card_data.get('card_config', {})
        daily_limit = card_config.get('transaction_limits', {}).get('daily_limit', 50000)
        
        remaining_limit = daily_limit - daily_spent
        can_process = transaction_amount <= remaining_limit
        
        return {
            'can_process': can_process,
            'daily_limit': daily_limit,
            'daily_spent': daily_spent,
            'remaining_limit': remaining_limit,
            'limit_exceeded': transaction_amount > remaining_limit,
            'suggested_amount': min(transaction_amount, remaining_limit)
        }
    
    @staticmethod
    def generate_debit_specific_data(card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate debit-specific EMV data"""
        debit_data = {
            'account_type': 'checking',  # or 'savings'
            'pin_verification_required': True,
            'offline_auth_supported': False,
            'cash_back_supported': True,
            'balance_inquiry_supported': True,
            'account_selection_supported': True,
            'issuer_authentication_indicator': '02',  # Online PIN
            'cvm_capability': 'PIN_SUPPORTED',
            'application_usage_control': '0800',  # Domestic transactions only
            'issuer_action_codes': {
                'denial': '0000010000',  # Deny if offline
                'online': 'DC4000A800',  # Go online for suspicious transactions
                'default': 'DC4004A800'  # Default action
            }
        }
        
        # Add debit-specific TLV tags
        debit_tlv_additions = [
            ('9F51', '02'),  # Application Currency Code (same as terminal)
            ('DF20', '01'),  # Debit Card Indicator
            ('DF21', card_data.get('pan', '')[-4:]),  # Account Identifier
            ('DF22', '00'),  # Account Type (00=Default, 10=Savings, 20=Checking)
            ('DF23', '01')   # PIN Verification Required Flag
        ]
        
        return {
            'debit_specific': debit_data,
            'additional_tlv': debit_tlv_additions
        }

class PrepaidCardManager:
    """Specialized prepaid card management and balance handling"""
    
    @staticmethod
    def initialize_balance(card_data: Dict[str, Any], initial_balance: int = 10000) -> Dict[str, Any]:
        """Initialize prepaid card balance"""
        card_config = card_data.get('card_config', {})
        max_balance = card_config.get('transaction_limits', {}).get('max_balance', 500000)
        
        balance = min(initial_balance, max_balance)
        
        return {
            'current_balance': balance,
            'initial_balance': balance,
            'max_balance': max_balance,
            'last_balance_update': datetime.now().isoformat(),
            'balance_currency': card_config.get('currency_code', '0840'),
            'low_balance_threshold': max_balance * 0.1,  # 10% of max balance
            'balance_inquiry_count': 0
        }
    
    @staticmethod
    def process_transaction(balance_data: Dict[str, Any], transaction_amount: int, transaction_type: str = 'purchase') -> Dict[str, Any]:
        """Process prepaid card transaction with balance validation"""
        current_balance = balance_data.get('current_balance', 0)
        
        if transaction_type.lower() == 'purchase':
            if current_balance >= transaction_amount:
                new_balance = current_balance - transaction_amount
                result = {
                    'approved': True,
                    'new_balance': new_balance,
                    'transaction_amount': transaction_amount,
                    'response_code': '00',  # Approved
                    'message': 'Transaction approved'
                }
            else:
                result = {
                    'approved': False,
                    'new_balance': current_balance,
                    'transaction_amount': transaction_amount,
                    'response_code': '51',  # Insufficient funds
                    'message': f'Insufficient funds. Available: ${current_balance/100:.2f}'
                }
        elif transaction_type.lower() == 'refund':
            new_balance = current_balance + transaction_amount
            result = {
                'approved': True,
                'new_balance': new_balance,
                'transaction_amount': transaction_amount,
                'response_code': '00',  # Approved
                'message': 'Refund processed'
            }
        else:
            result = {
                'approved': False,
                'new_balance': current_balance,
                'transaction_amount': 0,
                'response_code': '12',  # Invalid transaction
                'message': 'Invalid transaction type'
            }
        
        # Add balance warnings
        if result.get('new_balance', 0) < balance_data.get('low_balance_threshold', 0):
            result['low_balance_warning'] = True
        
        result['timestamp'] = datetime.now().isoformat()
        return result
    
    @staticmethod
    def reload_balance(balance_data: Dict[str, Any], reload_amount: int, card_config: Dict[str, Any]) -> Dict[str, Any]:
        """Reload prepaid card balance"""
        current_balance = balance_data.get('current_balance', 0)
        max_balance = card_config.get('transaction_limits', {}).get('max_balance', 500000)
        reload_limit = card_config.get('transaction_limits', {}).get('reload_limit', 200000)
        
        # Check reload limits
        if reload_amount > reload_limit:
            return {
                'success': False,
                'message': f'Reload amount exceeds limit of ${reload_limit/100:.2f}',
                'response_code': '61',  # Exceeds withdrawal amount limit
                'current_balance': current_balance
            }
        
        # Check maximum balance
        new_balance = current_balance + reload_amount
        if new_balance > max_balance:
            return {
                'success': False,
                'message': f'Reload would exceed maximum balance of ${max_balance/100:.2f}',
                'response_code': '61',  # Exceeds amount limit
                'current_balance': current_balance
            }
        
        return {
            'success': True,
            'message': f'Successfully reloaded ${reload_amount/100:.2f}',
            'response_code': '00',  # Approved
            'old_balance': current_balance,
            'new_balance': new_balance,
            'reload_amount': reload_amount,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_prepaid_specific_data(card_data: Dict[str, Any], balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate prepaid-specific EMV data"""
        prepaid_data = {
            'card_type': 'prepaid',
            'balance_inquiry_supported': True,
            'reload_supported': True,
            'expiry_management': 'balance_based',
            'pin_change_supported': False,
            'international_usage': True,
            'merchant_category_restrictions': [],
            'velocity_limits': {
                'transactions_per_day': 10,
                'amount_per_day': 100000  # $1000.00
            }
        }
        
        # Add prepaid-specific TLV tags
        prepaid_tlv_additions = [
            ('DF30', '01'),  # Prepaid Card Indicator
            ('DF31', f"{balance_data.get('current_balance', 0):012d}"),  # Current Balance
            ('DF32', f"{balance_data.get('max_balance', 0):012d}"),      # Maximum Balance
            ('DF33', card_data.get('card_config', {}).get('currency_code', '0840')),  # Balance Currency
            ('DF34', '01' if balance_data.get('current_balance', 0) > 0 else '00'),   # Funds Available
            ('DF35', datetime.now().strftime('%Y%m%d')),  # Last Balance Update
        ]
        
        return {
            'prepaid_specific': prepaid_data,
            'additional_tlv': prepaid_tlv_additions,
            'balance_info': balance_data
        }

class CardCategoryManager:
    """Manager for different card categories (credit, debit, prepaid)"""
    
    @staticmethod
    def get_card_category(card_type: str) -> str:
        """Determine card category from card type"""
        if card_type in CreditCardTypes.CARD_TYPES:
            return CreditCardTypes.CARD_TYPES[card_type].get('card_category', 'credit')
        return 'credit'  # Default to credit
    
    @staticmethod
    def create_category_specific_card(card_type: str, custom_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create card with category-specific features"""
        # Generate base card
        base_card = CreditCardGenerator.create_comprehensive_card(card_type, custom_data)
        category = CardCategoryManager.get_card_category(card_type)
        
        if category == 'debit':
            # Add debit-specific features
            debit_data = DebitCardManager.generate_debit_specific_data(base_card)
            base_card.update(debit_data)
            
            # Override some transaction features for debit
            base_card['security_features']['offline_auth_supported'] = False
            base_card['security_features']['pin_verification_required'] = True
            
        elif category == 'prepaid':
            # Initialize balance for prepaid cards
            initial_balance = custom_data.get('initial_balance', 10000) if custom_data else 10000
            balance_data = PrepaidCardManager.initialize_balance(base_card, initial_balance)
            
            # Add prepaid-specific features
            prepaid_data = PrepaidCardManager.generate_prepaid_specific_data(base_card, balance_data)
            base_card.update(prepaid_data)
            
            # Add balance to the card data
            base_card['balance_data'] = balance_data
        
        # Add category to card data
        base_card['card_category'] = category
        
        return base_card
    
    @staticmethod
    def get_supported_card_types() -> Dict[str, List[str]]:
        """Get all supported card types organized by category"""
        categories = {'credit': [], 'debit': [], 'prepaid': []}
        
        for card_type, config in CreditCardTypes.CARD_TYPES.items():
            category = config.get('card_category', 'credit')
            if category in categories:
                categories[category].append(card_type)
        
        return categories

def main():
    """Test the credit card generation functionality including debit and prepaid cards"""
    print("BANK CARD COMPREHENSIVE TESTING SYSTEM")
    print("=" * 60)
    
    # Test card category organization
    supported_types = CardCategoryManager.get_supported_card_types()
    
    print(f"\nSUPPORTED CARD CATEGORIES:")
    for category, card_types in supported_types.items():
        print(f"  {category.upper()}: {len(card_types)} types")
        for card_type in card_types[:3]:  # Show first 3 of each category
            print(f"    - {card_type}")
        if len(card_types) > 3:
            print(f"    ... and {len(card_types) - 3} more")
    
    print(f"\nCREDIT CARD TESTING:")
    print("-" * 30)
    # Test credit cards
    visa_credit = CardCategoryManager.create_category_specific_card('Visa')
    print(f"  Visa Credit: {visa_credit['masked_pan']} | Category: {visa_credit['card_category']}")
    print(f"  Features: {', '.join(visa_credit['supported_features'])}")
    print(f"  Verification: {', '.join(visa_credit['verification_methods'])}")
    
    print(f"\nDEBIT CARD TESTING:")
    print("-" * 30)
    # Test debit cards
    visa_debit = CardCategoryManager.create_category_specific_card('Visa Debit')
    print(f"  Visa Debit: {visa_debit['masked_pan']} | Category: {visa_debit['card_category']}")
    print(f"  Features: {', '.join(visa_debit['supported_features'])}")
    
    # Test debit transaction limits
    test_amount = 3000  # $30.00
    pin_check = DebitCardManager.validate_pin_requirements(visa_debit, test_amount)
    print(f"  PIN Required for ${test_amount/100:.2f}: {pin_check['pin_required']}")
    
    daily_check = DebitCardManager.check_daily_limits(visa_debit, test_amount, 15000)
    print(f"  Daily Limit Check: {'PASS' if daily_check['can_process'] else 'FAIL'}")
    print(f"  Remaining Daily Limit: ${daily_check['remaining_limit']/100:.2f}")
    
    print(f"\nPREPAID CARD TESTING:")
    print("-" * 30)
    # Test prepaid cards
    visa_prepaid = CardCategoryManager.create_category_specific_card('Visa Prepaid', {'initial_balance': 25000})
    print(f"  Visa Prepaid: {visa_prepaid['masked_pan']} | Category: {visa_prepaid['card_category']}")
    
    # Test prepaid transactions
    balance_info = visa_prepaid['balance_data']
    print(f"  Initial Balance: ${balance_info['current_balance']/100:.2f}")
    
    # Test purchase
    purchase_result = PrepaidCardManager.process_transaction(balance_info, 1500, 'purchase')
    print(f"  Purchase $15.00: {'APPROVED' if purchase_result['approved'] else 'DECLINED'}")
    if purchase_result['approved']:
        print(f"  New Balance: ${purchase_result['new_balance']/100:.2f}")
    
    # Test reload
    reload_result = PrepaidCardManager.reload_balance(balance_info, 5000, visa_prepaid['card_config'])
    print(f"  Reload $50.00: {'SUCCESS' if reload_result['success'] else 'FAILED'}")
    if reload_result['success']:
        print(f"  Balance after reload: ${reload_result['new_balance']/100:.2f}")
    
    print(f"\nGIFT CARD TESTING:")
    print("-" * 30)
    # Test gift cards
    gift_card = CardCategoryManager.create_category_specific_card('Gift Card Prepaid', {'initial_balance': 5000})
    print(f"  Gift Card: {gift_card['masked_pan']} | Category: {gift_card['card_category']}")
    print(f"  Balance: ${gift_card['balance_data']['current_balance']/100:.2f}")
    print(f"  Max Balance: ${gift_card['balance_data']['max_balance']/100:.2f}")
    
    print(f"\nADVANCED FEATURES TESTING:")
    print("-" * 30)
    
    # Test EMV data for different categories
    for category in ['credit', 'debit', 'prepaid']:
        sample_cards = [card_type for card_type, config in CreditCardTypes.CARD_TYPES.items() 
                       if config.get('card_category', 'credit') == category]
        if sample_cards:
            test_card = CardCategoryManager.create_category_specific_card(sample_cards[0])
            tlv_count = len(test_card['tlv_data'].split('|'))
            print(f"  {category.title()} EMV Tags: {tlv_count} tags")
            print(f"  {category.title()} AID: {test_card['emv_data']['aid']}")
    
    # Export comprehensive sample data
    sample_data = {
        'supported_card_types': supported_types,
        'card_type_configs': CreditCardTypes.CARD_TYPES,
        'emv_tags': EMVTags.TAGS,
        'sample_cards': {
            'credit': visa_credit,
            'debit': visa_debit,
            'prepaid': visa_prepaid,
            'gift_card': gift_card
        },
        'test_results': {
            'debit_pin_check': pin_check,
            'debit_daily_limits': daily_check,
            'prepaid_purchase': purchase_result,
            'prepaid_reload': reload_result
        }
    }
    
    output_file = 'comprehensive_card_sample_data.json'
    with open(output_file, 'w') as f:
        json.dump(sample_data, f, indent=2, default=str)
    
    print(f"\nSYSTEM SUMMARY:")
    print(f"  Total Card Types: {len(CreditCardTypes.CARD_TYPES)}")
    print(f"  Credit Cards: {len(supported_types['credit'])}")
    print(f"  Debit Cards: {len(supported_types['debit'])}")
    print(f"  Prepaid Cards: {len(supported_types['prepaid'])}")
    print(f"  EMV Tags Supported: {len(EMVTags.TAGS)}")
    print(f"  Sample Data: {output_file}")
    print(f"\nSUCCESS: Comprehensive card support enabled with debit and prepaid functionality!")

if __name__ == "__main__":
    main()
