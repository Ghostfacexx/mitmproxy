"""
Cryptographic operations including RSA key generation and data signing.
"""
import os
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from typing import Tuple
from ..utils.logger import Logger

logger = Logger("CryptoHandler")

SIGNATURE_TAG = 0x9F45


def generate_rsa_keypair(bits: int = 2048) -> Tuple[RSA.RsaKey, RSA.RsaKey]:
    """
    Generate RSA key pair.
    
    Args:
        bits: Key size in bits (default: 2048)
        
    Returns:
        Tuple of (private_key, public_key)
        
    Raises:
        Exception: If key generation fails
    """
    try:
        key = RSA.generate(bits)
        logger.info(f"Generated RSA key pair with {bits} bits")
        return key, key.publickey()
    except Exception as e:
        logger.error(f"generate_rsa_keypair error: {e}")
        raise


def sign_data(data: bytes, private_key: RSA.RsaKey) -> bytes:
    """
    Sign data with SHA256 and PKCS1.5.
    
    Args:
        data: Data to sign
        private_key: RSA private key
        
    Returns:
        Signature bytes
        
    Raises:
        Exception: If signing fails
    """
    try:
        h = SHA256.new(data)
        signature = pkcs1_15.new(private_key).sign(h)
        logger.debug(f"Signed {len(data)} bytes of data")
        return signature
    except Exception as e:
        logger.error(f"sign_data error: {e}")
        raise


def load_or_generate_private_key(key_path: str) -> RSA.RsaKey:
    """
    Load private key from file or generate new one if not exists.
    
    Args:
        key_path: Path to private key file
        
    Returns:
        RSA private key
    """
    if os.path.exists(key_path):
        logger.info(f"Loading private key from {key_path}")
        try:
            with open(key_path, 'rb') as f:
                private_key = RSA.import_key(f.read())
            logger.info("Private key loaded successfully")
            return private_key
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise
    else:
        logger.info("Generating new RSA key pair")
        private_key, _ = generate_rsa_keypair()
        
        # Save the new key
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        with open(key_path, 'wb') as f:
            f.write(private_key.export_key())
        logger.info(f"Generated and saved new private key at {key_path}")
        
        return private_key


def add_signature_to_tlvs(tlvs: list, signature: bytes) -> list:
    """
    Add signature TLV to the list.
    
    Args:
        tlvs: List of TLV dictionaries
        signature: Signature bytes
        
    Returns:
        Updated TLV list with signature
        
    Raises:
        Exception: If adding signature fails
    """
    try:
        tlvs.append({
            'tag': SIGNATURE_TAG,
            'length': len(signature),
            'value': signature,
            'children': None
        })
        logger.debug(f"Added signature TLV with tag {hex(SIGNATURE_TAG)}")
        return tlvs
    except Exception as e:
        logger.error(f"add_signature error: {e}")
        raise
