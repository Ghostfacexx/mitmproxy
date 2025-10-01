"""
HTTP request handlers for the proxy server.
"""
import base64
import traceback
from http.server import BaseHTTPRequestHandler
from binascii import hexlify
from typing import Optional
import sys
import os

# Handle imports - check if running as part of package or directly
try:
    from ..protocols.nfc_handler import process_wrapper_message
    from ..protocols.metaMessage_pb2 import Wrapper
    from ..protocols.c2c_pb2 import NFCData
    from ..mitm.transaction_mitm import RealTransactionMITM
    from ..utils.logger import Logger
except ImportError:
    # Running directly - add parent directories to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    project_dir = os.path.dirname(src_dir)
    sys.path.insert(0, project_dir)
    
    from src.protocols.nfc_handler import process_wrapper_message
    from src.protocols.metaMessage_pb2 import Wrapper
    from src.protocols.c2c_pb2 import NFCData
    from src.mitm.transaction_mitm import RealTransactionMITM
    from src.utils.logger import Logger

logger = Logger("HTTPHandlers")


class NFCGateHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for NFCGate proxy."""
    
    mitm: Optional[RealTransactionMITM] = None
    private_key = None
    state = {}

    @classmethod
    def initialize(cls, private_key, state: dict, mitm_config_path: str = "config/mitm_config.json") -> None:
        """
        Initialize the handler with required components.
        
        Args:
            private_key: RSA private key for signing
            state: MITM state dictionary
            mitm_config_path: Path to MITM configuration file
        """
        cls.private_key = private_key
        cls.state = state
        cls.mitm = RealTransactionMITM(mitm_config_path)
        
        logger.info(f"Initialized HTTP handler with state: {state}")

    def log_message(self, format: str, *args) -> None:
        """Override to use our custom logger."""
        logger.debug(f"HTTP {format % args}")

    def do_POST(self) -> None:
        """Handle POST requests."""
        logger.info(f"Received HTTP POST request from {self.client_address}, path: {self.path}")
        
        try:
            # Read request data
            content_length = int(self.headers.get('Content-Length', 0))
            content_type = self.headers.get('Content-Type', '')
            
            logger.debug(f"HTTP headers: {dict(self.headers)}")
            
            data = self.rfile.read(content_length).decode('utf-8')
            logger.info(f"HTTP request body: {data[:100]}... (length: {len(data)})")

            # Apply MITM logic to HTTP data
            modified_data = data  # Default to original data
            if self.mitm:
                modified_data, status_code, status_message = self.mitm.process_request(data, self.path)
                
                if status_code != 200:
                    logger.info(f"Sending HTTP response: status={status_code}, message={status_message.decode()}")
                    self.send_response(status_code)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(status_message)
                    return

            # Try parsing as base64-encoded Wrapper message
            try:
                wrapper_data = base64.b64decode(data)
                logger.debug(f"Decoded base64 data: {hexlify(wrapper_data).decode()[:100]}...")
                
                # Process the wrapper message
                result = process_wrapper_message(wrapper_data, self.private_key, self.state)
                
                if result:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.end_headers()
                    self.wfile.write(result)
                else:
                    self.send_response(400)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b"No NFCData in received Wrapper")
                    
            except Exception:
                logger.info("HTTP body is not base64-encoded, treating as plain text")
                
                # Return the (possibly modified) plain text data
                response_data = locals().get('modified_data', data) if self.mitm else data
                if response_data:
                    self.send_response(200)
                    self.send_header('Content-Type', content_type or 'application/json')
                    self.end_headers()
                    self.wfile.write(response_data.encode('utf-8'))
                
        except Exception as e:
            logger.error(f"Error processing HTTP request: {e}")
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode('utf-8'))

    def do_GET(self) -> None:
        """Handle GET requests."""
        logger.info(f"Received HTTP GET request from {self.client_address}, path: {self.path}")
        
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            status = {
                "status": "running",
                "mitm_enabled": bool(self.mitm),
                "state": self.state
            }
            
            import json
            self.wfile.write(json.dumps(status, indent=2).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Not Found")


if __name__ == "__main__":
    """Direct execution for testing purposes."""
    print("HTTP Handlers module loaded successfully!")
    print("This module is designed to be imported, not run directly.")
    print("To start the full NFC proxy system, run: python main.py")
    print("Or use the convenience script: .\\run.ps1")
    
    # Test initialization
    try:
        print("\nTesting handler initialization...")
        NFCGateHTTPRequestHandler.initialize(None, {})
        print("✅ Handler can be initialized")
    except Exception as e:
        print(f"❌ Handler initialization failed: {e}")
        
    print("\nFor full system operation, use main.py instead.")
