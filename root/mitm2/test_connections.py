#!/usr/bin/env python3
"""
Connection Test Script for NFCGate MITM
Simulates the connection patterns that were causing session ending issues
"""

import socket
import time
import threading
import sys

def test_connection(host="localhost", port=8080, num_connections=5):
    """Test multiple connections to the MITM server"""
    print(f"🔍 Testing {num_connections} connections to {host}:{port}")
    
    def single_connection_test(conn_id):
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            print(f"📱 Connection {conn_id}: Attempting to connect...")
            sock.connect((host, port))
            print(f"✅ Connection {conn_id}: Connected successfully")
            
            # Send some test data (simulating NFCGate client)
            test_data = b'\x00\xA4\x04\x00\x07\xA0\x00\x00\x00\x04\x10\x10\x00'  # SELECT command
            sock.send(test_data)
            print(f"📤 Connection {conn_id}: Sent test data ({len(test_data)} bytes)")
            
            # Wait for response
            response = sock.recv(1024)
            print(f"📥 Connection {conn_id}: Received response ({len(response)} bytes)")
            
            # Keep connection alive for a bit
            time.sleep(2)
            
            # Send PIN verification command
            pin_cmd = b'\x00\x20\x00\x00\x08\x12\x34\x56\x78\x9A\xBC\xDE\xF0'
            sock.send(pin_cmd)
            print(f"🔓 Connection {conn_id}: Sent PIN verification")
            
            pin_response = sock.recv(1024)
            if pin_response == b'\x90\x00':
                print(f"✅ Connection {conn_id}: PIN bypass successful!")
            else:
                print(f"⚠️ Connection {conn_id}: Unexpected PIN response: {pin_response.hex()}")
            
            # Keep connection alive longer
            time.sleep(3)
            
            duration = time.time() - start_time
            print(f"⏱️ Connection {conn_id}: Session lasted {duration:.2f}s")
            
        except ConnectionRefusedError:
            print(f"❌ Connection {conn_id}: Connection refused")
        except socket.timeout:
            print(f"⏰ Connection {conn_id}: Timeout")
        except Exception as e:
            print(f"❌ Connection {conn_id}: Error - {e}")
        finally:
            try:
                sock.close()
                print(f"🔌 Connection {conn_id}: Disconnected")
            except:
                pass
    
    # Start multiple connections
    threads = []
    for i in range(num_connections):
        thread = threading.Thread(target=single_connection_test, args=(i+1,), daemon=True)
        threads.append(thread)
        thread.start()
        time.sleep(0.5)  # Stagger connections
    
    # Wait for all connections to finish
    for thread in threads:
        thread.join()
    
    print(f"🏁 Test completed - {num_connections} connections tested")

def simulate_problematic_ip():
    """Simulate connections from the problematic IP (77.85.97.37 pattern)"""
    print("🌐 Simulating external IP connection pattern...")
    
    # Simulate rapid connection attempts that were failing
    for i in range(3):
        print(f"\n--- Attempt {i+1} (simulating session pattern) ---")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            start_time = time.time()
            sock.connect(("localhost", 8080))
            print(f"📱 Connected successfully")
            
            # Immediately try to send data (like the failing sessions)
            sock.send(b'\x00\xA4\x04\x00')
            response = sock.recv(1024)
            
            duration = time.time() - start_time
            print(f"⏱️ Session duration: {duration:.6f}s")
            
            if duration > 0.1:  # If session lasts longer than 0.1s, it's better than before
                print(f"✅ Session improvement: {duration:.6f}s vs previous ~0.001s")
            
            sock.close()
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
        
        time.sleep(1)

def main():
    print("🧪 NFCGate MITM Connection Tester")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "basic":
            test_connection(num_connections=3)
        elif sys.argv[1] == "stress":
            test_connection(num_connections=10)
        elif sys.argv[1] == "simulate":
            simulate_problematic_ip()
        else:
            print("Usage: python test_connections.py [basic|stress|simulate]")
    else:
        print("Choose test type:")
        print("1. Basic connection test (3 connections)")
        print("2. Stress test (10 connections)")  
        print("3. Simulate problematic IP pattern")
        print("0. Exit")
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            test_connection(num_connections=3)
        elif choice == "2":
            test_connection(num_connections=10)
        elif choice == "3":
            simulate_problematic_ip()
        elif choice == "0":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()
