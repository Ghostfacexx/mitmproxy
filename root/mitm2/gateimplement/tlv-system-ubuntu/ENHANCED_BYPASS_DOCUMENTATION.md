# Enhanced Bypass Engine Documentation

## Overview

The enhanced bypass engine provides comprehensive card type detection and specialized bypass strategies for different payment card brands and types. This system can identify and handle:

### Supported Card Brands

- **Visa**: Traditional and modern Visa cards
- **Mastercard**: All Mastercard variants including Maestro
- **American Express**: Personal and business Amex cards
- **Discover**: Discover and Diners Club cards
- **JCB**: Japanese Credit Bureau cards
- **UnionPay**: Chinese UnionPay cards

### Supported Card Types

- **Debit Cards**: Bank debit cards with PIN verification
- **Credit Cards**: Traditional credit cards with signature/CDCVM
- **Prepaid Cards**: Prepaid and gift cards
- **Business Cards**: Commercial and corporate cards

## Card Detection Methods

### 1. BIN Range Detection

The system uses Bank Identification Number (BIN) ranges to identify card brands:

```python
CARD_BRANDS = {
    'VISA': {
        'bin_ranges': [(4, 4)],  # Starts with 4
    },
    'MASTERCARD': {
        'bin_ranges': [(5, 5), (2221, 2720)],  # Starts with 5 or 2221-2720
    },
    'AMEX': {
        'bin_ranges': [(34, 34), (37, 37)],  # Starts with 34 or 37
    }
}
```text

### 2. Application ID (AID) Detection

Fallback detection using EMV Application Identifiers:

```python
'aid_patterns': [
    'A0000000031010',    # Visa Credit/Debit
    'A0000000041010',    # Mastercard Credit/Debit
    'A000000025010701',  # American Express
]
```text

### 3. Application Usage Control (AUC) Detection

Card type detection based on usage control bytes:

```python
CARD_TYPES = {
    'DEBIT': {
        'auc_patterns': ['08', '18', '28', '48'],  # Common debit patterns
    },
    'CREDIT': {
        'auc_patterns': ['00', '01', '02', '04', '40'],  # Common credit patterns
    }
}
```python

## Bypass Strategies

### Brand-Specific Bypasses

#### Visa Bypasses

- **Debit Cards**: CDCVM bypass with specific CVR handling
- **Credit Cards**: Signature verification preference
- **Business Cards**: Enhanced limits with no CVM

```python
def apply_visa_bypasses(tlvs, terminal_type, state, card_info):
    if card_info['type'] == 'Debit Card':
        tlvs = replace_tlv_value(tlvs, '9F10', '0110A00003220000000000000000000000FF')
    elif card_info['type'] == 'Credit Card':
        tlvs = replace_tlv_value(tlvs, '9F10', '0110A00001220000000000000000000000FF')
```python

#### Mastercard Bypasses

- **Different CVR patterns** for debit vs credit
- **CVM List modifications** for bypass
- **Enhanced business card** handling

#### American Express Bypasses

- **Signature-preferred** verification
- **Business card** enhanced processing
- **Amex-specific TLV** modifications

### Terminal-Specific Adaptations

#### ATM Terminals

- Stricter PIN requirements
- Online verification preference
- Debit card optimizations

#### POS Terminals

- Signature verification flexibility
- CDCVM support
- Business card optimizations

## Usage Examples

### Basic Card Detection

```python
from src.mitm.bypass_engine import get_comprehensive_card_info

card_info = get_comprehensive_card_info(tlvs)
print(f"Card: {card_info['brand']} {card_info['type']}")
```python

### Bypass Strategy Selection

```python
from src.mitm.bypass_engine import get_bypass_strategy

strategy = get_bypass_strategy(card_info, 'POS')
print(f"Strategy: {strategy['primary_method']}")
print(f"Success Rate: {strategy['success_probability']:.1%}")
```python

### Complete Bypass Application

```python
from src.mitm.bypass_engine import bypass_tlv_modifications

state = {
    'bypass_pin': True,
    'cdcvm_enabled': True,
    'enhanced_limits': True
}

modified_tlvs = bypass_tlv_modifications(tlvs, card_brand, terminal_type, state)
```python

## Configuration Options

### MITM State Parameters

- `bypass_pin`: Enable PIN bypass modifications
- `cdcvm_enabled`: Enable Consumer Device CVM
- `enhanced_limits`: Enable enhanced transaction limits
- `block_all`: Block all transactions (testing mode)

### Success Probability Factors

The system calculates bypass success probability based on:

- Card brand compatibility
- Card type characteristics
- Terminal type requirements
- Configuration state

## Advanced Features

### Strategy Validation

```python
def validate_bypass_compatibility(card_info, terminal_type, state):
    # Check for problematic combinations
    if card_info['brand'] == 'UnionPay' and terminal_type == 'ATM':
        return False  # Lower success rate
    return True
```bash

### Risk Assessment

- **Low Risk**: Amex signature verification
- **Medium Risk**: Visa/Mastercard standard bypass
- **High Risk**: UnionPay or unknown cards

### Fallback Methods

1. Primary method based on card/terminal combination
2. Fallback method if primary fails
3. Generic bypass for unknown cards

## Testing

Run the comprehensive test suite:
```bash
python test_enhanced_bypass.py
```bash

This tests:

- All card brand detection patternserns
- Card type identification
- Bypass strategy selection
- Compatibility validation
- Success probability calculation

## Security Considerations

### Detection Avoidance

- Uses standard EMV data fields
- Mimics legitimate transaction patterns
- Adaptive to different card/terminal combinations

### Logging and Monitoring

- Comprehensive logging of all bypass attempts
- Success/failure tracking
- Card type statistics
- Terminal compatibility reports

## Troubleshooting

### Common Issues

1. **Unknown Card Brand**: Falls back to generic bypass
2. **Incompatible Terminal**: Validation warns of low success
3. **Missing TLV Data**: Uses available information for partial detection

### Debug Information

Enable debug logging to see:

- Card detection process
- Bypass strategy selection
- TLV modification details
- Compatibility assessments

## Future Enhancements

### Planned Features

- Machine learning for strategy optimization
- Regional card variant support
- Dynamic bypass adaptation
- Enhanced business card detection
- Contactless payment optimization

### Regional Support

- European cards (Maestro, V Pay)
- Asian payment networks
- Regional business card patterns
- Local regulatory compliance
