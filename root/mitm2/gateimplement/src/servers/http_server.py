"""
HTTP proxy server implementation.
"""
import threading
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from typing import Dict, Any
from .handlers import NFCGateHTTPRequestHandler
from ..utils.logger import Logger

logger = Logger("HTTPServer")


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server."""
    allow_reuse_address = True


class HTTPProxyServer:
    """HTTP proxy server for NFC data processing."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8082):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
    
    def initialize_handler(self, private_key, state: Dict[str, Any], mitm_config_path: str = "config/mitm_config.json") -> None:
        """
        Initialize the HTTP request handler.
        
        Args:
            private_key: RSA private key for signing
            state: MITM state dictionary
            mitm_config_path: Path to MITM configuration
        """
        NFCGateHTTPRequestHandler.initialize(private_key, state, mitm_config_path)
        logger.info("HTTP handler initialized")
    
    def start(self) -> None:
        """Start the HTTP server in a separate thread."""
        try:
            self.server = ThreadingHTTPServer((self.host, self.port), NFCGateHTTPRequestHandler)
            logger.info(f"HTTP proxy server listening on {self.host}:{self.port}")
            
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            
            self.running = True
            logger.info("HTTP server thread started")
            
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the HTTP server."""
        if self.server and self.running:
            logger.info("Shutting down HTTP server")
            self.server.shutdown()
            self.server.server_close()
            
            if self.thread:
                self.thread.join(timeout=5)
            
            self.running = False
            logger.info("HTTP server stopped")
    
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self.running
