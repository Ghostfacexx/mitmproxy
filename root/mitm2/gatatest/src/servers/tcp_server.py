"""
TCP proxy server implementation for NFCGate clients.
"""
import socket
import threading
import traceback
from binascii import hexlify
from typing import Dict, Any
from ..protocols.nfc_handler import process_wrapper_message
from ..protocols.metaMessage_pb2 import Wrapper
from ..utils.logger import Logger

logger = Logger("TCPServer")


class TCPProxyServer:
    """TCP proxy server for NFCGate client connections."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8081):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.private_key = None
        self.state = {}
    
    def initialize(self, private_key, state: Dict[str, Any]) -> None:
        """
        Initialize the TCP server with required components.
        
        Args:
            private_key: RSA private key for signing
            state: MITM state dictionary
        """
        self.private_key = private_key
        self.state = state
        logger.info("TCP server initialized")
    
    def start(self) -> None:
        """Start the TCP server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            
            self.running = True
            logger.info(f"TCP proxy server listening on {self.host}:{self.port} for NFCGate clients")
            
        except Exception as e:
            logger.error(f"Failed to start TCP server: {e}")
            raise
    
    def handle_client(self, client_socket: socket.socket, addr: tuple) -> None:
        """
        Handle individual client connection.
        
        Args:
            client_socket: Client socket connection
            addr: Client address tuple
        """
        logger.info(f"TCP connection from NFCGate client at {addr}")
        
        try:
            # Receive data from client
            data = client_socket.recv(8192)
            
            if not data:
                logger.warning("No data received from client")
                client_socket.sendall(b"No data received")
                return

            # Log raw data
            try:
                ascii_data = data.decode('ascii', errors='ignore')
                logger.debug(f"Raw data from {addr}: {hexlify(data).decode()} (ASCII: {ascii_data[:100]}...)")
            except Exception:
                logger.debug(f"Raw data from {addr}: {hexlify(data).decode()} (non-ASCII)")

            # Try to parse as Wrapper message
            try:
                result = process_wrapper_message(data, self.private_key, self.state)
                
                if result:
                    client_socket.sendall(result)
                    logger.info(f"Sent modified data to client {addr}")
                else:
                    # No NFCData found, return original
                    client_socket.sendall(data)
                    logger.info(f"No NFCData found, returned original data to client {addr}")
                    
            except Exception as e:
                logger.error(f"Failed to process client data: {e}")
                traceback.print_exc()
                client_socket.sendall(data)  # Return original data on error
                
        except Exception as e:
            logger.error(f"Error handling TCP client {addr}: {e}")
            traceback.print_exc()
        finally:
            client_socket.close()
            logger.debug(f"Closed connection to client {addr}")
    
    def run(self) -> None:
        """Run the TCP server main loop."""
        if not self.socket or not self.running:
            raise RuntimeError("Server not started")
        
        try:
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:  # Only log if we're still supposed to be running
                        logger.error(f"Socket error accepting connection: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error accepting TCP connection: {e}")
                    traceback.print_exc()
                    
        except KeyboardInterrupt:
            logger.info("TCP server interrupted by user")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the TCP server."""
        if self.running:
            logger.info("Shutting down TCP server")
            self.running = False
            
            if self.socket:
                try:
                    self.socket.close()
                except Exception as e:
                    logger.error(f"Error closing TCP socket: {e}")
                
            logger.info("TCP server stopped")
    
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self.running
