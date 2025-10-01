"""
TLV (Tag-Length-Value) parsing and building utilities.
"""
from binascii import hexlify, unhexlify
from typing import List, Dict, Any, Optional
from ..utils.logger import Logger

logger = Logger("TLVParser")


def parse_tlv(data: bytes) -> List[Dict[str, Any]]:
    """
    Parse TLV data into a list of dictionaries, supporting multi-byte tags and lengths.
    
    Args:
        data: Raw TLV data bytes
        
    Returns:
        List of TLV dictionaries with keys: tag, length, value, children
        
    Raises:
        ValueError: If TLV data is invalid or incomplete
    """
    tlvs = []
    i = 0
    
    try:
        while i < len(data):
            if i >= len(data):
                raise ValueError("Incomplete TLV data: ran out of bytes")
            
            # Parse tag
            tag = data[i]
            i += 1
            
            # Handle multi-byte tags
            if (tag & 0x1F) == 0x1F:
                tag_bytes = [tag]
                while True:
                    if i >= len(data):
                        raise ValueError("Incomplete multi-byte tag")
                    b = data[i]
                    i += 1
                    tag_bytes.append(b)
                    if (b & 0x80) == 0:
                        break
                tag = int.from_bytes(bytes(tag_bytes), 'big')

            # Parse length
            if i >= len(data):
                raise ValueError("No bytes for TLV length")
            length = data[i]
            i += 1
            
            # Handle multi-byte lengths
            if length & 0x80:
                num_len_bytes = length & 0x7F
                if i + num_len_bytes > len(data):
                    raise ValueError("Incomplete multi-byte length")
                length = int.from_bytes(data[i:i+num_len_bytes], 'big')
                i += num_len_bytes

            # Parse value
            if i + length > len(data):
                raise ValueError(f"TLV value exceeds data length: i={i}, length={length}, data_len={len(data)}")
            value = data[i:i+length]
            i += length

            # Check if this is a constructed tag (has children)
            children = parse_tlv(value) if (tag & 0x20) == 0x20 else None
            
            tlvs.append({
                'tag': tag,
                'length': length,
                'value': value,
                'children': children
            })
            
        return tlvs
        
    except Exception as e:
        logger.error(f"parse_tlv error: {e}")
        raise


def build_tlv(tlvs: List[Dict[str, Any]]) -> bytes:
    """
    Build TLV data from a list of dictionaries.
    
    Args:
        tlvs: List of TLV dictionaries
        
    Returns:
        Built TLV data as bytes
        
    Raises:
        Exception: If building fails
    """
    result = bytearray()
    
    try:
        for tlv in tlvs:
            tag = tlv['tag']
            
            # Encode tag
            if tag <= 0xFF:
                tag_bytes = tag.to_bytes(1, 'big')
            else:
                tag_bytes_list = []
                temp_tag = tag
                while temp_tag > 0:
                    tag_bytes_list.insert(0, temp_tag & 0xFF)
                    temp_tag >>= 8
                tag_bytes = bytes(tag_bytes_list)

            # Get value (either from children or direct value)
            value = build_tlv(tlv['children']) if tlv['children'] else tlv['value']
            length = len(value)
            
            # Encode length
            if length < 0x80:
                length_bytes = length.to_bytes(1, 'big')
            else:
                length_len = (length.bit_length() + 7) // 8
                length_bytes = bytes([0x80 | length_len]) + length.to_bytes(length_len, 'big')

            # Combine tag, length, and value
            result.extend(tag_bytes)
            result.extend(length_bytes)
            result.extend(value)
            
        return bytes(result)
        
    except Exception as e:
        logger.error(f"build_tlv error: {e}")
        raise


def find_tlv(tlvs: List[Dict[str, Any]], tag: int) -> Optional[Dict[str, Any]]:
    """
    Find a TLV entry by tag, including in nested children.
    
    Args:
        tlvs: List of TLV dictionaries
        tag: Tag to search for
        
    Returns:
        TLV dictionary if found, None otherwise
    """
    for tlv in tlvs:
        if tlv['tag'] == tag:
            return tlv
        if tlv.get('children'):
            found = find_tlv(tlv['children'], tag)
            if found:
                return found
    return None


def replace_tlv_value(tlvs: List[Dict[str, Any]], tag_hex: str, new_value_hex: str) -> List[Dict[str, Any]]:
    """
    Replace or add a TLV entry with the given tag and value.
    
    Args:
        tlvs: List of TLV dictionaries
        tag_hex: Hexadecimal tag string
        new_value_hex: Hexadecimal value string
        
    Returns:
        Updated TLV list
        
    Raises:
        Exception: If replacement fails
    """
    try:
        tag = int(tag_hex, 16)
        new_value = unhexlify(new_value_hex)
        
        tlv = find_tlv(tlvs, tag)
        if tlv:
            # Update existing TLV
            tlv['value'] = new_value
            tlv['length'] = len(new_value)
            tlv['children'] = None
        else:
            # Add new TLV
            tlvs.append({
                'tag': tag,
                'length': len(new_value),
                'value': new_value,
                'children': None
            })
        
        return tlvs
        
    except Exception as e:
        logger.error(f"replace_tlv_value error: {e}")
        raise


def is_valid_tlv(data: bytes) -> bool:
    """
    Check if data is a valid TLV structure (starts with 0x6F or 0x77).
    
    Args:
        data: Data to validate
        
    Returns:
        True if valid TLV structure, False otherwise
    """
    if not data or len(data) < 2:
        return False
    return data[0] in (0x6F, 0x77)
