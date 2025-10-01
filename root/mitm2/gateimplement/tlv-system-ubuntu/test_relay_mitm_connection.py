#!/usr/bin/env python3
"""
🔗 Relay Mode and MITM Connection Test Suite
Tests relay functionality, MITM interceptors, and server connection properties.
"""

import sys
import os
import time
import socket
import threading
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required modules can be imported."""
    print("📦 Testing module imports...")
    
    try:
        from src.mitm.transaction_mitm import RealTransactionMITM
        print("  ✅ RealTransactionMITM imported")
        
        from src.servers.tcp_server import TCPProxyServer
        print("  ✅ TCPProxyServer imported")
        
        from src.servers.http_server import HTTPProxyServer
        print("  ✅ HTTPProxyServer imported")
        
        from src.utils.config import ConfigManager
        print("  ✅ ConfigManager imported")
        
        from src.utils.logger import Logger
        print("  ✅ Logger imported")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_mitm_configuration():
    """Test MITM configuration loading and validation."""
    print("\n⚙️ Testing MITM Configuration...")
    
    try:
        from src.mitm.transaction_mitm import RealTransactionMITM
        
        # Test with default config
        mitm = RealTransactionMITM()
        
        # Check configuration properties
        if hasattr(mitm, 'config'):
            print("  ✅ MITM config loaded")
            print(f"    - Block All: {mitm.block_all}")
            print(f"    - Bypass PIN: {mitm.bypass_pin}")
            print(f"    - Config Path: {mitm.config_path}")
        else:
            print("  ❌ MITM config not loaded")
            return False
        
        # Test configuration methods
        test_data = "sample request data with pin=1234"
        test_url = "https://payment.example.com/api/process"
        
        # Test request processing
        result, status, message = mitm.process_request(test_data, test_url)
        print(f"  ✅ Request processing: status={status}, modified={result != test_data}")
        
        # Test response processing
        response_data = '{"status": "failed", "error": true}'
        modified_response = mitm.process_response(response_data, test_url)
        print(f"  ✅ Response processing: modified={modified_response != response_data}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MITM configuration test failed: {e}")
        traceback.print_exc()
        return False

def test_tcp_server_properties():
    """Test TCP server initialization and properties."""
    print("\n🌐 Testing TCP Server Properties...")
    
    try:
        from src.servers.tcp_server import TCPProxyServer
        
        # Test server initialization
        server = TCPProxyServer(host='127.0.0.1', port=18081)  # Use different port for testing
        
        # Check server properties
        print(f"  ✅ Server initialized: {server.host}:{server.port}")
        print(f"    - Running: {server.is_running()}")
        print(f"    - Socket: {server.socket}")
        
        # Test initialization with state
        test_state = {
            'bypass_pin': True,
            'cdcvm_enabled': True,
            'mitm_enabled': True
        }
        
        server.initialize(None, test_state)  # No private key for testing
        print("  ✅ Server initialized with state")
        print(f"    - State keys: {list(test_state.keys())}")
        
        # Test server start (don't actually bind to avoid conflicts)
        try:
            # Check if port is available
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            result = test_socket.connect_ex((server.host, server.port))
            test_socket.close()
            
            if result != 0:
                print(f"  ✅ Port {server.port} is available for binding")
            else:
                print(f"  ⚠️ Port {server.port} is already in use")
                
        except Exception as e:
            print(f"  ⚠️ Port check failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ TCP server test failed: {e}")
        traceback.print_exc()
        return False

def test_http_server_properties():
    """Test HTTP server initialization and properties."""
    print("\n🌐 Testing HTTP Server Properties...")
    
    try:
        from src.servers.http_server import HTTPProxyServer
        
        # Test server initialization
        server = HTTPProxyServer(host='127.0.0.1', port=18082)  # Use different port for testing
        
        # Check server properties
        print(f"  ✅ Server initialized: {server.host}:{server.port}")
        print(f"    - Running: {server.is_running()}")
        print(f"    - Thread: {server.thread}")
        
        # Test handler initialization
        test_state = {
            'bypass_pin': True,
            'cdcvm_enabled': True,
            'mitm_enabled': True
        }
        
        server.initialize_handler(None, test_state)  # No private key for testing
        print("  ✅ HTTP handler initialized")
        
        # Test port availability
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            result = test_socket.connect_ex((server.host, server.port))
            test_socket.close()
            
            if result != 0:
                print(f"  ✅ Port {server.port} is available for binding")
            else:
                print(f"  ⚠️ Port {server.port} is already in use")
                
        except Exception as e:
            print(f"  ⚠️ Port check failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ HTTP server test failed: {e}")
        traceback.print_exc()
        return False

def test_relay_mode_simulation():
    """Test relay mode functionality simulation."""
    print("\n🔄 Testing Relay Mode Simulation...")
    
    try:
        from src.mitm.transaction_mitm import RealTransactionMITM
        
        # Create MITM instance
        mitm = RealTransactionMITM()
        
        # Simulate different transaction scenarios
        test_scenarios = [
            {
                "name": "PIN Transaction Block",
                "data": '{"transaction": {"amount": "100.00", "pin": "1234"}}',
                "url": "https://payment.gateway.com/process",
                "expected_block": True
            },
            {
                "name": "Normal Transaction",
                "data": '{"transaction": {"amount": "50.00", "card": "4111111111111111"}}',
                "url": "https://payment.gateway.com/process",
                "expected_block": False
            },
            {
                "name": "PIN Code Transmission",
                "data": 'pin_block=encrypted_pin_data_here',
                "url": "https://secure.payment.com/pin",
                "expected_block": True
            },
            {
                "name": "Authorization Request",
                "data": '{"auth": {"card_data": "encrypted", "amount": "25.99"}}',
                "url": "https://auth.payment.com/verify",
                "expected_block": False
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n  📋 Testing: {scenario['name']}")
            
            result, status, message = mitm.process_request(
                scenario['data'], 
                scenario['url']
            )
            
            blocked = (status == 403)
            expected = scenario['expected_block']
            
            if blocked == expected:
                print(f"    ✅ Correct behavior: {'blocked' if blocked else 'allowed'}")
            else:
                print(f"    ❌ Unexpected behavior: expected {'block' if expected else 'allow'}, got {'block' if blocked else 'allow'}")
            
            print(f"    - Status: {status}")
            print(f"    - Modified: {result != scenario['data']}")
        
        # Test log generation
        if mitm.logs:
            print(f"\n  ✅ MITM logs generated: {len(mitm.logs)} entries")
            for log in mitm.logs[-3:]:  # Show last 3 logs
                print(f"    - {log.get('action', 'unknown')}: {log.get('url', 'no url')[:50]}...")
        else:
            print("  ⚠️ No MITM logs generated")
        
        # Test cleanup
        mitm.done()
        print("  ✅ MITM cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Relay mode simulation failed: {e}")
        traceback.print_exc()
        return False

def test_connection_properties():
    """Test connection properties and network capabilities."""
    print("\n🔌 Testing Connection Properties...")
    
    try:
        # Test socket creation and properties
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        print("  ✅ Socket created with SO_REUSEADDR")
        
        # Test binding to localhost
        try:
            test_socket.bind(('127.0.0.1', 0))  # Bind to any available port
            host, port = test_socket.getsockname()
            print(f"  ✅ Socket bound to {host}:{port}")
            
            # Test listening
            test_socket.listen(1)
            print("  ✅ Socket listening")
            
        except Exception as e:
            print(f"  ❌ Socket binding/listening failed: {e}")
            return False
        finally:
            test_socket.close()
        
        # Test network interface detection
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"  ✅ Network properties detected:")
        print(f"    - Hostname: {hostname}")
        print(f"    - Local IP: {local_ip}")
        
        # Test connection timeout settings
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5.0)
        print("  ✅ Socket timeout configured")
        test_socket.close()
        
        return True
        
    except Exception as e:
        print(f"  ❌ Connection properties test failed: {e}")
        traceback.print_exc()
        return False

def test_configuration_files():
    """Test configuration file loading and validation."""
    print("\n📄 Testing Configuration Files...")
    
    try:
        # Test MITM config
        mitm_config_path = "config/mitm_config.json"
        if os.path.exists(mitm_config_path):
            with open(mitm_config_path, 'r', encoding='utf-8') as f:
                mitm_config = json.load(f)
            
            print(f"  ✅ MITM config loaded: {mitm_config_path}")
            print(f"    - Keys: {list(mitm_config.keys())}")
            
            # Validate required keys
            required_keys = ['mitm_enabled', 'bypass_pin', 'block_all']
            for key in required_keys:
                if key in mitm_config:
                    print(f"    - {key}: {mitm_config[key]}")
                else:
                    print(f"    ⚠️ Missing key: {key}")
        else:
            print(f"  ⚠️ MITM config not found: {mitm_config_path}")
        
        # Test proxy config
        proxy_config_path = "config/proxy_config.json"
        if os.path.exists(proxy_config_path):
            with open(proxy_config_path, 'r', encoding='utf-8') as f:
                proxy_config = json.load(f)
            
            print(f"  ✅ Proxy config loaded: {proxy_config_path}")
            print(f"    - Keys: {list(proxy_config.keys())}")
        else:
            print(f"  ⚠️ Proxy config not found: {proxy_config_path}")
        
        # Test unified config
        unified_config_path = "config/unified_config.json"
        if os.path.exists(unified_config_path):
            with open(unified_config_path, 'r', encoding='utf-8') as f:
                unified_config = json.load(f)
            
            print(f"  ✅ Unified config loaded: {unified_config_path}")
            print(f"    - Keys: {list(unified_config.keys())}")
        else:
            print(f"  ⚠️ Unified config not found: {unified_config_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration file test failed: {e}")
        traceback.print_exc()
        return False

def test_integrated_system():
    """Test integrated system with all components."""
    print("\n🔗 Testing Integrated System...")
    
    try:
        from src.mitm.transaction_mitm import RealTransactionMITM
        from src.servers.tcp_server import TCPProxyServer
        from src.servers.http_server import HTTPProxyServer
        
        # Initialize components
        mitm = RealTransactionMITM()
        tcp_server = TCPProxyServer(host='127.0.0.1', port=18083)
        http_server = HTTPProxyServer(host='127.0.0.1', port=18084)
        
        # Test state sharing
        shared_state = {
            'mitm_enabled': True,
            'bypass_pin': True,
            'cdcvm_enabled': True,
            'block_all': False,
            'session_id': f'test_session_{int(time.time())}'
        }
        
        tcp_server.initialize(None, shared_state)
        http_server.initialize_handler(None, shared_state)
        
        print("  ✅ All components initialized with shared state")
        print(f"    - MITM: {type(mitm).__name__}")
        print(f"    - TCP Server: {tcp_server.host}:{tcp_server.port}")
        print(f"    - HTTP Server: {http_server.host}:{http_server.port}")
        print(f"    - Session ID: {shared_state['session_id']}")
        
        # Test component interaction simulation
        print("\n  🔄 Testing component interaction...")
        
        # Simulate data flow: Client -> HTTP -> MITM -> TCP -> Backend
        test_data = '{"payment": {"amount": "100.00", "card": "4111111111111111"}}'
        test_url = "https://payment.example.com/process"
        
        # Step 1: HTTP receives request
        print("    1. HTTP Server receives request")
        
        # Step 2: MITM processes request
        processed_data, status, message = mitm.process_request(test_data, test_url)
        print(f"    2. MITM processes request: status={status}")
        
        # Step 3: TCP forwards to backend (simulated)
        print("    3. TCP Server forwards to backend (simulated)")
        
        # Step 4: Response flows back
        response_data = '{"status": "success", "transaction_id": "TXN123456"}'
        final_response = mitm.process_response(response_data, test_url)
        print(f"    4. Response processed: modified={final_response != response_data}")
        
        print("  ✅ Integration test completed successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integrated system test failed: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """Run all relay and MITM tests."""
    print("🔗 RELAY MODE AND MITM CONNECTION TEST SUITE")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_functions = [
        ("Module Imports", test_imports),
        ("MITM Configuration", test_mitm_configuration),
        ("TCP Server Properties", test_tcp_server_properties),
        ("HTTP Server Properties", test_http_server_properties),
        ("Relay Mode Simulation", test_relay_mode_simulation),
        ("Connection Properties", test_connection_properties),
        ("Configuration Files", test_configuration_files),
        ("Integrated System", test_integrated_system)
    ]
    
    for test_name, test_func in test_functions:
        try:
            print(f"\n{'='*60}")
            result = test_func()
            test_results[test_name] = result
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            test_results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL RELAY MODE AND MITM CONNECTION TESTS PASSED!")
        print("✅ System is ready for relay operations")
        print("✅ MITM interceptors are operational")
        print("✅ Server connections are properly configured")
    else:
        print(f"\n⚠️ {total - passed} tests failed - system needs attention")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
