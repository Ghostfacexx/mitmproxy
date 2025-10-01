"""
Country and currency lookup tables and integration functions.
Provides comprehensive mapping of issuer countries and currency codes with card recognition integration.
"""
from typing import Optional, Dict, List, Any
import json
from ..utils.logger import Logger

logger = Logger("CountryCurrencyLookup")

# ISO 3166-1 Country codes mapping (hex to country info)
COUNTRY_CODES = {
    # Major card issuing countries
    '0840': {'name': 'United States', 'code': 'US', 'region': 'North America', 'currency': 'USD'},
    '0124': {'name': 'Canada', 'code': 'CA', 'region': 'North America', 'currency': 'CAD'},
    '0826': {'name': 'United Kingdom', 'code': 'GB', 'region': 'Europe', 'currency': 'GBP'},
    '0276': {'name': 'Germany', 'code': 'DE', 'region': 'Europe', 'currency': 'EUR'},
    '0250': {'name': 'France', 'code': 'FR', 'region': 'Europe', 'currency': 'EUR'},
    '0380': {'name': 'Italy', 'code': 'IT', 'region': 'Europe', 'currency': 'EUR'},
    '0724': {'name': 'Spain', 'code': 'ES', 'region': 'Europe', 'currency': 'EUR'},
    '0528': {'name': 'Netherlands', 'code': 'NL', 'region': 'Europe', 'currency': 'EUR'},
    '0056': {'name': 'Belgium', 'code': 'BE', 'region': 'Europe', 'currency': 'EUR'},
    '0756': {'name': 'Switzerland', 'code': 'CH', 'region': 'Europe', 'currency': 'CHF'},
    '0040': {'name': 'Austria', 'code': 'AT', 'region': 'Europe', 'currency': 'EUR'},
    '0036': {'name': 'Australia', 'code': 'AU', 'region': 'Oceania', 'currency': 'AUD'},
    '0392': {'name': 'Japan', 'code': 'JP', 'region': 'Asia', 'currency': 'JPY'},
    '0410': {'name': 'South Korea', 'code': 'KR', 'region': 'Asia', 'currency': 'KRW'},
    '0156': {'name': 'China', 'code': 'CN', 'region': 'Asia', 'currency': 'CNY'},
    '0344': {'name': 'Hong Kong', 'code': 'HK', 'region': 'Asia', 'currency': 'HKD'},
    '0702': {'name': 'Singapore', 'code': 'SG', 'region': 'Asia', 'currency': 'SGD'},
    '0356': {'name': 'India', 'code': 'IN', 'region': 'Asia', 'currency': 'INR'},
    '0764': {'name': 'Thailand', 'code': 'TH', 'region': 'Asia', 'currency': 'THB'},
    '0608': {'name': 'Philippines', 'code': 'PH', 'region': 'Asia', 'currency': 'PHP'},
    '0458': {'name': 'Malaysia', 'code': 'MY', 'region': 'Asia', 'currency': 'MYR'},
    '0360': {'name': 'Indonesia', 'code': 'ID', 'region': 'Asia', 'currency': 'IDR'},
    '0076': {'name': 'Brazil', 'code': 'BR', 'region': 'South America', 'currency': 'BRL'},
    '0484': {'name': 'Mexico', 'code': 'MX', 'region': 'North America', 'currency': 'MXN'},
    '0032': {'name': 'Argentina', 'code': 'AR', 'region': 'South America', 'currency': 'ARS'},
    '0152': {'name': 'Chile', 'code': 'CL', 'region': 'South America', 'currency': 'CLP'},
    '0170': {'name': 'Colombia', 'code': 'CO', 'region': 'South America', 'currency': 'COP'},
    '0604': {'name': 'Peru', 'code': 'PE', 'region': 'South America', 'currency': 'PEN'},
    '0710': {'name': 'South Africa', 'code': 'ZA', 'region': 'Africa', 'currency': 'ZAR'},
    '0818': {'name': 'Egypt', 'code': 'EG', 'region': 'Africa', 'currency': 'EGP'},
    '0504': {'name': 'Morocco', 'code': 'MA', 'region': 'Africa', 'currency': 'MAD'},
    '0012': {'name': 'Algeria', 'code': 'DZ', 'region': 'Africa', 'currency': 'DZD'},
    '0784': {'name': 'United Arab Emirates', 'code': 'AE', 'region': 'Middle East', 'currency': 'AED'},
    '0682': {'name': 'Saudi Arabia', 'code': 'SA', 'region': 'Middle East', 'currency': 'SAR'},
    '0376': {'name': 'Israel', 'code': 'IL', 'region': 'Middle East', 'currency': 'ILS'},
    '0792': {'name': 'Turkey', 'code': 'TR', 'region': 'Europe/Asia', 'currency': 'TRY'},
    '0643': {'name': 'Russia', 'code': 'RU', 'region': 'Europe/Asia', 'currency': 'RUB'},
    '0616': {'name': 'Poland', 'code': 'PL', 'region': 'Europe', 'currency': 'PLN'},
    '0203': {'name': 'Czech Republic', 'code': 'CZ', 'region': 'Europe', 'currency': 'CZK'},
    '0348': {'name': 'Hungary', 'code': 'HU', 'region': 'Europe', 'currency': 'HUF'},
    '0642': {'name': 'Romania', 'code': 'RO', 'region': 'Europe', 'currency': 'RON'},
    '0208': {'name': 'Denmark', 'code': 'DK', 'region': 'Europe', 'currency': 'DKK'},
    '0752': {'name': 'Sweden', 'code': 'SE', 'region': 'Europe', 'currency': 'SEK'},
    '0578': {'name': 'Norway', 'code': 'NO', 'region': 'Europe', 'currency': 'NOK'},
    '0246': {'name': 'Finland', 'code': 'FI', 'region': 'Europe', 'currency': 'EUR'},
    '0372': {'name': 'Ireland', 'code': 'IE', 'region': 'Europe', 'currency': 'EUR'},
    '0620': {'name': 'Portugal', 'code': 'PT', 'region': 'Europe', 'currency': 'EUR'},
    '0300': {'name': 'Greece', 'code': 'GR', 'region': 'Europe', 'currency': 'EUR'},
}

# ISO 4217 Currency codes mapping (hex to currency info)
CURRENCY_CODES = {
    # Major world currencies
    '0840': {'name': 'US Dollar', 'code': 'USD', 'symbol': '$', 'decimals': 2, 'countries': ['US', 'EC', 'SV', 'PW', 'MH', 'FM', 'MP', 'PR', 'TC', 'VG', 'VI']},
    '0978': {'name': 'Euro', 'code': 'EUR', 'symbol': '€', 'decimals': 2, 'countries': ['AD', 'AT', 'BE', 'CY', 'EE', 'FI', 'FR', 'DE', 'GR', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'MC', 'ME', 'NL', 'PT', 'SM', 'SK', 'SI', 'ES', 'VA']},
    '0826': {'name': 'Pound Sterling', 'code': 'GBP', 'symbol': '£', 'decimals': 2, 'countries': ['GB', 'IM', 'JE', 'GG']},
    '0392': {'name': 'Japanese Yen', 'code': 'JPY', 'symbol': '¥', 'decimals': 0, 'countries': ['JP']},
    '0756': {'name': 'Swiss Franc', 'code': 'CHF', 'symbol': 'CHF', 'decimals': 2, 'countries': ['CH', 'LI']},
    '0124': {'name': 'Canadian Dollar', 'code': 'CAD', 'symbol': 'C$', 'decimals': 2, 'countries': ['CA']},
    '0036': {'name': 'Australian Dollar', 'code': 'AUD', 'symbol': 'A$', 'decimals': 2, 'countries': ['AU', 'CX', 'CC', 'HM', 'KI', 'NR', 'NF', 'TV']},
    '0156': {'name': 'Chinese Yuan', 'code': 'CNY', 'symbol': '¥', 'decimals': 2, 'countries': ['CN']},
    '0344': {'name': 'Hong Kong Dollar', 'code': 'HKD', 'symbol': 'HK$', 'decimals': 2, 'countries': ['HK']},
    '0702': {'name': 'Singapore Dollar', 'code': 'SGD', 'symbol': 'S$', 'decimals': 2, 'countries': ['SG']},
    '0410': {'name': 'South Korean Won', 'code': 'KRW', 'symbol': '₩', 'decimals': 0, 'countries': ['KR']},
    '0356': {'name': 'Indian Rupee', 'code': 'INR', 'symbol': '₹', 'decimals': 2, 'countries': ['IN', 'BT']},
    '0764': {'name': 'Thai Baht', 'code': 'THB', 'symbol': '฿', 'decimals': 2, 'countries': ['TH']},
    '0458': {'name': 'Malaysian Ringgit', 'code': 'MYR', 'symbol': 'RM', 'decimals': 2, 'countries': ['MY']},
    '0360': {'name': 'Indonesian Rupiah', 'code': 'IDR', 'symbol': 'Rp', 'decimals': 2, 'countries': ['ID']},
    '0608': {'name': 'Philippine Peso', 'code': 'PHP', 'symbol': '₱', 'decimals': 2, 'countries': ['PH']},
    '0076': {'name': 'Brazilian Real', 'code': 'BRL', 'symbol': 'R$', 'decimals': 2, 'countries': ['BR']},
    '0484': {'name': 'Mexican Peso', 'code': 'MXN', 'symbol': '$', 'decimals': 2, 'countries': ['MX']},
    '0032': {'name': 'Argentine Peso', 'code': 'ARS', 'symbol': '$', 'decimals': 2, 'countries': ['AR']},
    '0152': {'name': 'Chilean Peso', 'code': 'CLP', 'symbol': '$', 'decimals': 0, 'countries': ['CL']},
    '0170': {'name': 'Colombian Peso', 'code': 'COP', 'symbol': '$', 'decimals': 2, 'countries': ['CO']},
    '0604': {'name': 'Peruvian Sol', 'code': 'PEN', 'symbol': 'S/', 'decimals': 2, 'countries': ['PE']},
    '0710': {'name': 'South African Rand', 'code': 'ZAR', 'symbol': 'R', 'decimals': 2, 'countries': ['ZA', 'LS', 'NA', 'SZ']},
    '0818': {'name': 'Egyptian Pound', 'code': 'EGP', 'symbol': '£', 'decimals': 2, 'countries': ['EG']},
    '0504': {'name': 'Moroccan Dirham', 'code': 'MAD', 'symbol': 'DH', 'decimals': 2, 'countries': ['MA', 'EH']},
    '0784': {'name': 'UAE Dirham', 'code': 'AED', 'symbol': 'د.إ', 'decimals': 2, 'countries': ['AE']},
    '0682': {'name': 'Saudi Riyal', 'code': 'SAR', 'symbol': 'ر.س', 'decimals': 2, 'countries': ['SA']},
    '0376': {'name': 'Israeli Shekel', 'code': 'ILS', 'symbol': '₪', 'decimals': 2, 'countries': ['IL', 'PS']},
    '0792': {'name': 'Turkish Lira', 'code': 'TRY', 'symbol': '₺', 'decimals': 2, 'countries': ['TR']},
    '0643': {'name': 'Russian Ruble', 'code': 'RUB', 'symbol': '₽', 'decimals': 2, 'countries': ['RU']},
    '0985': {'name': 'Polish Zloty', 'code': 'PLN', 'symbol': 'zł', 'decimals': 2, 'countries': ['PL']},
    '0203': {'name': 'Czech Koruna', 'code': 'CZK', 'symbol': 'Kč', 'decimals': 2, 'countries': ['CZ']},
    '0348': {'name': 'Hungarian Forint', 'code': 'HUF', 'symbol': 'Ft', 'decimals': 2, 'countries': ['HU']},
    '0946': {'name': 'Romanian Leu', 'code': 'RON', 'symbol': 'lei', 'decimals': 2, 'countries': ['RO']},
    '0208': {'name': 'Danish Krone', 'code': 'DKK', 'symbol': 'kr', 'decimals': 2, 'countries': ['DK', 'FO', 'GL']},
    '0752': {'name': 'Swedish Krona', 'code': 'SEK', 'symbol': 'kr', 'decimals': 2, 'countries': ['SE']},
    '0578': {'name': 'Norwegian Krone', 'code': 'NOK', 'symbol': 'kr', 'decimals': 2, 'countries': ['NO', 'BV', 'SJ']},
}

# Card brand specific country preferences and restrictions
CARD_BRAND_COUNTRY_PATTERNS = {
    'Visa': {
        'strong_countries': ['US', 'CA', 'GB', 'AU', 'NZ', 'SG', 'HK'],
        'restricted_countries': [],
        'regional_preferences': {
            'North America': ['PIN bypass', 'signature'],
            'Europe': ['chip_and_pin', 'contactless'],
            'Asia': ['contactless', 'mobile_payments'],
            'Other': ['signature', 'PIN bypass']
        }
    },
    'Mastercard': {
        'strong_countries': ['US', 'CA', 'GB', 'DE', 'FR', 'NL', 'BE'],
        'restricted_countries': [],
        'regional_preferences': {
            'North America': ['PIN bypass', 'signature'],
            'Europe': ['chip_and_pin', 'contactless'],
            'Asia': ['contactless', 'chip_and_pin'],
            'Other': ['signature', 'PIN bypass']
        }
    },
    'American Express': {
        'strong_countries': ['US', 'CA', 'GB', 'AU', 'JP', 'SG'],
        'restricted_countries': ['CN', 'RU'],
        'regional_preferences': {
            'North America': ['signature', 'PIN bypass'],
            'Europe': ['signature', 'contactless'],
            'Asia': ['signature', 'contactless'],
            'Other': ['signature']
        }
    },
    'Discover': {
        'strong_countries': ['US', 'CA', 'MX'],
        'restricted_countries': [],
        'regional_preferences': {
            'North America': ['PIN bypass', 'signature'],
            'Other': ['signature']
        }
    },
    'JCB': {
        'strong_countries': ['JP', 'KR', 'CN', 'HK', 'SG', 'TH', 'PH'],
        'restricted_countries': [],
        'regional_preferences': {
            'Asia': ['contactless', 'chip_and_pin'],
            'North America': ['signature', 'PIN bypass'],
            'Other': ['signature']
        }
    },
    'UnionPay': {
        'strong_countries': ['CN', 'HK', 'SG', 'TH', 'MY', 'JP'],
        'restricted_countries': ['US'],
        'regional_preferences': {
            'Asia': ['chip_and_pin', 'contactless'],
            'Europe': ['chip_and_pin'],
            'Other': ['chip_and_pin']
        }
    }
}

# Currency-specific transaction patterns and restrictions
CURRENCY_TRANSACTION_PATTERNS = {
    'USD': {
        'common_amounts': [1.00, 5.00, 10.00, 20.00, 50.00, 100.00],
        'max_contactless': 100.00,
        'pin_threshold': 50.00,
        'bypass_preferences': ['signature', 'PIN bypass']
    },
    'EUR': {
        'common_amounts': [1.00, 5.00, 10.00, 20.00, 50.00, 100.00],
        'max_contactless': 50.00,
        'pin_threshold': 25.00,
        'bypass_preferences': ['contactless', 'chip_and_pin']
    },
    'GBP': {
        'common_amounts': [1.00, 5.00, 10.00, 20.00, 50.00, 100.00],
        'max_contactless': 100.00,
        'pin_threshold': 45.00,
        'bypass_preferences': ['contactless', 'signature']
    },
    'JPY': {
        'common_amounts': [100, 500, 1000, 5000, 10000],
        'max_contactless': 10000,
        'pin_threshold': 10000,
        'bypass_preferences': ['contactless', 'signature']
    }
}


class CountryCurrencyLookup:
    """Enhanced country and currency lookup with integration capabilities."""
    
    def __init__(self):
        """Initialize the lookup system."""
        self.country_cache = {}
        self.currency_cache = {}
        
    def get_country_info(self, country_code: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive country information.
        
        Args:
            country_code: ISO country code (hex or numeric)
            
        Returns:
            Dictionary with country information
        """
        try:
            # Normalize country code to hex format
            if country_code.startswith('0x'):
                country_code = country_code[2:]
            elif len(country_code) == 3 and country_code.isdigit():
                country_code = f"{int(country_code):04d}"
            elif len(country_code) < 4:
                country_code = country_code.zfill(4)
            
            # Check cache
            if country_code in self.country_cache:
                return self.country_cache[country_code]
            
            # Lookup country info
            country_info = COUNTRY_CODES.get(country_code)
            if country_info:
                enhanced_info = country_info.copy()
                enhanced_info['country_code'] = country_code
                enhanced_info['is_major_issuer'] = country_code in ['0840', '0124', '0826', '0276', '0250', '0392', '0036']
                enhanced_info['card_adoption_rate'] = self._get_card_adoption_rate(country_info['code'])
                
                # Cache result
                self.country_cache[country_code] = enhanced_info
                return enhanced_info
            
            logger.warning(f"Unknown country code: {country_code}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get country info for {country_code}: {e}")
            return None
    
    def get_currency_info(self, currency_code: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive currency information.
        
        Args:
            currency_code: ISO currency code (hex or numeric)
            
        Returns:
            Dictionary with currency information
        """
        try:
            # Normalize currency code to hex format
            if currency_code.startswith('0x'):
                currency_code = currency_code[2:]
            elif len(currency_code) == 3 and currency_code.isdigit():
                currency_code = f"{int(currency_code):04d}"
            elif len(currency_code) < 4:
                currency_code = currency_code.zfill(4)
            
            # Check cache
            if currency_code in self.currency_cache:
                return self.currency_cache[currency_code]
            
            # Lookup currency info
            currency_info = CURRENCY_CODES.get(currency_code)
            if currency_info:
                enhanced_info = currency_info.copy()
                enhanced_info['currency_code'] = currency_code
                enhanced_info['transaction_patterns'] = CURRENCY_TRANSACTION_PATTERNS.get(
                    currency_info['code'], {}
                )
                enhanced_info['is_major_currency'] = currency_code in ['0840', '0978', '0826', '0392', '0756']
                
                # Cache result
                self.currency_cache[currency_code] = enhanced_info
                return enhanced_info
            
            logger.warning(f"Unknown currency code: {currency_code}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get currency info for {currency_code}: {e}")
            return None
    
    def get_card_brand_country_preferences(self, card_brand: str, country_code: str) -> Dict[str, Any]:
        """
        Get card brand preferences for a specific country.
        
        Args:
            card_brand: Card brand name
            country_code: Country code
            
        Returns:
            Dictionary with preferences and restrictions
        """
        try:
            country_info = self.get_country_info(country_code)
            if not country_info:
                return {}
            
            country_alpha2 = country_info['code']
            region = country_info['region']
            
            brand_patterns = CARD_BRAND_COUNTRY_PATTERNS.get(card_brand, {})
            
            return {
                'is_strong_market': country_alpha2 in brand_patterns.get('strong_countries', []),
                'is_restricted': country_alpha2 in brand_patterns.get('restricted_countries', []),
                'regional_preferences': brand_patterns.get('regional_preferences', {}).get(region, []),
                'market_penetration': self._get_market_penetration(card_brand, country_alpha2),
                'recommended_bypasses': self._get_recommended_bypasses(card_brand, region),
                'risk_level': self._assess_risk_level(card_brand, country_alpha2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get brand country preferences: {e}")
            return {}
    
    def get_currency_transaction_preferences(self, currency_code: str, amount: float = None) -> Dict[str, Any]:
        """
        Get transaction preferences for a specific currency.
        
        Args:
            currency_code: Currency code
            amount: Transaction amount (optional)
            
        Returns:
            Dictionary with transaction preferences
        """
        try:
            currency_info = self.get_currency_info(currency_code)
            if not currency_info:
                return {}
            
            patterns = currency_info.get('transaction_patterns', {})
            preferences = {
                'currency_info': currency_info,
                'supports_contactless': True,
                'supports_chip_and_pin': True,
                'supports_signature': True,
                'preferred_methods': patterns.get('bypass_preferences', ['signature'])
            }
            
            if amount is not None:
                max_contactless = patterns.get('max_contactless', 100.00)
                pin_threshold = patterns.get('pin_threshold', 50.00)
                
                preferences.update({
                    'amount': amount,
                    'requires_pin': amount >= pin_threshold,
                    'allows_contactless': amount <= max_contactless,
                    'recommended_method': self._get_amount_based_method(amount, patterns),
                    'risk_level': self._assess_amount_risk(amount, currency_info['code'])
                })
            
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to get currency transaction preferences: {e}")
            return {}
    
    def analyze_card_geography(self, card_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive geographical analysis of card information.
        
        Args:
            card_info: Card information dictionary
            
        Returns:
            Geographical analysis results
        """
        try:
            issuer_country = card_info.get('issuer_country')
            currency_code = card_info.get('currency_code')
            card_brand = card_info.get('brand', 'Unknown')
            
            analysis = {
                'issuer_analysis': {},
                'currency_analysis': {},
                'compatibility_analysis': {},
                'risk_assessment': {},
                'recommendations': []
            }
            
            # Analyze issuer country
            if issuer_country:
                country_info = self.get_country_info(issuer_country)
                if country_info:
                    analysis['issuer_analysis'] = {
                        'country_info': country_info,
                        'brand_preferences': self.get_card_brand_country_preferences(card_brand, issuer_country),
                        'market_characteristics': self._get_market_characteristics(country_info['code'])
                    }
            
            # Analyze currency
            if currency_code:
                currency_info = self.get_currency_info(currency_code)
                if currency_info:
                    analysis['currency_analysis'] = {
                        'currency_info': currency_info,
                        'transaction_preferences': self.get_currency_transaction_preferences(currency_code)
                    }
            
            # Compatibility analysis
            if issuer_country and currency_code:
                analysis['compatibility_analysis'] = self._analyze_compatibility(
                    issuer_country, currency_code, card_brand
                )
            
            # Risk assessment
            analysis['risk_assessment'] = self._assess_geographical_risk(
                issuer_country, currency_code, card_brand
            )
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_geographical_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze card geography: {e}")
            return {}
    
    def _get_card_adoption_rate(self, country_code: str) -> str:
        """Get card adoption rate for country."""
        high_adoption = ['US', 'CA', 'GB', 'AU', 'SE', 'NO', 'DK', 'NL', 'SG']
        medium_adoption = ['DE', 'FR', 'IT', 'ES', 'JP', 'KR', 'HK']
        
        if country_code in high_adoption:
            return 'high'
        elif country_code in medium_adoption:
            return 'medium'
        else:
            return 'low'
    
    def _get_market_penetration(self, card_brand: str, country_code: str) -> str:
        """Get market penetration for card brand in country."""
        # Simplified penetration analysis
        brand_patterns = CARD_BRAND_COUNTRY_PATTERNS.get(card_brand, {})
        strong_countries = brand_patterns.get('strong_countries', [])
        
        if country_code in strong_countries:
            return 'high'
        elif card_brand in ['Visa', 'Mastercard']:
            return 'medium'
        else:
            return 'low'
    
    def _get_recommended_bypasses(self, card_brand: str, region: str) -> List[str]:
        """Get recommended bypass methods for brand and region."""
        brand_patterns = CARD_BRAND_COUNTRY_PATTERNS.get(card_brand, {})
        return brand_patterns.get('regional_preferences', {}).get(region, ['signature'])
    
    def _assess_risk_level(self, card_brand: str, country_code: str) -> str:
        """Assess risk level for card brand and country combination."""
        brand_patterns = CARD_BRAND_COUNTRY_PATTERNS.get(card_brand, {})
        
        if country_code in brand_patterns.get('restricted_countries', []):
            return 'high'
        elif country_code in brand_patterns.get('strong_countries', []):
            return 'low'
        else:
            return 'medium'
    
    def _get_amount_based_method(self, amount: float, patterns: Dict[str, Any]) -> str:
        """Get recommended method based on transaction amount."""
        max_contactless = patterns.get('max_contactless', 100.00)
        pin_threshold = patterns.get('pin_threshold', 50.00)
        
        if amount <= max_contactless:
            return 'contactless'
        elif amount < pin_threshold:
            return 'signature'
        else:
            return 'chip_and_pin'
    
    def _assess_amount_risk(self, amount: float, currency_code: str) -> str:
        """Assess risk level based on transaction amount."""
        if amount < 10:
            return 'low'
        elif amount < 100:
            return 'medium'
        elif amount < 1000:
            return 'high'
        else:
            return 'very_high'
    
    def _get_market_characteristics(self, country_code: str) -> Dict[str, Any]:
        """Get market characteristics for country."""
        return {
            'regulatory_environment': self._get_regulatory_environment(country_code),
            'fraud_protection_level': self._get_fraud_protection_level(country_code),
            'payment_preferences': self._get_payment_preferences(country_code)
        }
    
    def _get_regulatory_environment(self, country_code: str) -> str:
        """Get regulatory environment assessment."""
        strict_countries = ['US', 'CA', 'GB', 'DE', 'FR', 'AU', 'SG']
        return 'strict' if country_code in strict_countries else 'moderate'
    
    def _get_fraud_protection_level(self, country_code: str) -> str:
        """Get fraud protection level."""
        high_protection = ['US', 'CA', 'GB', 'DE', 'FR', 'AU', 'NL', 'SE']
        return 'high' if country_code in high_protection else 'medium'
    
    def _get_payment_preferences(self, country_code: str) -> List[str]:
        """Get payment method preferences by country."""
        preferences = {
            'US': ['signature', 'contactless', 'chip_and_pin'],
            'CA': ['chip_and_pin', 'contactless', 'signature'],
            'GB': ['contactless', 'chip_and_pin', 'signature'],
            'DE': ['chip_and_pin', 'contactless'],
            'FR': ['chip_and_pin', 'contactless'],
            'JP': ['contactless', 'signature'],
            'SG': ['contactless', 'chip_and_pin']
        }
        return preferences.get(country_code, ['chip_and_pin', 'signature'])
    
    def _analyze_compatibility(self, issuer_country: str, currency_code: str, card_brand: str) -> Dict[str, Any]:
        """Analyze compatibility between issuer country and currency."""
        country_info = self.get_country_info(issuer_country)
        currency_info = self.get_currency_info(currency_code)
        
        if not country_info or not currency_info:
            return {'compatible': False, 'reason': 'Invalid country or currency'}
        
        # Check if currency is used in issuer country
        country_currency = country_info.get('currency')
        transaction_currency = currency_info.get('code')
        
        return {
            'compatible': True,
            'domestic_currency': country_currency == transaction_currency,
            'cross_border': country_currency != transaction_currency,
            'compatibility_score': self._calculate_compatibility_score(country_info, currency_info),
            'potential_issues': self._identify_potential_issues(country_info, currency_info, card_brand)
        }
    
    def _assess_geographical_risk(self, issuer_country: str, currency_code: str, card_brand: str) -> Dict[str, Any]:
        """Assess geographical risk factors."""
        risk_factors = []
        risk_score = 0.0
        
        country_info = self.get_country_info(issuer_country)
        if country_info:
            # Country-based risk factors
            if country_info.get('is_major_issuer'):
                risk_score += 0.1
            else:
                risk_score += 0.3
                risk_factors.append('Non-major issuing country')
        
        # Brand-specific risk
        brand_patterns = CARD_BRAND_COUNTRY_PATTERNS.get(card_brand, {})
        if country_info and country_info['code'] in brand_patterns.get('restricted_countries', []):
            risk_score += 0.5
            risk_factors.append('Restricted country for card brand')
        
        # Determine overall risk level
        if risk_score < 0.3:
            risk_level = 'low'
        elif risk_score < 0.6:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'recommendations': self._get_risk_mitigation_recommendations(risk_level, risk_factors)
        }
    
    def _calculate_compatibility_score(self, country_info: Dict[str, Any], currency_info: Dict[str, Any]) -> float:
        """Calculate compatibility score between country and currency."""
        score = 0.5  # Base score
        
        # Same currency used in country
        if country_info.get('currency') == currency_info.get('code'):
            score += 0.3
        
        # Major currency
        if currency_info.get('is_major_currency'):
            score += 0.1
        
        # Major issuing country
        if country_info.get('is_major_issuer'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _identify_potential_issues(self, country_info: Dict[str, Any], currency_info: Dict[str, Any], card_brand: str) -> List[str]:
        """Identify potential compatibility issues."""
        issues = []
        
        # Cross-border transaction
        if country_info.get('currency') != currency_info.get('code'):
            issues.append('Cross-border transaction - additional verification may be required')
        
        # Restricted combinations
        brand_patterns = CARD_BRAND_COUNTRY_PATTERNS.get(card_brand, {})
        if country_info['code'] in brand_patterns.get('restricted_countries', []):
            issues.append(f'{card_brand} has restrictions in {country_info["name"]}')
        
        return issues
    
    def _generate_geographical_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on geographical analysis."""
        recommendations = []
        
        # Country-based recommendations
        issuer_analysis = analysis.get('issuer_analysis', {})
        if issuer_analysis:
            brand_prefs = issuer_analysis.get('brand_preferences', {})
            if brand_prefs.get('regional_preferences'):
                recommendations.append(f"Use regional preferences: {', '.join(brand_prefs['regional_preferences'])}")
        
        # Currency-based recommendations
        currency_analysis = analysis.get('currency_analysis', {})
        if currency_analysis:
            tx_prefs = currency_analysis.get('transaction_preferences', {})
            if tx_prefs.get('preferred_methods'):
                recommendations.append(f"Preferred methods: {', '.join(tx_prefs['preferred_methods'])}")
        
        # Risk-based recommendations
        risk_assessment = analysis.get('risk_assessment', {})
        if risk_assessment.get('risk_level') == 'high':
            recommendations.append("Use enhanced verification due to high risk profile")
        
        return recommendations
    
    def _get_risk_mitigation_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Get risk mitigation recommendations."""
        if risk_level == 'low':
            return ["Standard processing recommended"]
        elif risk_level == 'medium':
            return ["Consider additional verification", "Monitor transaction patterns"]
        else:
            return [
                "Enhanced verification strongly recommended",
                "Consider manual review",
                "Implement additional fraud checks"
            ]


# Global instance for easy access
country_currency_lookup = CountryCurrencyLookup()


def get_country_info(country_code: str) -> Optional[Dict[str, Any]]:
    """Global function to get country information."""
    return country_currency_lookup.get_country_info(country_code)


def get_currency_info(currency_code: str) -> Optional[Dict[str, Any]]:
    """Global function to get currency information."""
    return country_currency_lookup.get_currency_info(currency_code)


def analyze_card_geography(card_info: Dict[str, Any]) -> Dict[str, Any]:
    """Global function to analyze card geography."""
    return country_currency_lookup.analyze_card_geography(card_info)
