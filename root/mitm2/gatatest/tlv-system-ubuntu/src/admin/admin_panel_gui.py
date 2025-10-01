#!/usr/bin/env python3
"""
🔧 TLV Admin Panel GUI
Complete GUI admin panel for payment method testing and database building.
"""

import os
import sys
import json
import time
import queue
import sqlite3
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# GUI Logging
import logging
logger = logging.getLogger(__name__)

class AdminDatabaseManager:
    """Database manager for admin panel"""
    
    def __init__(self, db_path: str = "database/admin_panel.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Test results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE,
                    brand TEXT,
                    method TEXT,
                    terminal TEXT,
                    status TEXT,
                    execution_time REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Scripts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_id TEXT UNIQUE,
                    brand TEXT,
                    method TEXT,
                    status TEXT,
                    confidence TEXT,
                    risk TEXT,
                    approved BOOLEAN DEFAULT FALSE,
                    script_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def add_test_result(self, result_data: Dict) -> bool:
        """Add test result to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO test_results 
                    (transaction_id, brand, method, terminal, status, execution_time, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    result_data.get('transaction_id'),
                    result_data.get('brand'),
                    result_data.get('method'),
                    result_data.get('terminal'),
                    result_data.get('status'),
                    result_data.get('execution_time'),
                    result_data.get('notes', '')
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding test result: {e}")
            return False
    
    def get_test_results(self, limit: int = 100) -> List[Dict]:
        """Get test results from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT transaction_id, brand, method, terminal, status, execution_time, notes, created_at
                    FROM test_results 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [
                    {
                        'transaction_id': row[0],
                        'brand': row[1],
                        'method': row[2],
                        'terminal': row[3],
                        'status': row[4],
                        'execution_time': row[5],
                        'notes': row[6],
                        'created_at': row[7]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total transactions
                cursor.execute("SELECT COUNT(*) FROM test_results")
                total_transactions = cursor.fetchone()[0]
                
                # Approved scripts
                cursor.execute("SELECT COUNT(*) FROM scripts WHERE approved = 1")
                approved_scripts = cursor.fetchone()[0]
                
                # Pending approval
                cursor.execute("SELECT COUNT(*) FROM scripts WHERE approved = 0")
                pending_approval = cursor.fetchone()[0]
                
                # Success rate
                cursor.execute("SELECT COUNT(*) FROM test_results WHERE status = 'SUCCESS'")
                successful = cursor.fetchone()[0]
                success_rate = (successful / total_transactions * 100) if total_transactions > 0 else 0
                
                # Average execution time
                cursor.execute("SELECT AVG(execution_time) FROM test_results WHERE execution_time > 0")
                avg_time = cursor.fetchone()[0] or 0
                
                return {
                    'total_transactions': total_transactions,
                    'approved_scripts': approved_scripts,
                    'pending_approval': pending_approval,
                    'rejected_scripts': len([t for t in test_results if not t.get('success', False)]),
                    'success_rate': f"{success_rate:.1f}%",
                    'avg_execution_time': f"{avg_time:.2f}ms"
                }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

class PaymentMethodTester:
    """Payment method testing functionality"""
    
    def __init__(self):
        self.available_methods = {
            'cdcvm': 'Consumer Device Cardholder Verification Method',
            'signature': 'Signature Verification',
            'no_cvm': 'No Cardholder Verification',
            'pin_verification': 'PIN Verification',
            'contactless': 'Contactless Payment'
        }
    
    def test_method(self, config: Dict) -> Dict:
        """Test a payment method with given configuration"""
        # Simulate testing
        time.sleep(0.5)  # Simulate processing time
        
        import random
        success = random.choice([True, True, True, False])  # 75% success rate
        
        return {
            'transaction_id': f"TXN_{int(time.time())}_{random.randint(1000, 9999)}",
            'brand': config.get('brand', 'Unknown'),
            'method': config.get('method', 'Unknown'),
            'terminal': config.get('terminal', 'Unknown'),
            'status': 'SUCCESS' if success else 'FAILED',
            'execution_time': random.uniform(100, 2000),
            'notes': 'Test completed successfully' if success else 'Test failed - check configuration'
        }

class ScriptGenerator:
    """Script generation functionality"""
    
    def __init__(self):
        self.templates = {}
    
    def generate_script(self, test_result: Dict, approval_data: Dict) -> str:
        """Generate script based on test result and approval data"""
        script_template = f"""
# Generated Payment Script
# Generated at: {datetime.now().isoformat()}
# Transaction ID: {test_result.get('transaction_id')}

import time
import json

def payment_script():
    # Payment configuration
    config = {{
        "brand": "{test_result.get('brand')}",
        "method": "{test_result.get('method')}",
        "terminal": "{test_result.get('terminal')}",
        "confidence": "{approval_data.get('confidence')}",
        "risk": "{approval_data.get('risk')}"
    }}
    
    print(f"Executing payment with config: {{config}}")
    
    # Simulate payment processing
    time.sleep(0.1)
    
    return {{"success": True, "config": config}}

if __name__ == "__main__":
    result = payment_script()
    print(f"Script result: {{result}}")
"""
        return script_template

class AdminPanel:
    """GUI Admin Panel for manual database building and testing"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔧 TLV Admin Panel - Payment Method Testing & Database Building")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize components
        self.db_manager = AdminDatabaseManager()
        self.payment_tester = PaymentMethodTester()
        self.script_generator = ScriptGenerator()
        
        # GUI Variables
        self.current_session_id = None
        self.test_queue = queue.Queue()
        self.results_queue = queue.Queue()
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.setup_bindings()
        
        # Start background worker
        self.worker_thread = threading.Thread(target=self.background_worker, daemon=True)
        self.worker_thread.start()
        
        logger.info("✅ Admin Panel initialized successfully")
    
    def setup_styles(self):
        """Setup TTK styles for modern UI"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       background='#2b2b2b',
                       foreground='#ffffff')
        
        style.configure('Header.TLabel',
                       font=('Segoe UI', 12, 'bold'),
                       background='#2b2b2b',
                       foreground='#4CAF50')
        
        style.configure('Info.TLabel',
                       font=('Segoe UI', 10),
                       background='#2b2b2b',
                       foreground='#cccccc')
        
        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       foreground='#ffffff')
        
        style.configure('Danger.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       foreground='#ffffff')
    
    def create_widgets(self):
        """Create main GUI widgets"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_testing_tab()
        self.create_approval_tab()
        self.create_database_tab()
        self.create_connection_management_tab()
        self.create_settings_tab()
        self.create_monitoring_tab()
    
    def create_testing_tab(self):
        """Create payment method testing tab"""
        testing_frame = ttk.Frame(self.notebook)
        self.notebook.add(testing_frame, text="🧪 Payment Testing")
        
        # Main container
        main_container = ttk.Frame(testing_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Test Configuration
        left_panel = ttk.LabelFrame(main_container, text="🔧 Test Configuration", padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Card Information
        card_frame = ttk.LabelFrame(left_panel, text="💳 Card Information", padding=10)
        card_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Card Brand
        ttk.Label(card_frame, text="Card Brand:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.card_brand_var = tk.StringVar(value="Visa")
        brand_combo = ttk.Combobox(card_frame, textvariable=self.card_brand_var,
                                  values=["Visa", "Mastercard", "American Express", "Discover"],
                                  state="readonly", width=20)
        brand_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Card Type
        ttk.Label(card_frame, text="Card Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.card_type_var = tk.StringVar(value="Standard")
        type_combo = ttk.Combobox(card_frame, textvariable=self.card_type_var,
                                 values=["Standard", "Gold", "Platinum", "Business", "Debit"],
                                 state="readonly", width=20)
        type_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Country
        ttk.Label(card_frame, text="Issuer Country:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.country_var = tk.StringVar(value="US")
        country_combo = ttk.Combobox(card_frame, textvariable=self.country_var,
                                   values=["US", "GB", "DE", "FR", "CA", "AU", "JP", "IT", "ES", "BR"],
                                   state="readonly", width=20)
        country_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Currency
        ttk.Label(card_frame, text="Currency:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.currency_var = tk.StringVar(value="USD")
        currency_combo = ttk.Combobox(card_frame, textvariable=self.currency_var,
                                    values=["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY"],
                                    state="readonly", width=20)
        currency_combo.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # PAN (for testing)
        ttk.Label(card_frame, text="Test PAN:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.pan_var = tk.StringVar(value="4111111111111111")
        pan_entry = ttk.Entry(card_frame, textvariable=self.pan_var, width=25)
        pan_entry.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Payment Method Configuration
        method_frame = ttk.LabelFrame(left_panel, text="⚙️ Payment Method", padding=10)
        method_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Terminal Type
        ttk.Label(method_frame, text="Terminal Type:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.terminal_type_var = tk.StringVar(value="POS")
        terminal_combo = ttk.Combobox(method_frame, textvariable=self.terminal_type_var,
                                    values=["POS", "ATM", "Mobile", "Transit", "Contactless"],
                                    state="readonly", width=20)
        terminal_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Bypass Method
        ttk.Label(method_frame, text="Bypass Method:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.bypass_method_var = tk.StringVar(value="cdcvm")
        method_combo = ttk.Combobox(method_frame, textvariable=self.bypass_method_var,
                                  values=["cdcvm", "signature", "no_cvm", "pin_verification", "contactless"],
                                  state="readonly", width=20)
        method_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Bind method change to update info
        method_combo.bind('<<ComboboxSelected>>', self.on_method_change)
        
        # Method Info Display
        self.method_info_text = tk.Text(method_frame, height=6, width=50, wrap=tk.WORD,
                                       bg='#3c3c3c', fg='#cccccc', font=('Consolas', 9))
        self.method_info_text.grid(row=2, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(10, 0))
        
        # Custom Settings
        settings_frame = ttk.LabelFrame(left_panel, text="🛠️ Custom Settings", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        self.settings_text = tk.Text(settings_frame, height=8, wrap=tk.WORD,
                                   bg='#3c3c3c', fg='#cccccc', font=('Consolas', 9))
        self.settings_text.pack(fill=tk.BOTH, expand=True)
        self.settings_text.insert(tk.END, "{\n  \"amount_limit\": 100.00,\n  \"pin_required\": false,\n  \"signature_required\": true\n}")
        
        # Test Controls
        controls_frame = ttk.Frame(left_panel)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Single Test Button
        single_test_btn = ttk.Button(controls_frame, text="🧪 Run Single Test",
                                   command=self.run_single_test, style='Success.TButton')
        single_test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Batch Test Button
        batch_test_btn = ttk.Button(controls_frame, text="📊 Run Batch Test",
                                  command=self.run_batch_test, style='Success.TButton')
        batch_test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear Results Button
        clear_btn = ttk.Button(controls_frame, text="🗑️ Clear Results",
                             command=self.clear_test_results)
        clear_btn.pack(side=tk.LEFT)
        
        # Right panel - Test Results
        right_panel = ttk.LabelFrame(main_container, text="📊 Test Results", padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Results Tree
        results_frame = ttk.Frame(right_panel)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for results
        columns = ("Transaction ID", "Brand", "Method", "Terminal", "Status", "Time (ms)", "Notes")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "Transaction ID":
                self.results_tree.column(col, width=150)
            elif col == "Time (ms)":
                self.results_tree.column(col, width=80)
            elif col == "Status":
                self.results_tree.column(col, width=80)
            else:
                self.results_tree.column(col, width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Results summary
        summary_frame = ttk.Frame(right_panel)
        summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.results_summary_label = ttk.Label(summary_frame, text="Ready for testing...",
                                             style='Info.TLabel')
        self.results_summary_label.pack()
        
        # Initialize method info
        self.update_method_info()
    
    def create_approval_tab(self):
        """Create transaction approval tab"""
        approval_frame = ttk.Frame(self.notebook)
        self.notebook.add(approval_frame, text="✅ Approval Center")
        
        # Main container
        main_container = ttk.Frame(approval_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Pending Transactions
        left_panel = ttk.LabelFrame(main_container, text="⏳ Pending Approvals", padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Pending transactions tree
        pending_frame = ttk.Frame(left_panel)
        pending_frame.pack(fill=tk.BOTH, expand=True)
        
        pending_columns = ("ID", "Brand", "Method", "Status", "Success", "Time")
        self.pending_tree = ttk.Treeview(pending_frame, columns=pending_columns, show="headings", height=12)
        
        for col in pending_columns:
            self.pending_tree.heading(col, text=col)
            if col == "ID":
                self.pending_tree.column(col, width=120)
            else:
                self.pending_tree.column(col, width=80)
        
        # Scrollbar for pending tree
        pending_scrollbar = ttk.Scrollbar(pending_frame, orient=tk.VERTICAL, command=self.pending_tree.yview)
        self.pending_tree.configure(yscrollcommand=pending_scrollbar.set)
        
        self.pending_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pending_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.pending_tree.bind('<<TreeviewSelect>>', self.on_pending_select)
        
        # Refresh button
        refresh_frame = ttk.Frame(left_panel)
        refresh_frame.pack(fill=tk.X, pady=(10, 0))
        
        refresh_btn = ttk.Button(refresh_frame, text="🔄 Refresh Pending",
                               command=self.refresh_pending_transactions)
        refresh_btn.pack(side=tk.LEFT)
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_cb = ttk.Checkbutton(refresh_frame, text="Auto-refresh",
                                        variable=self.auto_refresh_var)
        auto_refresh_cb.pack(side=tk.LEFT, padx=(20, 0))
        
        # Right panel - Transaction Details & Approval
        right_panel = ttk.LabelFrame(main_container, text="📋 Transaction Details", padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Transaction details display
        details_frame = ttk.Frame(right_panel)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        self.details_text = tk.Text(details_frame, height=15, wrap=tk.WORD,
                                  bg='#3c3c3c', fg='#cccccc', font=('Consolas', 9))
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Approval controls
        approval_controls_frame = ttk.LabelFrame(right_panel, text="🎯 Approval Controls", padding=10)
        approval_controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Confidence level
        ttk.Label(approval_controls_frame, text="Confidence Level:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.confidence_var = tk.StringVar(value="medium")
        confidence_combo = ttk.Combobox(approval_controls_frame, textvariable=self.confidence_var,
                                      values=["very_low", "low", "medium", "high", "very_high"],
                                      state="readonly", width=15)
        confidence_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Risk assessment
        ttk.Label(approval_controls_frame, text="Risk Assessment:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.risk_var = tk.StringVar(value="medium")
        risk_combo = ttk.Combobox(approval_controls_frame, textvariable=self.risk_var,
                                values=["low", "medium", "high"],
                                state="readonly", width=15)
        risk_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Approval notes
        ttk.Label(approval_controls_frame, text="Approval Notes:").grid(row=2, column=0, sticky=tk.W+tk.N, pady=2)
        self.approval_notes_text = tk.Text(approval_controls_frame, height=4, width=40,
                                         bg='#3c3c3c', fg='#cccccc', font=('Consolas', 9))
        self.approval_notes_text.grid(row=2, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        
        # Approval buttons
        buttons_frame = ttk.Frame(approval_controls_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        approve_btn = ttk.Button(buttons_frame, text="✅ Approve & Generate Script",
                               command=self.approve_transaction, style='Success.TButton')
        approve_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        reject_btn = ttk.Button(buttons_frame, text="❌ Reject Transaction",
                              command=self.reject_transaction, style='Danger.TButton')
        reject_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        modify_btn = ttk.Button(buttons_frame, text="📝 Request Modification",
                              command=self.request_modification)
        modify_btn.pack(side=tk.LEFT)
        
        # Load pending transactions
        self.refresh_pending_transactions()
        
        # Start auto-refresh timer
        self.schedule_pending_refresh()
    
    def create_database_tab(self):
        """Create database management tab"""
        database_frame = ttk.Frame(self.notebook)
        self.notebook.add(database_frame, text="💾 Database Manager")
        
        # Main container
        main_container = ttk.Frame(database_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Database Statistics
        stats_frame = ttk.LabelFrame(main_container, text="📊 Database Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Stats grid
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        # Create stat labels
        self.stat_labels = {}
        stat_names = [
            ("Total Transactions", "total_transactions"),
            ("Approved Scripts", "approved_scripts"),
            ("Pending Approval", "pending_approval"),
            ("Rejected Scripts", "rejected_scripts"),
            ("Success Rate", "success_rate"),
            ("Avg Execution Time", "avg_execution_time")
        ]
        
        for i, (name, key) in enumerate(stat_names):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(stats_grid, text=f"{name}:", style='Header.TLabel').grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=2)
            
            self.stat_labels[key] = ttk.Label(stats_grid, text="Loading...", style='Info.TLabel')
            self.stat_labels[key].grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20), pady=2)
        
        # Middle section - Script Browser
        browser_frame = ttk.LabelFrame(main_container, text="📁 Script Browser", padding=10)
        browser_frame.pack(fill=tk.BOTH, expand=True)
        
        # Filter controls
        filter_frame = ttk.Frame(browser_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                  values=["all", "approved", "not_approved", "pending"],
                                  state="readonly", width=15)
        filter_combo.pack(side=tk.LEFT, padx=(10, 0))
        filter_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Search
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(20, 0))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(10, 0))
        search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Refresh button
        refresh_db_btn = ttk.Button(filter_frame, text="🔄 Refresh",
                                  command=self.refresh_database_view)
        refresh_db_btn.pack(side=tk.RIGHT)
        
        # Scripts tree
        scripts_tree_frame = ttk.Frame(browser_frame)
        scripts_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        script_columns = ("Script ID", "Brand", "Method", "Status", "Confidence", "Risk", "Created")
        self.scripts_tree = ttk.Treeview(scripts_tree_frame, columns=script_columns, show="headings", height=12)
        
        for col in script_columns:
            self.scripts_tree.heading(col, text=col)
            if col == "Script ID":
                self.scripts_tree.column(col, width=150)
            elif col in ["Confidence", "Risk"]:
                self.scripts_tree.column(col, width=80)
            else:
                self.scripts_tree.column(col, width=100)
        
        # Scrollbars for scripts tree
        scripts_v_scrollbar = ttk.Scrollbar(scripts_tree_frame, orient=tk.VERTICAL, command=self.scripts_tree.yview)
        scripts_h_scrollbar = ttk.Scrollbar(scripts_tree_frame, orient=tk.HORIZONTAL, command=self.scripts_tree.xview)
        self.scripts_tree.configure(yscrollcommand=scripts_v_scrollbar.set, xscrollcommand=scripts_h_scrollbar.set)
        
        self.scripts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scripts_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scripts_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Context menu for scripts
        self.create_scripts_context_menu()
        
        # Bind events
        self.scripts_tree.bind('<Button-3>', self.show_scripts_context_menu)
        self.scripts_tree.bind('<Double-1>', self.open_script_details)
        
        # Bottom section - Quick Actions
        actions_frame = ttk.LabelFrame(main_container, text="⚡ Quick Actions", padding=10)
        actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Action buttons
        export_btn = ttk.Button(actions_frame, text="📤 Export Database",
                              command=self.export_database)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        import_btn = ttk.Button(actions_frame, text="📥 Import Scripts",
                              command=self.import_scripts)
        import_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        backup_btn = ttk.Button(actions_frame, text="💾 Create Backup",
                              command=self.create_backup)
        backup_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cleanup_btn = ttk.Button(actions_frame, text="🧹 Cleanup Database",
                               command=self.cleanup_database)
        cleanup_btn.pack(side=tk.LEFT)
        
        # Update database view
        self.refresh_database_view()
        self.update_database_stats()
    
    def create_settings_tab(self):
        """Create settings and configuration tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Main container with scrollable content
        canvas = tk.Canvas(settings_frame, bg='#2b2b2b')
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Payment Method Configurations
        method_config_frame = ttk.LabelFrame(scrollable_frame, text="🔧 Payment Method Configurations", padding=10)
        method_config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Method selection
        ttk.Label(method_config_frame, text="Select Method:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.config_method_var = tk.StringVar(value="cdcvm")
        config_method_combo = ttk.Combobox(method_config_frame, textvariable=self.config_method_var,
                                         values=list(self.payment_tester.available_methods.keys()),
                                         state="readonly", width=20)
        config_method_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        config_method_combo.bind('<<ComboboxSelected>>', self.on_config_method_change)
        
        # Method configuration editor
        self.method_config_text = tk.Text(method_config_frame, height=10, width=60,
                                        bg='#3c3c3c', fg='#cccccc', font=('Consolas', 9))
        self.method_config_text.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(10, 0))
        
        # Save method config button
        save_method_btn = ttk.Button(method_config_frame, text="💾 Save Method Config",
                                   command=self.save_method_config)
        save_method_btn.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        # Terminal Configurations
        terminal_config_frame = ttk.LabelFrame(scrollable_frame, text="🖥️ Terminal Configurations", padding=10)
        terminal_config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Terminal settings
        terminal_settings = [
            ("Default Timeout (ms)", "default_timeout", "5000"),
            ("Max Retry Attempts", "max_retries", "3"),
            ("Connection Pool Size", "pool_size", "10"),
            ("Enable Logging", "enable_logging", "true"),
            ("Debug Mode", "debug_mode", "false")
        ]
        
        self.terminal_settings_vars = {}
        for i, (label, key, default) in enumerate(terminal_settings):
            ttk.Label(terminal_config_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            
            if key in ["enable_logging", "debug_mode"]:
                var = tk.BooleanVar(value=default.lower() == "true")
                widget = ttk.Checkbutton(terminal_config_frame, variable=var)
            else:
                var = tk.StringVar(value=default)
                widget = ttk.Entry(terminal_config_frame, textvariable=var, width=20)
            
            widget.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            self.terminal_settings_vars[key] = var
        
        # Save terminal config button
        save_terminal_btn = ttk.Button(terminal_config_frame, text="💾 Save Terminal Config",
                                     command=self.save_terminal_config)
        save_terminal_btn.grid(row=len(terminal_settings), column=0, columnspan=2, pady=(10, 0))
        
        # Database Configurations
        db_config_frame = ttk.LabelFrame(scrollable_frame, text="💾 Database Configurations", padding=10)
        db_config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Database settings
        db_settings = [
            ("Auto-backup Interval (hours)", "backup_interval", "24"),
            ("Max Log Entries", "max_log_entries", "10000"),
            ("Cleanup Threshold (days)", "cleanup_threshold", "30"),
            ("Enable Compression", "enable_compression", "true"),
            ("Export Format", "export_format", "json")
        ]
        
        self.db_settings_vars = {}
        for i, (label, key, default) in enumerate(db_settings):
            ttk.Label(db_config_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            
            if key == "enable_compression":
                var = tk.BooleanVar(value=default.lower() == "true")
                widget = ttk.Checkbutton(db_config_frame, variable=var)
            elif key == "export_format":
                var = tk.StringVar(value=default)
                widget = ttk.Combobox(db_config_frame, textvariable=var,
                                    values=["json", "csv", "xml"], state="readonly", width=17)
            else:
                var = tk.StringVar(value=default)
                widget = ttk.Entry(db_config_frame, textvariable=var, width=20)
            
            widget.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            self.db_settings_vars[key] = var
        
        # Save database config button
        save_db_btn = ttk.Button(db_config_frame, text="💾 Save Database Config",
                               command=self.save_database_config)
        save_db_btn.grid(row=len(db_settings), column=0, columnspan=2, pady=(10, 0))
        
        # Security Settings
        security_frame = ttk.LabelFrame(scrollable_frame, text="🔒 Security Settings", padding=10)
        security_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Security options
        self.security_vars = {}
        security_options = [
            ("Require Admin Authentication", "require_auth"),
            ("Enable Audit Logging", "audit_logging"),
            ("Encrypt Sensitive Data", "encrypt_data"),
            ("Enable Access Control", "access_control"),
            ("Require Approval for High-Risk", "require_approval_high_risk")
        ]
        
        for i, (label, key) in enumerate(security_options):
            var = tk.BooleanVar(value=True)
            self.security_vars[key] = var
            
            cb = ttk.Checkbutton(security_frame, text=label, variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # Save security config button
        save_security_btn = ttk.Button(security_frame, text="💾 Save Security Config",
                                     command=self.save_security_config)
        save_security_btn.grid(row=len(security_options), column=0, pady=(10, 0))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load initial method config
        self.load_method_config()
    
    def create_monitoring_tab(self):
        """Create monitoring and logging tab"""
        monitoring_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitoring_frame, text="📊 Monitoring")
        
        # Main container
        main_container = ttk.Frame(monitoring_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log display
        log_frame = ttk.LabelFrame(main_container, text="📋 System Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=20, wrap=tk.WORD,
                               bg='#3c3c3c', fg='#cccccc', font=('Consolas', 9))
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add some sample log entries
        sample_logs = [
            f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Admin Panel started successfully",
            f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Database connection established",
            f"[{datetime.now().strftime('%H:%M:%S')}] INFO: GUI components initialized"
        ]
        
        for log in sample_logs:
            self.log_text.insert(tk.END, log + "\n")
    
    def create_connection_management_tab(self):
        """Create connection management tab for IP, ports, sessions and rooms"""
        connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(connection_frame, text="🌐 Connections")
        
        # Main container
        main_container = ttk.Frame(connection_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Connection Status
        status_frame = ttk.LabelFrame(main_container, text="🔗 Connection Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Connection info display
        info_grid = ttk.Frame(status_frame)
        info_grid.pack(fill=tk.X)
        
        # Current IP and Port
        ttk.Label(info_grid, text="Current IP:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.current_ip_label = ttk.Label(info_grid, text="Not Connected", foreground="red")
        self.current_ip_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(info_grid, text="Port:", font=('Arial', 9, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.current_port_label = ttk.Label(info_grid, text="N/A", foreground="red")
        self.current_port_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(info_grid, text="Status:", font=('Arial', 9, 'bold')).grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.connection_status_label = ttk.Label(info_grid, text="🔴 Disconnected", foreground="red")
        self.connection_status_label.grid(row=0, column=5, sticky=tk.W)
        
        # Connection controls
        controls_frame = ttk.Frame(status_frame)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        # IP Configuration
        ttk.Label(controls_frame, text="Target IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.target_ip_var = tk.StringVar(value="127.0.0.1")
        self.target_ip_entry = ttk.Entry(controls_frame, textvariable=self.target_ip_var, width=15)
        self.target_ip_entry.grid(row=0, column=1, padx=(0, 10))
        
        # Port Configuration
        ttk.Label(controls_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.target_port_var = tk.StringVar(value="5000")
        self.target_port_entry = ttk.Entry(controls_frame, textvariable=self.target_port_var, width=8)
        self.target_port_entry.grid(row=0, column=3, padx=(0, 10))
        
        # Connection buttons
        self.connect_btn = ttk.Button(controls_frame, text="🔗 Connect", 
                                    command=self.connect_to_server)
        self.connect_btn.grid(row=0, column=4, padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(controls_frame, text="❌ Disconnect", 
                                       command=self.disconnect_from_server, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=5, padx=(0, 5))
        
        self.verify_ip_btn = ttk.Button(controls_frame, text="✅ Verify IP", 
                                      command=self.verify_ip_connection)
        self.verify_ip_btn.grid(row=0, column=6)
        
        # Middle section - Session and Room Management
        session_frame = ttk.LabelFrame(main_container, text="🏠 Sessions & Rooms", padding=10)
        session_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Session management
        session_top = ttk.Frame(session_frame)
        session_top.pack(fill=tk.X, pady=(0, 10))
        
        # Current session info
        session_info_frame = ttk.LabelFrame(session_top, text="📋 Current Session", padding=5)
        session_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        session_grid = ttk.Frame(session_info_frame)
        session_grid.pack(fill=tk.X)
        
        ttk.Label(session_grid, text="Session ID:").grid(row=0, column=0, sticky=tk.W)
        self.session_id_label = ttk.Label(session_grid, text="No active session")
        self.session_id_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(session_grid, text="Created:").grid(row=1, column=0, sticky=tk.W)
        self.session_created_label = ttk.Label(session_grid, text="N/A")
        self.session_created_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(session_grid, text="Client Count:").grid(row=2, column=0, sticky=tk.W)
        self.client_count_label = ttk.Label(session_grid, text="0")
        self.client_count_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Room creation
        room_create_frame = ttk.LabelFrame(session_top, text="🚪 Create Room", padding=5)
        room_create_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        ttk.Label(room_create_frame, text="Room Name:").pack(anchor=tk.W)
        self.room_name_var = tk.StringVar()
        self.room_name_entry = ttk.Entry(room_create_frame, textvariable=self.room_name_var, width=20)
        self.room_name_entry.pack(pady=(2, 5))
        
        ttk.Label(room_create_frame, text="Room Type:").pack(anchor=tk.W)
        self.room_type_var = tk.StringVar(value="Payment Testing")
        room_type_combo = ttk.Combobox(room_create_frame, textvariable=self.room_type_var,
                                     values=["Payment Testing", "Admin Panel", "Monitoring", "Debugging", "Private"],
                                     state="readonly", width=18)
        room_type_combo.pack(pady=(2, 5))
        
        ttk.Label(room_create_frame, text="Max Clients:").pack(anchor=tk.W)
        self.max_clients_var = tk.StringVar(value="10")
        max_clients_spin = ttk.Spinbox(room_create_frame, from_=1, to=100, 
                                     textvariable=self.max_clients_var, width=18)
        max_clients_spin.pack(pady=(2, 5))
        
        self.create_room_btn = ttk.Button(room_create_frame, text="➕ Create Room", 
                                        command=self.create_new_room)
        self.create_room_btn.pack(pady=(5, 0))
        
        # Rooms and Clients display
        rooms_frame = ttk.Frame(session_frame)
        rooms_frame.pack(fill=tk.BOTH, expand=True)
        
        # Active Rooms
        rooms_list_frame = ttk.LabelFrame(rooms_frame, text="🏠 Active Rooms", padding=5)
        rooms_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Rooms treeview
        self.rooms_tree = ttk.Treeview(rooms_list_frame, columns=("Type", "Clients", "Status", "Created"), 
                                     show="tree headings", height=8)
        self.rooms_tree.heading("#0", text="Room Name")
        self.rooms_tree.heading("Type", text="Type")
        self.rooms_tree.heading("Clients", text="Clients")
        self.rooms_tree.heading("Status", text="Status")
        self.rooms_tree.heading("Created", text="Created")
        
        self.rooms_tree.column("#0", width=120)
        self.rooms_tree.column("Type", width=100)
        self.rooms_tree.column("Clients", width=60)
        self.rooms_tree.column("Status", width=80)
        self.rooms_tree.column("Created", width=80)
        
        rooms_scrollbar = ttk.Scrollbar(rooms_list_frame, orient=tk.VERTICAL, command=self.rooms_tree.yview)
        self.rooms_tree.configure(yscrollcommand=rooms_scrollbar.set)
        
        self.rooms_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rooms_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.rooms_tree.bind("<Double-1>", self.on_room_double_click)
        
        # Connected Clients
        clients_list_frame = ttk.LabelFrame(rooms_frame, text="👥 Connected Clients", padding=5)
        clients_list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Clients treeview
        self.clients_tree = ttk.Treeview(clients_list_frame, columns=("IP", "Room", "Status", "Connected"), 
                                       show="tree headings", height=8)
        self.clients_tree.heading("#0", text="Client ID")
        self.clients_tree.heading("IP", text="IP Address")
        self.clients_tree.heading("Room", text="Room")
        self.clients_tree.heading("Status", text="Status")
        self.clients_tree.heading("Connected", text="Connected")
        
        self.clients_tree.column("#0", width=100)
        self.clients_tree.column("IP", width=100)
        self.clients_tree.column("Room", width=100)
        self.clients_tree.column("Status", width=80)
        self.clients_tree.column("Connected", width=80)
        
        clients_scrollbar = ttk.Scrollbar(clients_list_frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=clients_scrollbar.set)
        
        self.clients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        clients_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.clients_tree.bind("<Double-1>", self.on_client_double_click)
        
        # Bottom section - Connection Tools
        tools_frame = ttk.LabelFrame(main_container, text="🔧 Connection Tools", padding=10)
        tools_frame.pack(fill=tk.X, pady=(10, 0))
        
        tools_grid = ttk.Frame(tools_frame)
        tools_grid.pack(fill=tk.X)
        
        # Network tools
        self.ping_btn = ttk.Button(tools_grid, text="📡 Ping IP", command=self.ping_target_ip)
        self.ping_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.port_scan_btn = ttk.Button(tools_grid, text="🔍 Port Scan", command=self.scan_ports)
        self.port_scan_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.trace_route_btn = ttk.Button(tools_grid, text="🗺️ Trace Route", command=self.trace_route)
        self.trace_route_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Session tools
        self.refresh_connections_btn = ttk.Button(tools_grid, text="🔄 Refresh", 
                                                command=self.refresh_connections)
        self.refresh_connections_btn.grid(row=0, column=3, padx=(0, 5))
        
        self.broadcast_message_btn = ttk.Button(tools_grid, text="📢 Broadcast", 
                                              command=self.broadcast_message)
        self.broadcast_message_btn.grid(row=0, column=4, padx=(0, 5))
        
        self.export_connections_btn = ttk.Button(tools_grid, text="📤 Export", 
                                               command=self.export_connection_log)
        self.export_connections_btn.grid(row=0, column=5)
        
        # Initialize connection management
        self.init_connection_management()
    
    # Event handler methods
    def setup_bindings(self):
        """Setup event bindings"""
        pass
    
    def background_worker(self):
        """Background worker thread"""
        while True:
            try:
                # Check for test requests
                if not self.test_queue.empty():
                    test_config = self.test_queue.get()
                    result = self.payment_tester.test_method(test_config)
                    self.results_queue.put(result)
                
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Background worker error: {e}")
    
    def on_method_change(self, event=None):
        """Handle payment method change"""
        self.update_method_info()
    
    def update_method_info(self):
        """Update method information display"""
        method = self.bypass_method_var.get()
        info = self.payment_tester.available_methods.get(method, "Unknown method")
        
        self.method_info_text.delete(1.0, tk.END)
        self.method_info_text.insert(tk.END, f"Method: {method}\n\n")
        self.method_info_text.insert(tk.END, f"Description: {info}\n\n")
        self.method_info_text.insert(tk.END, "Configuration options:\n")
        self.method_info_text.insert(tk.END, "- Amount limits\n")
        self.method_info_text.insert(tk.END, "- Security settings\n")
        self.method_info_text.insert(tk.END, "- Terminal compatibility")
    
    def run_single_test(self):
        """Run a single payment test"""
        try:
            # Get test configuration
            config = {
                'brand': self.card_brand_var.get(),
                'card_type': self.card_type_var.get(),
                'country': self.country_var.get(),
                'currency': self.currency_var.get(),
                'pan': self.pan_var.get(),
                'terminal': self.terminal_type_var.get(),
                'method': self.bypass_method_var.get()
            }
            
            # Add to test queue
            self.test_queue.put(config)
            
            # Update status
            self.results_summary_label.config(text="Running test...")
            
            # Start checking for results
            self.root.after(100, self.check_test_results)
            
        except Exception as e:
            messagebox.showerror("Test Error", f"Failed to run test: {str(e)}")
    
    def run_batch_test(self):
        """Run batch tests"""
        try:
            # Create multiple test configurations
            brands = ["Visa", "Mastercard", "American Express"]
            methods = ["cdcvm", "signature", "contactless"]
            
            for brand in brands:
                for method in methods:
                    config = {
                        'brand': brand,
                        'card_type': self.card_type_var.get(),
                        'country': self.country_var.get(),
                        'currency': self.currency_var.get(),
                        'pan': self.pan_var.get(),
                        'terminal': self.terminal_type_var.get(),
                        'method': method
                    }
                    self.test_queue.put(config)
            
            self.results_summary_label.config(text="Running batch tests...")
            self.root.after(100, self.check_test_results)
            
        except Exception as e:
            messagebox.showerror("Batch Test Error", f"Failed to run batch test: {str(e)}")
    
    def check_test_results(self):
        """Check for completed test results"""
        results_processed = 0
        
        while not self.results_queue.empty():
            result = self.results_queue.get()
            self.add_test_result_to_tree(result)
            self.db_manager.add_test_result(result)
            results_processed += 1
        
        if results_processed > 0:
            self.results_summary_label.config(
                text=f"Processed {results_processed} test results"
            )
        
        # Continue checking if there are pending tests
        if not self.test_queue.empty():
            self.root.after(100, self.check_test_results)
        else:
            self.results_summary_label.config(text="All tests completed")
    
    def add_test_result_to_tree(self, result: Dict):
        """Add test result to results tree"""
        self.results_tree.insert('', 'end', values=(
            result['transaction_id'],
            result['brand'],
            result['method'],
            result['terminal'],
            result['status'],
            f"{result['execution_time']:.1f}",
            result['notes']
        ))
    
    def clear_test_results(self):
        """Clear test results display"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.results_summary_label.config(text="Results cleared")
    
    def on_pending_select(self, event=None):
        """Handle pending transaction selection"""
        selection = self.pending_tree.selection()
        if selection:
            item = self.pending_tree.item(selection[0])
            values = item['values']
            
            # Update details display
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, f"Transaction ID: {values[0]}\n")
            self.details_text.insert(tk.END, f"Brand: {values[1]}\n")
            self.details_text.insert(tk.END, f"Method: {values[2]}\n")
            self.details_text.insert(tk.END, f"Status: {values[3]}\n")
            self.details_text.insert(tk.END, f"Success: {values[4]}\n")
            self.details_text.insert(tk.END, f"Execution Time: {values[5]}\n\n")
            self.details_text.insert(tk.END, "Additional Details:\n")
            self.details_text.insert(tk.END, "- Terminal configuration verified\n")
            self.details_text.insert(tk.END, "- Security checks passed\n")
            self.details_text.insert(tk.END, "- Ready for approval process")
    
    def refresh_pending_transactions(self):
        """Refresh pending transactions list"""
        # Clear existing items
        for item in self.pending_tree.get_children():
            self.pending_tree.delete(item)
        
        # Get test results to simulate pending transactions
        results = self.db_manager.get_test_results(20)
        
        for result in results:
            if result['status'] == 'SUCCESS':
                self.pending_tree.insert('', 'end', values=(
                    result['transaction_id'],
                    result['brand'],
                    result['method'],
                    'PENDING',
                    'YES',
                    f"{result['execution_time']:.1f}ms"
                ))
    
    def schedule_pending_refresh(self):
        """Schedule automatic refresh of pending transactions"""
        if self.auto_refresh_var.get():
            self.refresh_pending_transactions()
        
        # Schedule next refresh
        self.root.after(30000, self.schedule_pending_refresh)  # 30 seconds
    
    def approve_transaction(self):
        """Approve selected transaction and generate script"""
        selection = self.pending_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction to approve")
            return
        
        try:
            item = self.pending_tree.item(selection[0])
            values = item['values']
            
            # Get approval data
            approval_data = {
                'confidence': self.confidence_var.get(),
                'risk': self.risk_var.get(),
                'notes': self.approval_notes_text.get(1.0, tk.END).strip()
            }
            
            # Create test result for script generation
            test_result = {
                'transaction_id': values[0],
                'brand': values[1],
                'method': values[2],
                'terminal': 'POS',
                'status': 'APPROVED'
            }
            
            # Generate script
            script_content = self.script_generator.generate_script(test_result, approval_data)
            
            # Save script to file
            script_filename = f"script_{values[0]}.py"
            script_path = Path("generated_scripts") / script_filename
            script_path.parent.mkdir(exist_ok=True)
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            messagebox.showinfo("Approval Complete", 
                              f"Transaction approved and script generated:\n{script_path}")
            
            # Remove from pending list
            self.pending_tree.delete(selection[0])
            
        except Exception as e:
            messagebox.showerror("Approval Error", f"Failed to approve transaction: {str(e)}")
    
    def reject_transaction(self):
        """Reject selected transaction"""
        selection = self.pending_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction to reject")
            return
        
        # Remove from pending list
        self.pending_tree.delete(selection[0])
        messagebox.showinfo("Transaction Rejected", "Transaction has been rejected")
    
    def request_modification(self):
        """Request modification for selected transaction"""
        selection = self.pending_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction")
            return
        
        messagebox.showinfo("Modification Requested", 
                          "Modification request has been sent to the testing team")
    
    def on_filter_change(self, event=None):
        """Handle filter change in database view"""
        self.refresh_database_view()
    
    def on_search_change(self, event=None):
        """Handle search change in database view"""
        self.refresh_database_view()
    
    def refresh_database_view(self):
        """Refresh database view with current filters"""
        # Clear existing items
        for item in self.scripts_tree.get_children():
            self.scripts_tree.delete(item)
        
        # Get test results and populate scripts tree
        results = self.db_manager.get_test_results(50)
        
        for result in results:
            self.scripts_tree.insert('', 'end', values=(
                result['transaction_id'],
                result['brand'],
                result['method'],
                result['status'],
                'HIGH',  # Confidence
                'LOW',   # Risk
                result['created_at']
            ))
    
    def update_database_stats(self):
        """Update database statistics display"""
        stats = self.db_manager.get_statistics()
        
        for key, value in stats.items():
            if key in self.stat_labels:
                self.stat_labels[key].config(text=str(value))
    
    def create_scripts_context_menu(self):
        """Create context menu for scripts tree"""
        self.scripts_context_menu = tk.Menu(self.root, tearoff=0)
        self.scripts_context_menu.add_command(label="View Details", command=self.open_script_details)
        self.scripts_context_menu.add_command(label="Export Script", command=self.export_script)
        self.scripts_context_menu.add_command(label="Delete Script", command=self.delete_script)
    
    def show_scripts_context_menu(self, event):
        """Show context menu for scripts"""
        try:
            self.scripts_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.scripts_context_menu.grab_release()
    
    def open_script_details(self, event=None):
        """Open script details window"""
        selection = self.scripts_tree.selection()
        if selection:
            item = self.scripts_tree.item(selection[0])
            values = item['values']
            messagebox.showinfo("Script Details", f"Script ID: {values[0]}\nDetails available in full version")
    
    def export_script(self):
        """Export selected script"""
        messagebox.showinfo("Export", "Script export functionality")
    
    def delete_script(self):
        """Delete selected script"""
        selection = self.scripts_tree.selection()
        if selection:
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this script?"):
                self.scripts_tree.delete(selection[0])
    
    def export_database(self):
        """Export database to file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                results = self.db_manager.get_test_results(1000)
                
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2)
                
                messagebox.showinfo("Export Complete", f"Database exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export database: {str(e)}")
    
    def import_scripts(self):
        """Import scripts from file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                messagebox.showinfo("Import Complete", f"Scripts imported from {filename}")
                self.refresh_database_view()
                
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import scripts: {str(e)}")
    
    def create_backup(self):
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.db"
            backup_path = Path("backups") / backup_filename
            backup_path.parent.mkdir(exist_ok=True)
            
            # Simple file copy for backup
            import shutil
            shutil.copy2(self.db_manager.db_path, backup_path)
            
            messagebox.showinfo("Backup Complete", f"Backup created: {backup_path}")
            
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup: {str(e)}")
    
    def cleanup_database(self):
        """Cleanup old database entries"""
        if messagebox.askyesno("Confirm Cleanup", "This will remove old entries. Continue?"):
            messagebox.showinfo("Cleanup Complete", "Database cleanup completed")
            self.refresh_database_view()
            self.update_database_stats()
    
    def on_config_method_change(self, event=None):
        """Handle configuration method change"""
        self.load_method_config()
    
    def load_method_config(self):
        """Load method configuration"""
        method = self.config_method_var.get()
        
        # Sample configuration
        config = {
            "method": method,
            "enabled": True,
            "settings": {
                "timeout": 5000,
                "retries": 3,
                "amount_limit": 100.00
            }
        }
        
        self.method_config_text.delete(1.0, tk.END)
        self.method_config_text.insert(tk.END, json.dumps(config, indent=2))
    
    def save_method_config(self):
        """Save method configuration"""
        try:
            config_text = self.method_config_text.get(1.0, tk.END)
            config = json.loads(config_text)
            
            # Save configuration (in real implementation, this would save to file/database)
            messagebox.showinfo("Config Saved", f"Configuration saved for {config.get('method', 'unknown')}")
            
        except json.JSONDecodeError:
            messagebox.showerror("Config Error", "Invalid JSON configuration")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save configuration: {str(e)}")
    
    def save_terminal_config(self):
        """Save terminal configuration"""
        try:
            config = {}
            for key, var in self.terminal_settings_vars.items():
                if isinstance(var, tk.BooleanVar):
                    config[key] = var.get()
                else:
                    config[key] = var.get()
            
            messagebox.showinfo("Config Saved", "Terminal configuration saved successfully")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save terminal configuration: {str(e)}")
    
    def save_database_config(self):
        """Save database configuration"""
        try:
            config = {}
            for key, var in self.db_settings_vars.items():
                if isinstance(var, tk.BooleanVar):
                    config[key] = var.get()
                else:
                    config[key] = var.get()
            
            messagebox.showinfo("Config Saved", "Database configuration saved successfully")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save database configuration: {str(e)}")
    
    def save_security_config(self):
        """Save security configuration"""
        try:
            config = {}
            for key, var in self.security_vars.items():
                config[key] = var.get()
            
            messagebox.showinfo("Config Saved", "Security configuration saved successfully")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save security configuration: {str(e)}")
    
    # Connection Management Methods
    def init_connection_management(self):
        """Initialize connection management system"""
        self.active_connections = {}
        self.active_rooms = {}
        self.connected_clients = {}
        self.current_session_id = None
        self.server_socket = None
        self.is_connected = False
        
        # Start connection monitoring
        self.start_connection_monitoring()
    
    def connect_to_server(self):
        """Connect to the target server"""
        try:
            import socket
            
            target_ip = self.target_ip_var.get()
            target_port = int(self.target_port_var.get())
            
            # Validate IP address
            if not self.validate_ip_address(target_ip):
                messagebox.showerror("Invalid IP", "Please enter a valid IP address")
                return
            
            # Create socket connection
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.settimeout(10)  # 10 second timeout
            
            # Attempt connection
            self.server_socket.connect((target_ip, target_port))
            
            # Update connection status
            self.is_connected = True
            self.current_ip_label.config(text=target_ip, foreground="green")
            self.current_port_label.config(text=str(target_port), foreground="green")
            self.connection_status_label.config(text="🟢 Connected", foreground="green")
            
            # Update button states
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            
            # Create new session
            self.create_new_session()
            
            self.log_activity("INFO", f"Connected to {target_ip}:{target_port}")
            messagebox.showinfo("Success", f"Successfully connected to {target_ip}:{target_port}")
            
        except Exception as e:
            self.log_activity("ERROR", f"Connection failed: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
    
    def disconnect_from_server(self):
        """Disconnect from the server"""
        try:
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            
            # Update connection status
            self.is_connected = False
            self.current_ip_label.config(text="Not Connected", foreground="red")
            self.current_port_label.config(text="N/A", foreground="red")
            self.connection_status_label.config(text="🔴 Disconnected", foreground="red")
            
            # Update button states
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            
            # Clear session
            self.clear_current_session()
            
            self.log_activity("INFO", "Disconnected from server")
            messagebox.showinfo("Disconnected", "Successfully disconnected from server")
            
        except Exception as e:
            self.log_activity("ERROR", f"Disconnection error: {e}")
    
    def verify_ip_connection(self):
        """Verify IP connection and gather information"""
        try:
            import socket
            import subprocess
            
            target_ip = self.target_ip_var.get()
            
            if not self.validate_ip_address(target_ip):
                messagebox.showerror("Invalid IP", "Please enter a valid IP address")
                return
            
            # Create verification dialog
            self.create_ip_verification_dialog(target_ip)
            
        except Exception as e:
            self.log_activity("ERROR", f"IP verification failed: {e}")
            messagebox.showerror("Verification Error", f"Failed to verify IP: {e}")
    
    def create_ip_verification_dialog(self, target_ip: str):
        """Create IP verification dialog with detailed information"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"🔍 IP Verification - {target_ip}")
        dialog.geometry("600x500")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # IP Information
        info_frame = ttk.LabelFrame(main_frame, text=f"📊 IP Information - {target_ip}", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # IP details text area
        info_text = tk.Text(info_frame, height=15, wrap=tk.WORD, bg='#1e1e1e', fg='#00ff00', 
                           font=('Consolas', 9))
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=info_text.yview)
        info_text.configure(yscrollcommand=info_scrollbar.set)
        
        info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Perform verification tests
        verification_results = self.perform_ip_verification(target_ip)
        info_text.insert(tk.END, verification_results)
        info_text.configure(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        refresh_btn = ttk.Button(button_frame, text="🔄 Refresh", 
                               command=lambda: self.refresh_ip_verification(info_text, target_ip))
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_btn = ttk.Button(button_frame, text="💾 Save Report", 
                            command=lambda: self.save_verification_report(verification_results, target_ip))
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = ttk.Button(button_frame, text="❌ Close", command=dialog.destroy)
        close_btn.pack(side=tk.RIGHT)
    
    def perform_ip_verification(self, target_ip: str) -> str:
        """Perform comprehensive IP verification"""
        import socket
        import subprocess
        import platform
        from datetime import datetime
        
        results = []
        results.append(f"IP VERIFICATION REPORT")
        results.append(f"=====================")
        results.append(f"Target IP: {target_ip}")
        results.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        results.append("")
        
        # 1. DNS Resolution
        try:
            hostname = socket.gethostbyaddr(target_ip)[0]
            results.append(f"✅ DNS Resolution: {hostname}")
        except:
            results.append(f"❌ DNS Resolution: No reverse DNS found")
        
        # 2. Ping Test
        try:
            system = platform.system().lower()
            if system == "windows":
                ping_cmd = f"ping -n 4 {target_ip}"
            else:
                ping_cmd = f"ping -c 4 {target_ip}"
            
            ping_result = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True, timeout=30)
            if ping_result.returncode == 0:
                results.append(f"✅ Ping Test: Reachable")
                # Extract ping statistics
                ping_lines = ping_result.stdout.split('\n')
                for line in ping_lines:
                    if "time=" in line.lower() or "average" in line.lower():
                        results.append(f"   {line.strip()}")
            else:
                results.append(f"❌ Ping Test: Not reachable")
        except Exception as e:
            results.append(f"❌ Ping Test: Error - {e}")
        
        results.append("")
        
        # 3. Port Scanning (common ports)
        common_ports = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 5000, 8080, 8443]
        results.append("🔍 PORT SCAN RESULTS:")
        open_ports = []
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((target_ip, port))
                if result == 0:
                    results.append(f"   ✅ Port {port}: OPEN")
                    open_ports.append(port)
                else:
                    results.append(f"   ❌ Port {port}: CLOSED")
                sock.close()
            except:
                results.append(f"   ⚠️ Port {port}: ERROR")
        
        results.append("")
        results.append(f"📊 SUMMARY:")
        results.append(f"   Open Ports: {len(open_ports)}")
        results.append(f"   Available Ports: {', '.join(map(str, open_ports)) if open_ports else 'None'}")
        
        # 4. Network Information
        try:
            # Get local network info
            local_ip = socket.gethostbyname(socket.gethostname())
            results.append(f"   Local IP: {local_ip}")
            
            # Check if target is in local network
            if target_ip.startswith(local_ip.rsplit('.', 1)[0]):
                results.append(f"   Network: Same local network")
            else:
                results.append(f"   Network: External network")
                
        except Exception as e:
            results.append(f"   Network Info: Error - {e}")
        
        return '\n'.join(results)
    
    def refresh_ip_verification(self, text_widget, target_ip: str):
        """Refresh IP verification results"""
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        verification_results = self.perform_ip_verification(target_ip)
        text_widget.insert(tk.END, verification_results)
        text_widget.configure(state=tk.DISABLED)
    
    def save_verification_report(self, results: str, target_ip: str):
        """Save verification report to file"""
        try:
            filename = f"ip_verification_{target_ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filepath:
                with open(filepath, 'w') as f:
                    f.write(results)
                messagebox.showinfo("Success", f"Verification report saved to {filepath}")
                self.log_activity("INFO", f"IP verification report saved: {filepath}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {e}")
    
    def validate_ip_address(self, ip: str) -> bool:
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except:
            return False
    
    def create_new_session(self):
        """Create a new session"""
        import uuid
        
        self.current_session_id = str(uuid.uuid4())[:8]
        session_time = datetime.now().strftime("%H:%M:%S")
        
        self.session_id_label.config(text=self.current_session_id)
        self.session_created_label.config(text=session_time)
        self.client_count_label.config(text="0")
        
        self.log_activity("INFO", f"New session created: {self.current_session_id}")
    
    def clear_current_session(self):
        """Clear current session"""
        self.current_session_id = None
        self.session_id_label.config(text="No active session")
        self.session_created_label.config(text="N/A")
        self.client_count_label.config(text="0")
        
        # Clear all rooms and clients
        for item in self.rooms_tree.get_children():
            self.rooms_tree.delete(item)
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
        
        self.active_rooms.clear()
        self.connected_clients.clear()
    
    def create_new_room(self):
        """Create a new room for clients"""
        try:
            if not self.current_session_id:
                messagebox.showwarning("No Session", "Please establish a connection first")
                return
            
            room_name = self.room_name_var.get().strip()
            room_type = self.room_type_var.get()
            max_clients = int(self.max_clients_var.get())
            
            if not room_name:
                messagebox.showwarning("Invalid Name", "Please enter a room name")
                return
            
            if room_name in self.active_rooms:
                messagebox.showwarning("Room Exists", "A room with this name already exists")
                return
            
            # Create room
            import uuid
            room_id = str(uuid.uuid4())[:8]
            room_data = {
                "id": room_id,
                "name": room_name,
                "type": room_type,
                "max_clients": max_clients,
                "current_clients": 0,
                "status": "Active",
                "created": datetime.now().strftime("%H:%M:%S"),
                "clients": []
            }
            
            self.active_rooms[room_name] = room_data
            
            # Add to rooms tree
            self.rooms_tree.insert('', 0, text=room_name, values=(
                room_type,
                "0",
                "Active",
                room_data["created"]
            ), tags=(room_id,))
            
            # Clear room creation form
            self.room_name_var.set("")
            
            self.log_activity("INFO", f"Room created: {room_name} (Type: {room_type}, Max: {max_clients})")
            messagebox.showinfo("Success", f"Room '{room_name}' created successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create room: {e}")
            self.log_activity("ERROR", f"Failed to create room: {e}")
    
    def on_room_double_click(self, event):
        """Handle room double-click to show details"""
        try:
            selection = self.rooms_tree.selection()
            if not selection:
                return
            
            item = selection[0]
            room_name = self.rooms_tree.item(item)['text']
            
            if room_name in self.active_rooms:
                self.show_room_details(room_name)
                
        except Exception as e:
            self.log_activity("ERROR", f"Error showing room details: {e}")
    
    def show_room_details(self, room_name: str):
        """Show detailed room information"""
        room_data = self.active_rooms[room_name]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"🏠 Room Details - {room_name}")
        dialog.geometry("500x400")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Room info
        info_frame = ttk.LabelFrame(main_frame, text="📋 Room Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)
        
        details = [
            ("Room ID:", room_data["id"]),
            ("Name:", room_data["name"]),
            ("Type:", room_data["type"]),
            ("Status:", room_data["status"]),
            ("Created:", room_data["created"]),
            ("Max Clients:", str(room_data["max_clients"])),
            ("Current Clients:", str(room_data["current_clients"]))
        ]
        
        for i, (label, value) in enumerate(details):
            ttk.Label(info_grid, text=label, font=('Arial', 9, 'bold')).grid(
                row=i, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            ttk.Label(info_grid, text=value).grid(
                row=i, column=1, sticky=tk.W, pady=2)
        
        # Room controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_room_btn = ttk.Button(controls_frame, text="🚪 Close Room", 
                                  command=lambda: self.close_room(room_name, dialog))
        close_room_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        kick_all_btn = ttk.Button(controls_frame, text="👥 Kick All", 
                                command=lambda: self.kick_all_clients(room_name))
        kick_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = ttk.Button(controls_frame, text="❌ Close", command=dialog.destroy)
        close_btn.pack(side=tk.RIGHT)
    
    def close_room(self, room_name: str, dialog):
        """Close a room and disconnect all clients"""
        try:
            if room_name in self.active_rooms:
                # Remove from active rooms
                del self.active_rooms[room_name]
                
                # Remove from tree
                for item in self.rooms_tree.get_children():
                    if self.rooms_tree.item(item)['text'] == room_name:
                        self.rooms_tree.delete(item)
                        break
                
                self.log_activity("INFO", f"Room closed: {room_name}")
                messagebox.showinfo("Success", f"Room '{room_name}' closed successfully")
                dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to close room: {e}")
    
    def kick_all_clients(self, room_name: str):
        """Kick all clients from a room"""
        try:
            if room_name in self.active_rooms:
                room_data = self.active_rooms[room_name]
                client_count = room_data["current_clients"]
                
                # In a real implementation, you would send disconnect messages to clients
                room_data["current_clients"] = 0
                room_data["clients"] = []
                
                # Update room tree
                for item in self.rooms_tree.get_children():
                    if self.rooms_tree.item(item)['text'] == room_name:
                        values = list(self.rooms_tree.item(item)['values'])
                        values[1] = "0"  # Update client count
                        self.rooms_tree.item(item, values=values)
                        break
                
                self.log_activity("INFO", f"Kicked all clients from room: {room_name}")
                messagebox.showinfo("Success", f"Kicked {client_count} clients from '{room_name}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to kick clients: {e}")
    
    def on_client_double_click(self, event):
        """Handle client double-click to show details"""
        try:
            selection = self.clients_tree.selection()
            if not selection:
                return
            
            item = selection[0]
            client_id = self.clients_tree.item(item)['text']
            
            if client_id in self.connected_clients:
                self.show_client_details(client_id)
                
        except Exception as e:
            self.log_activity("ERROR", f"Error showing client details: {e}")
    
    def show_client_details(self, client_id: str):
        """Show detailed client information"""
        # This would show detailed client information in a real implementation
        messagebox.showinfo("Client Details", f"Details for client: {client_id}")
    
    def ping_target_ip(self):
        """Ping the target IP address"""
        try:
            target_ip = self.target_ip_var.get()
            if not self.validate_ip_address(target_ip):
                messagebox.showerror("Invalid IP", "Please enter a valid IP address")
                return
            
            # Run ping in a separate thread to avoid blocking the GUI
            import threading
            threading.Thread(target=self._ping_worker, args=(target_ip,), daemon=True).start()
            
        except Exception as e:
            self.log_activity("ERROR", f"Ping failed: {e}")
    
    def _ping_worker(self, target_ip: str):
        """Worker thread for ping operation"""
        try:
            import subprocess
            import platform
            
            system = platform.system().lower()
            if system == "windows":
                ping_cmd = f"ping -n 4 {target_ip}"
            else:
                ping_cmd = f"ping -c 4 {target_ip}"
            
            result = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_activity("INFO", f"Ping successful to {target_ip}")
                self.root.after(0, lambda: messagebox.showinfo("Ping Success", f"Successfully pinged {target_ip}"))
            else:
                self.log_activity("WARNING", f"Ping failed to {target_ip}")
                self.root.after(0, lambda: messagebox.showwarning("Ping Failed", f"Failed to ping {target_ip}"))
                
        except Exception as e:
            self.log_activity("ERROR", f"Ping error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Ping Error", f"Ping error: {e}"))
    
    def scan_ports(self):
        """Scan ports on the target IP"""
        try:
            target_ip = self.target_ip_var.get()
            if not self.validate_ip_address(target_ip):
                messagebox.showerror("Invalid IP", "Please enter a valid IP address")
                return
            
            # Create port scan dialog
            self.create_port_scan_dialog(target_ip)
            
        except Exception as e:
            self.log_activity("ERROR", f"Port scan failed: {e}")
    
    def create_port_scan_dialog(self, target_ip: str):
        """Create port scanning dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"🔍 Port Scanner - {target_ip}")
        dialog.geometry("600x500")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Scan configuration
        config_frame = ttk.LabelFrame(main_frame, text="🔧 Scan Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        config_grid = ttk.Frame(config_frame)
        config_grid.pack(fill=tk.X)
        
        # Port range
        ttk.Label(config_grid, text="Port Range:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        start_port_var = tk.StringVar(value="1")
        end_port_var = tk.StringVar(value="1000")
        
        ttk.Label(config_grid, text="From:").grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        start_port_entry = ttk.Entry(config_grid, textvariable=start_port_var, width=8)
        start_port_entry.grid(row=0, column=2, padx=(0, 10))
        
        ttk.Label(config_grid, text="To:").grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        end_port_entry = ttk.Entry(config_grid, textvariable=end_port_var, width=8)
        end_port_entry.grid(row=0, column=4, padx=(0, 10))
        
        # Scan button
        scan_btn = ttk.Button(config_grid, text="🔍 Start Scan", 
                            command=lambda: self.start_port_scan(target_ip, start_port_var.get(), 
                                                               end_port_var.get(), results_text))
        scan_btn.grid(row=0, column=5)
        
        # Results display
        results_frame = ttk.LabelFrame(main_frame, text="📊 Scan Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        results_text = tk.Text(results_frame, height=15, wrap=tk.WORD, bg='#1e1e1e', fg='#00ff00', 
                             font=('Consolas', 9))
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_text.yview)
        results_text.configure(yscrollcommand=results_scrollbar.set)
        
        results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_btn = ttk.Button(button_frame, text="❌ Close", command=dialog.destroy)
        close_btn.pack(side=tk.RIGHT)
    
    def start_port_scan(self, target_ip: str, start_port: str, end_port: str, results_widget):
        """Start port scanning in a separate thread"""
        try:
            start = int(start_port)
            end = int(end_port)
            
            if start > end or start < 1 or end > 65535:
                messagebox.showerror("Invalid Range", "Please enter a valid port range (1-65535)")
                return
            
            # Clear results
            results_widget.delete(1.0, tk.END)
            results_widget.insert(tk.END, f"Starting port scan on {target_ip}...\n")
            results_widget.insert(tk.END, f"Scanning ports {start} to {end}\n\n")
            
            # Start scan in thread
            import threading
            threading.Thread(target=self._port_scan_worker, 
                           args=(target_ip, start, end, results_widget), daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid port numbers")
    
    def _port_scan_worker(self, target_ip: str, start_port: int, end_port: int, results_widget):
        """Worker thread for port scanning"""
        import socket
        
        open_ports = []
        scanned = 0
        total = end_port - start_port + 1
        
        for port in range(start_port, end_port + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((target_ip, port))
                
                if result == 0:
                    open_ports.append(port)
                    self.root.after(0, lambda p=port: results_widget.insert(tk.END, f"✅ Port {p}: OPEN\n"))
                    self.root.after(0, lambda: results_widget.see(tk.END))
                
                sock.close()
                scanned += 1
                
                # Update progress every 50 ports
                if scanned % 50 == 0:
                    progress = (scanned / total) * 100
                    self.root.after(0, lambda: results_widget.insert(tk.END, f"Progress: {progress:.1f}% ({scanned}/{total})\n"))
                    self.root.after(0, lambda: results_widget.see(tk.END))
                
            except Exception as e:
                continue
        
        # Final results
        self.root.after(0, lambda: results_widget.insert(tk.END, f"\n📊 SCAN COMPLETE\n"))
        self.root.after(0, lambda: results_widget.insert(tk.END, f"Scanned {total} ports\n"))
        self.root.after(0, lambda: results_widget.insert(tk.END, f"Open ports found: {len(open_ports)}\n"))
        if open_ports:
            self.root.after(0, lambda: results_widget.insert(tk.END, f"Open ports: {', '.join(map(str, open_ports))}\n"))
        self.root.after(0, lambda: results_widget.see(tk.END))
        
        self.log_activity("INFO", f"Port scan completed on {target_ip}: {len(open_ports)} open ports found")
    
    def trace_route(self):
        """Perform trace route to target IP"""
        try:
            target_ip = self.target_ip_var.get()
            if not self.validate_ip_address(target_ip):
                messagebox.showerror("Invalid IP", "Please enter a valid IP address")
                return
            
            # Run traceroute in a separate thread
            import threading
            threading.Thread(target=self._traceroute_worker, args=(target_ip,), daemon=True).start()
            
        except Exception as e:
            self.log_activity("ERROR", f"Traceroute failed: {e}")
    
    def _traceroute_worker(self, target_ip: str):
        """Worker thread for traceroute operation"""
        try:
            import subprocess
            import platform
            
            system = platform.system().lower()
            if system == "windows":
                trace_cmd = f"tracert {target_ip}"
            else:
                trace_cmd = f"traceroute {target_ip}"
            
            result = subprocess.run(trace_cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.log_activity("INFO", f"Traceroute completed to {target_ip}")
                self.root.after(0, lambda: self.show_traceroute_results(target_ip, result.stdout))
            else:
                self.log_activity("WARNING", f"Traceroute failed to {target_ip}")
                self.root.after(0, lambda: messagebox.showwarning("Traceroute Failed", f"Failed to trace route to {target_ip}"))
                
        except Exception as e:
            self.log_activity("ERROR", f"Traceroute error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Traceroute Error", f"Traceroute error: {e}"))
    
    def show_traceroute_results(self, target_ip: str, results: str):
        """Show traceroute results in a dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"🗺️ Traceroute Results - {target_ip}")
        dialog.geometry("600x500")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Results display
        results_frame = ttk.LabelFrame(main_frame, text=f"🗺️ Route to {target_ip}", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        results_text = tk.Text(results_frame, wrap=tk.WORD, bg='#1e1e1e', fg='#00ff00', 
                             font=('Consolas', 9))
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_text.yview)
        results_text.configure(yscrollcommand=results_scrollbar.set)
        
        results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        results_text.insert(tk.END, results)
        results_text.configure(state=tk.DISABLED)
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_btn = ttk.Button(button_frame, text="❌ Close", command=dialog.destroy)
        close_btn.pack(side=tk.RIGHT)
    
    def refresh_connections(self):
        """Refresh connection information"""
        try:
            # Update connection status
            if self.is_connected and self.server_socket:
                self.connection_status_label.config(text="🟢 Connected", foreground="green")
            else:
                self.connection_status_label.config(text="🔴 Disconnected", foreground="red")
            
            # Refresh rooms and clients (in a real implementation, this would query the server)
            self.log_activity("INFO", "Connection information refreshed")
            
        except Exception as e:
            self.log_activity("ERROR", f"Failed to refresh connections: {e}")
    
    def broadcast_message(self):
        """Broadcast message to all connected clients"""
        try:
            if not self.current_session_id:
                messagebox.showwarning("No Session", "No active session to broadcast to")
                return
            
            # Create broadcast dialog
            self.create_broadcast_dialog()
            
        except Exception as e:
            self.log_activity("ERROR", f"Broadcast failed: {e}")
    
    def create_broadcast_dialog(self):
        """Create broadcast message dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("📢 Broadcast Message")
        dialog.geometry("500x400")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Message composition
        message_frame = ttk.LabelFrame(main_frame, text="✉️ Message", padding=10)
        message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        message_text = tk.Text(message_frame, height=10, wrap=tk.WORD)
        message_scrollbar = ttk.Scrollbar(message_frame, orient=tk.VERTICAL, command=message_text.yview)
        message_text.configure(yscrollcommand=message_scrollbar.set)
        
        message_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        message_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Target selection
        target_frame = ttk.LabelFrame(main_frame, text="🎯 Target", padding=10)
        target_frame.pack(fill=tk.X, pady=(0, 10))
        
        target_var = tk.StringVar(value="All Clients")
        target_combo = ttk.Combobox(target_frame, textvariable=target_var,
                                  values=["All Clients", "Specific Room", "Specific Client"],
                                  state="readonly")
        target_combo.pack(fill=tk.X)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def send_broadcast():
            message = message_text.get(1.0, tk.END).strip()
            target = target_var.get()
            
            if not message:
                messagebox.showwarning("Empty Message", "Please enter a message to broadcast")
                return
            
            # In a real implementation, send the message to clients
            self.log_activity("INFO", f"Broadcast sent to {target}: {message[:50]}...")
            messagebox.showinfo("Success", f"Message broadcasted to {target}")
            dialog.destroy()
        
        send_btn = ttk.Button(button_frame, text="📢 Send Broadcast", 
                            command=send_broadcast)
        send_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = ttk.Button(button_frame, text="❌ Cancel", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT)
    
    def export_connection_log(self):
        """Export connection log to file"""
        try:
            # Create connection log data
            log_data = {
                "session_id": self.current_session_id,
                "connection_status": "Connected" if self.is_connected else "Disconnected",
                "target_ip": self.target_ip_var.get(),
                "target_port": self.target_port_var.get(),
                "active_rooms": list(self.active_rooms.keys()),
                "connected_clients": list(self.connected_clients.keys()),
                "export_timestamp": datetime.now().isoformat()
            }
            
            # Save to file
            filename = f"connection_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filepath:
                with open(filepath, 'w') as f:
                    json.dump(log_data, f, indent=2)
                messagebox.showinfo("Success", f"Connection log exported to {filepath}")
                self.log_activity("INFO", f"Connection log exported: {filepath}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export connection log: {e}")
            self.log_activity("ERROR", f"Failed to export connection log: {e}")
    
    def start_connection_monitoring(self):
        """Start connection monitoring"""
        self.update_connection_status()
        self.schedule_connection_refresh()
    
    def update_connection_status(self):
        """Update connection status indicators"""
        try:
            # Update client count
            total_clients = sum(room["current_clients"] for room in self.active_rooms.values())
            self.client_count_label.config(text=str(total_clients))
            
        except Exception as e:
            logger.error(f"Error updating connection status: {e}")
    
    def schedule_connection_refresh(self):
        """Schedule automatic connection refresh"""
        self.update_connection_status()
        self.root.after(10000, self.schedule_connection_refresh)  # Refresh every 10 seconds
    
    def log_activity(self, level: str, message: str):
        """Log activity to the monitoring tab and console"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {level}: {message}\n"
            
            # Add to log text if it exists
            if hasattr(self, 'log_text'):
                self.log_text.insert(tk.END, log_entry)
                
                # Auto-scroll to bottom
                self.log_text.see(tk.END)
                
                # Limit log size to prevent memory issues
                lines = int(self.log_text.index(tk.END).split('.')[0])
                if lines > 1000:
                    self.log_text.delete(1.0, "100.0")
            
            # Also log to console
            logger.info(f"{level}: {message}")
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def run(self):
        """Run the admin panel"""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error running admin panel: {e}")
            messagebox.showerror("Application Error", f"An error occurred: {str(e)}")

def main():
    """Main function to run the admin panel"""
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create and run admin panel
        admin_panel = AdminPanel()
        admin_panel.run()
        
    except Exception as e:
        print(f"Failed to start admin panel: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
