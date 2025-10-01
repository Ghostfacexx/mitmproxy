#!/usr/bin/env python3
"""
📡 Enhanced RFID Client - Device Registration and Live Communication with Admin Panel
Demonstrates device registration, IP tracking, card analysis, and manipulation features.
"""

import json
import time
import requests
import threading
import hashlib
import random
import socket
from datetime import datetime
from typing import Dict, List, Optional
import uuid

class EnhancedRFIDClient:
    """Enhanced RFID client with device registration and advanced features"""
    
    def __init__(self, server_url: str = "http://localhost:5000", device_type: str = "reader"):
        self.server_url = server_url
        self.device_type = device_type  # reader, emulator, analyzer
        self.device_id = str(uuid.uuid4())
        self.device_name = f"{device_type.title()}_{random.randint(1000, 9999)}"
        self.session_id = str(uuid.uuid4())
        self.is_running = False
        self.paired_device = None
        
        # Get local IP
        try:
            hostname = socket.gethostname()
            self.local_ip = socket.gethostbyname(hostname)
        except:
            self.local_ip = "127.0.0.1"
        
        # Device capabilities based on type
        self.capabilities = self.get_device_capabilities()
        
        # Enhanced TLV data with real card examples
        self.real_card_data = [
            {
                "card_brand": "Visa",
                "card_type": "Credit", 
                "aid": "A0000000031010",
                "tlv": "4F:A0000000031010|50:56495341|87:01|9F38:9F66049F02069F03069F1A0295055F2A029A039C019F37049F35019F45029F4C089F34039F21039F7C14|9F33:E0F8C8|9F40:6000F0A001|9F26:1234567890ABCDEF|9F27:40|9F34:010203",
                "issuer_country": "0840"
            },
            {
                "card_brand": "Mastercard",
                "card_type": "Debit",
                "aid": "A0000000041010", 
                "tlv": "4F:A0000000041010|50:4D4153544552434152442044454249542056315350|87:01|9F33:E0F0C8|9F40:6000F0A001|9F26:ABCDEF1234567890|9F27:80|9F34:1E0300",
                "issuer_country": "0276"
            },
            {
                "card_brand": "American Express",
                "card_type": "Credit",
                "aid": "A00000002501",
                "tlv": "4F:A00000002501|50:414D45524943414E2045585052455353|87:01|9F33:E0F8C8|9F40:6000F0A001|9F26:FEDCBA0987654321|9F27:40|9F34:1F0000",
                "issuer_country": "0840"
            }
        ]
        
        self.protocols = ["ISO14443A", "ISO14443B", "ISO15693"]
        self.commands = [
            "RATS", "SELECT", "READ_BINARY", "GET_CHALLENGE", "VERIFY",
            "GET_PROCESSING_OPTIONS", "READ_RECORD", "GENERATE_AC",
            "GET_DATA", "COMPUTE_CRYPTOGRAPHIC_CHECKSUM", "EXTERNAL_AUTHENTICATE"
        ]
    
    def get_device_capabilities(self) -> Dict:
        """Get device capabilities based on type"""
        base_capabilities = {
            "protocols": self.protocols,
            "frequency": "13.56MHz",
            "max_distance": "10cm"
        }
        
        if self.device_type == "reader":
            return {
                **base_capabilities,
                "supports_sniffing": True,
                "supports_emulation": False,
                "can_manipulate": False,
                "max_data_rate": "848kbps",
                "antenna_gain": "3dBi"
            }
        elif self.device_type == "emulator":
            return {
                **base_capabilities,
                "supports_sniffing": False,
                "supports_emulation": True,
                "can_manipulate": True,
                "supported_cards": ["Visa", "Mastercard", "American Express"],
                "emulation_modes": ["card", "reader", "relay"]
            }
        elif self.device_type == "analyzer":
            return {
                **base_capabilities,
                "supports_sniffing": True,
                "supports_emulation": False,
                "can_manipulate": True,
                "analysis_modes": ["passive", "active", "mitm"],
                "capture_formats": ["raw", "decoded", "tlv"]
            }
        else:
            return base_capabilities
    
    def register_device(self) -> bool:
        """Register this device with enhanced information"""
        try:
            device_data = {
                "device_id": self.device_id,
                "name": self.device_name,
                "type": self.device_type,
                "port": random.randint(8000, 9000),
                "capabilities": self.capabilities,
                "throughput_bps": random.uniform(100000, 848000),  # Up to 848kbps
                "latency_ms": random.uniform(1.0, 10.0)
            }
            
            response = requests.post(
                f"{self.server_url}/api/register_device",
                json=device_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.device_id = result.get('device_id', self.device_id)
                print(f"✅ Device registered successfully: {self.device_id}")
                print(f"📍 Device type: {self.device_type}")
                print(f"📡 IP Address: {self.local_ip}")
                print(f"🔧 Capabilities: {list(self.capabilities.keys())}")
                return True
            else:
                print(f"❌ Failed to register device: {response.status_code}")
                print(f"📍 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error registering device: {e}")
            return False
    
    def generate_realistic_capture(self, card_data: Optional[Dict] = None) -> Dict:
        """Generate realistic RFID capture with card analysis data"""
        if not card_data:
            card_data = random.choice(self.real_card_data)
        
        # Generate realistic tag UID for card brand
        if card_data["card_brand"] == "Visa":
            tag_uid = "04" + ''.join([f"{random.randint(0, 255):02X}" for _ in range(6)])
        elif card_data["card_brand"] == "Mastercard":
            tag_uid = "08" + ''.join([f"{random.randint(0, 255):02X}" for _ in range(6)])
        else:
            tag_uid = ''.join([f"{random.randint(0, 255):02X}" for _ in range(7)])
        
        command = random.choice(self.commands)
        
        # Generate appropriate response based on command
        if command in ["SELECT", "GET_PROCESSING_OPTIONS"]:
            response = "9000"  # Success
            data_hex = card_data["aid"] + "6F19840E315041592E5359532E444446303195057569736101"
        elif command == "READ_RECORD":
            response = "9000"
            data_hex = "7081A85F20" + ''.join([f"{random.randint(0, 255):02X}" for _ in range(20)])
        elif command == "GENERATE_AC":
            response = "9000" 
            data_hex = card_data["tlv"].split("|")[0].split(":")[1]  # Use cryptogram
        else:
            response = "9000"
            data_hex = ''.join([f"{random.randint(0, 255):02X}" for _ in range(random.randint(8, 32))])
        
        # Simulate manipulation occasionally
        is_manipulated = random.random() < 0.1  # 10% chance
        manipulation_type = "none"
        original_data = ""
        modified_data = ""
        
        if is_manipulated:
            manipulation_type = random.choice(["intercept", "modify", "replay"])
            original_data = data_hex
            if manipulation_type == "modify":
                # Modify some bytes
                modified_data = data_hex[:8] + "DEADBEEF" + data_hex[16:]
                data_hex = modified_data
            elif manipulation_type == "replay":
                modified_data = "REPLAY_" + data_hex
        
        capture_data = {
            "timestamp": datetime.now().isoformat(),
            "reader_id": self.device_id,
            "tag_uid": tag_uid,
            "command": command,
            "response": response,
            "protocol": random.choice(self.protocols),
            "frequency": "13.56MHz",
            "data_hex": data_hex,
            "tlv_data": card_data["tlv"],
            "signal_strength": round(random.uniform(-60.0, -20.0), 2),
            "error_rate": round(random.uniform(0.0, 2.0), 2),
            "session_id": self.session_id,
            "capture_type": random.choice(["sniffed", "live"]),
            
            # Enhanced fields
            "reader_ip": self.local_ip,
            "emulator_ip": self.paired_device if self.paired_device else "",
            "card_type": card_data["card_type"],
            "card_brand": card_data["card_brand"], 
            "card_issuer": f"{card_data['card_brand']} Bank",
            "manipulation_type": manipulation_type,
            "is_manipulated": is_manipulated,
            "original_data": original_data,
            "modified_data": modified_data
        }
        
        return capture_data
    
    def send_rfid_capture(self, capture_data: Dict) -> bool:
        """Send enhanced RFID capture data"""
        try:
            response = requests.post(
                f"{self.server_url}/api/rfid_data",
                json=capture_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status_icon = "🛠️" if capture_data.get("is_manipulated") else "✅"
                card_info = f"{capture_data.get('card_brand', 'Unknown')} {capture_data.get('card_type', '')}"
                print(f"{status_icon} RFID capture sent: {result.get('capture_id')} ({card_info})")
                return True
            else:
                print(f"❌ Failed to send RFID capture: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending RFID capture: {e}")
            return False
    
    def pair_with_device(self, target_device_id: str) -> bool:
        """Pair this device with another device"""
        try:
            if self.device_type == "reader":
                data = {"reader_id": self.device_id, "emulator_id": target_device_id}
            else:
                data = {"reader_id": target_device_id, "emulator_id": self.device_id}
            
            response = requests.post(
                f"{self.server_url}/api/pair_devices",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.paired_device = target_device_id
                print(f"✅ Device paired successfully with {target_device_id}")
                return True
            else:
                print(f"❌ Failed to pair device: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error pairing device: {e}")
            return False
    
    def manipulate_capture(self, capture_id: str, manipulation_type: str = "modify") -> bool:
        """Demonstrate communication manipulation"""
        try:
            data = {
                "capture_id": capture_id,
                "operator_id": self.device_id,
                "manipulation_type": manipulation_type,
                "new_command": "DEADBEEF" if manipulation_type == "modify" else "",
                "new_response": "CAFEBABE" if manipulation_type == "modify" else "",
                "reason": f"Demonstration manipulation by {self.device_name}"
            }
            
            response = requests.post(
                f"{self.server_url}/api/manipulate_communication",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🛠️ Communication manipulated: {result.get('manipulation_id')}")
                return True
            else:
                print(f"❌ Failed to manipulate communication: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error manipulating communication: {e}")
            return False
    
    def start_enhanced_simulation(self, interval: float = 3.0):
        """Start enhanced simulation with realistic card data"""
        self.is_running = True
        
        def simulation_loop():
            capture_count = 0
            card_types_used = set()
            
            print(f"\n🔴 Starting enhanced {self.device_type} simulation...")
            print(f"📡 Device: {self.device_name} ({self.device_id[:8]}...)")
            print(f"📍 IP: {self.local_ip}")
            print(f"⏱️ Interval: {interval}s")
            print("=" * 60)
            
            while self.is_running:
                try:
                    # Generate realistic capture with card analysis
                    card_data = random.choice(self.real_card_data)
                    capture = self.generate_realistic_capture(card_data)
                    
                    if self.send_rfid_capture(capture):
                        capture_count += 1
                        card_types_used.add(f"{card_data['card_brand']} {card_data['card_type']}")
                        
                        # Show progress
                        if capture_count % 5 == 0:
                            print(f"📊 Progress: {capture_count} captures | Card types: {len(card_types_used)}")
                    
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Simulation stopped by user")
                    break
                except Exception as e:
                    print(f"❌ Error in simulation: {e}")
                    time.sleep(1)
            
            self.is_running = False
            print(f"\n✅ Enhanced simulation completed!")
            print(f"📊 Total captures: {capture_count}")
            print(f"💳 Card types tested: {', '.join(card_types_used)}")
        
        simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        simulation_thread.start()
        return simulation_thread
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.is_running = False

def main():
    """Main function with enhanced device options"""
    print("📡 ENHANCED RFID CLIENT - Device Registration & Live Communication")
    print("=" * 70)
    print()
    
    # Configuration
    server_url = input("🌐 Server URL (default: http://localhost:5000): ").strip()
    if not server_url:
        server_url = "http://localhost:5000"
    
    print("\n📱 Device Types:")
    print("  1. 📡 Reader (captures data from cards)")
    print("  2. 🔄 Emulator (emulates cards)")
    print("  3. 🔍 Analyzer (monitors communications)")
    
    device_choice = input("\n👉 Select device type (1-3, default: 1): ").strip()
    device_types = {"1": "reader", "2": "emulator", "3": "analyzer"}
    device_type = device_types.get(device_choice, "reader")
    
    print(f"\n🔧 Configuration:")
    print(f"  Server: {server_url}")
    print(f"  Device Type: {device_type.title()}")
    print()
    
    # Create enhanced client
    client = EnhancedRFIDClient(server_url, device_type)
    
    # Register device
    print("📝 Registering enhanced device...")
    if not client.register_device():
        print("❌ Failed to register device. Exiting...")
        return 1
    
    print()
    print("📋 Available options:")
    print("  1. 🔴 Start enhanced live simulation")
    print("  2. 📤 Send single realistic capture")
    print("  3. 🔗 Pair with another device")
    print("  4. 🛠️ Demonstrate manipulation")
    print("  5. 📊 Device status")
    print("  q. 🚪 Quit")
    print()
    
    try:
        while True:
            choice = input("👉 Select option: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == '1':
                print(f"\n🔴 Starting enhanced {device_type} simulation...")
                interval = float(input("⏱️ Interval between captures (seconds, default: 3.0): ") or "3.0")
                
                thread = client.start_enhanced_simulation(interval)
                
                print("✅ Enhanced simulation started! Press Ctrl+C to stop...")
                try:
                    thread.join()
                except KeyboardInterrupt:
                    client.stop_simulation()
                    print("\n🛑 Enhanced simulation stopped")
                
            elif choice == '2':
                print(f"\n📤 Sending realistic {device_type} capture...")
                card_data = random.choice(client.real_card_data)
                capture = client.generate_realistic_capture(card_data)
                client.send_rfid_capture(capture)
                
            elif choice == '3':
                print("\n🔗 Device pairing...")
                target_id = input("📱 Enter target device ID: ").strip()
                if target_id:
                    client.pair_with_device(target_id)
                else:
                    print("❌ Device ID required")
                    
            elif choice == '4':
                print("\n🛠️ Communication manipulation demo...")
                capture_id = input("📡 Enter capture ID to manipulate: ").strip()
                if capture_id:
                    manip_type = input("🔧 Manipulation type (intercept/modify/replay, default: modify): ").strip() or "modify"
                    client.manipulate_capture(capture_id, manip_type)
                else:
                    print("❌ Capture ID required")
            
            elif choice == '5':
                print(f"\n📊 Device Status:")
                print(f"  Device ID: {client.device_id}")
                print(f"  Device Name: {client.device_name}")
                print(f"  Device Type: {client.device_type}")
                print(f"  IP Address: {client.local_ip}")
                print(f"  Session ID: {client.session_id}")
                print(f"  Paired Device: {client.paired_device or 'None'}")
                print(f"  Running: {client.is_running}")
                print(f"  Capabilities: {list(client.capabilities.keys())}")
            
            else:
                print("❌ Invalid option. Please try again.")
            
            print()
    
    except KeyboardInterrupt:
        print("\n\n🛑 Enhanced client stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    print("👋 Enhanced RFID client session ended!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
