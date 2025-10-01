"""
Payment approval database for tracking successful transactions and card recognition.
"""
import sqlite3
import json
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import sys
import os

# Add parent directories to path for imports
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir.parent
root_dir = src_dir.parent
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(root_dir))

# Create a simple logger class that always works
class Logger:
    def __init__(self, name):
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

logger = Logger("PaymentDatabase")


class PaymentDatabase:
    """Database for storing and retrieving approved payment transactions."""
    
    def __init__(self, db_path: str = "database/payments.db"):
        """
        Initialize the payment database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approved_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_hash TEXT NOT NULL,
                    card_brand TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    terminal_type TEXT NOT NULL,
                    bypass_method TEXT NOT NULL,
                    success_count INTEGER DEFAULT 1,
                    failure_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 1.0,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tlv_modifications TEXT,
                    transaction_amount REAL,
                    currency_code TEXT,
                    merchant_data TEXT,
                    notes TEXT,
                    UNIQUE(card_hash, terminal_type, bypass_method)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transaction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_hash TEXT NOT NULL,
                    transaction_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    card_brand TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    terminal_type TEXT NOT NULL,
                    bypass_method TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    amount REAL,
                    currency_code TEXT,
                    response_code TEXT,
                    error_message TEXT,
                    tlv_data TEXT,
                    processing_time_ms INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS card_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_hash TEXT UNIQUE NOT NULL,
                    card_brand TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    issuer_country TEXT,
                    bin_range TEXT,
                    preferred_bypass TEXT,
                    risk_level TEXT DEFAULT 'medium',
                    total_transactions INTEGER DEFAULT 0,
                    successful_transactions INTEGER DEFAULT 0,
                    average_amount REAL DEFAULT 0.0,
                    last_bypass_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    profile_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_card_hash ON approved_payments(card_hash);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transaction_timestamp ON transaction_history(timestamp);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_card_profiles_hash ON card_profiles(card_hash);
            """)
            
            conn.commit()
    
    def _hash_card_data(self, card_data: Dict[str, Any]) -> str:
        """
        Create a secure hash of card data for identification.
        
        Args:
            card_data: Dictionary containing card information
            
        Returns:
            SHA-256 hash of card data
        """
        # Extract key identifying fields
        key_data = {
            'pan': card_data.get('pan', ''),
            'expiry': card_data.get('expiry_date', ''),
            'aid': card_data.get('application_id', ''),
            'brand': card_data.get('brand', ''),
            'type': card_data.get('type', '')
        }
        
        # Create deterministic hash
        data_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def add_approved_payment(self, card_data: Dict[str, Any], terminal_type: str, 
                           bypass_method: str, tlv_modifications: List[Dict[str, Any]] = None,
                           amount: Optional[float] = None, currency_code: Optional[str] = None,
                           merchant_data: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """
        Add a successful payment to the approved database.
        
        Args:
            card_data: Card information dictionary
            terminal_type: Type of terminal (POS/ATM)
            bypass_method: Bypass method used
            tlv_modifications: TLV modifications applied
            amount: Transaction amount
            currency_code: Currency code
            merchant_data: Merchant information
            notes: Additional notes
            
        Returns:
            True if added successfully
        """
        try:
            card_hash = self._hash_card_data(card_data)
            
            with sqlite3.connect(self.db_path) as conn:
                # Check if entry exists
                existing = conn.execute("""
                    SELECT id, success_count, failure_count FROM approved_payments 
                    WHERE card_hash = ? AND terminal_type = ? AND bypass_method = ?
                """, (card_hash, terminal_type, bypass_method)).fetchone()
                
                if existing:
                    # Update existing entry
                    new_success_count = existing[1] + 1
                    new_success_rate = new_success_count / (new_success_count + existing[2])
                    
                    conn.execute("""
                        UPDATE approved_payments 
                        SET success_count = ?, success_rate = ?, last_seen = CURRENT_TIMESTAMP,
                            transaction_amount = COALESCE(?, transaction_amount),
                            currency_code = COALESCE(?, currency_code),
                            merchant_data = COALESCE(?, merchant_data),
                            notes = COALESCE(?, notes)
                        WHERE id = ?
                    """, (new_success_count, new_success_rate, amount, currency_code, 
                         merchant_data, notes, existing[0]))
                else:
                    # Insert new entry
                    tlv_json = json.dumps(tlv_modifications) if tlv_modifications else None
                    
                    conn.execute("""
                        INSERT INTO approved_payments 
                        (card_hash, card_brand, card_type, terminal_type, bypass_method,
                         tlv_modifications, transaction_amount, currency_code, merchant_data, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (card_hash, card_data.get('brand', ''), card_data.get('type', ''),
                         terminal_type, bypass_method, tlv_json, amount, currency_code,
                         merchant_data, notes))
                
                # Update card profile
                self._update_card_profile(conn, card_hash, card_data, bypass_method, True)
                
                conn.commit()
                logger.info(f"Added approved payment for {card_data.get('brand', 'Unknown')} card")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add approved payment: {e}")
            return False
    
    def record_transaction(self, card_data: Dict[str, Any], transaction_id: str,
                          terminal_type: str, bypass_method: str, success: bool,
                          amount: Optional[float] = None, currency_code: Optional[str] = None,
                          response_code: Optional[str] = None, error_message: Optional[str] = None,
                          tlv_data: Optional[List[Dict[str, Any]]] = None,
                          processing_time_ms: Optional[int] = None) -> bool:
        """
        Record a transaction attempt in the history.
        
        Args:
            card_data: Card information
            transaction_id: Unique transaction identifier
            terminal_type: Terminal type
            bypass_method: Bypass method used
            success: Whether transaction succeeded
            amount: Transaction amount
            currency_code: Currency code
            response_code: Response code from terminal
            error_message: Error message if failed
            tlv_data: TLV data from transaction
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            True if recorded successfully
        """
        try:
            card_hash = self._hash_card_data(card_data)
            tlv_json = json.dumps(tlv_data) if tlv_data else None
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO transaction_history
                    (card_hash, transaction_id, card_brand, card_type, terminal_type,
                     bypass_method, success, amount, currency_code, response_code,
                     error_message, tlv_data, processing_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (card_hash, transaction_id, card_data.get('brand', ''),
                     card_data.get('type', ''), terminal_type, bypass_method, success,
                     amount, currency_code, response_code, error_message, tlv_json,
                     processing_time_ms))
                
                # Update card profile
                self._update_card_profile(conn, card_hash, card_data, bypass_method, success)
                
                # Update approved payments if failure
                if not success:
                    self._record_failure(conn, card_hash, terminal_type, bypass_method)
                
                conn.commit()
                logger.debug(f"Recorded transaction: {transaction_id} - {'SUCCESS' if success else 'FAILURE'}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to record transaction: {e}")
            return False
    
    def _update_card_profile(self, conn: sqlite3.Connection, card_hash: str,
                           card_data: Dict[str, Any], bypass_method: str, success: bool):
        """Update card profile with transaction data."""
        # Get existing profile
        profile = conn.execute("""
            SELECT total_transactions, successful_transactions, preferred_bypass, average_amount
            FROM card_profiles WHERE card_hash = ?
        """, (card_hash,)).fetchone()
        
        if profile:
            # Update existing profile
            new_total = profile[0] + 1
            new_successful = profile[1] + (1 if success else 0)
            success_rate = new_successful / new_total if new_total > 0 else 0
            
            # Update preferred bypass if this one has better success rate
            current_preferred = profile[2]
            if success_rate > 0.8 and (not current_preferred or success):
                new_preferred = bypass_method
            else:
                new_preferred = current_preferred
            
            conn.execute("""
                UPDATE card_profiles 
                SET total_transactions = ?, successful_transactions = ?, 
                    preferred_bypass = ?, last_bypass_update = CURRENT_TIMESTAMP
                WHERE card_hash = ?
            """, (new_total, new_successful, new_preferred, card_hash))
        else:
            # Create new profile with enhanced geographical data
            profile_data = {
                'pan_prefix': card_data.get('pan', '')[:6] if card_data.get('pan') else '',
                'issuer_country': card_data.get('issuer_country', ''),
                'currency_code': card_data.get('currency_code', ''),
                'application_label': card_data.get('application_label', ''),
                'bin_analysis': card_data.get('bin_analysis', {}),
                'international_capability': card_data.get('international_card', True),
                'domestic_usage': card_data.get('domestic_card', False)
            }
            
            # Enhanced geographical analysis
            try:
                from ..database.country_currency_lookup import analyze_card_geography
                geo_analysis = analyze_card_geography(card_data)
                profile_data['geographical_analysis'] = geo_analysis
                
                # Extract risk level from geographical analysis
                risk_assessment = geo_analysis.get('risk_assessment', {})
                risk_level = risk_assessment.get('risk_level', 'medium')
            except ImportError:
                risk_level = 'medium'
            
            conn.execute("""
                INSERT INTO card_profiles
                (card_hash, card_brand, card_type, issuer_country, bin_range,
                 preferred_bypass, risk_level, total_transactions, successful_transactions, profile_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (card_hash, card_data.get('brand', ''), card_data.get('type', ''),
                 card_data.get('issuer_country', ''), card_data.get('pan', '')[:6],
                 bypass_method if success else None, risk_level, 1, 1 if success else 0,
                 json.dumps(profile_data)))
    
    def _record_failure(self, conn: sqlite3.Connection, card_hash: str,
                       terminal_type: str, bypass_method: str):
        """Record a failure for existing approved payment."""
        conn.execute("""
            UPDATE approved_payments 
            SET failure_count = failure_count + 1,
                success_rate = CAST(success_count AS REAL) / (success_count + failure_count + 1),
                last_seen = CURRENT_TIMESTAMP
            WHERE card_hash = ? AND terminal_type = ? AND bypass_method = ?
        """, (card_hash, terminal_type, bypass_method))
    
    def get_approved_bypass(self, card_data: Dict[str, Any], terminal_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the best approved bypass method for a card.
        
        Args:
            card_data: Card information
            terminal_type: Terminal type
            
        Returns:
            Dictionary with bypass information or None
        """
        try:
            card_hash = self._hash_card_data(card_data)
            
            with sqlite3.connect(self.db_path) as conn:
                # Get the best bypass method for this card and terminal
                result = conn.execute("""
                    SELECT bypass_method, success_rate, success_count, failure_count,
                           tlv_modifications, last_seen, notes
                    FROM approved_payments 
                    WHERE card_hash = ? AND terminal_type = ?
                    ORDER BY success_rate DESC, success_count DESC
                    LIMIT 1
                """, (card_hash, terminal_type)).fetchone()
                
                if result:
                    tlv_mods = json.loads(result[4]) if result[4] else []
                    
                    return {
                        'bypass_method': result[0],
                        'success_rate': result[1],
                        'success_count': result[2],
                        'failure_count': result[3],
                        'tlv_modifications': tlv_mods,
                        'last_seen': result[5],
                        'notes': result[6],
                        'confidence': 'high' if result[1] > 0.8 else 'medium' if result[1] > 0.6 else 'low'
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get approved bypass: {e}")
            return None
    
    def get_card_history(self, card_data: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get transaction history for a card.
        
        Args:
            card_data: Card information
            limit: Maximum number of records to return
            
        Returns:
            List of transaction records
        """
        try:
            card_hash = self._hash_card_data(card_data)
            
            with sqlite3.connect(self.db_path) as conn:
                results = conn.execute("""
                    SELECT transaction_id, timestamp, terminal_type, bypass_method,
                           success, amount, currency_code, response_code, error_message,
                           processing_time_ms
                    FROM transaction_history 
                    WHERE card_hash = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (card_hash, limit)).fetchall()
                
                history = []
                for row in results:
                    history.append({
                        'transaction_id': row[0],
                        'timestamp': row[1],
                        'terminal_type': row[2],
                        'bypass_method': row[3],
                        'success': bool(row[4]),
                        'amount': row[5],
                        'currency_code': row[6],
                        'response_code': row[7],
                        'error_message': row[8],
                        'processing_time_ms': row[9]
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get card history: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total approved payments
                total_approved = conn.execute("SELECT COUNT(*) FROM approved_payments").fetchone()[0]
                
                # Total transactions
                total_transactions = conn.execute("SELECT COUNT(*) FROM transaction_history").fetchone()[0]
                
                # Success rate
                successful = conn.execute("SELECT COUNT(*) FROM transaction_history WHERE success = 1").fetchone()[0]
                success_rate = successful / total_transactions if total_transactions > 0 else 0
                
                # Card brands breakdown
                brand_stats = conn.execute("""
                    SELECT card_brand, COUNT(*) 
                    FROM approved_payments 
                    GROUP BY card_brand
                """).fetchall()
                
                # Top bypass methods
                bypass_stats = conn.execute("""
                    SELECT bypass_method, COUNT(*), AVG(success_rate)
                    FROM approved_payments 
                    GROUP BY bypass_method
                    ORDER BY COUNT(*) DESC
                """).fetchall()
                
                return {
                    'total_approved_payments': total_approved,
                    'total_transactions': total_transactions,
                    'overall_success_rate': success_rate,
                    'card_brands': dict(brand_stats),
                    'bypass_methods': [
                        {
                            'method': row[0],
                            'count': row[1],
                            'avg_success_rate': row[2]
                        } for row in bypass_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def cleanup_old_records(self, days: int = 90):
        """
        Clean up old transaction records.
        
        Args:
            days: Number of days to keep records
        """
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                deleted = conn.execute("""
                    DELETE FROM transaction_history 
                    WHERE timestamp < ?
                """, (cutoff_date,)).rowcount
                
                conn.commit()
                logger.info(f"Cleaned up {deleted} old transaction records")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
    
    def export_data(self, output_file: str):
        """
        Export database data to JSON file.
        
        Args:
            output_file: Path to output file
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Export all tables
                data = {
                    'approved_payments': [],
                    'transaction_history': [],
                    'card_profiles': [],
                    'exported_at': datetime.datetime.now().isoformat()
                }
                
                # Get approved payments
                for row in conn.execute("SELECT * FROM approved_payments"):
                    data['approved_payments'].append(dict(zip([col[0] for col in conn.description], row)))
                
                # Get transaction history (last 1000 records)
                for row in conn.execute("SELECT * FROM transaction_history ORDER BY timestamp DESC LIMIT 1000"):
                    data['transaction_history'].append(dict(zip([col[0] for col in conn.description], row)))
                
                # Get card profiles
                for row in conn.execute("SELECT * FROM card_profiles"):
                    data['card_profiles'].append(dict(zip([col[0] for col in conn.description], row)))
                
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                
                logger.info(f"Exported database to {output_file}")
                
        except Exception as e:
            logger.error(f"Failed to export data: {e}")


def main():
    """Main function for testing and demonstrating payment database functionality."""
    print("🏦 Payment Database System - Test Suite")
    print("=" * 50)
    
    # Initialize database
    db = PaymentDatabase()
    
    # Test database operations
    print("📊 Database Statistics:")
    stats = db.get_statistics()
    if stats:
        print(f"  Total Approved Payments: {stats.get('total_approved_payments', 0)}")
        print(f"  Total Transactions: {stats.get('total_transactions', 0)}")
        print(f"  Success Rate: {stats.get('overall_success_rate', 0):.1f}%")
        
        if stats.get('card_brands'):
            print("  Card Brands:")
            for brand, count in stats['card_brands'].items():
                print(f"    {brand}: {count}")
    else:
        print("  No data available - database is empty")
    
    # Test adding sample data
    print("\n🧪 Adding sample test data...")
    
    # Sample approved payment
    sample_card_data = {
        'uid': '04112233445566',
        'card_type': 'Visa',
        'pan': '4111111111111111',
        'expiry_date': '12/26'
    }
    
    try:
        db.add_approved_payment(
            card_data=sample_card_data,
            terminal_type='POS',
            bypass_method='emv_replay',
            amount=25.00,
            currency_code='USD',
            notes='Sample test payment'
        )
        print("  ✅ Sample payment added successfully")
    except Exception as e:
        print(f"  ❌ Failed to add sample payment: {e}")
    
    # Sample transaction
    sample_transaction_data = {
        'uid': '04112233445566',
        'card_type': 'Visa',
        'pan': '4111111111111111'
    }
    
    try:
        db.record_transaction(
            card_data=sample_transaction_data,
            transaction_id='TXN_TEST_001',
            terminal_type='POS',
            bypass_method='emv_replay',
            success=True,
            amount=25.00,
            currency_code='USD',
            response_code='00',
            processing_time_ms=250
        )
        print("  ✅ Sample transaction recorded successfully")
    except Exception as e:
        print(f"  ❌ Failed to record sample transaction: {e}")
    
    # Show updated statistics
    print("\n📊 Updated Statistics:")
    stats = db.get_statistics()
    if stats:
        print(f"  Total Approved Payments: {stats.get('total_approved_payments', 0)}")
        print(f"  Total Transactions: {stats.get('total_transactions', 0)}")
        print(f"  Success Rate: {stats.get('overall_success_rate', 0):.1f}%")
    
    # Test export functionality
    print("\n📤 Testing export functionality...")
    try:
        export_file = "database/payment_export_test.json"
        db.export_data(export_file)
        print(f"  ✅ Data exported to {export_file}")
    except Exception as e:
        print(f"  ❌ Export failed: {e}")
    
    print("\n✅ Payment database test completed!")
    print("💡 The database is ready for use with your credit card testing system.")


if __name__ == "__main__":
    main()
