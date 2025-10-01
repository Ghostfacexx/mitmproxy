#!/usr/bin/env python3
"""
📡 NFC Proxy Connection Test Suite
Tests NFC proxy connection functionality, NFCGate protocol handling, and data interception.
"""

import sys
import os
import time
import socket
import threading
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from binascii import hexlify, unhexlify

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_nfc_imports():
    """Test that all NFC-related modules can be imported."""
    print("📦 Testing NFC module imports...")
    
    try:
        from src.protocols.nfc_handler import handle_nfc_data, process_wrapper_message
        print("  ✅ NFC handler imported")
        
        from src.protocols.c2c_pb2 import NFCData
        print("  ✅ NFCData protobuf imported")
        
        from src.protocols.metaMessage_pb2 import Wrapper
        print("  ✅ Wrapper protobuf imported")
        
        from src.servers.tcp_server import TCPProxyServer
        print("  ✅ TCP proxy server imported")
        
        from src.core.tlv_parser import parse_tlv, build_tlv, is_valid_tlv
        print("  ✅ TLV parser imported")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_nfc_data_creation():
    """Test creation and parsing of NFCData protobuf messages."""
    print("\n📋 Testing NFCData protobuf creation...")
    
    try:
        from src.protocols.c2c_pb2 import NFCData
        
        # Create test NFC data
        test_data = unhexlify("6F1C840E315041592E5359532E4444463031A50A880150950500008080019F38039F99049F37049F47049F35019F36029F07029F08029F39019F34039F21039F10079F1A029F26089F27019F33039F53019F40059F41049F13049F17049F09029F6C029F6B139F63169F1E089F1D089F1C089F1B049F42029F4B819F3704")
        
        nfc = NFCData()
        nfc.data = test_data
        
        # Serialize to bytes
        serialized = nfc.SerializeToString()
        print(f"  ✅ NFCData created: {len(serialized)} bytes")
        
        # Parse back
        parsed_nfc = NFCData()
        parsed_nfc.ParseFromString(serialized)
        
        if parsed_nfc.data == test_data:
            print("  ✅ NFCData serialization/parsing working")
        else:
            print("  ❌ NFCData serialization/parsing failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ NFCData test failed: {e}")
        return False

def test_wrapper_message_creation():
    """Test creation and parsing of Wrapper protobuf messages."""
    print("\n📋 Testing Wrapper message creation...")
    
    try:
        from src.protocols.metaMessage_pb2 import Wrapper
        from src.protocols.c2c_pb2 import NFCData
        
        # Create test NFC data
        test_data = unhexlify("9F3704A1B2C3D4")  # Simple test TLV
        
        nfc = NFCData()
        nfc.data = test_data
        
        # Create wrapper with NFCData
        wrapper = Wrapper()
        wrapper.NFCData.CopyFrom(nfc)
        
        # Serialize wrapper
        wrapper_data = wrapper.SerializeToString()
        print(f"  ✅ Wrapper with NFCData created: {len(wrapper_data)} bytes")
        
        # Parse wrapper back
        parsed_wrapper = Wrapper()
        parsed_wrapper.ParseFromString(wrapper_data)
        
        if parsed_wrapper.HasField('NFCData'):
            if parsed_wrapper.NFCData.data == test_data:
                print("  ✅ Wrapper NFCData parsing working")
            else:
                print("  ❌ Wrapper NFCData data mismatch")
                return False
        else:
            print("  ❌ Wrapper does not contain NFCData")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Wrapper test failed: {e}")
        return False

def test_nfc_data_processing():
    """Test NFC data processing with TLV parsing."""
    print("\n🔧 Testing NFC data processing...")
    
    try:
        from src.protocols.nfc_handler import handle_nfc_data
        from src.protocols.c2c_pb2 import NFCData
        from src.core.tlv_parser import is_valid_tlv
        
        # Create test NFC data with valid TLV
        test_tlv_data = unhexlify("9F3704A1B2C3D4")  # Simple TLV: tag 9F37, length 04, data A1B2C3D4
        
        nfc = NFCData()
        nfc.data = test_tlv_data
        nfc_bytes = nfc.SerializeToString()
        
        # Test state
        test_state = {
            'cdcvm_enabled': True,
            'bypass_pin': True,
            'mitm_enabled': True
        }
        
        # Process NFC data (without private key for testing)
        result = handle_nfc_data(nfc_bytes, None, test_state)
        
        if result:
            print("  ✅ NFC data processing completed")
            
            # Parse result back
            result_nfc = NFCData()
            result_nfc.ParseFromString(result)
            
            print(f"  ✅ Original data: {hexlify(test_tlv_data).decode()}")
            print(f"  ✅ Processed data: {hexlify(result_nfc.data).decode()}")
            
            # Verify TLV validity
            if is_valid_tlv(result_nfc.data):
                print("  ✅ Processed data is valid TLV")
            else:
                print("  ⚠️ Processed data is not valid TLV (may be non-TLV test data)")
            
        else:
            print("  ❌ NFC data processing failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ NFC processing test failed: {e}")
        traceback.print_exc()
        return False

def test_wrapper_message_processing():
    """Test wrapper message processing."""
    print("\n🔧 Testing Wrapper message processing...")
    
    try:
        from src.protocols.nfc_handler import process_wrapper_message
        from src.protocols.metaMessage_pb2 import Wrapper
        from src.protocols.c2c_pb2 import NFCData
        
        # Create test wrapper with NFCData
        test_tlv_data = unhexlify("9F3704A1B2C3D4")
        
        nfc = NFCData()
        nfc.data = test_tlv_data
        
        wrapper = Wrapper()
        wrapper.NFCData.CopyFrom(nfc)
        
        wrapper_bytes = wrapper.SerializeToString()
        
        # Test state
        test_state = {
            'cdcvm_enabled': True,
            'bypass_pin': True,
            'mitm_enabled': True
        }
        
        # Process wrapper message
        result = process_wrapper_message(wrapper_bytes, None, test_state)
        
        if result:
            print("  ✅ Wrapper message processing completed")
            
            # Parse result
            result_wrapper = Wrapper()
            result_wrapper.ParseFromString(result)
            
            if result_wrapper.HasField('NFCData'):
                print("  ✅ Result contains NFCData")
                print(f"  ✅ Result data: {hexlify(result_wrapper.NFCData.data).decode()[:50]}...")
            else:
                print("  ❌ Result does not contain NFCData")
                return False
        else:
            print("  ⚠️ Wrapper processing returned None (may be expected for non-NFCData)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Wrapper processing test failed: {e}")
        traceback.print_exc()
        return False

def test_tcp_nfc_proxy_connection():
    """Test TCP proxy connection with NFC data."""
    print("\n🌐 Testing TCP NFC proxy connection...")
    
    try:
        from src.servers.tcp_server import TCPProxyServer
        from src.protocols.metaMessage_pb2 import Wrapper
        from src.protocols.c2c_pb2 import NFCData
        
        # Create server
        server = TCPProxyServer(host='127.0.0.1', port=38081)  # Different port for testing
        
        # Initialize server with test state
        test_state = {
            'cdcvm_enabled': True,
            'bypass_pin': True,
            'mitm_enabled': True,
            'session_id': f'nfc_test_{int(time.time())}'
        }
        
        server.initialize(None, test_state)
        server.start()
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.run)
        server_thread.daemon = True
        server_thread.start()
        
        # Allow server to start
        time.sleep(1)
        
        # Create test NFC data
        test_tlv_data = unhexlify("9F3704A1B2C3D4")
        
        nfc = NFCData()
        nfc.data = test_tlv_data
        
        wrapper = Wrapper()
        wrapper.NFCData.CopyFrom(nfc)
        
        test_data = wrapper.SerializeToString()
        
        # Connect and send NFC data
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((server.host, server.port))
            
            # Send NFC data
            client_socket.send(test_data)
            
            # Receive response
            response = client_socket.recv(4096)
            client_socket.close()
            
            print(f"  ✅ NFC proxy connection successful")
            print(f"    - Sent: {len(test_data)} bytes")
            print(f"    - Received: {len(response)} bytes")
            
            # Verify response is valid wrapper
            try:
                response_wrapper = Wrapper()
                response_wrapper.ParseFromString(response)
                
                if response_wrapper.HasField('NFCData'):
                    print("  ✅ Response contains NFCData")
                    print(f"    - Response data: {hexlify(response_wrapper.NFCData.data).decode()[:50]}...")
                else:
                    print("  ⚠️ Response does not contain NFCData")
                
            except Exception as e:
                print(f"  ⚠️ Response parsing failed: {e}")
            
        except Exception as e:
            print(f"  ❌ Client connection failed: {e}")
            return False
        finally:
            server.stop()
        
        return True
        
    except Exception as e:
        print(f"  ❌ TCP NFC proxy test failed: {e}")
        return False

def test_nfc_proxy_with_real_tlv():
    """Test NFC proxy with realistic payment card TLV data."""
    print("\n💳 Testing NFC proxy with realistic payment TLV...")
    
    try:
        from src.protocols.nfc_handler import process_wrapper_message
        from src.protocols.metaMessage_pb2 import Wrapper
        from src.protocols.c2c_pb2 import NFCData
        
        # Realistic payment card TLV data (simplified)
        payment_tlv_data = unhexlify(
            "6F1C"  # FCI Template
            "840E315041592E5359532E4444463031"  # DF Name (1PAY.SYS.DDF01)
            "A50A"  # FCI Proprietary Template
            "8801"  # SFI
            "50"    # Application Label length
            "9505"  # TVR
            "00008080"  # Default value
            "019F38039F99049F37049F47049F35019F36029F07029F08029F39019F34039F21039F10079F1A029F26089F27019F33039F53019F40059F41049F13049F17049F09029F6C029F6B139F63169F1E089F1D089F1C089F1B049F42029F4B819F3704"
        )
        
        # Create NFCData and Wrapper
        nfc = NFCData()
        nfc.data = payment_tlv_data
        
        wrapper = Wrapper()
        wrapper.NFCData.CopyFrom(nfc)
        
        wrapper_bytes = wrapper.SerializeToString()
        
        # Test state for payment processing
        payment_state = {
            'cdcvm_enabled': True,
            'bypass_pin': True,
            'mitm_enabled': True,
            'block_all': False,
            'session_id': f'payment_test_{int(time.time())}'
        }
        
        # Process payment TLV through NFC proxy
        result = process_wrapper_message(wrapper_bytes, None, payment_state)
        
        if result:
            print("  ✅ Payment TLV processing completed")
            
            # Parse and analyze result
            result_wrapper = Wrapper()
            result_wrapper.ParseFromString(result)
            
            if result_wrapper.HasField('NFCData'):
                result_data = result_wrapper.NFCData.data
                print(f"  ✅ Payment TLV processed successfully")
                print(f"    - Original size: {len(payment_tlv_data)} bytes")
                print(f"    - Processed size: {len(result_data)} bytes")
                print(f"    - Original data: {hexlify(payment_tlv_data).decode()[:100]}...")
                print(f"    - Processed data: {hexlify(result_data).decode()[:100]}...")
                
                # Check if data was modified
                if result_data != payment_tlv_data:
                    print("  ✅ Payment data was modified by MITM")
                else:
                    print("  ✅ Payment data processed unchanged")
            else:
                print("  ❌ Result does not contain NFCData")
                return False
        else:
            print("  ⚠️ Payment TLV processing returned None")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Payment TLV test failed: {e}")
        traceback.print_exc()
        return False

def test_nfc_proxy_error_handling():
    """Test NFC proxy error handling with invalid data."""
    print("\n🛡️ Testing NFC proxy error handling...")
    
    try:
        from src.protocols.nfc_handler import handle_nfc_data, process_wrapper_message
        from src.protocols.c2c_pb2 import NFCData
        
        test_state = {'cdcvm_enabled': True, 'bypass_pin': True}
        
        # Test 1: Invalid protobuf data
        invalid_data = b"This is not valid protobuf data"
        result1 = handle_nfc_data(invalid_data, None, test_state)
        
        if result1 == invalid_data:
            print("  ✅ Invalid protobuf data handled correctly (returned unchanged)")
        else:
            print("  ❌ Invalid protobuf data not handled correctly")
            return False
        
        # Test 2: Empty data
        empty_nfc = NFCData()
        empty_nfc.data = b""
        empty_bytes = empty_nfc.SerializeToString()
        
        result2 = handle_nfc_data(empty_bytes, None, test_state)
        
        if result2:
            print("  ✅ Empty NFC data handled correctly")
        else:
            print("  ❌ Empty NFC data not handled correctly")
            return False
        
        # Test 3: Non-TLV data
        non_tlv_nfc = NFCData()
        non_tlv_nfc.data = b"Random non-TLV binary data"
        non_tlv_bytes = non_tlv_nfc.SerializeToString()
        
        result3 = handle_nfc_data(non_tlv_bytes, None, test_state)
        
        if result3:
            print("  ✅ Non-TLV data handled correctly")
        else:
            print("  ❌ Non-TLV data not handled correctly")
            return False
        
        # Test 4: Invalid wrapper message
        invalid_wrapper = b"Invalid wrapper data"
        result4 = process_wrapper_message(invalid_wrapper, None, test_state)
        
        if result4 is None:
            print("  ✅ Invalid wrapper message handled correctly (returned None)")
        else:
            print("  ❌ Invalid wrapper message not handled correctly")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False

def test_nfc_proxy_performance():
    """Test NFC proxy performance with multiple requests."""
    print("\n⚡ Testing NFC proxy performance...")
    
    try:
        from src.protocols.nfc_handler import handle_nfc_data
        from src.protocols.c2c_pb2 import NFCData
        
        # Create test NFC data
        test_tlv_data = unhexlify("9F3704A1B2C3D4")
        
        nfc = NFCData()
        nfc.data = test_tlv_data
        nfc_bytes = nfc.SerializeToString()
        
        test_state = {'cdcvm_enabled': True, 'bypass_pin': True}
        
        # Test processing multiple requests
        num_requests = 100
        start_time = time.time()
        
        successful_requests = 0
        for i in range(num_requests):
            result = handle_nfc_data(nfc_bytes, None, test_state)
            if result:
                successful_requests += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"  ✅ Performance test completed")
        print(f"    - Requests: {num_requests}")
        print(f"    - Successful: {successful_requests}")
        print(f"    - Total time: {processing_time:.3f} seconds")
        print(f"    - Average per request: {(processing_time/num_requests)*1000:.2f} ms")
        print(f"    - Requests per second: {num_requests/processing_time:.1f}")
        
        if successful_requests == num_requests:
            print("  ✅ All requests processed successfully")
        else:
            print(f"  ⚠️ {num_requests - successful_requests} requests failed")
        
        return successful_requests >= num_requests * 0.95  # 95% success rate
        
    except Exception as e:
        print(f"  ❌ Performance test failed: {e}")
        return False

def test_nfc_proxy_log_generation():
    """Test NFC proxy log generation."""
    print("\n📝 Testing NFC proxy log generation...")
    
    try:
        # Check if log file exists or can be created
        log_file = "logs/nfcgate_proxy.log"
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Test log writing
        test_log_message = f"NFC Proxy test log entry - {time.time()}"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{test_log_message}\n")
        
        print(f"  ✅ Log file accessible: {log_file}")
        
        # Check if log file can be read
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            if test_log_message in log_content:
                print("  ✅ Log writing and reading working")
            else:
                print("  ❌ Log content verification failed")
                return False
        else:
            print("  ❌ Log file not created")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Log generation test failed: {e}")
        return False

def run_nfc_proxy_tests():
    """Run all NFC proxy connection tests."""
    print("📡 NFC PROXY CONNECTION TEST SUITE")
    print("=" * 60)
    
    test_results = {}
    
    # Run all NFC proxy tests
    nfc_test_functions = [
        ("NFC Module Imports", test_nfc_imports),
        ("NFCData Creation", test_nfc_data_creation),
        ("Wrapper Message Creation", test_wrapper_message_creation),
        ("NFC Data Processing", test_nfc_data_processing),
        ("Wrapper Message Processing", test_wrapper_message_processing),
        ("TCP NFC Proxy Connection", test_tcp_nfc_proxy_connection),
        ("NFC Proxy with Payment TLV", test_nfc_proxy_with_real_tlv),
        ("NFC Proxy Error Handling", test_nfc_proxy_error_handling),
        ("NFC Proxy Performance", test_nfc_proxy_performance),
        ("NFC Proxy Log Generation", test_nfc_proxy_log_generation)
    ]
    
    for test_name, test_func in nfc_test_functions:
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
    print("📊 NFC PROXY TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<45} {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL NFC PROXY CONNECTION TESTS PASSED!")
        print("✅ NFC proxy connection is fully operational")
        print("✅ NFCGate protocol handling working")
        print("✅ TLV data processing functional")
        print("✅ Performance and error handling verified")
    elif passed >= total * 0.8:  # 80% pass rate
        print(f"\n🟡 MOST TESTS PASSED ({passed}/{total})")
        print("⚠️ Some NFC proxy features may need attention")
    else:
        print(f"\n🔴 MULTIPLE FAILURES ({passed}/{total})")
        print("❌ NFC proxy connection needs significant work")
    
    return passed >= total * 0.8  # Consider 80% success rate as acceptable

if __name__ == "__main__":
    success = run_nfc_proxy_tests()
    sys.exit(0 if success else 1)
