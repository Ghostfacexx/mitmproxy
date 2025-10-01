#!/usr/bin/env python3
"""
📡 RFID Data Sender Client - Send Live RFID Captures to Online Admin Panel
This client simulates or forwards real RFID reader data to the online admin panel.
"""

import json
import time
import requests
import threading
import hashlib
import random
from datetime import datetime
from typing import Dict, List
import uuid

class RFIDDataSender:
    """Client to send RFID data to online admin panel"""
    
    def __init__(self, server_url: str = "http://localhost:5000", client_name: str = "RFID Reader Client"):
        self.server_url = server_url
        self.client_name = client_name
        self.client_id = None
        self.session_id = str(uuid.uuid4())
        self.is_running = False
        
        # Sample TLV data for simulation
        self.sample_tlv_data = [
            "9F34:010203|9F26:1234567890ABCDEF|9F27:40",
            "9F33:E0F8C8|9F35:22|9F40:6000F0A001",
            "4F:A0000000031010|50:VISA|87:01",
            "9F02:000000001000|9F03:000000000000|5F2A:0840",
            "9F37:12345678|9A:250716|9C:00|9F07:FF00",
            "8E:000000000000000042031E031F00|9F0D:F040A48000|9F0E:0000000000|9F0F:F040ACB000",
            "DF12:VISA CONTACTLESS|9F38:9F66049F02069F03069F1A0295055F2A029A039C019F37049F35019F45029F4C089F34039F21039F7C14",
            "9F32:03|90:123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF012345",
            "9F46:1234567890ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF|9F47:03"
        ]
        
        self.card_brands = ["Visa", "Mastercard", "American Express", "Discover"]
        self.protocols = ["ISO14443A", "ISO14443B", "ISO15693"]
        self.terminal_types = ["POS", "ATM", "Mobile", "Transit", "Contactless"]
        self.bypass_methods = ["CDCVM", "Signature", "No_CVM", "PIN", "Contactless"]
    
    def register_client(self) -> bool:
        """Register this client with the online admin panel"""
        try:
            client_data = {
                "name": self.client_name,
                "type": "rfid_reader",
                "capabilities": {
                    "protocols": self.protocols,
                    "frequency": "13.56MHz",
                    "max_distance": "10cm",
                    "supports_sniffing": True,
                    "supports_emulation": True
                },
                "version": "1.0"
            }
            
            response = requests.post(
                f"{self.server_url}/api/register_client",
                json=client_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.client_id = result.get('client_id')
                print(f"✅ Client registered successfully: {self.client_id}")
                print(f"📍 Server response: {result.get('message')}")
                return True
            else:
                print(f"❌ Failed to register client: {response.status_code}")
                print(f"📍 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error registering client: {e}")
            return False
    
    def send_rfid_capture(self, capture_data: Dict) -> bool:
        """Send RFID capture data to the online admin panel"""
        try:
            response = requests.post(
                f"{self.server_url}/api/rfid_data",
                json=capture_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RFID capture sent: {result.get('capture_id')}")
                return True
            else:
                print(f"❌ Failed to send RFID capture: {response.status_code}")
                print(f"📍 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending RFID capture: {e}")
            return False
    
    def send_test_transaction(self, transaction_data: Dict) -> bool:
        """Send test transaction data to the online admin panel"""
        try:
            response = requests.post(
                f"{self.server_url}/api/test_transaction",
                json=transaction_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test transaction sent: {result.get('transaction_id')}")
                return True
            else:
                print(f"❌ Failed to send test transaction: {response.status_code}")
                print(f"📍 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending test transaction: {e}")
            return False
    
    def generate_sample_capture(self) -> Dict:
        """Generate sample RFID capture data"""
        reader_id = f"READER_{random.randint(1, 5):02d}"
        tag_uid = ''.join([f"{random.randint(0, 255):02X}" for _ in range(7)])
        
        commands = [
            "RATS", "SELECT", "READ_BINARY", "GET_CHALLENGE", "VERIFY",
            "GET_PROCESSING_OPTIONS", "READ_RECORD", "GENERATE_AC",
            "GET_DATA", "COMPUTE_CRYPTOGRAPHIC_CHECKSUM"
        ]
        
        command = random.choice(commands)
        response_length = random.randint(4, 32)
        response = ''.join([f"{random.randint(0, 255):02X}" for _ in range(response_length)])
        
        data_length = random.randint(8, 64)
        data_hex = ''.join([f"{random.randint(0, 255):02X}" for _ in range(data_length)])
        
        capture_data = {
            "timestamp": datetime.now().isoformat(),
            "reader_id": reader_id,
            "tag_uid": tag_uid,
            "command": command,
            "response": response,
            "protocol": random.choice(self.protocols),
            "frequency": "13.56MHz",
            "data_hex": data_hex,
            "tlv_data": random.choice(self.sample_tlv_data),
            "signal_strength": round(random.uniform(-60.0, -20.0), 2),
            "error_rate": round(random.uniform(0.0, 5.0), 2),
            "session_id": self.session_id,
            "capture_type": random.choice(["sniffed", "test", "live"])
        }
        
        return capture_data
    
    def generate_sample_transaction(self) -> Dict:
        """Generate sample test transaction"""
        card_pan = f"4{random.randint(100000000000000, 999999999999999)}"  # Visa test PAN
        
        transaction_data = {
            "session_id": self.session_id,
            "card_pan": card_pan,
            "card_brand": random.choice(self.card_brands),
            "card_type": random.choice(["Standard", "Gold", "Platinum", "Corporate"]),
            "issuer_country": random.choice(["US", "GB", "DE", "FR", "CA", "AU"]),
            "currency_code": random.choice(["USD", "EUR", "GBP", "CAD", "AUD"]),
            "terminal_type": random.choice(self.terminal_types),
            "bypass_method": random.choice(self.bypass_methods),
            "tlv_data": random.choice(self.sample_tlv_data),
            "execution_time_ms": random.randint(50, 500),
            "success": random.choice([True, True, True, False]),  # 75% success rate
            "client_id": self.client_id,
            "live_captures": []
        }
        
        # Add some live captures to the transaction
        for _ in range(random.randint(1, 3)):
            capture = self.generate_sample_capture()
            capture["capture_type"] = "test"
            transaction_data["live_captures"].append(capture)
        
        # Add error message if transaction failed
        if not transaction_data["success"]:
            errors = [
                "Authentication failed",
                "Invalid cryptogram",
                "Card blocked",
                "Insufficient funds",
                "Terminal error",
                "Communication timeout"
            ]
            transaction_data["error_message"] = random.choice(errors)
        
        return transaction_data
    
    def start_live_simulation(self, interval: float = 2.0):
        """Start live simulation of RFID captures"""
        self.is_running = True
        
        def simulation_loop():
            capture_count = 0
            transaction_count = 0
            
            while self.is_running:
                try:
                    # Send RFID capture
                    if random.random() < 0.8:  # 80% chance for capture
                        capture = self.generate_sample_capture()
                        if self.send_rfid_capture(capture):
                            capture_count += 1
                    
                    # Send test transaction occasionally
                    if random.random() < 0.3:  # 30% chance for transaction
                        transaction = self.generate_sample_transaction()
                        if self.send_test_transaction(transaction):
                            transaction_count += 1
                    
                    print(f"📊 Sent: {capture_count} captures, {transaction_count} transactions")
                    
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Simulation stopped by user")
                    break
                except Exception as e:
                    print(f"❌ Error in simulation loop: {e}")
                    time.sleep(1)
            
            self.is_running = False
            print(f"✅ Simulation completed: {capture_count} captures, {transaction_count} transactions sent")
        
        simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        simulation_thread.start()
        
        return simulation_thread
    
    def stop_simulation(self):
        """Stop the live simulation"""
        self.is_running = False
    
    def send_custom_capture(self, reader_id: str, tag_uid: str, tlv_data: str, 
                           protocol: str = "ISO14443A", capture_type: str = "live") -> bool:
        """Send custom RFID capture"""
        capture_data = {
            "timestamp": datetime.now().isoformat(),
            "reader_id": reader_id,
            "tag_uid": tag_uid,
            "command": "CUSTOM",
            "response": "9000",  # Success response
            "protocol": protocol,
            "frequency": "13.56MHz",
            "data_hex": tlv_data.replace(":", "").replace("|", ""),
            "tlv_data": tlv_data,
            "signal_strength": -30.0,
            "error_rate": 0.0,
            "session_id": self.session_id,
            "capture_type": capture_type
        }
        
        return self.send_rfid_capture(capture_data)

def main():
    """Main function"""
    print("📡 RFID Data Sender Client")
    print("=" * 50)
    print()
    
    # Configuration
    server_url = input("🌐 Server URL (default: http://localhost:5000): ").strip()
    if not server_url:
        server_url = "http://localhost:5000"
    
    client_name = input("📛 Client name (default: RFID Reader Client): ").strip()
    if not client_name:
        client_name = "RFID Reader Client"
    
    print()
    print(f"🔧 Configuration:")
    print(f"  Server: {server_url}")
    print(f"  Client: {client_name}")
    print()
    
    # Create client
    client = RFIDDataSender(server_url, client_name)
    
    # Register with server
    print("📝 Registering client...")
    if not client.register_client():
        print("❌ Failed to register client. Exiting...")
        return 1
    
    print()
    print("📋 Available options:")
    print("  1. 🔴 Start live simulation")
    print("  2. 📤 Send single capture")
    print("  3. 🧪 Send test transaction")
    print("  4. 📊 Send custom data")
    print("  q. 🚪 Quit")
    print()
    
    try:
        while True:
            choice = input("👉 Select option: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == '1':
                print("\n🔴 Starting live simulation...")
                interval = float(input("⏱️ Interval between sends (seconds, default: 2.0): ") or "2.0")
                
                thread = client.start_live_simulation(interval)
                
                print("✅ Live simulation started! Press Ctrl+C to stop...")
                try:
                    thread.join()
                except KeyboardInterrupt:
                    client.stop_simulation()
                    print("\n🛑 Live simulation stopped")
                
            elif choice == '2':
                print("\n📤 Sending single RFID capture...")
                capture = client.generate_sample_capture()
                client.send_rfid_capture(capture)
                
            elif choice == '3':
                print("\n🧪 Sending test transaction...")
                transaction = client.generate_sample_transaction()
                client.send_test_transaction(transaction)
                
            elif choice == '4':
                print("\n📊 Send custom RFID data:")
                reader_id = input("📻 Reader ID: ").strip() or "CUSTOM_READER"
                tag_uid = input("🏷️ Tag UID: ").strip() or "1234567890ABCDEF"
                tlv_data = input("📋 TLV Data: ").strip() or "9F34:010203|9F26:1234567890ABCDEF"
                
                success = client.send_custom_capture(reader_id, tag_uid, tlv_data)
                if success:
                    print("✅ Custom capture sent successfully!")
                else:
                    print("❌ Failed to send custom capture")
            
            else:
                print("❌ Invalid option. Please try again.")
            
            print()
    
    except KeyboardInterrupt:
        print("\n\n🛑 Client stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    print("👋 Goodbye!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
