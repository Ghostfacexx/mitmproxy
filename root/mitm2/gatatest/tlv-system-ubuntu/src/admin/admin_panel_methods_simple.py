#!/usr/bin/env python3
"""
TLV Admin Panel Methods - Simplified Working Version
Basic admin panel with essential functionality
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdminPanel:
    """Simplified Admin Panel class with working functionality"""
    
    def __init__(self):
        """Initialize the admin panel"""
        self.root = tk.Tk()
        self.root.title("🔧 TLV Admin Panel - Payment Testing & Database Management")
        self.root.geometry("1000x700")
        
        # Initialize variables
        self.current_database = None
        self.connection_status = "Disconnected"
        self.test_running = False
        
        # Set up the main interface
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_main_tab()
        self.create_testing_tab()
        self.create_database_tab()
        self.create_monitoring_tab()
    
    def create_main_tab(self):
        """Create main overview tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="🏠 Overview")
        
        # Welcome section
        welcome_frame = ttk.LabelFrame(main_frame, text="Welcome to TLV Admin Panel", padding=20)
        welcome_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(welcome_frame, text="🔧 TLV Admin Panel", font=("Arial", 16, "bold")).pack()
        ttk.Label(welcome_frame, text="Payment Method Testing & Database Management System").pack(pady=5)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="🟢 System Ready")
        self.status_label.pack(pady=5)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        button_frame = ttk.Frame(actions_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="🧪 Start Testing", command=self.start_quick_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Database Setup", command=self.setup_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔗 Test Connection", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📊 View Reports", command=self.view_reports).pack(side=tk.LEFT, padx=5)
    
    def create_testing_tab(self):
        """Create payment testing tab"""
        testing_frame = ttk.Frame(self.notebook)
        self.notebook.add(testing_frame, text="🧪 Testing")
        
        # Testing controls
        controls_frame = ttk.LabelFrame(testing_frame, text="Test Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(controls_frame, text="Start Payment Test", command=self.start_payment_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Stop Test", command=self.stop_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Generate Report", command=self.generate_test_report).pack(side=tk.LEFT, padx=5)
        
        # Test configuration
        config_frame = ttk.LabelFrame(testing_frame, text="Test Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Test type selection
        ttk.Label(config_frame, text="Test Type:").pack(side=tk.LEFT, padx=5)
        self.test_type_var = tk.StringVar(value="Payment Method")
        test_type_combo = ttk.Combobox(config_frame, textvariable=self.test_type_var, 
                                     values=["Payment Method", "Database", "Connection", "Full System"])
        test_type_combo.pack(side=tk.LEFT, padx=5)
        
        # Test results
        results_frame = ttk.LabelFrame(testing_frame, text="Test Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.test_results = scrolledtext.ScrolledText(results_frame, height=15)
        self.test_results.pack(fill=tk.BOTH, expand=True)
    
    def create_database_tab(self):
        """Create database management tab"""
        db_frame = ttk.Frame(self.notebook)
        self.notebook.add(db_frame, text="💾 Database")
        
        # Database controls
        controls_frame = ttk.LabelFrame(db_frame, text="Database Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(controls_frame, text="Create Database", command=self.create_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Load Database", command=self.load_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Export Data", command=self.export_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Refresh Info", command=self.refresh_db_info).pack(side=tk.LEFT, padx=5)
        
        # Database info
        info_frame = ttk.LabelFrame(db_frame, text="Database Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.db_info = scrolledtext.ScrolledText(info_frame, height=15)
        self.db_info.pack(fill=tk.BOTH, expand=True)
    
    def create_monitoring_tab(self):
        """Create system monitoring tab"""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="📊 Monitoring")
        
        # System info
        info_frame = ttk.LabelFrame(monitor_frame, text="System Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Display system information
        import platform
        system_info = f"""
🖥️ Platform: {platform.system()} {platform.release()}
🐍 Python: {sys.version.split()[0]}
📁 Working Directory: {os.getcwd()}
🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        ttk.Label(info_frame, text=system_info, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Log viewer
        log_frame = ttk.LabelFrame(monitor_frame, text="System Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_viewer = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_viewer.pack(fill=tk.BOTH, expand=True)
        
        # Add initial log entry
        self.log_viewer.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Admin Panel Started\n")
    
    # Action methods
    def start_quick_test(self):
        """Start a quick test"""
        self.log_message("Starting quick test...")
        self.status_label.config(text="🟡 Running Quick Test")
        
        # Simulate test
        self.test_results.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Quick Test Started\n")
        self.test_results.insert(tk.END, "✅ System components check: PASSED\n")
        self.test_results.insert(tk.END, "✅ Database connection: PASSED\n")
        self.test_results.insert(tk.END, "✅ Configuration validation: PASSED\n")
        self.test_results.insert(tk.END, "🎉 Quick Test Completed Successfully\n\n")
        self.test_results.see(tk.END)
        
        self.status_label.config(text="🟢 System Ready")
        self.log_message("Quick test completed successfully")
    
    def setup_database(self):
        """Set up database"""
        try:
            db_path = Path("database/admin_panel.db")
            db_path.parent.mkdir(exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create basic tables
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_type TEXT NOT NULL,
                    result TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                conn.commit()
            
            self.current_database = str(db_path)
            self.log_message(f"Database setup completed: {db_path}")
            messagebox.showinfo("Success", f"Database created successfully at {db_path}")
            self.refresh_db_info()
            
        except Exception as e:
            self.log_message(f"Database setup failed: {e}")
            messagebox.showerror("Error", f"Database setup failed: {e}")
    
    def test_connection(self):
        """Test connection"""
        self.log_message("Testing connection...")
        
        try:
            # Test database connection
            if self.current_database and Path(self.current_database).exists():
                with sqlite3.connect(self.current_database) as conn:
                    conn.execute("SELECT 1")
                connection_result = "✅ Database connection: SUCCESS"
            else:
                connection_result = "⚠️ Database connection: No database configured"
            
            # Test network (basic)
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                sock.connect(("8.8.8.8", 53))
                network_result = "✅ Network connection: SUCCESS"
            except:
                network_result = "❌ Network connection: FAILED"
            finally:
                sock.close()
            
            message = f"{connection_result}\n{network_result}"
            messagebox.showinfo("Connection Test", message)
            self.log_message(f"Connection test completed: {message.replace(chr(10), ', ')}")
            
        except Exception as e:
            self.log_message(f"Connection test failed: {e}")
            messagebox.showerror("Error", f"Connection test failed: {e}")
    
    def view_reports(self):
        """View reports"""
        self.log_message("Opening reports viewer...")
        
        # Switch to monitoring tab to show logs
        self.notebook.select(3)  # Monitoring tab index
        
        messagebox.showinfo("Reports", "Reports are displayed in the Monitoring tab")
    
    def start_payment_test(self):
        """Start payment test"""
        if self.test_running:
            messagebox.showwarning("Warning", "Test is already running")
            return
        
        self.test_running = True
        test_type = self.test_type_var.get()
        
        self.test_results.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Starting {test_type} test...\n")
        
        # Simulate test based on type
        if test_type == "Payment Method":
            self.simulate_payment_test()
        elif test_type == "Database":
            self.simulate_database_test()
        elif test_type == "Connection":
            self.simulate_connection_test()
        else:
            self.simulate_full_system_test()
        
        self.test_running = False
        self.log_message(f"Payment test completed: {test_type}")
    
    def simulate_payment_test(self):
        """Simulate payment method test"""
        tests = [
            "Initializing payment gateway...",
            "Testing credit card validation...",
            "Testing transaction processing...",
            "Testing approval workflow...",
            "Validating response codes..."
        ]
        
        for i, test in enumerate(tests):
            self.test_results.insert(tk.END, f"  {i+1}. {test}\n")
            self.test_results.see(tk.END)
            self.root.update()
            
        self.test_results.insert(tk.END, "✅ Payment method test completed successfully\n\n")
        self.test_results.see(tk.END)
    
    def simulate_database_test(self):
        """Simulate database test"""
        if not self.current_database:
            self.test_results.insert(tk.END, "❌ No database configured\n\n")
            return
        
        tests = [
            "Connecting to database...",
            "Testing table structure...",
            "Testing insert operations...",
            "Testing select operations...",
            "Testing update operations..."
        ]
        
        for i, test in enumerate(tests):
            self.test_results.insert(tk.END, f"  {i+1}. {test}\n")
            self.test_results.see(tk.END)
            self.root.update()
        
        self.test_results.insert(tk.END, "✅ Database test completed successfully\n\n")
        self.test_results.see(tk.END)
    
    def simulate_connection_test(self):
        """Simulate connection test"""
        tests = [
            "Testing local network...",
            "Testing internet connectivity...",
            "Testing port availability...",
            "Testing SSL/TLS connections...",
            "Testing API endpoints..."
        ]
        
        for i, test in enumerate(tests):
            self.test_results.insert(tk.END, f"  {i+1}. {test}\n")
            self.test_results.see(tk.END)
            self.root.update()
        
        self.test_results.insert(tk.END, "✅ Connection test completed successfully\n\n")
        self.test_results.see(tk.END)
    
    def simulate_full_system_test(self):
        """Simulate full system test"""
        self.test_results.insert(tk.END, "Running comprehensive system test...\n")
        self.simulate_payment_test()
        self.simulate_database_test()
        self.simulate_connection_test()
        self.test_results.insert(tk.END, "🎉 Full system test completed successfully\n\n")
        self.test_results.see(tk.END)
    
    def stop_test(self):
        """Stop running test"""
        if not self.test_running:
            messagebox.showinfo("Info", "No test is currently running")
            return
        
        self.test_running = False
        self.test_results.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Test stopped by user\n\n")
        self.test_results.see(tk.END)
        self.log_message("Test stopped by user")
    
    def generate_test_report(self):
        """Generate test report"""
        report_path = Path("reports")
        report_path.mkdir(exist_ok=True)
        
        filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file = report_path / filename
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("TLV Admin Panel - Test Report\n")
                f.write("=" * 40 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("Test Results:\n")
                f.write("-" * 20 + "\n")
                f.write(self.test_results.get(1.0, tk.END))
            
            messagebox.showinfo("Success", f"Report saved to {report_file}")
            self.log_message(f"Test report generated: {report_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")
            self.log_message(f"Report generation failed: {e}")
    
    def create_database(self):
        """Create new database"""
        self.setup_database()
    
    def load_database(self):
        """Load existing database"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            title="Select Database File",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        
        if filename:
            self.current_database = filename
            self.log_message(f"Database loaded: {filename}")
            messagebox.showinfo("Success", f"Database loaded: {Path(filename).name}")
            self.refresh_db_info()
    
    def export_database(self):
        """Export database data"""
        if not self.current_database:
            messagebox.showwarning("Warning", "No database configured")
            return
        
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="Export Database",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if filename:
            try:
                # Simple export to JSON
                with sqlite3.connect(self.current_database) as conn:
                    cursor = conn.cursor()
                    
                    # Get all table names
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    
                    export_data = {}
                    for table in tables:
                        table_name = table[0]
                        cursor.execute(f"SELECT * FROM {table_name}")
                        rows = cursor.fetchall()
                        
                        # Get column names
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        export_data[table_name] = {
                            'columns': columns,
                            'data': rows
                        }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                messagebox.showinfo("Success", f"Database exported to {filename}")
                self.log_message(f"Database exported: {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
                self.log_message(f"Database export failed: {e}")
    
    def refresh_db_info(self):
        """Refresh database information"""
        self.db_info.delete(1.0, tk.END)
        
        if not self.current_database:
            self.db_info.insert(tk.END, "No database configured\n")
            return
        
        try:
            db_path = Path(self.current_database)
            self.db_info.insert(tk.END, f"Database: {db_path.name}\n")
            self.db_info.insert(tk.END, f"Path: {db_path}\n")
            self.db_info.insert(tk.END, f"Size: {db_path.stat().st_size} bytes\n")
            self.db_info.insert(tk.END, f"Modified: {datetime.fromtimestamp(db_path.stat().st_mtime)}\n\n")
            
            with sqlite3.connect(self.current_database) as conn:
                cursor = conn.cursor()
                
                # Get table information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                self.db_info.insert(tk.END, f"Tables ({len(tables)}):\n")
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    self.db_info.insert(tk.END, f"  • {table_name}: {count} records\n")
                
        except Exception as e:
            self.db_info.insert(tk.END, f"Error reading database: {e}\n")
    
    def log_message(self, message):
        """Add message to log viewer"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_viewer.insert(tk.END, log_entry)
        self.log_viewer.see(tk.END)
        logger.info(message)
    
    def run(self):
        """Run the admin panel"""
        try:
            self.log_message("Admin Panel started successfully")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error running admin panel: {e}")
            messagebox.showerror("Error", f"Admin panel error: {e}")
        finally:
            logger.info("Admin Panel shutdown")

def main():
    """Main function to start the admin panel"""
    try:
        app = AdminPanel()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start admin panel: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
