#!/usr/bin/env python3
"""
Quick Fix Script for NFCGate MITM Connection Issues
Addresses the specific [Errno 111] Connection refused errors
"""

import socket
import subprocess
import sys
import time
import threading
import json

def check_and_kill_port_processes(port):
    """Check and optionally kill processes using a specific port"""
    try:
        if sys.platform == "win32":
            # Windows command to find processes using the port
            cmd = f'netstat -ano | findstr :{port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                print(f"Processes using port {port}:")
                lines = result.stdout.strip().split('\n')
                pids = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids.append(pid)
                            print(f"  PID: {pid}")
                
                if pids:
                    kill = input(f"Kill processes using port {port}? (y/N): ").strip().lower()
                    if kill == 'y':
                        for pid in set(pids):  # Remove duplicates
                            try:
                                subprocess.run(f'taskkill /PID {pid} /F', shell=True, check=True)
                                print(f"✅ Killed process {pid}")
                            except subprocess.CalledProcessError:
                                print(f"❌ Failed to kill process {pid}")
            else:
                print(f"✅ Port {port} is free")
                
    except Exception as e:
        print(f"Error checking port {port}: {e}")

def start_mock_nfcgate(port=5566):
    """Start a simple mock NFCGate service"""
    def mock_server():
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('127.0.0.1', port))
            server_socket.listen(5)
            print(f"✅ Mock NFCGate service started on 127.0.0.1:{port}")
            
            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    print(f"📱 Mock NFCGate: Connection from {addr}")
                    
                    # Simple echo server for testing
                    def handle_client(sock):
                        try:
                            while True:
                                data = sock.recv(1024)
                                if not data:
                                    break
                                # Echo back with success response
                                sock.send(b'\x90\x00')  # Success response
                        except:
                            pass
                        finally:
                            sock.close()
                    
                    threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Mock server error: {e}")
                    
        except Exception as e:
            print(f"Failed to start mock NFCGate: {e}")
        finally:
            try:
                if 'server_socket' in locals():
                    server_socket.close()
            except:
                pass
    
    # Start mock server in background thread
    mock_thread = threading.Thread(target=mock_server, daemon=True)
    mock_thread.start()
    time.sleep(1)  # Give it time to start

def test_connectivity(host, port):
    """Test if we can connect to a host:port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def update_config_for_localhost():
    """Update config.json to use localhost instead of 0.0.0.0"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Update target host to localhost
        config['server']['target_host'] = '127.0.0.1'
        config['nfcgate']['mock_mode_enabled'] = True
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Updated config.json to use localhost and enable mock mode")
        return True
    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        return False

def main():
    print("🔧 NFCGate MITM Quick Fix Tool")
    print("=" * 40)
    print("Addressing [Errno 111] Connection refused errors")
    print()
    
    # Step 1: Check and fix port conflicts
    print("1️⃣ Checking port conflicts...")
    check_and_kill_port_processes(8080)  # MITM listen port
    check_and_kill_port_processes(5566)  # NFCGate target port
    print()
    
    # Step 2: Update configuration
    print("2️⃣ Updating configuration...")
    update_config_for_localhost()
    print()
    
    # Step 3: Start mock NFCGate service
    print("3️⃣ Starting mock NFCGate service...")
    start_mock_nfcgate(5566)
    
    # Test connectivity
    if test_connectivity('127.0.0.1', 5566):
        print("✅ Mock NFCGate is running and accessible")
    else:
        print("❌ Failed to start mock NFCGate")
        return
    
    print()
    
    # Step 4: Test MITM port availability
    print("4️⃣ Testing MITM port availability...")
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind(('0.0.0.0', 8080))
        test_socket.close()
        print("✅ Port 8080 is available for MITM server")
    except Exception as e:
        print(f"❌ Port 8080 is not available: {e}")
        return
    
    print()
    print("🎉 Quick fix completed!")
    print()
    print("Next steps:")
    print("  1. Run: python nfcgate_mitm.py")
    print("  2. Select option 1 to start MITM server")
    print("  3. Connect your clients to localhost:8080")
    print()
    
    # Option to start MITM immediately
    start_now = input("Start MITM server now? (Y/n): ").strip().lower()
    if start_now != 'n':
        print("Starting MITM server...")
        try:
            subprocess.run([sys.executable, 'nfcgate_mitm.py'], check=True)
        except KeyboardInterrupt:
            print("\nShutdown requested")
        except Exception as e:
            print(f"Error starting MITM: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")
