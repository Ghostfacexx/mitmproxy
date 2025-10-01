"""
Main entry point for the NFC proxy system.
"""
import os
import sys
import signal
import threading
import traceback
from src.utils.config import ConfigManager
from src.utils.logger import setup_logger, Logger
from src.core.crypto_handler import load_or_generate_private_key
from src.servers.tcp_server import TCPProxyServer
from src.servers.http_server import HTTPProxyServer

# Initialize logger
setup_logger()
logger = Logger("Main")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point for the NFC proxy system."""
    logger.info("Starting NFCGate proxy server")
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        proxy_config = config_manager.get_proxy_config()
        mitm_config = config_manager.get_mitm_config()
        
        # Extract configuration values
        tcp_port = proxy_config.get('tcp_port', 8081)
        http_port = proxy_config.get('http_port', 8082)
        keys_dir = proxy_config.get('keys_directory', 'keys')
        logs_dir = proxy_config.get('logs_directory', 'logs')
        
        # Initialize state from configuration
        state = {
            'block_all': mitm_config.get('block_all', False),
            'bypass_pin': mitm_config.get('bypass_pin', True),
            'cdcvm_enabled': mitm_config.get('cdcvm_enabled', True)
        }
        
        logger.info(f"Server configuration: tcp_port={tcp_port}, http_port={http_port}")
        logger.info(f"MITM state: {state}")
        
        # Ensure directories exist
        os.makedirs(keys_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        
        # Load or generate private key
        private_key_path = os.path.join(keys_dir, 'private.pem')
        private_key = load_or_generate_private_key(private_key_path)
        
        # Initialize servers
        tcp_server = TCPProxyServer('0.0.0.0', tcp_port)
        http_server = HTTPProxyServer('0.0.0.0', http_port)
        
        # Initialize server components
        tcp_server.initialize(private_key, state)
        http_server.initialize_handler(private_key, state, 'config/mitm_config.json')
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start HTTP server in background
        http_server.start()
        
        # Start TCP server
        tcp_server.start()
        
        logger.info("All servers started successfully")
        logger.info("Press Ctrl+C to stop the servers")
        
        # Run TCP server in main thread (blocking)
        try:
            tcp_server.run()
        except KeyboardInterrupt:
            logger.info("Shutting down servers...")
        finally:
            # Stop servers
            tcp_server.stop()
            http_server.stop()
            logger.info("All servers stopped gracefully")
            
    except Exception as e:
        logger.error(f"Main function failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
