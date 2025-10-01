#!/usr/bin/env python3
"""
🌐 ONLINE ADMIN PANEL - Live RFID Communication & Test Management
Web-based admin panel for receiving live test data and sniffed communication 
from RFID readers and tags in real-time with SQLite3 database integration.
"""

import json
import sqlite3
import hashlib
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import socket
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LiveRFIDCapture:
    """Live RFID communication capture data structure"""
    capture_id: str
    timestamp: str
    reader_id: str
    tag_uid: str
    command: str
    response: str
    protocol: str  # ISO14443A, ISO14443B, ISO15693, etc.
    frequency: str  # 13.56MHz, etc.
    data_hex: str
    parsed_tlv: Dict
    signal_strength: float
    error_rate: float
    session_id: str
    capture_type: str  # "sniffed", "test", "live"
    reader_ip: str = ""
    emulator_ip: str = ""
    card_type: str = ""
    card_brand: str = ""
    card_issuer: str = ""
    manipulation_type: str = ""  # "none", "intercept", "modify", "replay"
    is_manipulated: bool = False
    original_data: str = ""
    modified_data: str = ""

@dataclass
class DeviceConnection:
    """Device connection information"""
    device_id: str
    device_name: str
    device_type: str  # "reader", "emulator", "analyzer"
    ip_address: str
    port: int
    status: str  # "connected", "disconnected", "error"
    capabilities: Dict
    connection_time: str
    last_activity: str
    paired_device: str = ""  # ID of paired device (reader<->emulator)
    throughput_bps: float = 0.0
    latency_ms: float = 0.0

@dataclass
class CardInformation:
    """Enhanced card information from TLV analysis"""
    card_type: str
    card_brand: str
    card_issuer: str
    issuer_country: str
    application_label: str
    aid: str  # Application Identifier
    pan_hash: str
    expiry_date: str = ""
    service_code: str = ""
    cvv_method: str = ""
    track_data: Optional[Dict] = None
    chip_capabilities: Optional[List[str]] = None

@dataclass
class OnlineTestTransaction:
    """Online test transaction with live data"""
    transaction_id: str
    session_id: str
    card_hash: str
    card_brand: str
    card_type: str
    issuer_country: str
    currency_code: str
    terminal_type: str
    bypass_method: str
    tlv_data: str
    execution_time_ms: int
    success: bool
    live_captures: List[LiveRFIDCapture]
    error_message: Optional[str] = None
    operator_notes: str = ""
    risk_assessment: str = "medium"
    test_timestamp: str = ""
    approval_status: str = "pending"
    remote_client_id: str = ""

class OnlineDatabaseManager:
    """Enhanced database manager for online operations"""
    
    def __init__(self, db_path: str = "database/online_admin.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize online database with enhanced tables"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Enhanced live RFID captures table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS live_rfid_captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capture_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    reader_id TEXT NOT NULL,
                    tag_uid TEXT NOT NULL,
                    command TEXT NOT NULL,
                    response TEXT NOT NULL,
                    protocol TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    data_hex TEXT NOT NULL,
                    parsed_tlv TEXT NOT NULL,
                    signal_strength REAL NOT NULL,
                    error_rate REAL NOT NULL,
                    session_id TEXT NOT NULL,
                    capture_type TEXT NOT NULL,
                    reader_ip TEXT DEFAULT '',
                    emulator_ip TEXT DEFAULT '',
                    card_type TEXT DEFAULT '',
                    card_brand TEXT DEFAULT '',
                    card_issuer TEXT DEFAULT '',
                    manipulation_type TEXT DEFAULT 'none',
                    is_manipulated BOOLEAN DEFAULT FALSE,
                    original_data TEXT DEFAULT '',
                    modified_data TEXT DEFAULT '',
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Device connections table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    device_name TEXT NOT NULL,
                    device_type TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    capabilities TEXT NOT NULL,
                    connection_time TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    paired_device TEXT DEFAULT '',
                    throughput_bps REAL DEFAULT 0.0,
                    latency_ms REAL DEFAULT 0.0,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Card information analysis table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS card_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capture_id TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    card_brand TEXT NOT NULL,
                    card_issuer TEXT NOT NULL,
                    issuer_country TEXT NOT NULL,
                    application_label TEXT NOT NULL,
                    aid TEXT NOT NULL,
                    pan_hash TEXT NOT NULL,
                    expiry_date TEXT DEFAULT '',
                    service_code TEXT DEFAULT '',
                    cvv_method TEXT DEFAULT '',
                    track_data TEXT DEFAULT '',
                    chip_capabilities TEXT DEFAULT '',
                    analysis_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (capture_id) REFERENCES live_rfid_captures (capture_id)
                )
            """)
            
            # Communication manipulation log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS manipulation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manipulation_id TEXT UNIQUE NOT NULL,
                    capture_id TEXT NOT NULL,
                    operator_id TEXT NOT NULL,
                    manipulation_type TEXT NOT NULL,
                    original_command TEXT NOT NULL,
                    modified_command TEXT NOT NULL,
                    original_response TEXT NOT NULL,
                    modified_response TEXT NOT NULL,
                    manipulation_reason TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (capture_id) REFERENCES live_rfid_captures (capture_id)
                )
            """)
            
            # Online test transactions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS online_test_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    session_id TEXT NOT NULL,
                    card_hash TEXT NOT NULL,
                    card_brand TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    issuer_country TEXT NOT NULL,
                    currency_code TEXT NOT NULL,
                    terminal_type TEXT NOT NULL,
                    bypass_method TEXT NOT NULL,
                    tlv_data TEXT NOT NULL,
                    execution_time_ms INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    live_captures TEXT NOT NULL,
                    error_message TEXT,
                    operator_notes TEXT DEFAULT '',
                    risk_assessment TEXT DEFAULT 'medium',
                    test_timestamp TEXT NOT NULL,
                    approval_status TEXT DEFAULT 'pending',
                    remote_client_id TEXT NOT NULL,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Connected clients tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connected_clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT UNIQUE NOT NULL,
                    client_name TEXT NOT NULL,
                    client_type TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    connection_time TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    capabilities TEXT NOT NULL
                )
            """)
            
            # Live sessions tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS live_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    session_name TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_captures INTEGER DEFAULT 0,
                    total_transactions INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    session_data TEXT NOT NULL
                )
            """)
            
            conn.commit()
            logger.info("✅ Online admin database initialized successfully")
    
    def save_live_capture(self, capture: LiveRFIDCapture) -> bool:
        """Save live RFID capture to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO live_rfid_captures 
                    (capture_id, timestamp, reader_id, tag_uid, command, response, 
                     protocol, frequency, data_hex, parsed_tlv, signal_strength, 
                     error_rate, session_id, capture_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    capture.capture_id, capture.timestamp, capture.reader_id,
                    capture.tag_uid, capture.command, capture.response,
                    capture.protocol, capture.frequency, capture.data_hex,
                    json.dumps(capture.parsed_tlv), capture.signal_strength,
                    capture.error_rate, capture.session_id, capture.capture_type
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Error saving live capture: {e}")
            return False
    
    def save_online_transaction(self, transaction: OnlineTestTransaction) -> bool:
        """Save online test transaction to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Convert live captures to JSON
                captures_json = json.dumps([asdict(capture) for capture in transaction.live_captures])
                
                conn.execute("""
                    INSERT OR REPLACE INTO online_test_transactions 
                    (transaction_id, session_id, card_hash, card_brand, card_type, 
                     issuer_country, currency_code, terminal_type, bypass_method, 
                     tlv_data, execution_time_ms, success, live_captures, error_message, 
                     operator_notes, risk_assessment, test_timestamp, approval_status, remote_client_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.transaction_id, transaction.session_id, transaction.card_hash,
                    transaction.card_brand, transaction.card_type, transaction.issuer_country,
                    transaction.currency_code, transaction.terminal_type, transaction.bypass_method,
                    transaction.tlv_data, transaction.execution_time_ms, transaction.success,
                    captures_json, transaction.error_message, transaction.operator_notes,
                    transaction.risk_assessment, transaction.test_timestamp, 
                    transaction.approval_status, transaction.remote_client_id
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Error saving online transaction: {e}")
            return False
    
    def get_live_captures(self, session_id: Optional[str] = None, limit: int = 100) -> List[LiveRFIDCapture]:
        """Get live RFID captures"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if session_id:
                    cursor = conn.execute("""
                        SELECT * FROM live_rfid_captures 
                        WHERE session_id = ? 
                        ORDER BY timestamp DESC LIMIT ?
                    """, (session_id, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM live_rfid_captures 
                        ORDER BY timestamp DESC LIMIT ?
                    """, (limit,))
                
                captures = []
                for row in cursor.fetchall():
                    capture = LiveRFIDCapture(
                        capture_id=row['capture_id'],
                        timestamp=row['timestamp'],
                        reader_id=row['reader_id'],
                        tag_uid=row['tag_uid'],
                        command=row['command'],
                        response=row['response'],
                        protocol=row['protocol'],
                        frequency=row['frequency'],
                        data_hex=row['data_hex'],
                        parsed_tlv=json.loads(row['parsed_tlv']),
                        signal_strength=row['signal_strength'],
                        error_rate=row['error_rate'],
                        session_id=row['session_id'],
                        capture_type=row['capture_type']
                    )
                    captures.append(capture)
                
                return captures
        except Exception as e:
            logger.error(f"❌ Error getting live captures: {e}")
            return []
    
    def register_client(self, client_id: str, client_data: Dict) -> bool:
        """Register a connected client"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO connected_clients 
                    (client_id, client_name, client_type, ip_address, 
                     connection_time, last_activity, status, capabilities)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    client_id, client_data.get('name', 'Unknown'),
                    client_data.get('type', 'reader'), client_data.get('ip', ''),
                    datetime.now().isoformat(), datetime.now().isoformat(),
                    'connected', json.dumps(client_data.get('capabilities', {}))
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Error registering client: {e}")
            return False

class LiveRFIDReceiver:
    """Enhanced live RFID data receiver with device management and card analysis"""
    
    def __init__(self, db_manager: OnlineDatabaseManager):
        self.db_manager = db_manager
        self.connected_devices = {}
        self.active_sessions = {}
        self.device_pairs = {}  # reader_id -> emulator_id mapping
        
    def register_device(self, device_data: Dict) -> DeviceConnection:
        """Register a new device (reader/emulator/analyzer)"""
        device_id = device_data.get('device_id', str(uuid.uuid4()))
        
        device = DeviceConnection(
            device_id=device_id,
            device_name=device_data.get('name', 'Unknown Device'),
            device_type=device_data.get('type', 'reader'),
            ip_address=device_data.get('ip_address', ''),
            port=int(device_data.get('port', 0)),
            status='connected',
            capabilities=device_data.get('capabilities', {}),
            connection_time=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
            paired_device=device_data.get('paired_device', ''),
            throughput_bps=float(device_data.get('throughput_bps', 0.0)),
            latency_ms=float(device_data.get('latency_ms', 0.0))
        )
        
        self.connected_devices[device_id] = device
        
        # Save to database
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO device_connections 
                    (device_id, device_name, device_type, ip_address, port, status, 
                     capabilities, connection_time, last_activity, paired_device, 
                     throughput_bps, latency_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    device.device_id, device.device_name, device.device_type,
                    device.ip_address, device.port, device.status,
                    json.dumps(device.capabilities), device.connection_time,
                    device.last_activity, device.paired_device,
                    device.throughput_bps, device.latency_ms
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Error saving device to database: {e}")
        
        return device
    
    def pair_devices(self, reader_id: str, emulator_id: str) -> bool:
        """Pair a reader with an emulator"""
        try:
            if reader_id in self.connected_devices and emulator_id in self.connected_devices:
                self.device_pairs[reader_id] = emulator_id
                self.device_pairs[emulator_id] = reader_id
                
                # Update database
                with sqlite3.connect(self.db_manager.db_path) as conn:
                    conn.execute("""
                        UPDATE device_connections 
                        SET paired_device = ? 
                        WHERE device_id = ?
                    """, (emulator_id, reader_id))
                    
                    conn.execute("""
                        UPDATE device_connections 
                        SET paired_device = ? 
                        WHERE device_id = ?
                    """, (reader_id, emulator_id))
                    
                    conn.commit()
                
                logger.info(f"✅ Devices paired: {reader_id} <-> {emulator_id}")
                return True
            else:
                logger.warning(f"❌ Cannot pair devices: one or both not connected")
                return False
        except Exception as e:
            logger.error(f"❌ Error pairing devices: {e}")
            return False
    
    def analyze_card_information(self, tlv_data: str, data_hex: str) -> CardInformation:
        """Analyze card information from TLV data and raw hex"""
        try:
            parsed_tlv = self.parse_tlv_string(tlv_data) if tlv_data else {}
            
            # Extract card information from TLV tags
            card_type = "Unknown"
            card_brand = "Unknown"
            card_issuer = "Unknown"
            issuer_country = "Unknown"
            application_label = ""
            aid = ""
            pan_hash = ""
            
            # Analyze AID (Application Identifier) - Tag 4F
            if '4F' in parsed_tlv:
                aid = parsed_tlv['4F']['value']
                card_brand, card_type = self.identify_card_from_aid(aid)
            
            # Analyze Application Label - Tag 50
            if '50' in parsed_tlv:
                application_label = self.hex_to_ascii(parsed_tlv['50']['value'])
                if not card_brand or card_brand == "Unknown":
                    card_brand = self.identify_brand_from_label(application_label)
            
            # Analyze PAN (if available) - Tag 5A
            if '5A' in parsed_tlv:
                pan_data = parsed_tlv['5A']['value']
                pan_hash = hashlib.sha256(pan_data.encode()).hexdigest()
                card_brand_from_pan = self.identify_brand_from_pan(pan_data)
                if card_brand_from_pan != "Unknown":
                    card_brand = card_brand_from_pan
            
            # Analyze issuer country - Tag 5F28
            if '5F28' in parsed_tlv:
                issuer_country = self.get_country_from_code(parsed_tlv['5F28']['value'])
            
            # Analyze track data if present
            track_data = {}
            if '9F1F' in parsed_tlv:  # Track 1 Discretionary Data
                track_data['track1'] = parsed_tlv['9F1F']['value']
            if '9F20' in parsed_tlv:  # Track 2 Discretionary Data
                track_data['track2'] = parsed_tlv['9F20']['value']
            
            # Analyze chip capabilities
            chip_capabilities = []
            if '9F33' in parsed_tlv:  # Terminal Capabilities
                chip_capabilities.extend(self.parse_terminal_capabilities(parsed_tlv['9F33']['value']))
            if '9F40' in parsed_tlv:  # Additional Terminal Capabilities
                chip_capabilities.extend(self.parse_additional_capabilities(parsed_tlv['9F40']['value']))
            
            # Get expiry date - Tag 5F24
            expiry_date = ""
            if '5F24' in parsed_tlv:
                expiry_date = self.format_expiry_date(parsed_tlv['5F24']['value'])
            
            # Get service code - Tag 5F30
            service_code = ""
            if '5F30' in parsed_tlv:
                service_code = parsed_tlv['5F30']['value']
            
            # Determine CVM method
            cvv_method = ""
            if '8E' in parsed_tlv:  # CVM List
                cvv_method = self.parse_cvm_list(parsed_tlv['8E']['value'])
            elif '9F34' in parsed_tlv:  # CVM Results
                cvv_method = self.parse_cvm_results(parsed_tlv['9F34']['value'])
            
            return CardInformation(
                card_type=card_type,
                card_brand=card_brand,
                card_issuer=card_issuer,
                issuer_country=issuer_country,
                application_label=application_label,
                aid=aid,
                pan_hash=pan_hash,
                expiry_date=expiry_date,
                service_code=service_code,
                cvv_method=cvv_method,
                track_data=track_data or {},
                chip_capabilities=chip_capabilities or []
            )
            
        except Exception as e:
            logger.error(f"❌ Error analyzing card information: {e}")
            return CardInformation(
                card_type="Unknown",
                card_brand="Unknown", 
                card_issuer="Unknown",
                issuer_country="Unknown",
                application_label="",
                aid="",
                pan_hash="",
                track_data={},
                chip_capabilities=[]
            )
    
    def identify_card_from_aid(self, aid: str) -> tuple:
        """Identify card brand and type from AID"""
        aid_mappings = {
            'A0000000031010': ('Visa', 'Credit'),
            'A0000000032010': ('Visa', 'Debit'),
            'A0000000033010': ('Visa', 'Electron'),
            'A0000000034010': ('Visa', 'V PAY'),
            'A0000000041010': ('Mastercard', 'Credit'),
            'A0000000042010': ('Mastercard', 'Debit'),
            'A0000000043010': ('Mastercard', 'Maestro'),
            'A00000002501': ('American Express', 'Credit'),
            'A000000025010104': ('American Express', 'ExpressPay'),
            'A0000001523010': ('Discover', 'Credit'),
            'A0000001524010': ('Discover', 'Debit'),
            'A0000002771010': ('Interac', 'Debit'),
            'A0000003330101': ('Union Pay', 'Credit'),
            'A0000005241010': ('JCB', 'Credit'),
        }
        
        # Check for exact match
        if aid in aid_mappings:
            return aid_mappings[aid]
        
        # Check for partial matches
        for known_aid, (brand, card_type) in aid_mappings.items():
            if aid.startswith(known_aid[:12]):  # Match first 6 bytes
                return (brand, card_type)
        
        return ("Unknown", "Unknown")
    
    def identify_brand_from_label(self, label: str) -> str:
        """Identify card brand from application label"""
        label_lower = label.lower()
        if 'visa' in label_lower:
            return 'Visa'
        elif 'mastercard' in label_lower or 'master' in label_lower:
            return 'Mastercard'
        elif 'american express' in label_lower or 'amex' in label_lower:
            return 'American Express'
        elif 'discover' in label_lower:
            return 'Discover'
        elif 'jcb' in label_lower:
            return 'JCB'
        elif 'union' in label_lower or 'unionpay' in label_lower:
            return 'Union Pay'
        elif 'interac' in label_lower:
            return 'Interac'
        return "Unknown"
    
    def identify_brand_from_pan(self, pan: str) -> str:
        """Identify card brand from PAN"""
        if pan.startswith('4'):
            return 'Visa'
        elif pan.startswith('5') or pan.startswith('2'):
            return 'Mastercard'
        elif pan.startswith('34') or pan.startswith('37'):
            return 'American Express'
        elif pan.startswith('6011') or pan.startswith('65'):
            return 'Discover'
        elif pan.startswith('35'):
            return 'JCB'
        elif pan.startswith('62'):
            return 'Union Pay'
        return "Unknown"
    
    def hex_to_ascii(self, hex_string: str) -> str:
        """Convert hex string to ASCII"""
        try:
            return bytes.fromhex(hex_string).decode('ascii', errors='ignore')
        except:
            return hex_string
    
    def get_country_from_code(self, country_code: str) -> str:
        """Get country name from ISO country code"""
        country_codes = {
            '0840': 'United States',
            '0124': 'Canada', 
            '0276': 'Germany',
            '0250': 'France',
            '0826': 'United Kingdom',
            '0036': 'Australia',
            '0392': 'Japan',
            '0156': 'China',
            '0356': 'India',
            '0076': 'Brazil'
        }
        return country_codes.get(country_code, f"Country {country_code}")
    
    def parse_terminal_capabilities(self, capabilities_hex: str) -> List[str]:
        """Parse terminal capabilities from hex"""
        capabilities = []
        try:
            # Convert hex to binary and analyze capability bits
            cap_bytes = bytes.fromhex(capabilities_hex)
            if len(cap_bytes) >= 3:
                byte1, byte2, byte3 = cap_bytes[:3]
                
                if byte1 & 0x80: capabilities.append("Manual key entry")
                if byte1 & 0x40: capabilities.append("Magnetic stripe")
                if byte1 & 0x20: capabilities.append("IC with contacts")
                if byte2 & 0x80: capabilities.append("Plain text PIN verification")
                if byte2 & 0x40: capabilities.append("Enciphered PIN verification")
                if byte2 & 0x20: capabilities.append("Signature")
                if byte3 & 0x80: capabilities.append("SDA supported")
                if byte3 & 0x40: capabilities.append("DDA supported")
                if byte3 & 0x20: capabilities.append("Card capture")
        except:
            pass
        return capabilities
    
    def parse_additional_capabilities(self, capabilities_hex: str) -> List[str]:
        """Parse additional terminal capabilities"""
        capabilities = []
        try:
            cap_bytes = bytes.fromhex(capabilities_hex)
            if len(cap_bytes) >= 5:
                if cap_bytes[0] & 0x80: capabilities.append("Cash transactions")
                if cap_bytes[0] & 0x40: capabilities.append("Goods transactions")
                if cap_bytes[0] & 0x20: capabilities.append("Services transactions")
                if cap_bytes[1] & 0x80: capabilities.append("Contactless transactions")
        except:
            pass
        return capabilities
    
    def format_expiry_date(self, expiry_hex: str) -> str:
        """Format expiry date from hex YYMMDD"""
        try:
            if len(expiry_hex) >= 4:
                year = expiry_hex[:2]
                month = expiry_hex[2:4]
                return f"{month}/{year}"
        except:
            pass
        return expiry_hex
    
    def parse_cvm_list(self, cvm_hex: str) -> str:
        """Parse CVM list to determine verification method"""
        try:
            cvm_bytes = bytes.fromhex(cvm_hex)
            if len(cvm_bytes) >= 2:
                cvm_code = cvm_bytes[0]
                if cvm_code == 0x1E: return "Signature"
                elif cvm_code == 0x1F: return "No CVM"
                elif cvm_code == 0x41: return "PIN"
                elif cvm_code == 0x42: return "Online PIN"
        except:
            pass
        return "Unknown CVM"
    
    def parse_cvm_results(self, results_hex: str) -> str:
        """Parse CVM results"""
        try:
            if len(results_hex) >= 6:
                cvm_performed = results_hex[0:2]
                if cvm_performed == "1E": return "Signature performed"
                elif cvm_performed == "1F": return "No CVM performed" 
                elif cvm_performed == "41": return "PIN verified"
                elif cvm_performed == "42": return "Online PIN performed"
        except:
            pass
        return "Unknown result"
        
    def parse_rfid_data(self, raw_data: Dict) -> LiveRFIDCapture:
        """Parse incoming RFID data with enhanced card analysis"""
        try:
            # Generate capture ID
            capture_id = f"CAP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
            
            # Parse TLV data if present
            parsed_tlv = {}
            tlv_data = raw_data.get('tlv_data', '')
            if tlv_data:
                parsed_tlv = self.parse_tlv_string(tlv_data)
            
            # Analyze card information
            card_info = self.analyze_card_information(tlv_data, raw_data.get('data_hex', ''))
            
            # Get device IPs from connected devices
            reader_id = raw_data.get('reader_id', 'unknown')
            reader_ip = ""
            emulator_ip = ""
            
            # Find reader IP
            for device in self.connected_devices.values():
                if device.device_id == reader_id or device.device_name == reader_id:
                    reader_ip = device.ip_address
                    # Find paired emulator
                    if device.paired_device:
                        for paired_device in self.connected_devices.values():
                            if paired_device.device_id == device.paired_device:
                                emulator_ip = paired_device.ip_address
                                break
                    break
            
            # Check for manipulation indicators
            is_manipulated = raw_data.get('is_manipulated', False)
            manipulation_type = raw_data.get('manipulation_type', 'none')
            original_data = raw_data.get('original_data', '')
            modified_data = raw_data.get('modified_data', '')
            
            capture = LiveRFIDCapture(
                capture_id=capture_id,
                timestamp=raw_data.get('timestamp', datetime.now().isoformat()),
                reader_id=reader_id,
                tag_uid=raw_data.get('tag_uid', ''),
                command=raw_data.get('command', ''),
                response=raw_data.get('response', ''),
                protocol=raw_data.get('protocol', 'ISO14443A'),
                frequency=raw_data.get('frequency', '13.56MHz'),
                data_hex=raw_data.get('data_hex', ''),
                parsed_tlv=parsed_tlv,
                signal_strength=float(raw_data.get('signal_strength', 0.0)),
                error_rate=float(raw_data.get('error_rate', 0.0)),
                session_id=raw_data.get('session_id', 'default'),
                capture_type=raw_data.get('capture_type', 'sniffed'),
                reader_ip=reader_ip,
                emulator_ip=emulator_ip,
                card_type=card_info.card_type,
                card_brand=card_info.card_brand,
                card_issuer=card_info.card_issuer,
                manipulation_type=manipulation_type,
                is_manipulated=is_manipulated,
                original_data=original_data,
                modified_data=modified_data
            )
            
            # Save card analysis to database
            if card_info.aid:
                self.save_card_analysis(capture_id, card_info)
            
            return capture
            
        except Exception as e:
            logger.error(f"❌ Error parsing RFID data: {e}")
            raise
    
    def save_card_analysis(self, capture_id: str, card_info: CardInformation) -> bool:
        """Save card analysis to database"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO card_analysis 
                    (capture_id, card_type, card_brand, card_issuer, issuer_country, 
                     application_label, aid, pan_hash, expiry_date, service_code, 
                     cvv_method, track_data, chip_capabilities)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    capture_id, card_info.card_type, card_info.card_brand,
                    card_info.card_issuer, card_info.issuer_country,
                    card_info.application_label, card_info.aid, card_info.pan_hash,
                    card_info.expiry_date, card_info.service_code, card_info.cvv_method,
                    json.dumps(card_info.track_data or {}), 
                    json.dumps(card_info.chip_capabilities or [])
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Error saving card analysis: {e}")
            return False
    
    def manipulate_communication(self, capture_id: str, operator_id: str, 
                                manipulation_type: str, new_command: str = "", 
                                new_response: str = "", reason: str = "") -> Dict:
        """Manually manipulate RFID communication"""
        try:
            manipulation_id = f"MAN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
            
            # Get original capture data
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.execute("""
                    SELECT command, response FROM live_rfid_captures 
                    WHERE capture_id = ?
                """, (capture_id,))
                
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': 'Capture not found'}
                
                original_command, original_response = row
                
                # Log manipulation
                conn.execute("""
                    INSERT INTO manipulation_log 
                    (manipulation_id, capture_id, operator_id, manipulation_type,
                     original_command, modified_command, original_response, 
                     modified_response, manipulation_reason, success)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    manipulation_id, capture_id, operator_id, manipulation_type,
                    original_command, new_command or original_command,
                    original_response, new_response or original_response,
                    reason, True
                ))
                
                # Update capture with manipulation info
                conn.execute("""
                    UPDATE live_rfid_captures 
                    SET is_manipulated = TRUE, 
                        manipulation_type = ?,
                        original_data = ?,
                        modified_data = ?
                    WHERE capture_id = ?
                """, (
                    manipulation_type, 
                    json.dumps({'command': original_command, 'response': original_response}),
                    json.dumps({'command': new_command or original_command, 'response': new_response or original_response}),
                    capture_id
                ))
                
                conn.commit()
                
                return {
                    'success': True,
                    'manipulation_id': manipulation_id,
                    'original_command': original_command,
                    'original_response': original_response,
                    'modified_command': new_command or original_command,
                    'modified_response': new_response or original_response
                }
                
        except Exception as e:
            logger.error(f"❌ Error manipulating communication: {e}")
            return {'success': False, 'error': str(e)}
    
    def parse_tlv_string(self, tlv_string: str) -> Dict:
        """Parse TLV string into structured data"""
        try:
            parsed = {}
            
            # Handle different TLV formats
            if '|' in tlv_string:
                # Format: tag:value|tag:value
                pairs = tlv_string.split('|')
            elif ';' in tlv_string:
                # Format: tag:value;tag:value
                pairs = tlv_string.split(';')
            else:
                # Single tag:value
                pairs = [tlv_string]
            
            for pair in pairs:
                if ':' in pair:
                    tag, value = pair.split(':', 1)
                    parsed[tag.strip()] = {
                        'value': value.strip(),
                        'description': self.get_tag_description(tag.strip())
                    }
            
            return parsed
            
        except Exception as e:
            logger.error(f"❌ Error parsing TLV string: {e}")
            return {}
    
    def get_tag_description(self, tag: str) -> str:
        """Get description for EMV/RFID tag"""
        descriptions = {
            '9F34': 'CVM Results',
            '9F26': 'Application Cryptogram',
            '9F27': 'Cryptogram Information Data',
            '8E': 'CVM List',
            '9F33': 'Terminal Capabilities',
            '9F35': 'Terminal Type',
            '9F40': 'Additional Terminal Capabilities',
            '9F37': 'Unpredictable Number',
            '9F02': 'Amount Authorized',
            '9F03': 'Amount Other',
            '9F1A': 'Terminal Country Code',
            '5F2A': 'Transaction Currency Code',
            '9A': 'Transaction Date',
            '9C': 'Transaction Type',
            '9F07': 'Application Usage Control',
            '9F08': 'Application Version Number',
            '9F09': 'Application Version Number',
            '9F0D': 'IAC Default',
            '9F0E': 'IAC Denial',
            '9F0F': 'IAC Online',
            'DF12': 'Contactless Application Label',
            '4F': 'Application Identifier (AID)',
            '50': 'Application Label',
            '87': 'Application Priority Indicator',
            '9F38': 'PDOL',
            '9F32': 'Issuer Public Key Exponent',
            '90': 'Issuer Public Key Certificate',
            '9F46': 'ICC Public Key Certificate',
            '9F47': 'ICC Public Key Exponent',
            '9F48': 'ICC Public Key Remainder'
        }
        return descriptions.get(tag, f'Unknown Tag {tag}')

# Flask Web Application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
db_manager = OnlineDatabaseManager()
rfid_receiver = LiveRFIDReceiver(db_manager)

# HTML Templates
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌐 Online Admin Panel - Live RFID Monitor</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status-bar {
            background: rgba(255,255,255,0.95);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .status-item {
            text-align: center;
        }
        .status-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #4CAF50;
        }
        .status-label {
            color: #666;
            font-size: 0.9em;
        }
        .panels {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .panel {
            background: rgba(255,255,255,0.95);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .panel h3 {
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
        }
        .live-feed {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            background: #f9f9f9;
        }
        .capture-item {
            background: white;
            border-left: 4px solid #4CAF50;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .capture-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        .capture-id {
            font-weight: bold;
            color: #333;
        }
        .capture-time {
            color: #666;
            font-size: 0.9em;
        }
        .capture-details {
            font-size: 0.9em;
            color: #555;
        }
        .capture-data {
            background: #f0f0f0;
            padding: 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
            margin-top: 5px;
        }
        .controls {
            background: rgba(255,255,255,0.95);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }
        button:hover {
            background: #45a049;
        }
        button.danger {
            background: #f44336;
        }
        button.danger:hover {
            background: #da190b;
        }
        .input-group {
            margin-bottom: 15px;
        }
        .input-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .input-group input, .input-group select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 5px;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .connected {
            background: #4CAF50;
            color: white;
        }
        .disconnected {
            background: #f44336;
            color: white;
        }
        .log-entry {
            padding: 5px;
            border-bottom: 1px solid #eee;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        .log-info { color: #4CAF50; }
        .log-warning { color: #ff9800; }
        .log-error { color: #f44336; }
        
        /* Enhanced device grid */
        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            max-height: 400px;
            overflow-y: auto;
        }
        .device-card {
            background: white;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s ease;
        }
        .device-card:hover {
            border-color: #4CAF50;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .device-card.reader {
            border-color: #2196F3;
        }
        .device-card.emulator {
            border-color: #FF9800;
        }
        .device-card.analyzer {
            border-color: #9C27B0;
        }
        .device-card.paired {
            border-color: #4CAF50;
            border-style: dashed;
        }
        .device-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .device-ip {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .device-status {
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
        }
        .device-status.connected {
            background: #4CAF50;
            color: white;
        }
        .device-status.disconnected {
            background: #f44336;
            color: white;
        }
        
        /* Card analysis styles */
        .card-analysis {
            max-height: 400px;
            overflow-y: auto;
        }
        .card-info {
            background: white;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .card-brand {
            font-size: 1.2em;
            font-weight: bold;
        }
        .card-type {
            background: #2196F3;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8em;
        }
        .card-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 0.9em;
        }
        .card-info-placeholder {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        
        /* Manipulation controls */
        .manipulation-controls {
            margin-bottom: 20px;
        }
        .manipulation-btn {
            background: #FF5722;
            width: 100%;
            margin-top: 10px;
        }
        .manipulation-btn:hover {
            background: #D84315;
        }
        .manipulation-log {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            background: #f9f9f9;
        }
        .manipulation-entry {
            background: white;
            border-left: 4px solid #FF5722;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .manipulation-header {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .manipulation-details {
            font-size: 0.9em;
            color: #555;
        }
        
        /* Capture controls */
        .capture-controls, .device-controls {
            margin-bottom: 15px;
            display: flex;
            gap: 10px;
        }
        .capture-controls button, .device-controls button {
            flex: 1;
            padding: 8px;
            font-size: 0.9em;
        }
        
        /* Enhanced capture item */
        .capture-item.manipulated {
            border-left-color: #FF5722;
            background: #FFF3E0;
        }
        .capture-manipulation {
            background: #FFEBEE;
            padding: 5px;
            border-radius: 3px;
            margin-top: 5px;
            font-size: 0.8em;
        }
        .capture-ips {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }
        .card-badge {
            display: inline-block;
            background: #E3F2FD;
            color: #1976D2;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-right: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Online Admin Panel</h1>
            <p>Live RFID Communication & Test Management</p>
        </div>

        <div class="connection-status" id="connectionStatus">
            <span id="statusText">Connecting...</span>
        </div>

        <div class="status-bar">
            <div class="status-item">
                <div class="status-value" id="liveCaptures">0</div>
                <div class="status-label">Live Captures</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="connectedClients">0</div>
                <div class="status-label">Connected Clients</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="activeSessions">0</div>
                <div class="status-label">Active Sessions</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="totalTransactions">0</div>
                <div class="status-label">Total Transactions</div>
            </div>
        </div>

        <div class="panels">
            <div class="panel">
                <h3>🔴 Live RFID Captures</h3>
                <div class="capture-controls">
                    <button onclick="pauseCaptures()" id="pauseBtn">⏸️ Pause</button>
                    <button onclick="clearCaptures()">🗑️ Clear</button>
                    <button onclick="exportCaptures()">📤 Export</button>
                </div>
                <div class="live-feed" id="liveFeed">
                    <div class="log-entry log-info">Waiting for live data...</div>
                </div>
            </div>

            <div class="panel">
                <h3>� Device Connections</h3>
                <div class="device-controls">
                    <button onclick="refreshDevices()">🔄 Refresh</button>
                    <button onclick="pairDevices()">🔗 Pair Devices</button>
                    <button onclick="showDeviceMap()">🗺️ Network Map</button>
                </div>
                <div class="device-grid" id="deviceGrid">
                    <div class="log-entry log-info">No devices connected</div>
                </div>
            </div>
        </div>

        <div class="panels">
            <div class="panel">
                <h3>💳 Card Analysis</h3>
                <div class="card-analysis" id="cardAnalysis">
                    <div class="card-info-placeholder">
                        <p>🔍 Card information will appear here when RFID captures are received</p>
                    </div>
                </div>
            </div>

            <div class="panel">
                <h3>🛠️ Communication Manipulation</h3>
                <div class="manipulation-controls">
                    <div class="input-group">
                        <label for="captureSelect">Select Capture:</label>
                        <select id="captureSelect">
                            <option value="">Select a capture to manipulate...</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label for="manipulationType">Manipulation Type:</label>
                        <select id="manipulationType">
                            <option value="intercept">📡 Intercept</option>
                            <option value="modify">✏️ Modify</option>
                            <option value="replay">🔄 Replay</option>
                            <option value="block">🚫 Block</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label for="newCommand">New Command (hex):</label>
                        <input type="text" id="newCommand" placeholder="Enter hex command...">
                    </div>
                    <div class="input-group">
                        <label for="newResponse">New Response (hex):</label>
                        <input type="text" id="newResponse" placeholder="Enter hex response...">
                    </div>
                    <div class="input-group">
                        <label for="manipulationReason">Reason:</label>
                        <input type="text" id="manipulationReason" placeholder="Why manipulate this communication?">
                    </div>
                    <button onclick="applyManipulation()" class="manipulation-btn">🛠️ Apply Manipulation</button>
                </div>
                <div class="manipulation-log" id="manipulationLog">
                    <div class="log-entry log-info">No manipulations performed</div>
                </div>
            </div>
        </div>

        <div class="controls">
            <h3>🎛️ Control Panel</h3>
            
            <div class="button-group">
                <button onclick="startNewSession()">🆕 New Session</button>
                <button onclick="exportData()">📤 Export Data</button>
                <button onclick="clearLogs()">🗑️ Clear Logs</button>
                <button onclick="refreshStats()" class="info">🔄 Refresh</button>
            </div>

            <div class="input-group">
                <label for="sessionName">Session Name:</label>
                <input type="text" id="sessionName" placeholder="Enter session name...">
            </div>

            <div class="input-group">
                <label for="filterType">Filter Captures:</label>
                <select id="filterType" onchange="applyFilter()">
                    <option value="all">All Captures</option>
                    <option value="sniffed">Sniffed Only</option>
                    <option value="test">Test Only</option>
                    <option value="live">Live Only</option>
                </select>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection
        const socket = io();
        let currentFilter = 'all';
        let captureCount = 0;
        let isPaused = false;
        let connectedDevices = {};
        let recentCaptures = [];

        // Connection status
        socket.on('connect', function() {
            document.getElementById('connectionStatus').className = 'connection-status connected';
            document.getElementById('statusText').textContent = '🟢 Connected';
            console.log('Connected to server');
        });

        socket.on('disconnect', function() {
            document.getElementById('connectionStatus').className = 'connection-status disconnected';
            document.getElementById('statusText').textContent = '🔴 Disconnected';
            console.log('Disconnected from server');
        });

        // Enhanced live data handlers
        socket.on('live_capture', function(data) {
            if (!isPaused) {
                addLiveCapture(data);
                updateCardAnalysis(data);
                addCaptureToManipulationList(data);
            }
            updateStats();
        });

        socket.on('device_connected', function(data) {
            addDevice(data);
            updateStats();
        });

        socket.on('device_disconnected', function(data) {
            removeDevice(data);
            updateStats();
        });

        socket.on('device_paired', function(data) {
            updateDevicePairing(data);
        });

        socket.on('manipulation_applied', function(data) {
            addManipulationToLog(data);
        });

        socket.on('stats_update', function(data) {
            updateStatsDisplay(data);
        });

        // Enhanced capture display with device info and card analysis
        function addLiveCapture(capture) {
            if (currentFilter !== 'all' && capture.capture_type !== currentFilter) {
                return;
            }

            const liveFeed = document.getElementById('liveFeed');
            const captureDiv = document.createElement('div');
            captureDiv.className = 'capture-item';
            
            if (capture.is_manipulated) {
                captureDiv.classList.add('manipulated');
            }
            
            const timestamp = new Date(capture.timestamp).toLocaleTimeString();
            
            // Create card info badges
            let cardBadges = '';
            if (capture.card_brand && capture.card_brand !== 'Unknown') {
                cardBadges += `<span class="card-badge">${capture.card_brand}</span>`;
            }
            if (capture.card_type && capture.card_type !== 'Unknown') {
                cardBadges += `<span class="card-badge">${capture.card_type}</span>`;
            }
            
            // Create IP information
            let ipInfo = '';
            if (capture.reader_ip || capture.emulator_ip) {
                ipInfo = `<div class="capture-ips">
                    📡 Reader: ${capture.reader_ip || 'Unknown'} 
                    ${capture.emulator_ip ? '🔄 Emulator: ' + capture.emulator_ip : ''}
                </div>`;
            }
            
            // Create manipulation info
            let manipulationInfo = '';
            if (capture.is_manipulated) {
                manipulationInfo = `<div class="capture-manipulation">
                    🛠️ MANIPULATED (${capture.manipulation_type})
                </div>`;
            }
            
            captureDiv.innerHTML = `
                <div class="capture-header">
                    <span class="capture-id">${capture.capture_id}</span>
                    <span class="capture-time">${timestamp}</span>
                </div>
                <div class="capture-details">
                    <strong>Reader:</strong> ${capture.reader_id} | 
                    <strong>Tag:</strong> ${capture.tag_uid} | 
                    <strong>Protocol:</strong> ${capture.protocol} |
                    <strong>Type:</strong> ${capture.capture_type}
                </div>
                ${cardBadges}
                ${ipInfo}
                <div class="capture-data">
                    <strong>Command:</strong> ${capture.command}<br>
                    <strong>Response:</strong> ${capture.response}<br>
                    <strong>Data:</strong> ${capture.data_hex}
                </div>
                ${manipulationInfo}
            `;
            
            liveFeed.insertBefore(captureDiv, liveFeed.firstChild);
            
            // Keep only last 50 captures
            while (liveFeed.children.length > 50) {
                liveFeed.removeChild(liveFeed.lastChild);
            }

            captureCount++;
            document.getElementById('liveCaptures').textContent = captureCount;
            
            // Store for manipulation
            recentCaptures.unshift(capture);
            if (recentCaptures.length > 100) {
                recentCaptures.pop();
            }
        }

        // Device management functions
        function addDevice(device) {
            connectedDevices[device.device_id] = device;
            updateDeviceGrid();
        }

        function removeDevice(device) {
            delete connectedDevices[device.device_id];
            updateDeviceGrid();
        }

        function updateDeviceGrid() {
            const deviceGrid = document.getElementById('deviceGrid');
            deviceGrid.innerHTML = '';
            
            if (Object.keys(connectedDevices).length === 0) {
                deviceGrid.innerHTML = '<div class="log-entry log-info">No devices connected</div>';
                return;
            }
            
            Object.values(connectedDevices).forEach(device => {
                const deviceCard = document.createElement('div');
                deviceCard.className = `device-card ${device.device_type}`;
                
                if (device.paired_device) {
                    deviceCard.classList.add('paired');
                }
                
                const deviceIcon = {
                    'reader': '📡',
                    'emulator': '🔄',
                    'analyzer': '🔍'
                }[device.device_type] || '📱';
                
                deviceCard.innerHTML = `
                    <div class="device-name">${deviceIcon} ${device.device_name}</div>
                    <div class="device-ip">📍 ${device.ip_address}:${device.port}</div>
                    <div class="device-status ${device.status}">${device.status}</div>
                    ${device.paired_device ? '<div style="margin-top:5px;">🔗 Paired</div>' : ''}
                `;
                
                deviceCard.onclick = () => selectDevice(device.device_id);
                deviceGrid.appendChild(deviceCard);
            });
        }

        // Card analysis display
        function updateCardAnalysis(capture) {
            if (!capture.card_brand || capture.card_brand === 'Unknown') {
                return;
            }
            
            const cardAnalysis = document.getElementById('cardAnalysis');
            const cardInfo = document.createElement('div');
            cardInfo.className = 'card-info';
            
            cardInfo.innerHTML = `
                <div class="card-header">
                    <span class="card-brand">💳 ${capture.card_brand}</span>
                    <span class="card-type">${capture.card_type}</span>
                </div>
                <div class="card-details">
                    <div><strong>Issuer:</strong> ${capture.card_issuer}</div>
                    <div><strong>Capture:</strong> ${capture.capture_id}</div>
                    <div><strong>Protocol:</strong> ${capture.protocol}</div>
                    <div><strong>Frequency:</strong> ${capture.frequency}</div>
                </div>
            `;
            
            cardAnalysis.insertBefore(cardInfo, cardAnalysis.firstChild);
            
            // Keep only last 10 card analyses
            while (cardAnalysis.children.length > 10) {
                cardAnalysis.removeChild(cardAnalysis.lastChild);
            }
        }

        // Manipulation functions
        function addCaptureToManipulationList(capture) {
            const captureSelect = document.getElementById('captureSelect');
            const option = document.createElement('option');
            option.value = capture.capture_id;
            option.textContent = `${capture.capture_id} - ${capture.reader_id} - ${capture.command}`;
            captureSelect.insertBefore(option, captureSelect.children[1]);
            
            // Keep only last 20 captures in select
            while (captureSelect.children.length > 21) {
                captureSelect.removeChild(captureSelect.lastChild);
            }
        }

        function applyManipulation() {
            const captureId = document.getElementById('captureSelect').value;
            const manipulationType = document.getElementById('manipulationType').value;
            const newCommand = document.getElementById('newCommand').value;
            const newResponse = document.getElementById('newResponse').value;
            const reason = document.getElementById('manipulationReason').value;
            
            if (!captureId) {
                alert('Please select a capture to manipulate');
                return;
            }
            
            socket.emit('apply_manipulation', {
                capture_id: captureId,
                manipulation_type: manipulationType,
                new_command: newCommand,
                new_response: newResponse,
                reason: reason,
                operator_id: 'web_admin'
            });
            
            // Clear form
            document.getElementById('newCommand').value = '';
            document.getElementById('newResponse').value = '';
            document.getElementById('manipulationReason').value = '';
        }

        function addManipulationToLog(data) {
            const manipulationLog = document.getElementById('manipulationLog');
            const entry = document.createElement('div');
            entry.className = 'manipulation-entry';
            
            const timestamp = new Date().toLocaleTimeString();
            
            entry.innerHTML = `
                <div class="manipulation-header">
                    🛠️ ${data.manipulation_type.toUpperCase()} - ${data.manipulation_id}
                </div>
                <div class="manipulation-details">
                    <strong>Time:</strong> ${timestamp}<br>
                    <strong>Capture:</strong> ${data.capture_id}<br>
                    <strong>Original Command:</strong> ${data.original_command}<br>
                    <strong>Modified Command:</strong> ${data.modified_command}<br>
                    <strong>Status:</strong> ${data.success ? '✅ Success' : '❌ Failed'}
                </div>
            `;
            
            manipulationLog.insertBefore(entry, manipulationLog.firstChild);
            
            // Keep only last 20 manipulations
            while (manipulationLog.children.length > 20) {
                manipulationLog.removeChild(manipulationLog.lastChild);
            }
        }

        // Control functions
        function pauseCaptures() {
            isPaused = !isPaused;
            const pauseBtn = document.getElementById('pauseBtn');
            pauseBtn.textContent = isPaused ? '▶️ Resume' : '⏸️ Pause';
            pauseBtn.style.background = isPaused ? '#4CAF50' : '#ff9800';
        }

        function clearCaptures() {
            document.getElementById('liveFeed').innerHTML = '<div class="log-entry log-info">Captures cleared</div>';
            captureCount = 0;
            document.getElementById('liveCaptures').textContent = '0';
        }

        function exportCaptures() {
            socket.emit('export_captures', {format: 'json'});
        }

        function refreshDevices() {
            socket.emit('refresh_devices');
        }

        function pairDevices() {
            // Simple pairing - pair first reader with first emulator
            const readers = Object.values(connectedDevices).filter(d => d.device_type === 'reader');
            const emulators = Object.values(connectedDevices).filter(d => d.device_type === 'emulator');
            
            if (readers.length > 0 && emulators.length > 0) {
                socket.emit('pair_devices', {
                    reader_id: readers[0].device_id,
                    emulator_id: emulators[0].device_id
                });
            } else {
                alert('Need at least one reader and one emulator to pair');
            }
        }

        function showDeviceMap() {
            // Create a simple network topology view
            alert('Network Map feature coming soon!');
        }

        function updateStats() {
            socket.emit('request_stats');
        }

        function updateStatsDisplay(stats) {
            document.getElementById('liveCaptures').textContent = stats.live_captures || 0;
            document.getElementById('connectedClients').textContent = stats.connected_clients || 0;
            document.getElementById('activeSessions').textContent = stats.active_sessions || 0;
            document.getElementById('totalTransactions').textContent = stats.total_transactions || 0;
        }

        function startNewSession() {
            const sessionName = document.getElementById('sessionName').value || 'Unnamed Session';
            socket.emit('start_session', {name: sessionName});
            document.getElementById('sessionName').value = '';
        }

        function exportData() {
            socket.emit('export_data');
        }

        function clearLogs() {
            document.getElementById('liveFeed').innerHTML = '<div class="log-entry log-info">Logs cleared</div>';
            document.getElementById('clientsList').innerHTML = '<div class="log-entry log-info">Client list cleared</div>';
            captureCount = 0;
            document.getElementById('liveCaptures').textContent = '0';
        }

        function refreshStats() {
            updateStats();
            location.reload();
        }

        function applyFilter() {
            currentFilter = document.getElementById('filterType').value;
            clearLogs();
        }

        // Initialize
        window.onload = function() {
            updateStats();
        };
    </script>
</body>
</html>
"""

# Flask Routes
@app.route('/')
def index():
    """Main admin panel page"""
    return render_template_string(MAIN_TEMPLATE)

@app.route('/api/rfid_data', methods=['POST'])
def receive_rfid_data():
    """API endpoint to receive RFID data from external clients"""
    try:
        data = request.json
        
        # Validate data exists
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Parse and save the RFID capture
        capture = rfid_receiver.parse_rfid_data(data)
        success = db_manager.save_live_capture(capture)
        
        if success:
            # Broadcast to connected web clients
            socketio.emit('live_capture', asdict(capture))
            
            logger.info(f"✅ Received RFID data: {capture.capture_id}")
            return jsonify({
                'status': 'success',
                'capture_id': capture.capture_id,
                'message': 'RFID data received and processed'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save RFID data'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error processing RFID data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/test_transaction', methods=['POST'])
def receive_test_transaction():
    """API endpoint to receive test transaction data"""
    try:
        data = request.json
        
        # Validate data exists
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Create online test transaction
        transaction_id = f"ONLINE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
        # Parse live captures if included
        live_captures = []
        if 'live_captures' in data and data['live_captures']:
            for capture_data in data['live_captures']:
                capture = rfid_receiver.parse_rfid_data(capture_data)
                live_captures.append(capture)
        
        transaction = OnlineTestTransaction(
            transaction_id=transaction_id,
            session_id=data.get('session_id', 'default'),
            card_hash=hashlib.sha256(data.get('card_pan', '').encode()).hexdigest(),
            card_brand=data.get('card_brand', 'Unknown'),
            card_type=data.get('card_type', 'Standard'),
            issuer_country=data.get('issuer_country', 'Unknown'),
            currency_code=data.get('currency_code', 'USD'),
            terminal_type=data.get('terminal_type', 'POS'),
            bypass_method=data.get('bypass_method', 'unknown'),
            tlv_data=data.get('tlv_data', ''),
            execution_time_ms=int(data.get('execution_time_ms', 0)),
            success=bool(data.get('success', False)),
            live_captures=live_captures,
            error_message=data.get('error_message'),
            test_timestamp=datetime.now().isoformat(),
            remote_client_id=data.get('client_id', 'unknown')
        )
        
        # Save transaction
        success = db_manager.save_online_transaction(transaction)
        
        if success:
            # Broadcast to connected web clients
            socketio.emit('new_transaction', asdict(transaction))
            
            logger.info(f"✅ Received test transaction: {transaction_id}")
            return jsonify({
                'status': 'success',
                'transaction_id': transaction_id,
                'message': 'Test transaction received and processed'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save test transaction'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error processing test transaction: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/register_device', methods=['POST'])
def register_device():
    """API endpoint for devices to register with enhanced info"""
    try:
        data = request.json
        
        # Validate data exists
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Enhanced device registration
        device_data = {
            'device_id': data.get('device_id', str(uuid.uuid4())),
            'name': data.get('name', 'Unknown Device'),
            'type': data.get('type', 'reader'),  # reader, emulator, analyzer
            'ip_address': request.remote_addr,
            'port': int(data.get('port', 0)),
            'capabilities': data.get('capabilities', {}),
            'paired_device': data.get('paired_device', ''),
            'throughput_bps': float(data.get('throughput_bps', 0.0)),
            'latency_ms': float(data.get('latency_ms', 0.0))
        }
        
        device = rfid_receiver.register_device(device_data)
        
        # Broadcast to web clients
        socketio.emit('device_connected', {
            'device_id': device.device_id,
            'device_name': device.device_name,
            'device_type': device.device_type,
            'ip_address': device.ip_address,
            'port': device.port,
            'status': device.status,
            'paired_device': device.paired_device
        })
        
        logger.info(f"✅ Device registered: {device.device_id} ({device.device_type})")
        return jsonify({
            'status': 'success',
            'device_id': device.device_id,
            'message': 'Device registered successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Error registering device: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/pair_devices', methods=['POST'])
def pair_devices():
    """API endpoint to pair reader with emulator"""
    try:
        data = request.json
        
        # Validate data exists
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
            
        reader_id = data.get('reader_id')
        emulator_id = data.get('emulator_id')
        
        if not reader_id or not emulator_id:
            return jsonify({
                'status': 'error',
                'message': 'Both reader_id and emulator_id required'
            }), 400
        
        success = rfid_receiver.pair_devices(reader_id, emulator_id)
        
        if success:
            # Broadcast pairing to web clients
            socketio.emit('device_paired', {
                'reader_id': reader_id,
                'emulator_id': emulator_id,
                'status': 'paired'
            })
            
            return jsonify({
                'status': 'success',
                'message': f'Devices paired: {reader_id} <-> {emulator_id}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to pair devices'
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error pairing devices: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/manipulate_communication', methods=['POST'])
def manipulate_communication():
    """API endpoint to manually manipulate RFID communication"""
    try:
        data = request.json
        
        # Validate data exists
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        capture_id = data.get('capture_id')
        operator_id = data.get('operator_id', 'api_user')
        manipulation_type = data.get('manipulation_type', 'modify')
        new_command = data.get('new_command', '')
        new_response = data.get('new_response', '')
        reason = data.get('reason', 'Manual manipulation via API')
        
        if not capture_id:
            return jsonify({
                'status': 'error',
                'message': 'capture_id is required'
            }), 400
        
        result = rfid_receiver.manipulate_communication(
            capture_id, operator_id, manipulation_type, 
            new_command, new_response, reason
        )
        
        if result['success']:
            # Broadcast manipulation to web clients
            socketio.emit('manipulation_applied', result)
            
            logger.info(f"✅ Communication manipulated: {capture_id}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Error manipulating communication: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/get_devices')
def get_devices():
    """Get list of connected devices"""
    try:
        devices = []
        for device in rfid_receiver.connected_devices.values():
            devices.append({
                'device_id': device.device_id,
                'device_name': device.device_name,
                'device_type': device.device_type,
                'ip_address': device.ip_address,
                'port': device.port,
                'status': device.status,
                'paired_device': device.paired_device,
                'connection_time': device.connection_time,
                'last_activity': device.last_activity,
                'throughput_bps': device.throughput_bps,
                'latency_ms': device.latency_ms
            })
        
        return jsonify({
            'devices': devices,
            'total_count': len(devices)
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting devices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_card_analysis/<capture_id>')
def get_card_analysis(capture_id):
    """Get detailed card analysis for a specific capture"""
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM card_analysis 
                WHERE capture_id = ?
            """, (capture_id,))
            
            row = cursor.fetchone()
            if row:
                analysis = dict(row)
                analysis['track_data'] = json.loads(analysis['track_data'] or '{}')
                analysis['chip_capabilities'] = json.loads(analysis['chip_capabilities'] or '[]')
                return jsonify(analysis)
            else:
                return jsonify({'error': 'Card analysis not found'}), 404
                
    except Exception as e:
        logger.error(f"❌ Error getting card analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get current system statistics"""
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            # Get statistics
            cursor = conn.execute("SELECT COUNT(*) FROM live_rfid_captures")
            live_captures = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM online_test_transactions")
            total_transactions = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM connected_clients WHERE status = 'connected'")
            connected_clients = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM live_sessions WHERE status = 'active'")
            active_sessions = cursor.fetchone()[0]
            
        return jsonify({
            'live_captures': live_captures,
            'total_transactions': total_transactions,
            'connected_clients': connected_clients,
            'active_sessions': active_sessions
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

# Enhanced SocketIO Events
@socketio.on('connect')
def handle_connect():
    """Handle web client connection"""
    logger.info(f"✅ Web client connected")
    emit('connected', {'message': 'Connected to Enhanced Online Admin Panel'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle web client disconnection"""
    logger.info(f"🔴 Web client disconnected")

@socketio.on('request_stats')
def handle_stats_request():
    """Handle stats request from web client"""
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM live_rfid_captures")
            live_captures = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM online_test_transactions")
            total_transactions = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM device_connections WHERE status = 'connected'")
            connected_devices = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM live_sessions WHERE status = 'active'")
            active_sessions = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM manipulation_log")
            total_manipulations = cursor.fetchone()[0]
            
        emit('stats_update', {
            'live_captures': live_captures,
            'total_transactions': total_transactions,
            'connected_devices': connected_devices,
            'active_sessions': active_sessions,
            'total_manipulations': total_manipulations
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")

@socketio.on('refresh_devices')
def handle_refresh_devices():
    """Handle device refresh request"""
    try:
        devices = []
        for device in rfid_receiver.connected_devices.values():
            devices.append({
                'device_id': device.device_id,
                'device_name': device.device_name,
                'device_type': device.device_type,
                'ip_address': device.ip_address,
                'port': device.port,
                'status': device.status,
                'paired_device': device.paired_device,
                'connection_time': device.connection_time,
                'last_activity': device.last_activity
            })
        
        emit('devices_list', {'devices': devices})
        
    except Exception as e:
        logger.error(f"❌ Error refreshing devices: {e}")
        emit('error', {'message': str(e)})

@socketio.on('pair_devices')
def handle_pair_devices(data):
    """Handle device pairing request"""
    try:
        reader_id = data.get('reader_id')
        emulator_id = data.get('emulator_id')
        
        if not reader_id or not emulator_id:
            emit('error', {'message': 'Both reader_id and emulator_id required'})
            return
        
        success = rfid_receiver.pair_devices(reader_id, emulator_id)
        
        if success:
            emit('device_paired', {
                'reader_id': reader_id,
                'emulator_id': emulator_id,
                'status': 'paired',
                'message': f'Devices paired successfully'
            })
            
            # Broadcast to all clients
            socketio.emit('device_paired', {
                'reader_id': reader_id,
                'emulator_id': emulator_id,
                'status': 'paired'
            })
            
            logger.info(f"✅ Devices paired via WebSocket: {reader_id} <-> {emulator_id}")
        else:
            emit('error', {'message': 'Failed to pair devices'})
            
    except Exception as e:
        logger.error(f"❌ Error pairing devices: {e}")
        emit('error', {'message': str(e)})

@socketio.on('apply_manipulation')
def handle_apply_manipulation(data):
    """Handle communication manipulation request"""
    try:
        capture_id = data.get('capture_id')
        operator_id = data.get('operator_id', 'web_admin')
        manipulation_type = data.get('manipulation_type', 'modify')
        new_command = data.get('new_command', '')
        new_response = data.get('new_response', '')
        reason = data.get('reason', 'Manual manipulation via web interface')
        
        if not capture_id:
            emit('error', {'message': 'capture_id is required'})
            return
        
        result = rfid_receiver.manipulate_communication(
            capture_id, operator_id, manipulation_type, 
            new_command, new_response, reason
        )
        
        if result['success']:
            emit('manipulation_applied', result)
            
            # Broadcast to all clients
            socketio.emit('manipulation_applied', result)
            
            logger.info(f"✅ Communication manipulated via WebSocket: {capture_id}")
        else:
            emit('error', {'message': result.get('error', 'Manipulation failed')})
            
    except Exception as e:
        logger.error(f"❌ Error applying manipulation: {e}")
        emit('error', {'message': str(e)})

@socketio.on('export_captures')
def handle_export_captures(data):
    """Handle capture export request"""
    try:
        export_format = data.get('format', 'json')
        export_filename = f"enhanced_captures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'export_type': 'enhanced_online_admin_panel',
            'live_captures': [],
            'devices': [],
            'manipulations': [],
            'card_analysis': []
        }
        
        # Export live captures with enhanced data
        with sqlite3.connect(db_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Captures
            cursor = conn.execute("""
                SELECT * FROM live_rfid_captures 
                ORDER BY timestamp DESC LIMIT 1000
            """)
            for row in cursor.fetchall():
                capture_data = dict(row)
                capture_data['parsed_tlv'] = json.loads(capture_data['parsed_tlv'] or '{}')
                export_data['live_captures'].append(capture_data)
            
            # Devices
            cursor = conn.execute("""
                SELECT * FROM device_connections 
                ORDER BY connection_time DESC
            """)
            for row in cursor.fetchall():
                device_data = dict(row)
                device_data['capabilities'] = json.loads(device_data['capabilities'] or '{}')
                export_data['devices'].append(device_data)
            
            # Manipulations
            cursor = conn.execute("""
                SELECT * FROM manipulation_log 
                ORDER BY timestamp DESC LIMIT 500
            """)
            for row in cursor.fetchall():
                export_data['manipulations'].append(dict(row))
            
            # Card analysis
            cursor = conn.execute("""
                SELECT * FROM card_analysis 
                ORDER BY analysis_timestamp DESC LIMIT 500
            """)
            for row in cursor.fetchall():
                analysis_data = dict(row)
                analysis_data['track_data'] = json.loads(analysis_data['track_data'] or '{}')
                analysis_data['chip_capabilities'] = json.loads(analysis_data['chip_capabilities'] or '[]')
                export_data['card_analysis'].append(analysis_data)
        
        # Save export file
        with open(export_filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        emit('export_complete', {
            'filename': export_filename,
            'captures': len(export_data['live_captures']),
            'devices': len(export_data['devices']),
            'manipulations': len(export_data['manipulations']),
            'card_analysis': len(export_data['card_analysis']),
            'message': f'Enhanced data exported to {export_filename}'
        })
        
        logger.info(f"✅ Enhanced data exported: {export_filename}")
        
    except Exception as e:
        logger.error(f"❌ Error exporting captures: {e}")
        emit('error', {'message': str(e)})

@socketio.on('start_session')
def handle_start_session(data):
    """Handle new session start request"""
    try:
        session_id = str(uuid.uuid4())
        session_name = data.get('name', 'Unnamed Session')
        
        # Create new session in database
        with sqlite3.connect(db_manager.db_path) as conn:
            conn.execute("""
                INSERT INTO live_sessions 
                (session_id, session_name, client_id, start_time, session_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id, session_name, 'web_admin',
                datetime.now().isoformat(), json.dumps({'created_by': 'web_admin'})
            ))
            conn.commit()
        
        emit('session_started', {
            'session_id': session_id,
            'session_name': session_name,
            'message': f'Session "{session_name}" started successfully'
        })
        
        logger.info(f"✅ New session started: {session_name} ({session_id})")
        
    except Exception as e:
        logger.error(f"❌ Error starting session: {e}")
        emit('error', {'message': str(e)})

@socketio.on('export_data')
def handle_export_data():
    """Handle data export request"""
    try:
        export_filename = f"online_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'export_type': 'online_admin_panel',
            'live_captures': [],
            'transactions': []
        }
        
        # Export live captures
        captures = db_manager.get_live_captures(limit=1000)
        for capture in captures:
            export_data['live_captures'].append(asdict(capture))
        
        # Export transactions
        with sqlite3.connect(db_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM online_test_transactions 
                ORDER BY created_date DESC LIMIT 1000
            """)
            
            for row in cursor.fetchall():
                transaction_data = dict(row)
                export_data['transactions'].append(transaction_data)
        
        # Save export file
        with open(export_filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        emit('export_complete', {
            'filename': export_filename,
            'captures': len(export_data['live_captures']),
            'transactions': len(export_data['transactions']),
            'message': f'Data exported to {export_filename}'
        })
        
        logger.info(f"✅ Data exported: {export_filename}")
        
    except Exception as e:
        logger.error(f"❌ Error exporting data: {e}")
        emit('error', {'message': str(e)})

def main():
    """Main function to start the online admin panel"""
    print("🌐 ONLINE ADMIN PANEL - Live RFID Communication & Test Management")
    print("=" * 80)
    print()
    print("Features:")
    print("  🔴 Live RFID Data Reception")
    print("  📊 Real-time Communication Monitoring")
    print("  💾 SQLite3 Database Integration")
    print("  🌐 Web-based Interface")
    print("  📡 REST API Endpoints")
    print("  🔌 WebSocket Live Updates")
    print()
    
    try:
        # Get local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print(f"🚀 Starting online admin panel...")
        print(f"📍 Local access: http://localhost:5000")
        print(f"🌐 Network access: http://{local_ip}:5000")
        print(f"💾 Database: {db_manager.db_path}")
        print()
        print("📡 API Endpoints:")
        print(f"  POST http://{local_ip}:5000/api/rfid_data - Receive RFID captures")
        print(f"  POST http://{local_ip}:5000/api/test_transaction - Receive test transactions")
        print(f"  POST http://{local_ip}:5000/api/register_client - Register client")
        print(f"  GET  http://{local_ip}:5000/api/stats - Get statistics")
        print()
        print("🔌 WebSocket Events:")
        print("  live_capture - Real-time RFID captures")
        print("  new_transaction - New test transactions")
        print("  client_connected/disconnected - Client status")
        print()
        print("✅ Online admin panel ready for connections!")
        print("=" * 80)
        
        # Start Flask-SocketIO server
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Online admin panel stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting online admin panel: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
