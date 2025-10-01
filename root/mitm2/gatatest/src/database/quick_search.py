"""
Quick Search and Recognition System for Previously Approved Models.
Provides instant card recognition and auto-approval using internal database patterns.
"""
import time
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from ..database.payment_db import PaymentDatabase
from ..database.card_recognition import CardRecognitionEngine
from ..database.country_currency_lookup import analyze_card_geography
from ..mitm.bypass_engine import get_comprehensive_card_info
from ..utils.logger import Logger

logger = Logger("QuickRecognition")


class QuickRecognitionCache:
    """High-performance cache for quick card recognition."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize the recognition cache."""
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached recognition result."""
        if key in self.cache:
            self.access_times[key] = time.time()
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def put(self, key: str, value: Dict[str, Any]):
        """Cache recognition result."""
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def _evict_oldest(self):
        """Remove oldest cache entry."""
        if self.access_times:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache)
        }


class QuickSearchEngine:
    """High-speed search engine for previously approved card models."""
    
    def __init__(self, db_path: str = "database/payments.db"):
        """Initialize the quick search engine."""
        self.db = PaymentDatabase(db_path)
        self.recognition_engine = CardRecognitionEngine(db_path)
        self.cache = QuickRecognitionCache()
        
        # Pre-built search indexes for fast lookup
        self.bin_index = {}          # BIN -> card patterns
        self.brand_index = {}        # Brand -> card patterns  
        self.country_index = {}      # Country -> card patterns
        self.hash_index = {}         # Card hash -> full details
        
        # Performance tracking
        self.search_times = []
        self.recognition_times = []
        
        # Initialize indexes
        self._build_search_indexes()
        
        logger.info("Quick search engine initialized with indexed database")
    
    def _build_search_indexes(self):
        """Build search indexes from approved payments database."""
        try:
            start_time = time.time()
            
            # Get all approved payments for indexing
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute("""
                    SELECT card_hash, card_brand, card_type, bypass_method, 
                           success_rate, success_count, failure_count, notes,
                           tlv_modifications, last_seen
                    FROM approved_payments 
                    WHERE success_rate > 0.5
                    ORDER BY success_rate DESC, success_count DESC
                """)
                
                approved_payments = cursor.fetchall()
                
                for payment in approved_payments:
                    card_hash, brand, card_type, bypass_method = payment[:4]
                    success_rate, success_count, failure_count = payment[4:7]
                    notes, tlv_mods, last_seen = payment[7:10]
                    
                    # Create quick lookup pattern
                    pattern = {
                        'card_hash': card_hash,
                        'brand': brand,
                        'type': card_type,
                        'bypass_method': bypass_method,
                        'success_rate': success_rate,
                        'success_count': success_count,
                        'failure_count': failure_count,
                        'confidence': 'high' if success_rate > 0.8 else 'medium',
                        'tlv_modifications': json.loads(tlv_mods) if tlv_mods else [],
                        'last_seen': last_seen,
                        'auto_approve': success_rate > 0.7 and success_count >= 2
                    }
                    
                    # Index by card hash (primary lookup)
                    self.hash_index[card_hash] = pattern
                    
                    # Index by brand
                    if brand not in self.brand_index:
                        self.brand_index[brand] = []
                    self.brand_index[brand].append(pattern)
                    
                    # Get BIN from card profiles for BIN indexing
                    profile_cursor = conn.execute("""
                        SELECT bin_range, issuer_country FROM card_profiles 
                        WHERE card_hash = ?
                    """, (card_hash,))
                    profile = profile_cursor.fetchone()
                    
                    if profile and profile[0]:
                        bin_range = profile[0]
                        country = profile[1]
                        
                        # Index by BIN
                        if bin_range not in self.bin_index:
                            self.bin_index[bin_range] = []
                        self.bin_index[bin_range].append(pattern)
                        
                        # Index by country
                        if country and country not in self.country_index:
                            self.country_index[country] = []
                        if country:
                            self.country_index[country].append(pattern)
            
            build_time = time.time() - start_time
            logger.info(f"Search indexes built in {build_time:.3f}s - "
                       f"Hash: {len(self.hash_index)}, Brand: {len(self.brand_index)}, "
                       f"BIN: {len(self.bin_index)}, Country: {len(self.country_index)}")
            
        except Exception as e:
            logger.error(f"Failed to build search indexes: {e}")
    
    def quick_search(self, tlvs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform ultra-fast card recognition using pre-built indexes.
        
        Args:
            tlvs: TLV data from card
            
        Returns:
            Quick recognition result with auto-approval recommendation
        """
        start_time = time.time()
        
        try:
            # Extract basic card info for search
            card_info = get_comprehensive_card_info(tlvs)
            search_key = self._generate_search_key(card_info)
            
            # Check cache first (fastest path)
            cached_result = self.cache.get(search_key)
            if cached_result:
                cached_result['cache_hit'] = True
                cached_result['search_time_ms'] = int((time.time() - start_time) * 1000)
                logger.debug(f"Cache hit for card search: {card_info.get('brand', 'Unknown')}")
                return cached_result
            
            # Generate card hash for exact lookup
            card_hash = self._hash_card_data(card_info)
            
            # Primary search: Exact hash match (most reliable)
            exact_match = self.hash_index.get(card_hash)
            if exact_match:
                result = self._build_quick_result(card_info, exact_match, 'exact_match', start_time)
                self.cache.put(search_key, result)
                return result
            
            # Secondary search: BIN-based pattern matching
            bin_code = card_info.get('pan', '')[:6] if card_info.get('pan') else ''
            if bin_code and bin_code in self.bin_index:
                best_match = self._find_best_bin_match(card_info, self.bin_index[bin_code])
                if best_match:
                    result = self._build_quick_result(card_info, best_match, 'bin_match', start_time)
                    self.cache.put(search_key, result)
                    return result
            
            # Tertiary search: Brand-based pattern matching
            brand = card_info.get('brand', 'Unknown')
            if brand in self.brand_index:
                best_match = self._find_best_brand_match(card_info, self.brand_index[brand])
                if best_match:
                    result = self._build_quick_result(card_info, best_match, 'brand_match', start_time)
                    self.cache.put(search_key, result)
                    return result
            
            # Quaternary search: Country-based pattern matching
            country = card_info.get('issuer_country')
            if country and country in self.country_index:
                best_match = self._find_best_country_match(card_info, self.country_index[country])
                if best_match:
                    result = self._build_quick_result(card_info, best_match, 'country_match', start_time)
                    self.cache.put(search_key, result)
                    return result
            
            # No match found - return new card result
            result = self._build_new_card_result(card_info, start_time)
            self.cache.put(search_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Quick search failed: {e}")
            return self._build_error_result({}, start_time, str(e))
    
    def instant_auto_approve(self, tlvs: List[Dict[str, Any]], terminal_type: str) -> Dict[str, Any]:
        """
        Instant auto-approval decision based on quick search results.
        
        Args:
            tlvs: TLV data from card
            terminal_type: Terminal type (POS/ATM)
            
        Returns:
            Instant auto-approval decision with bypass instructions
        """
        start_time = time.time()
        
        try:
            # Perform quick search
            search_result = self.quick_search(tlvs)
            
            # Check if auto-approval is possible
            if not search_result.get('auto_approve', False):
                return {
                    'auto_approve': False,
                    'reason': search_result.get('reason', 'No approved pattern found'),
                    'search_result': search_result,
                    'requires_manual_review': True,
                    'processing_time_ms': int((time.time() - start_time) * 1000)
                }
            
            # Get approved bypass method
            bypass_method = search_result.get('bypass_method')
            tlv_modifications = search_result.get('tlv_modifications', [])
            
            # Validate compatibility with terminal
            card_info = search_result.get('card_info', {})
            if bypass_method and not self._validate_terminal_compatibility(card_info, terminal_type, bypass_method):
                return {
                    'auto_approve': False,
                    'reason': f'Bypass method {bypass_method} not compatible with {terminal_type}',
                    'search_result': search_result,
                    'requires_manual_review': True,
                    'processing_time_ms': int((time.time() - start_time) * 1000)
                }
            
            if not bypass_method:
                return {
                    'auto_approve': False,
                    'reason': 'No bypass method specified',
                    'search_result': search_result,
                    'requires_manual_review': True,
                    'processing_time_ms': int((time.time() - start_time) * 1000)
                }
            
            # Generate transaction ID for tracking
            transaction_id = self._generate_transaction_id()
            
            # Build auto-approval result
            return {
                'auto_approve': True,
                'transaction_id': transaction_id,
                'bypass_method': bypass_method,
                'tlv_modifications': tlv_modifications,
                'confidence_level': search_result.get('confidence', 'medium'),
                'success_rate': search_result.get('success_rate', 0.0),
                'match_type': search_result.get('match_type', 'unknown'),
                'card_info': card_info,
                'search_result': search_result,
                'instructions': self._generate_bypass_instructions(bypass_method, tlv_modifications),
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'requires_manual_review': False
            }
            
        except Exception as e:
            logger.error(f"Instant auto-approval failed: {e}")
            return {
                'auto_approve': False,
                'reason': f'Auto-approval error: {str(e)}',
                'requires_manual_review': True,
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'error': str(e)
            }
    
    def batch_recognition(self, card_list: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Batch recognition for multiple cards with optimized performance.
        
        Args:
            card_list: List of TLV data lists for multiple cards
            
        Returns:
            List of recognition results for each card
        """
        start_time = time.time()
        results = []
        
        logger.info(f"Starting batch recognition for {len(card_list)} cards")
        
        for i, tlvs in enumerate(card_list):
            try:
                result = self.quick_search(tlvs)
                result['batch_index'] = i
                results.append(result)
                
                # Log progress for large batches
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(card_list)} cards")
                    
            except Exception as e:
                logger.error(f"Batch recognition failed for card {i}: {e}")
                results.append({
                    'batch_index': i,
                    'error': str(e),
                    'auto_approve': False,
                    'requires_manual_review': True
                })
        
        total_time = time.time() - start_time
        logger.info(f"Batch recognition completed: {len(results)} cards in {total_time:.3f}s "
                   f"({len(results)/total_time:.1f} cards/sec)")
        
        return results
    
    def get_recognition_patterns(self, brand: Optional[str] = None, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Get available recognition patterns for analysis.
        
        Args:
            brand: Filter by card brand (optional)
            country: Filter by issuer country (optional)
            
        Returns:
            Available recognition patterns and statistics
        """
        patterns = {
            'total_patterns': len(self.hash_index),
            'by_brand': {},
            'by_country': {},
            'by_confidence': {'high': 0, 'medium': 0, 'low': 0},
            'auto_approve_count': 0
        }
        
        # Analyze patterns by brand
        for brand_name, brand_patterns in self.brand_index.items():
            if brand and brand.lower() != brand_name.lower():
                continue
            patterns['by_brand'][brand_name] = {
                'count': len(brand_patterns),
                'avg_success_rate': sum(p['success_rate'] for p in brand_patterns) / len(brand_patterns),
                'auto_approve_count': sum(1 for p in brand_patterns if p['auto_approve'])
            }
        
        # Analyze patterns by country
        for country_code, country_patterns in self.country_index.items():
            if country and country != country_code:
                continue
            patterns['by_country'][country_code] = {
                'count': len(country_patterns),
                'avg_success_rate': sum(p['success_rate'] for p in country_patterns) / len(country_patterns),
                'auto_approve_count': sum(1 for p in country_patterns if p['auto_approve'])
            }
        
        # Analyze by confidence and auto-approve counts
        for pattern in self.hash_index.values():
            patterns['by_confidence'][pattern['confidence']] += 1
            if pattern['auto_approve']:
                patterns['auto_approve_count'] += 1
        
        return patterns
    
    def _generate_search_key(self, card_info: Dict[str, Any]) -> str:
        """Generate cache key for card search."""
        key_data = {
            'pan_prefix': card_info.get('pan', '')[:8],
            'brand': card_info.get('brand', ''),
            'type': card_info.get('type', ''),
            'country': card_info.get('issuer_country', ''),
            'currency': card_info.get('currency_code', '')
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _hash_card_data(self, card_data: Dict[str, Any]) -> str:
        """Create hash of card data for exact matching."""
        key_data = {
            'pan': card_data.get('pan', ''),
            'expiry': card_data.get('expiry_date', ''),
            'aid': card_data.get('application_id', ''),
            'brand': card_data.get('brand', ''),
            'type': card_data.get('type', '')
        }
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _find_best_bin_match(self, card_info: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find best match from BIN candidates."""
        if not candidates:
            return None
        
        # Score candidates by similarity
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            score = 0
            
            # Brand match
            if card_info.get('brand') == candidate.get('brand'):
                score += 3
            
            # Type match  
            if card_info.get('type') == candidate.get('type'):
                score += 2
            
            # Success rate bonus
            score += candidate.get('success_rate', 0) * 2
            
            # Recent activity bonus
            if candidate.get('last_seen'):
                try:
                    from datetime import datetime, timedelta
                    last_seen = datetime.fromisoformat(candidate['last_seen'].replace('Z', '+00:00'))
                    if datetime.now() - last_seen < timedelta(days=30):
                        score += 1
                except:
                    pass
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        return best_match if best_score >= 3 else None  # Minimum score threshold
    
    def _find_best_brand_match(self, card_info: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find best match from brand candidates."""
        # Filter by type first
        type_matches = [c for c in candidates if c.get('type') == card_info.get('type')]
        if type_matches:
            # Return highest success rate match
            return max(type_matches, key=lambda x: x.get('success_rate', 0))
        
        # Fallback to highest success rate regardless of type
        return max(candidates, key=lambda x: x.get('success_rate', 0)) if candidates else None
    
    def _find_best_country_match(self, card_info: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find best match from country candidates."""
        # Prefer brand + type match within country
        for candidate in candidates:
            if (candidate.get('brand') == card_info.get('brand') and 
                candidate.get('type') == card_info.get('type')):
                return candidate
        
        # Fallback to brand match
        brand_matches = [c for c in candidates if c.get('brand') == card_info.get('brand')]
        if brand_matches:
            return max(brand_matches, key=lambda x: x.get('success_rate', 0))
        
        # Last resort - highest success rate in country
        return max(candidates, key=lambda x: x.get('success_rate', 0)) if candidates else None
    
    def _build_quick_result(self, card_info: Dict[str, Any], match: Dict[str, Any], 
                           match_type: str, start_time: float) -> Dict[str, Any]:
        """Build quick recognition result."""
        return {
            'card_info': card_info,
            'match_type': match_type,
            'auto_approve': match.get('auto_approve', False),
            'bypass_method': match.get('bypass_method'),
            'tlv_modifications': match.get('tlv_modifications', []),
            'confidence': match.get('confidence', 'medium'),
            'success_rate': match.get('success_rate', 0.0),
            'success_count': match.get('success_count', 0),
            'failure_count': match.get('failure_count', 0),
            'last_seen': match.get('last_seen'),
            'reason': f'Found {match_type} with {match.get("success_rate", 0):.1%} success rate',
            'search_time_ms': int((time.time() - start_time) * 1000),
            'cache_hit': False,
            'requires_manual_review': not match.get('auto_approve', False)
        }
    
    def _build_new_card_result(self, card_info: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Build result for new/unknown card."""
        return {
            'card_info': card_info,
            'match_type': 'new_card',
            'auto_approve': False,
            'bypass_method': None,
            'tlv_modifications': [],
            'confidence': 'none',
            'success_rate': 0.0,
            'success_count': 0,
            'failure_count': 0,
            'reason': 'New card - no previous approval pattern found',
            'search_time_ms': int((time.time() - start_time) * 1000),
            'cache_hit': False,
            'requires_manual_review': True
        }
    
    def _build_error_result(self, card_info: Dict[str, Any], start_time: float, error: str) -> Dict[str, Any]:
        """Build error result."""
        return {
            'card_info': card_info,
            'match_type': 'error',
            'auto_approve': False,
            'error': error,
            'reason': f'Search error: {error}',
            'search_time_ms': int((time.time() - start_time) * 1000),
            'cache_hit': False,
            'requires_manual_review': True
        }
    
    def _validate_terminal_compatibility(self, card_info: Dict[str, Any], terminal_type: str, bypass_method: str) -> bool:
        """Validate if bypass method is compatible with terminal type."""
        # Basic compatibility checks
        incompatible_combinations = {
            ('ATM', 'signature'),  # ATMs don't support signature
            ('POS', 'cash_advance'),  # POS doesn't support cash advance bypasses
        }
        
        return (terminal_type, bypass_method) not in incompatible_combinations
    
    def _generate_bypass_instructions(self, bypass_method: str, tlv_modifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed bypass execution instructions."""
        instructions = {
            'method': bypass_method,
            'steps': [],
            'tlv_changes': tlv_modifications,
            'verification_required': False
        }
        
        if bypass_method == 'signature':
            instructions['steps'] = [
                'Set CVM to signature verification',
                'Disable PIN requirement',
                'Apply TLV modifications if specified'
            ]
        elif bypass_method == 'cdcvm':
            instructions['steps'] = [
                'Enable Consumer Device CVM',
                'Set appropriate CVM list',
                'Apply TLV modifications if specified'
            ]
        elif bypass_method == 'no_cvm':
            instructions['steps'] = [
                'Disable all CVM requirements',
                'Set transaction as no verification',
                'Apply TLV modifications if specified'
            ]
        else:
            instructions['steps'] = [
                f'Apply {bypass_method} bypass method',
                'Apply TLV modifications if specified'
            ]
            instructions['verification_required'] = True
        
        return instructions
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        import uuid
        return f"QS_{int(time.time())}_{str(uuid.uuid4())[:8]}"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        cache_stats = self.cache.get_stats()
        
        return {
            'cache_performance': cache_stats,
            'index_sizes': {
                'hash_index': len(self.hash_index),
                'brand_index': len(self.brand_index),
                'bin_index': len(self.bin_index),
                'country_index': len(self.country_index)
            },
            'search_performance': {
                'avg_search_time_ms': sum(self.search_times) / len(self.search_times) if self.search_times else 0,
                'total_searches': len(self.search_times)
            }
        }


def create_quick_search_engine(db_path: str = "database/payments.db") -> QuickSearchEngine:
    """
    Factory function to create a quick search engine.
    
    Args:
        db_path: Path to payment database
        
    Returns:
        Configured QuickSearchEngine instance
    """
    engine = QuickSearchEngine(db_path)
    logger.info("Quick search engine created and ready for high-speed recognition")
    return engine
