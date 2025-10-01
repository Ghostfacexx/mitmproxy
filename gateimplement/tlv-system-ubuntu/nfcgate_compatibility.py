#!/usr/bin/env python3
"""
🌐 NFCGate Client Compatibility System
Provides complete compatibility between NFC readers/emulators and Android NFCGate server
"""

import socket
import threading
import time
import json
import base64
import struct
import random
import hashlib
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NFCGateProtocol:
    """NFCGate protocol handler for Android APK compatibility"""
    
    # NFCGate message types
    MESSAGE_TYPES = {
        'INIT': 0x01,
        'NFC_DATA': 0x02,
        'STATUS': 0x03,
        'CONFIG': 0x04,
        'ERROR': 0x05,
        'HEARTBEAT': 0x06,
        'RELAY': 0x07,
        'EMULATION': 0x08
    }
    
    # NFC protocols supported
    NFC_PROTOCOLS = {
        'ISO14443A': 0x01,
        'ISO14443B': 0x02,
        'ISO15693': 0x03,
        'FELICA': 0x04,
        'MIFARE': 0x05
    }
    
    @staticmethod
    def create_message(msg_type: int, data: bytes, session_id: str = None) -> bytes:
        """Create NFCGate compatible message"""
        # NFCGate message format: [HEADER][LENGTH][SESSION_ID][TYPE][DATA][CHECKSUM]
        session_bytes = (session_id or "00000000").encode('utf-8')[:8].ljust(8, b'\x00')
        
        # Create header
        header = b'NFCG'  # Magic bytes
        length = struct.pack('<I', len(data) + 16)  # Data + session + type + checksum
        msg_type_bytes = struct.pack('<B', msg_type)
        
        # Calculate checksum
        checksum_data = session_bytes + msg_type_bytes + data
        checksum = hashlib.md5(checksum_data).digest()[:4]
        
        return header + length + session_bytes + msg_type_bytes + data + checksum
    
    @staticmethod
    def parse_message(data: bytes) -> Dict[str, Any]:
        """Parse NFCGate message"""
        try:
            if len(data) < 20:  # Minimum message size
                return None
                
            # Check magic bytes
            if data[:4] != b'NFCG':
                return None
            
            # Parse header
            length = struct.unpack('<I', data[4:8])[0]
            session_id = data[8:16].rstrip(b'\x00').decode('utf-8')
            msg_type = data[16]
            
            # Extract data and checksum
            payload_end = 17 + length - 12  # Subtract session + type + checksum
            payload = data[17:payload_end]
            checksum = data[payload_end:payload_end + 4]
            
            # Verify checksum
            expected_checksum = hashlib.md5(data[8:payload_end]).digest()[:4]
            if checksum != expected_checksum:
                logger.warning("Message checksum mismatch")
            
            return {
                'session_id': session_id,
                'type': msg_type,
                'data': payload,
                'checksum_valid': checksum == expected_checksum
            }
            
        except Exception as e:
            logger.error(f"Error parsing NFCGate message: {e}")
            return None

class NFCDevice:
    """Base class for NFC devices (readers/emulators)"""
    
    def __init__(self, device_id: str, device_type: str, capabilities: Dict[str, Any]):
        self.device_id = device_id
        self.device_type = device_type  # 'reader', 'emulator', 'relay'
        self.capabilities = capabilities
        self.is_connected = False
        self.session_id = str(uuid.uuid4())[:8]
        self.last_heartbeat = time.time()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary"""
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'capabilities': self.capabilities,
            'is_connected': self.is_connected,
            'session_id': self.session_id,
            'last_heartbeat': self.last_heartbeat
        }

class NFCReader(NFCDevice):
    """NFC Reader implementation"""
    
    def __init__(self, reader_id: str = None):
        reader_id = reader_id or f"reader_{random.randint(1000, 9999)}"
        capabilities = {
            'protocols': ['ISO14443A', 'ISO14443B', 'ISO15693'],
            'max_distance': '10cm',
            'frequency': '13.56MHz',
            'can_read': True,
            'can_write': False,
            'can_emulate': False,
            'antenna_power': 'high'
        }
        super().__init__(reader_id, 'reader', capabilities)
        
    def read_card(self) -> Dict[str, Any]:
        """Simulate card reading with comprehensive credit card data"""
        # Comprehensive credit card types with proper structure
        credit_card_types = {
            'Visa': {
                'bin_ranges': ['4000', '4111', '4444', '4567', '4712', '4999'],
                'aid': 'A0000000031010',
                'application_label': 'VISA',
                'kernel_id': '01',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            },
            'Mastercard': {
                'bin_ranges': ['5100', '5200', '5300', '5400', '5500', '2720'],
                'aid': 'A0000000041010',
                'application_label': 'MASTERCARD',
                'kernel_id': '02',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            },
            'American Express': {
                'bin_ranges': ['3400', '3700', '3780'],
                'aid': 'A000000025010801',
                'application_label': 'AMERICAN EXPRESS',
                'kernel_id': '03',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            },
            'Discover': {
                'bin_ranges': ['6011', '6500', '6550'],
                'aid': 'A0000001523010',
                'application_label': 'DISCOVER',
                'kernel_id': '04',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            },
            'JCB': {
                'bin_ranges': ['3528', '3589'],
                'aid': 'A0000000651010',
                'application_label': 'JCB',
                'kernel_id': '05',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0392',  # JPY
                'country_code': '0392'
            },
            'UnionPay': {
                'bin_ranges': ['6200', '6220', '6240'],
                'aid': 'A000000333010101',
                'application_label': 'UNIONPAY',
                'kernel_id': '06',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0156',  # CNY
                'country_code': '0156'
            },
            'Diners Club': {
                'bin_ranges': ['3000', '3010', '3020'],
                'aid': 'A0000001523010',
                'application_label': 'DINERS CLUB',
                'kernel_id': '07',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            }
        }
        
        protocols = ['ISO14443A', 'ISO14443B']
        selected_card_type = random.choice(list(credit_card_types.keys()))
        card_config = credit_card_types[selected_card_type]
        
        # Generate realistic PAN (Primary Account Number)
        bin_range = random.choice(card_config['bin_ranges'])
        pan_digits = bin_range + ''.join([str(random.randint(0, 9)) for _ in range(12)])
        
        # Calculate Luhn checksum for realistic PAN
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        pan = pan_digits + str((10 - luhn_checksum(pan_digits)) % 10)
        
        card_data = {
            'uid': ''.join([f"{random.randint(0, 255):02X}" for _ in range(7)]),
            'atqa': f"{random.randint(0x0001, 0xFFFF):04X}",
            'sak': f"{random.randint(0x08, 0x28):02X}",
            'protocol': random.choice(protocols),
            'card_type': selected_card_type,
            'pan': pan,
            'expiry_date': f"{random.randint(1, 12):02d}{random.randint(25, 35):02d}",
            'service_code': f"{random.randint(101, 999)}",
            'timestamp': datetime.now().isoformat(),
            'reader_id': self.device_id,
            'session_id': self.session_id,
            'card_config': card_config
        }
        
        # Add comprehensive TLV data for EMV compliance
        tlv_tags = [
            ('4F', card_config['aid']),  # Application Identifier (AID)
            ('50', card_config['application_label']),  # Application Label
            ('5A', pan),  # Application Primary Account Number (PAN)
            ('5F20', f"{selected_card_type} CARDHOLDER"),  # Cardholder Name
            ('5F24', card_data['expiry_date']),  # Application Expiration Date
            ('5F25', card_data['expiry_date'][:2]),  # Application Effective Date
            ('5F28', card_config['country_code']),  # Issuer Country Code
            ('5F2A', card_config['currency_code']),  # Transaction Currency Code
            ('5F30', card_data['service_code']),  # Service Code
            ('5F34', pan[-4:]),  # Application PAN Sequence Number
            ('82', '5800'),  # Application Interchange Profile
            ('84', card_config['aid']),  # Dedicated File (DF) Name
            ('87', '01'),  # Application Priority Indicator
            ('88', '01'),  # Short File Identifier
            ('8A', '3030'),  # Authorization Response Code
            ('8C', '159F02069F03069F1A0295055F2A029A039C019F37049F35019F45029F4C089F34038D0C910A8A0295059F37049F4C08'),  # Card Risk Management Data Object List 1
            ('8D', '910A8A0295059F37049F4C08'),  # Card Risk Management Data Object List 2
            ('8E', '000000000000000042031E031F00'),  # Cardholder Verification Method (CVM) List
            ('8F', '01'),  # Certification Authority Public Key Index
            ('90', ''.join([f"{random.randint(0, 255):02X}" for _ in range(64)])),  # Issuer Public Key Certificate
            ('92', ''.join([f"{random.randint(0, 255):02X}" for _ in range(32)])),  # Issuer Public Key Remainder
            ('93', ''.join([f"{random.randint(0, 255):02X}" for _ in range(64)])),  # Signed Static Application Data
            ('94', '08010100'),  # Application File Locator (AFL)
            ('95', '0000000000'),  # Terminal Verification Results
            ('9A', datetime.now().strftime('%y%m%d')),  # Transaction Date
            ('9B', 'E800'),  # Transaction Status Information
            ('9C', '00'),  # Transaction Type
            ('9F01', card_config['country_code']),  # Acquirer Country Code
            ('9F02', '000000001000'),  # Amount, Authorized (Numeric)
            ('9F03', '000000000000'),  # Amount, Other (Numeric)
            ('9F06', card_config['aid']),  # Application Identifier (AID) - terminal
            ('9F07', 'FF00'),  # Application Usage Control
            ('9F08', '0002'),  # Application Version Number
            ('9F09', '008C'),  # Application Version Number (Terminal)
            ('9F0D', 'F040AC8000'),  # Issuer Action Code - Default
            ('9F0E', '0000000000'),  # Issuer Action Code - Denial
            ('9F0F', 'F040ACA000'),  # Issuer Action Code - Online
            ('9F11', '01'),  # Issuer Code Table Index
            ('9F12', card_config['application_label']),  # Application Preferred Name
            ('9F13', '0000'),  # Last Online Application Transaction Counter (ATC) Register
            ('9F14', '0000'),  # Lower Consecutive Offline Limit
            ('9F15', '5999'),  # Merchant Category Code
            ('9F16', '0F'),  # Merchant Identifier
            ('9F17', '03'),  # Personal Identification Number (PIN) Try Counter
            ('9F18', '00'),  # Issuer Script Counter
            ('9F1A', card_config['country_code']),  # Terminal Country Code
            ('9F1C', '00000000'),  # Terminal Identification
            ('9F1E', '0000000000000000'),  # Interface Device (IFD) Serial Number
            ('9F21', datetime.now().strftime('%H%M%S')),  # Transaction Time
            ('9F26', ''.join([f"{random.randint(0, 255):02X}" for _ in range(8)])),  # Application Cryptogram
            ('9F27', '80'),  # Cryptogram Information Data
            ('9F33', card_config['capabilities']),  # Terminal Capabilities
            ('9F34', '1E0300'),  # Cardholder Verification Method (CVM) Results
            ('9F35', card_config['terminal_type']),  # Terminal Type
            ('9F36', ''.join([f"{random.randint(0, 255):02X}" for _ in range(2)])),  # Application Transaction Counter (ATC)
            ('9F37', ''.join([f"{random.randint(0, 255):02X}" for _ in range(4)])),  # Unpredictable Number
            ('9F38', '9F1A029F35019F40059F33039F1E089F03069F0206'),  # Processing Options Data Object List (PDOL)
            ('9F39', '07'),  # Point-of-Service (POS) Entry Mode
            ('9F40', 'F000F0A001'),  # Additional Terminal Capabilities
            ('9F41', f"{random.randint(1, 9999):04d}"),  # Transaction Sequence Counter
            ('9F42', card_config['currency_code']),  # Application Currency Code
            ('9F43', '000000'),  # Application Currency Exponent
            ('9F44', card_config['currency_code']),  # Application Reference Currency
            ('9F45', '00'),  # Data Authentication Code
            ('9F46', ''.join([f"{random.randint(0, 255):02X}" for _ in range(64)])),  # ICC Public Key Certificate
            ('9F47', '03'),  # ICC Public Key Exponent
            ('9F48', ''.join([f"{random.randint(0, 255):02X}" for _ in range(32)])),  # ICC Public Key Remainder
            ('9F49', '9F37049F4C08'),  # Dynamic Data Authentication Data Object List (DDOL)
            ('9F4A', '82'),  # Static Data Authentication Tag List
            ('9F4B', ''.join([f"{random.randint(0, 255):02X}" for _ in range(32)])),  # Signed Dynamic Application Data
            ('9F4C', ''.join([f"{random.randint(0, 255):02X}" for _ in range(8)])),  # ICC Dynamic Number
            ('9F4D', '0B'),  # Log Entry
            ('9F4E', '00'),  # Merchant Name and Location
            ('9F53', card_config['kernel_id']),  # Transaction Category Code/Kernel Identifier
            ('9F6E', 'F8E09800'),  # Visa Low-Value Payment (VLP) Issuer Authorisation Code
            ('DF01', pan[-4:]),  # Application PAN Suffix
            ('DF02', datetime.now().strftime('%Y%m%d%H%M%S')),  # Transaction Timestamp
            ('DF03', self.device_id),  # Reader Device ID
            ('DF04', card_data['uid']),  # Card UID
            ('DF05', selected_card_type),  # Card Brand
        ]
        
        card_data['tlv_data'] = '|'.join([f"{tag}:{value}" for tag, value in tlv_tags])
        
        # Add Track 1 and Track 2 equivalent data
        track1_data = f"%B{pan}^{selected_card_type} CARDHOLDER^{card_data['expiry_date']}{card_data['service_code']}00000000000000000000?"
        track2_data = f";{pan}={card_data['expiry_date']}{card_data['service_code']}00000000000000000000?"
        
        card_data['track1'] = track1_data
        card_data['track2'] = track2_data
        
        # Add EMV application data
        card_data['emv_data'] = {
            'aid': card_config['aid'],
            'application_label': card_config['application_label'],
            'kernel_id': card_config['kernel_id'],
            'preferred_name': card_config['application_label'],
            'priority': '01',
            'application_version': '0008',
            'terminal_capabilities': card_config['capabilities'],
            'additional_terminal_capabilities': 'F000F0A001',
            'terminal_type': card_config['terminal_type'],
            'terminal_country_code': card_config['country_code'],
            'transaction_currency_code': card_config['currency_code'],
            'acquirer_country_code': card_config['country_code']
        }
        
        # Add security features
        card_data['security_features'] = {
            'cvv': f"{random.randint(100, 999):03d}",
            'cvv2': f"{random.randint(100, 999):03d}",
            'icvv': f"{random.randint(100, 999):03d}",
            'pin_verification_method': 'online',
            'cvm_list': ['PIN', 'Signature', 'No CVM'],
            'offline_auth_supported': True,
            'online_auth_supported': True,
            'contactless_supported': True,
            'chip_supported': True,
            'magstripe_supported': True
        }
        
        return card_data

class NFCEmulator(NFCDevice):
    """NFC Emulator implementation with comprehensive credit card support"""
    
    def __init__(self, emulator_id: str = None):
        emulator_id = emulator_id or f"emulator_{random.randint(1000, 9999)}"
        capabilities = {
            'protocols': ['ISO14443A', 'ISO14443B', 'FELICA'],
            'emulation_modes': ['card', 'reader', 'relay'],
            'supported_cards': ['Visa', 'Mastercard', 'American Express', 'Discover', 'JCB', 'UnionPay', 'Diners Club'],
            'can_read': False,
            'can_write': True,
            'can_emulate': True,
            'max_concurrent': 5,
            'contactless_supported': True,
            'chip_supported': True,
            'magstripe_supported': True
        }
        super().__init__(emulator_id, 'emulator', capabilities)
        self.emulated_cards = []
        
    def create_credit_card(self, card_type: str = None, custom_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a comprehensive credit card for emulation"""
        # Use the same credit card structure as NFCReader
        credit_card_types = {
            'Visa': {
                'bin_ranges': ['4000', '4111', '4444', '4567', '4712', '4999'],
                'aid': 'A0000000031010',
                'application_label': 'VISA',
                'kernel_id': '01',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            },
            'Mastercard': {
                'bin_ranges': ['5100', '5200', '5300', '5400', '5500', '2720'],
                'aid': 'A0000000041010',
                'application_label': 'MASTERCARD',
                'kernel_id': '02',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            },
            'American Express': {
                'bin_ranges': ['3400', '3700', '3780'],
                'aid': 'A000000025010801',
                'application_label': 'AMERICAN EXPRESS',
                'kernel_id': '03',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            },
            'Discover': {
                'bin_ranges': ['6011', '6500', '6550'],
                'aid': 'A0000001523010',
                'application_label': 'DISCOVER',
                'kernel_id': '04',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            },
            'JCB': {
                'bin_ranges': ['3528', '3589'],
                'aid': 'A0000000651010',
                'application_label': 'JCB',
                'kernel_id': '05',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0392',  # JPY
                'country_code': '0392'
            },
            'UnionPay': {
                'bin_ranges': ['6200', '6220', '6240'],
                'aid': 'A000000333010101',
                'application_label': 'UNIONPAY',
                'kernel_id': '06',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0156',  # CNY
                'country_code': '0156'
            },
            'Diners Club': {
                'bin_ranges': ['3000', '3010', '3020'],
                'aid': 'A0000001523010',
                'application_label': 'DINERS CLUB',
                'kernel_id': '07',
                'terminal_type': '22',
                'capabilities': 'E0F8C8',
                'currency_code': '0840',  # USD
                'country_code': '0840'
            }
        }
        
        # Select card type
        if card_type and card_type in credit_card_types:
            selected_card_type = card_type
        else:
            selected_card_type = random.choice(list(credit_card_types.keys()))
        
        card_config = credit_card_types[selected_card_type]
        
        # Generate PAN with Luhn checksum
        bin_range = random.choice(card_config['bin_ranges'])
        pan_digits = bin_range + ''.join([str(random.randint(0, 9)) for _ in range(12)])
        
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        pan = pan_digits + str((10 - luhn_checksum(pan_digits)) % 10)
        
        # Create comprehensive card data
        card_data = {
            'uid': ''.join([f"{random.randint(0, 255):02X}" for _ in range(7)]),
            'atqa': f"{random.randint(0x0001, 0xFFFF):04X}",
            'sak': f"{random.randint(0x08, 0x28):02X}",
            'protocol': 'ISO14443A',
            'card_type': selected_card_type,
            'pan': pan,
            'expiry_date': f"{random.randint(1, 12):02d}{random.randint(25, 35):02d}",
            'service_code': f"{random.randint(101, 999)}",
            'timestamp': datetime.now().isoformat(),
            'emulator_id': self.device_id,
            'session_id': self.session_id,
            'card_config': card_config,
            'emulation_type': 'credit_card'
        }
        
        # Add custom data if provided
        if custom_data:
            card_data.update(custom_data)
        
        # Add all the comprehensive TLV data, tracks, EMV data, and security features
        # (Same as in NFCReader.read_card method)
        self._add_comprehensive_card_data(card_data, card_config, selected_card_type)
        
        return card_data
    
    def _add_comprehensive_card_data(self, card_data: Dict[str, Any], card_config: Dict[str, Any], selected_card_type: str):
        """Add comprehensive card data including TLV, tracks, EMV, and security features"""
        pan = card_data['pan']
        
        # Add comprehensive TLV data for EMV compliance (same as NFCReader)
        tlv_tags = [
            ('4F', card_config['aid']),  # Application Identifier (AID)
            ('50', card_config['application_label']),  # Application Label
            ('5A', pan),  # Application Primary Account Number (PAN)
            ('5F20', f"{selected_card_type} CARDHOLDER"),  # Cardholder Name
            ('5F24', card_data['expiry_date']),  # Application Expiration Date
            ('5F25', card_data['expiry_date'][:2]),  # Application Effective Date
            ('5F28', card_config['country_code']),  # Issuer Country Code
            ('5F2A', card_config['currency_code']),  # Transaction Currency Code
            ('5F30', card_data['service_code']),  # Service Code
            ('5F34', pan[-4:]),  # Application PAN Sequence Number
            ('82', '5800'),  # Application Interchange Profile
            ('84', card_config['aid']),  # Dedicated File (DF) Name
            ('87', '01'),  # Application Priority Indicator
            ('88', '01'),  # Short File Identifier
            ('8A', '3030'),  # Authorization Response Code
            ('9F02', '000000001000'),  # Amount, Authorized (Numeric)
            ('9F03', '000000000000'),  # Amount, Other (Numeric)
            ('9F06', card_config['aid']),  # Application Identifier (AID) - terminal
            ('9F07', 'FF00'),  # Application Usage Control
            ('9F08', '0002'),  # Application Version Number
            ('9F09', '008C'),  # Application Version Number (Terminal)
            ('9F12', card_config['application_label']),  # Application Preferred Name
            ('9F1A', card_config['country_code']),  # Terminal Country Code
            ('9F26', ''.join([f"{random.randint(0, 255):02X}" for _ in range(8)])),  # Application Cryptogram
            ('9F27', '80'),  # Cryptogram Information Data
            ('9F33', card_config['capabilities']),  # Terminal Capabilities
            ('9F35', card_config['terminal_type']),  # Terminal Type
            ('9F36', ''.join([f"{random.randint(0, 255):02X}" for _ in range(2)])),  # Application Transaction Counter (ATC)
            ('9F37', ''.join([f"{random.randint(0, 255):02X}" for _ in range(4)])),  # Unpredictable Number
            ('9F42', card_config['currency_code']),  # Application Currency Code
            ('9F53', card_config['kernel_id']),  # Transaction Category Code/Kernel Identifier
            ('DF01', pan[-4:]),  # Application PAN Suffix
            ('DF02', datetime.now().strftime('%Y%m%d%H%M%S')),  # Transaction Timestamp
            ('DF03', self.device_id),  # Emulator Device ID
            ('DF04', card_data['uid']),  # Card UID
            ('DF05', selected_card_type),  # Card Brand
        ]
        
        card_data['tlv_data'] = '|'.join([f"{tag}:{value}" for tag, value in tlv_tags])
        
        # Add Track 1 and Track 2 equivalent data
        track1_data = f"%B{pan}^{selected_card_type} CARDHOLDER^{card_data['expiry_date']}{card_data['service_code']}00000000000000000000?"
        track2_data = f";{pan}={card_data['expiry_date']}{card_data['service_code']}00000000000000000000?"
        
        card_data['track1'] = track1_data
        card_data['track2'] = track2_data
        
        # Add EMV application data
        card_data['emv_data'] = {
            'aid': card_config['aid'],
            'application_label': card_config['application_label'],
            'kernel_id': card_config['kernel_id'],
            'preferred_name': card_config['application_label'],
            'priority': '01',
            'application_version': '0008',
            'terminal_capabilities': card_config['capabilities'],
            'additional_terminal_capabilities': 'F000F0A001',
            'terminal_type': card_config['terminal_type'],
            'terminal_country_code': card_config['country_code'],
            'transaction_currency_code': card_config['currency_code'],
            'acquirer_country_code': card_config['country_code']
        }
        
        # Add security features
        card_data['security_features'] = {
            'cvv': f"{random.randint(100, 999):03d}",
            'cvv2': f"{random.randint(100, 999):03d}",
            'icvv': f"{random.randint(100, 999):03d}",
            'pin_verification_method': 'online',
            'cvm_list': ['PIN', 'Signature', 'No CVM'],
            'offline_auth_supported': True,
            'online_auth_supported': True,
            'contactless_supported': True,
            'chip_supported': True,
            'magstripe_supported': True
        }
        
    def add_emulated_card(self, card_data: Dict[str, Any]) -> bool:
        """Add card to emulation list"""
        if len(self.emulated_cards) >= self.capabilities['max_concurrent']:
            return False
            
        card_data['emulator_id'] = self.device_id
        card_data['added_at'] = datetime.now().isoformat()
        self.emulated_cards.append(card_data)
        return True
        
    def remove_emulated_card(self, card_uid: str) -> bool:
        """Remove card from emulation"""
        for i, card in enumerate(self.emulated_cards):
            if card.get('uid') == card_uid:
                del self.emulated_cards[i]
                return True
        return False
        
    def get_emulated_cards(self) -> List[Dict[str, Any]]:
        """Get list of emulated cards"""
        return self.emulated_cards.copy()

class NFCGateServer:
    """NFCGate compatible server for Android APK integration"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.clients = {}  # client_socket -> client_info
        self.devices = {}  # device_id -> NFCDevice
        self.sessions = {}  # session_id -> session_info
        self.message_handlers = {
            NFCGateProtocol.MESSAGE_TYPES['INIT']: self.handle_init,
            NFCGateProtocol.MESSAGE_TYPES['NFC_DATA']: self.handle_nfc_data,
            NFCGateProtocol.MESSAGE_TYPES['STATUS']: self.handle_status,
            NFCGateProtocol.MESSAGE_TYPES['CONFIG']: self.handle_config,
            NFCGateProtocol.MESSAGE_TYPES['HEARTBEAT']: self.handle_heartbeat,
            NFCGateProtocol.MESSAGE_TYPES['RELAY']: self.handle_relay,
            NFCGateProtocol.MESSAGE_TYPES['EMULATION']: self.handle_emulation
        }
        
    def start(self) -> None:
        """Start the NFCGate server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
            self.running = True
            
            logger.info(f"🌐 NFCGate server started on {self.host}:{self.port}")
            
            # Start heartbeat monitor
            threading.Thread(target=self.heartbeat_monitor, daemon=True).start()
            
            # Accept connections
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    logger.info(f"📱 New client connected from {addr}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Socket error: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to start NFCGate server: {e}")
            raise
            
    def stop(self) -> None:
        """Stop the NFCGate server"""
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("🛑 NFCGate server stopped")
        
    def handle_client(self, client_socket: socket.socket, addr: Tuple[str, int]) -> None:
        """Handle client connection"""
        try:
            # Add client to registry
            client_info = {
                'address': addr,
                'connected_at': datetime.now().isoformat(),
                'device_id': None,
                'session_id': None
            }
            self.clients[client_socket] = client_info
            
            while self.running:
                try:
                    # Receive data
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    # Parse NFCGate message
                    message = NFCGateProtocol.parse_message(data)
                    if not message:
                        logger.warning(f"Invalid message from {addr}")
                        continue
                    
                    # Update client info
                    client_info['session_id'] = message['session_id']
                    
                    # Handle message
                    response = self.process_message(message, client_socket, addr)
                    if response:
                        client_socket.sendall(response)
                        
                except socket.timeout:
                    continue
                except socket.error as e:
                    logger.warning(f"Client {addr} disconnected: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            # Cleanup
            if client_socket in self.clients:
                device_id = self.clients[client_socket].get('device_id')
                if device_id and device_id in self.devices:
                    self.devices[device_id].is_connected = False
                del self.clients[client_socket]
            client_socket.close()
            logger.info(f"🔌 Client {addr} disconnected")
            
    def process_message(self, message: Dict[str, Any], client_socket: socket.socket, addr: Tuple[str, int]) -> Optional[bytes]:
        """Process incoming NFCGate message"""
        msg_type = message['type']
        handler = self.message_handlers.get(msg_type)
        
        if handler:
            return handler(message, client_socket, addr)
        else:
            logger.warning(f"Unknown message type {msg_type} from {addr}")
            return None
            
    def handle_init(self, message: Dict[str, Any], client_socket: socket.socket, addr: Tuple[str, int]) -> bytes:
        """Handle initialization message"""
        try:
            # Parse init data
            init_data = json.loads(message['data'].decode('utf-8'))
            device_type = init_data.get('device_type', 'unknown')
            device_capabilities = init_data.get('capabilities', {})
            
            # Create device
            if device_type == 'reader':
                device = NFCReader(init_data.get('device_id'))
            elif device_type == 'emulator':
                device = NFCEmulator(init_data.get('device_id'))
            else:
                device = NFCDevice(
                    init_data.get('device_id', f"device_{random.randint(1000, 9999)}"),
                    device_type,
                    device_capabilities
                )
            
            device.is_connected = True
            self.devices[device.device_id] = device
            
            # Update client info
            self.clients[client_socket]['device_id'] = device.device_id
            
            # Create session
            session_info = {
                'session_id': message['session_id'],
                'device_id': device.device_id,
                'client_address': addr,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            self.sessions[message['session_id']] = session_info
            
            logger.info(f"✅ Device registered: {device.device_id} ({device_type}) from {addr}")
            
            # Send response
            response_data = {
                'status': 'success',
                'device_id': device.device_id,
                'session_id': message['session_id'],
                'server_version': '1.0.0',
                'supported_protocols': list(NFCGateProtocol.NFC_PROTOCOLS.keys())
            }
            
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['STATUS'],
                json.dumps(response_data).encode('utf-8'),
                message['session_id']
            )
            
        except Exception as e:
            logger.error(f"Error handling init message: {e}")
            error_data = {'status': 'error', 'message': str(e)}
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['ERROR'],
                json.dumps(error_data).encode('utf-8'),
                message['session_id']
            )
            
    def handle_nfc_data(self, message: Dict[str, Any], client_socket: socket.socket, addr: Tuple[str, int]) -> bytes:
        """Handle NFC data message"""
        try:
            # Parse NFC data
            nfc_data = json.loads(message['data'].decode('utf-8'))
            device_id = self.clients[client_socket].get('device_id')
            
            if not device_id or device_id not in self.devices:
                raise ValueError("Device not registered")
            
            device = self.devices[device_id]
            
            logger.info(f"📡 NFC data received from {device_id}: {len(nfc_data.get('raw_data', ''))} bytes")
            
            # Process based on device type
            if device.device_type == 'reader':
                # Process read data
                processed_data = self.process_reader_data(nfc_data, device)
            elif device.device_type == 'emulator':
                # Process emulation data
                processed_data = self.process_emulator_data(nfc_data, device)
            else:
                processed_data = nfc_data
            
            # Add metadata
            processed_data.update({
                'device_id': device_id,
                'session_id': message['session_id'],
                'processed_at': datetime.now().isoformat(),
                'client_address': f"{addr[0]}:{addr[1]}"
            })
            
            # Send response
            response_data = {
                'status': 'success',
                'processed_data': processed_data,
                'message': 'NFC data processed successfully'
            }
            
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['NFC_DATA'],
                json.dumps(response_data).encode('utf-8'),
                message['session_id']
            )
            
        except Exception as e:
            logger.error(f"Error handling NFC data: {e}")
            error_data = {'status': 'error', 'message': str(e)}
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['ERROR'],
                json.dumps(error_data).encode('utf-8'),
                message['session_id']
            )
            
    def handle_status(self, message: Dict[str, Any], client_socket: socket.socket, addr: Tuple[str, int]) -> bytes:
        """Handle status request"""
        try:
            # Get server status
            status_data = {
                'server_status': 'running',
                'connected_devices': len([d for d in self.devices.values() if d.is_connected]),
                'active_sessions': len(self.sessions),
                'total_clients': len(self.clients),
                'uptime': time.time() - getattr(self, 'start_time', time.time()),
                'devices': {device_id: device.to_dict() for device_id, device in self.devices.items()}
            }
            
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['STATUS'],
                json.dumps(status_data).encode('utf-8'),
                message['session_id']
            )
            
        except Exception as e:
            logger.error(f"Error handling status request: {e}")
            error_data = {'status': 'error', 'message': str(e)}
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['ERROR'],
                json.dumps(error_data).encode('utf-8'),
                message['session_id']
            )
            
    def handle_config(self, message: Dict[str, Any], client_socket: socket.socket, addr: Tuple[str, int]) -> bytes:
        """Handle configuration message"""
        try:
            config_data = json.loads(message['data'].decode('utf-8'))
            device_id = self.clients[client_socket].get('device_id')
            
            if device_id and device_id in self.devices:
                device = self.devices[device_id]
                
                # Update device configuration
                if 'capabilities' in config_data:
                    device.capabilities.update(config_data['capabilities'])
                
                logger.info(f"⚙️ Configuration updated for device {device_id}")
                
                response_data = {
                    'status': 'success',
                    'message': 'Configuration updated',
                    'current_config': device.capabilities
                }
            else:
                response_data = {
                    'status': 'error',
                    'message': 'Device not found'
                }
            
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['CONFIG'],
                json.dumps(response_data).encode('utf-8'),
                message['session_id']
            )
            
        except Exception as e:
            logger.error(f"Error handling config message: {e}")
            error_data = {'status': 'error', 'message': str(e)}
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['ERROR'],
                json.dumps(error_data).encode('utf-8'),
                message['session_id']
            )
            
    def handle_heartbeat(self, message: Dict[str, Any], client_socket: socket.socket, addr: Tuple[str, int]) -> bytes:
        """Handle heartbeat message"""
        device_id = self.clients[client_socket].get('device_id')
        
        if device_id and device_id in self.devices:
            self.devices[device_id].last_heartbeat = time.time()
        
        # Send heartbeat response
        response_data = {
            'status': 'alive',
            'server_time': time.time(),
            'timestamp': datetime.now().isoformat()
        }
        
        return NFCGateProtocol.create_message(
            NFCGateProtocol.MESSAGE_TYPES['HEARTBEAT'],
            json.dumps(response_data).encode('utf-8'),
            message['session_id']
        )
        
    def handle_relay(self, message: Dict[str, Any], client_socket: socket.socket, addr: Tuple[str, int]) -> bytes:
        """Handle relay message for device-to-device communication"""
        try:
            relay_data = json.loads(message['data'].decode('utf-8'))
            target_device = relay_data.get('target_device')
            relay_payload = relay_data.get('payload')
            
            # Find target device
            if target_device in self.devices:
                target = self.devices[target_device]
                
                # Find target client socket
                target_socket = None
                for sock, client_info in self.clients.items():
                    if client_info.get('device_id') == target_device:
                        target_socket = sock
                        break
                
                if target_socket:
                    # Forward message to target device
                    relay_message = NFCGateProtocol.create_message(
                        NFCGateProtocol.MESSAGE_TYPES['RELAY'],
                        json.dumps(relay_payload).encode('utf-8'),
                        message['session_id']
                    )
                    target_socket.sendall(relay_message)
                    
                    response_data = {
                        'status': 'success',
                        'message': f'Message relayed to {target_device}'
                    }
                else:
                    response_data = {
                        'status': 'error',
                        'message': f'Target device {target_device} not connected'
                    }
            else:
                response_data = {
                    'status': 'error',
                    'message': f'Target device {target_device} not found'
                }
            
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['RELAY'],
                json.dumps(response_data).encode('utf-8'),
                message['session_id']
            )
            
        except Exception as e:
            logger.error(f"Error handling relay message: {e}")
            error_data = {'status': 'error', 'message': str(e)}
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['ERROR'],
                json.dumps(error_data).encode('utf-8'),
                message['session_id']
            )
            
    def handle_emulation(self, message: Dict[str, Any], client_socket: socket.socket, addr: Tuple[str, int]) -> bytes:
        """Handle emulation control message"""
        try:
            emulation_data = json.loads(message['data'].decode('utf-8'))
            device_id = self.clients[client_socket].get('device_id')
            
            if not device_id or device_id not in self.devices:
                raise ValueError("Device not registered")
            
            device = self.devices[device_id]
            
            if device.device_type != 'emulator':
                raise ValueError("Device does not support emulation")
            
            emulator = device  # Should be NFCEmulator instance
            action = emulation_data.get('action')
            
            if action == 'add_card':
                card_data = emulation_data.get('card_data')
                success = emulator.add_emulated_card(card_data)
                if success:
                    response_data = {
                        'status': 'success',
                        'message': 'Card added to emulation',
                        'emulated_cards': emulator.get_emulated_cards()
                    }
                else:
                    response_data = {
                        'status': 'error',
                        'message': 'Failed to add card (limit reached?)'
                    }
                    
            elif action == 'remove_card':
                card_uid = emulation_data.get('card_uid')
                success = emulator.remove_emulated_card(card_uid)
                response_data = {
                    'status': 'success' if success else 'error',
                    'message': 'Card removed' if success else 'Card not found',
                    'emulated_cards': emulator.get_emulated_cards()
                }
                
            elif action == 'list_cards':
                response_data = {
                    'status': 'success',
                    'emulated_cards': emulator.get_emulated_cards()
                }
                
            else:
                response_data = {
                    'status': 'error',
                    'message': f'Unknown emulation action: {action}'
                }
            
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['EMULATION'],
                json.dumps(response_data).encode('utf-8'),
                message['session_id']
            )
            
        except Exception as e:
            logger.error(f"Error handling emulation message: {e}")
            error_data = {'status': 'error', 'message': str(e)}
            return NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['ERROR'],
                json.dumps(error_data).encode('utf-8'),
                message['session_id']
            )
            
    def process_reader_data(self, nfc_data: Dict[str, Any], device: NFCReader) -> Dict[str, Any]:
        """Process data from NFC reader"""
        # Add reader-specific processing
        processed = nfc_data.copy()
        processed.update({
            'device_type': 'reader',
            'processing_type': 'read_operation',
            'reader_capabilities': device.capabilities
        })
        
        # Parse TLV data if present
        if 'tlv_data' in nfc_data:
            processed['parsed_tlv'] = self.parse_tlv_data(nfc_data['tlv_data'])
        
        return processed
        
    def process_emulator_data(self, nfc_data: Dict[str, Any], device: NFCEmulator) -> Dict[str, Any]:
        """Process data from NFC emulator"""
        # Add emulator-specific processing
        processed = nfc_data.copy()
        processed.update({
            'device_type': 'emulator',
            'processing_type': 'emulation_operation',
            'emulator_capabilities': device.capabilities,
            'active_emulations': len(device.emulated_cards)
        })
        
        return processed
        
    def parse_tlv_data(self, tlv_string: str) -> Dict[str, str]:
        """Parse TLV data string"""
        tlv_dict = {}
        try:
            pairs = tlv_string.split('|')
            for pair in pairs:
                if ':' in pair:
                    tag, value = pair.split(':', 1)
                    tlv_dict[tag] = value
        except Exception as e:
            logger.warning(f"Error parsing TLV data: {e}")
        
        return tlv_dict
        
    def heartbeat_monitor(self) -> None:
        """Monitor device heartbeats and cleanup stale connections"""
        while self.running:
            try:
                current_time = time.time()
                timeout_threshold = 30  # 30 seconds timeout
                
                # Check for stale devices
                stale_devices = []
                for device_id, device in self.devices.items():
                    if device.is_connected and (current_time - device.last_heartbeat) > timeout_threshold:
                        stale_devices.append(device_id)
                
                # Mark stale devices as disconnected
                for device_id in stale_devices:
                    self.devices[device_id].is_connected = False
                    logger.warning(f"📴 Device {device_id} marked as disconnected (heartbeat timeout)")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")

class NFCGateClient:
    """NFCGate client for connecting to Android NFCGate server"""
    
    def __init__(self, server_host: str = '127.0.0.1', server_port: int = 5566, device_type: str = 'reader'):
        self.server_host = server_host
        self.server_port = server_port
        self.device_type = device_type
        self.socket = None
        self.connected = False
        self.session_id = str(uuid.uuid4())[:8]
        self.device_id = f"{device_type}_{random.randint(1000, 9999)}"
        
        # Create appropriate device
        if device_type == 'reader':
            self.device = NFCReader(self.device_id)
        elif device_type == 'emulator':
            self.device = NFCEmulator(self.device_id)
        else:
            self.device = NFCDevice(self.device_id, device_type, {})
            
    def connect(self) -> bool:
        """Connect to NFCGate server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            
            logger.info(f"🔗 Connected to NFCGate server at {self.server_host}:{self.server_port}")
            
            # Send initialization message
            init_data = {
                'device_id': self.device_id,
                'device_type': self.device_type,
                'capabilities': self.device.capabilities,
                'client_version': '1.0.0'
            }
            
            init_message = NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['INIT'],
                json.dumps(init_data).encode('utf-8'),
                self.session_id
            )
            
            self.socket.sendall(init_message)
            
            # Wait for response
            response_data = self.socket.recv(4096)
            response = NFCGateProtocol.parse_message(response_data)
            
            if response and response['type'] == NFCGateProtocol.MESSAGE_TYPES['STATUS']:
                response_json = json.loads(response['data'].decode('utf-8'))
                if response_json.get('status') == 'success':
                    logger.info(f"✅ Device registered successfully: {self.device_id}")
                    
                    # Start heartbeat
                    threading.Thread(target=self.heartbeat_loop, daemon=True).start()
                    
                    return True
                else:
                    logger.error(f"❌ Registration failed: {response_json.get('message')}")
                    return False
            else:
                logger.error("❌ Invalid response from server")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.connected = False
            return False
            
    def disconnect(self) -> None:
        """Disconnect from NFCGate server"""
        self.connected = False
        if self.socket:
            self.socket.close()
        logger.info("🔌 Disconnected from NFCGate server")
        
    def send_nfc_data(self, nfc_data: Dict[str, Any]) -> bool:
        """Send NFC data to server"""
        if not self.connected:
            logger.error("Not connected to server")
            return False
            
        try:
            message = NFCGateProtocol.create_message(
                NFCGateProtocol.MESSAGE_TYPES['NFC_DATA'],
                json.dumps(nfc_data).encode('utf-8'),
                self.session_id
            )
            
            self.socket.sendall(message)
            
            # Wait for response
            response_data = self.socket.recv(4096)
            response = NFCGateProtocol.parse_message(response_data)
            
            if response and response['type'] == NFCGateProtocol.MESSAGE_TYPES['NFC_DATA']:
                logger.info("📡 NFC data sent successfully")
                return True
            else:
                logger.error("❌ Failed to send NFC data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending NFC data: {e}")
            return False
            
    def heartbeat_loop(self) -> None:
        """Send periodic heartbeats"""
        while self.connected:
            try:
                heartbeat_message = NFCGateProtocol.create_message(
                    NFCGateProtocol.MESSAGE_TYPES['HEARTBEAT'],
                    b'{}',
                    self.session_id
                )
                
                self.socket.sendall(heartbeat_message)
                time.sleep(10)  # Send heartbeat every 10 seconds
                
            except Exception as e:
                logger.error(f"❌ Heartbeat failed: {e}")
                self.connected = False
                break

def main():
    """Main function for testing NFCGate compatibility"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NFCGate Compatibility System')
    parser.add_argument('--mode', choices=['server', 'client'], default='server',
                       help='Run as server or client')
    parser.add_argument('--host', default='127.0.0.1', help='Server host')
    parser.add_argument('--port', type=int, default=5566, help='Server port')
    parser.add_argument('--device-type', choices=['reader', 'emulator'], default='reader',
                       help='Device type for client mode')
    
    args = parser.parse_args()
    
    if args.mode == 'server':
        # Start NFCGate server
        server = NFCGateServer(args.host, args.port)
        server.start_time = time.time()
        
        try:
            server.start()
        except KeyboardInterrupt:
            logger.info("🛑 Server interrupted by user")
            server.stop()
            
    else:
        # Start NFCGate client
        client = NFCGateClient(args.host, args.port, args.device_type)
        
        if client.connect():
            try:
                # Simulate NFC operations
                for i in range(10):
                    if args.device_type == 'reader':
                        # Simulate card reading
                        card_data = client.device.read_card()
                        client.send_nfc_data(card_data)
                    elif args.device_type == 'emulator':
                        # Simulate card emulation
                        emulation_data = {
                            'operation': 'emulate_card',
                            'card_type': 'Visa',
                            'uid': ''.join([f"{random.randint(0, 255):02X}" for _ in range(7)]),
                            'timestamp': datetime.now().isoformat()
                        }
                        client.send_nfc_data(emulation_data)
                    
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Client interrupted by user")
            finally:
                client.disconnect()

if __name__ == "__main__":
    main()
