"""
Payment scheme detection from card data.
"""
from typing import List, Dict, Any, Optional
from ..core.tlv_parser import find_tlv
from ..utils.logger import Logger

logger = Logger("PaymentDetector")


def get_scheme_from_tlvs(tlvs: List[Dict[str, Any]]) -> str:
    """
    Detect payment scheme (Visa/Mastercard) from PAN tag.
    
    Args:
        tlvs: List of TLV dictionaries
        
    Returns:
        Payment scheme name ('Visa', 'Mastercard', or 'Unknown')
    """
    pan_tlv = find_tlv(tlvs, 0x5A)  # PAN (Primary Account Number) tag
    
    if pan_tlv and len(pan_tlv['value']) > 0:
        first_digit = (pan_tlv['value'][0] >> 4) & 0x0F
        
        if first_digit == 4:
            scheme = 'Visa'
        elif first_digit == 5:
            scheme = 'Mastercard'
        else:
            scheme = 'Unknown'
            
        logger.debug(f"Detected payment scheme: {scheme} (first digit: {first_digit})")
        return scheme
    
    logger.debug("No PAN found, payment scheme unknown")
    return 'Unknown'


def detect_terminal_type(tlvs: List[Dict[str, Any]]) -> str:
    """
    Detect terminal type from TLV data.
    
    Args:
        tlvs: List of TLV dictionaries
        
    Returns:
        Terminal type ('POS', 'ATM', or 'generic')
    """
    term_tlv = find_tlv(tlvs, 0x9F35)  # Terminal Type tag
    
    if term_tlv:
        term_type = term_tlv['value']
        
        if term_type == b'\x21':
            terminal_type = 'POS'
        elif term_type == b'\x22':
            terminal_type = 'ATM'
        else:
            terminal_type = 'generic'
            
        logger.debug(f"Detected terminal type: {terminal_type}")
        return terminal_type
    
    logger.debug("No terminal type found, using generic")
    return 'generic'


def extract_card_info(tlvs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract comprehensive card information from TLV data.
    
    Args:
        tlvs: List of TLV dictionaries
        
    Returns:
        Dictionary with card information
    """
    info = {
        'scheme': get_scheme_from_tlvs(tlvs),
        'terminal_type': detect_terminal_type(tlvs),
        'pan': None,
        'expiry_date': None,
        'cardholder_name': None,
        'application_id': None
    }
    
    # Extract PAN
    pan_tlv = find_tlv(tlvs, 0x5A)
    if pan_tlv:
        info['pan'] = pan_tlv['value'].hex()
    
    # Extract expiry date
    expiry_tlv = find_tlv(tlvs, 0x5F24)
    if expiry_tlv:
        info['expiry_date'] = expiry_tlv['value'].hex()
    
    # Extract cardholder name
    name_tlv = find_tlv(tlvs, 0x5F20)
    if name_tlv:
        try:
            info['cardholder_name'] = name_tlv['value'].decode('ascii', errors='ignore').strip()
        except:
            info['cardholder_name'] = name_tlv['value'].hex()
    
    # Extract Application ID (AID)
    aid_tlv = find_tlv(tlvs, 0x4F)
    if aid_tlv:
        info['application_id'] = aid_tlv['value'].hex()
    
    logger.info(f"Extracted card info: scheme={info['scheme']}, terminal={info['terminal_type']}")
    return info
