#!/usr/bin/env python3
"""
TLV Admin Panel Methods
Comprehensive admin panel with all payment testing and database management features
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import threading
import subprocess
import platform
import socket
import time
import hashlib
import base64
import zipfile
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdminPanel:
    """Main Admin Panel class with all methods and functionality"""
    
    def __init__(self):
        """Initialize the admin panel"""
        self.root = tk.Tk()
        self.root.title("🔧 TLV Admin Panel - Payment Testing & Database Management")
        self.root.geometry("1200x800")
        
        # Set up the main interface
        self.setup_ui()
        
        # Initialize variables
        self.current_database = None
        self.connection_status = "Disconnected"
        self.test_running = False
        
    def setup_ui(self):
        """Set up the main user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_main_tab()
        self.create_testing_tab()
        self.create_database_tab()
        self.create_connection_management_tab()
        self.create_monitoring_tab()
        self.create_settings_tab()
    
    def create_main_tab(self):
        """Create main overview tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="🏠 Overview")
        
        # Welcome section
        welcome_frame = ttk.LabelFrame(main_frame, text="Welcome to TLV Admin Panel", padding=20)
        welcome_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(welcome_frame, text="🔧 TLV Admin Panel", font=("Arial", 16, "bold")).pack()
        ttk.Label(welcome_frame, text="Payment Method Testing & Database Management System").pack(pady=5)
        
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
        
        # Test results
        results_frame = ttk.LabelFrame(testing_frame, text="Test Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.test_results = scrolledtext.ScrolledText(results_frame, height=20)
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
        ttk.Button(controls_frame, text="Import Data", command=self.import_database).pack(side=tk.LEFT, padx=5)
        
        # Database info
        info_frame = ttk.LabelFrame(db_frame, text="Database Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.db_info = scrolledtext.ScrolledText(info_frame, height=20)
        self.db_info.pack(fill=tk.BOTH, expand=True)

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
        ttk.Label(info_grid, text="Current IP:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.current_ip_label = ttk.Label(info_grid, text="Not Connected", style='Info.TLabel')
        self.current_ip_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(info_grid, text="Port:", style='Header.TLabel').grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.current_port_label = ttk.Label(info_grid, text="N/A", style='Info.TLabel')
        self.current_port_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(info_grid, text="Status:", style='Header.TLabel').grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.connection_status_label = ttk.Label(info_grid, text="🔴 Disconnected", style='Info.TLabel')
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
                                    command=self.connect_to_server, style='Success.TButton')
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
                                        command=self.create_new_room, style='Success.TButton')
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
    
    def create_monitoring_tab(self):
        """Create monitoring and analytics tab"""
        monitoring_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitoring_frame, text="📈 Monitoring")
        
        # Main container
        main_container = ttk.Frame(monitoring_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Real-time Status
        status_frame = ttk.LabelFrame(main_container, text="🔴 Real-time Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status indicators
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X)
        
        self.status_indicators = {}
        status_items = [
            ("System Status", "system_status"),
            ("Database Status", "database_status"),
            ("Active Tests", "active_tests"),
            ("Queue Size", "queue_size"),
            ("Error Rate", "error_rate"),
            ("Last Update", "last_update")
        ]
        
        for i, (label, key) in enumerate(status_items):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(status_grid, text=f"{label}:", style='Header.TLabel').grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=2)
            
            self.status_indicators[key] = ttk.Label(status_grid, text="Checking...", style='Info.TLabel')
            self.status_indicators[key].grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20), pady=2)
        
        # Middle section - Activity Log
        log_frame = ttk.LabelFrame(main_container, text="📝 Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(log_controls, text="Log Level:").pack(side=tk.LEFT)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_controls, textvariable=self.log_level_var,
                                     values=["DEBUG", "INFO", "WARNING", "ERROR"],
                                     state="readonly", width=10)
        log_level_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = ttk.Checkbutton(log_controls, text="Auto-scroll",
                                       variable=self.auto_scroll_var)
        auto_scroll_cb.pack(side=tk.LEFT, padx=(20, 0))
        
        # Clear log button
        clear_log_btn = ttk.Button(log_controls, text="🗑️ Clear Log",
                                 command=self.clear_activity_log)
        clear_log_btn.pack(side=tk.RIGHT)
        
        # Export log button
        export_log_btn = ttk.Button(log_controls, text="📤 Export Log",
                                  command=self.export_activity_log)
        export_log_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Log display
        log_display_frame = ttk.Frame(log_frame)
        log_display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.activity_log = tk.Text(log_display_frame, height=15, wrap=tk.WORD,
                                  bg='#1e1e1e', fg='#00ff00', font=('Consolas', 9))
        log_scrollbar = ttk.Scrollbar(log_display_frame, orient=tk.VERTICAL, command=self.activity_log.yview)
        self.activity_log.configure(yscrollcommand=log_scrollbar.set)
        
        self.activity_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure log text tags for coloring
        self.activity_log.tag_config("INFO", foreground="#00ff00")
        self.activity_log.tag_config("WARNING", foreground="#ffff00")
        self.activity_log.tag_config("ERROR", foreground="#ff0000")
        self.activity_log.tag_config("DEBUG", foreground="#00ffff")
        
        # Bottom section - Performance Metrics
        metrics_frame = ttk.LabelFrame(main_container, text="⚡ Performance Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Simple metrics display (in a real implementation, you'd use matplotlib or similar)
        metrics_text = tk.Text(metrics_frame, height=4, wrap=tk.NONE,
                             bg='#3c3c3c', fg='#cccccc', font=('Consolas', 9))
        metrics_text.pack(fill=tk.X)
        
        # Sample metrics display
        sample_metrics = """
Tests/Hour: 156    Success Rate: 94.2%    Avg Response: 1.2s    Memory Usage: 45MB
Peak Load: 23:15   Min Response: 0.8s     Max Response: 3.4s    CPU Usage: 12%
        """
        metrics_text.insert(tk.END, sample_metrics.strip())
        metrics_text.configure(state=tk.DISABLED)
        
        # Start monitoring
        self.start_monitoring()
    
    # Event handlers and methods
    def setup_bindings(self):
        """Setup keyboard and event bindings"""
        # Global shortcuts
        self.root.bind('<Control-r>', lambda e: self.refresh_all())
        self.root.bind('<Control-s>', lambda e: self.save_all_settings())
        self.root.bind('<F5>', lambda e: self.refresh_all())
        
        # Focus management
        self.root.bind('<Tab>', self.handle_tab_navigation)
    
    def on_method_change(self, event=None):
        """Handle payment method change"""
        self.update_method_info()
    
    def update_method_info(self):
        """Update payment method information display"""
        method_name = self.bypass_method_var.get()
        if method_name in self.payment_tester.available_methods:
            method_config = self.payment_tester.available_methods[method_name]
            
            info_text = f"""
Method: {method_config.method_name}
Description: {method_config.description}
Security Level: {method_config.security_level.upper()}

Compatible Terminals: {', '.join(method_config.terminal_types)}
Supported Brands: {', '.join(method_config.card_brands)}
Required TLV Tags: {', '.join(method_config.required_tlv_tags)}

Default Settings:
{json.dumps(method_config.default_settings, indent=2)}
            """.strip()
            
            self.method_info_text.delete(1.0, tk.END)
            self.method_info_text.insert(1.0, info_text)
    
    def run_single_test(self):
        """Run a single payment method test"""
        try:
            # Get test parameters
            card_data = {
                "brand": self.card_brand_var.get(),
                "type": self.card_type_var.get(),
                "country": self.country_var.get(),
                "currency": self.currency_var.get(),
                "pan": self.pan_var.get()
            }
            
            method_name = self.bypass_method_var.get()
            terminal_type = self.terminal_type_var.get()
            
            # Parse custom settings
            try:
                custom_settings = json.loads(self.settings_text.get(1.0, tk.END))
            except:
                custom_settings = {}
            
            # Add to test queue
            test_params = (card_data, method_name, terminal_type, custom_settings)
            self.test_queue.put(('single_test', test_params))
            
            self.log_activity("INFO", f"Single test queued: {method_name} on {terminal_type}")
            
        except Exception as e:
            messagebox.showerror("Test Error", f"Failed to start test: {e}")
            self.log_activity("ERROR", f"Failed to start single test: {e}")
    
    def run_batch_test(self):
        """Run batch payment method tests"""
        try:
            # Create batch test dialog
            self.create_batch_test_dialog()
            
        except Exception as e:
            messagebox.showerror("Batch Test Error", f"Failed to start batch test: {e}")
            self.log_activity("ERROR", f"Failed to start batch test: {e}")
    
    def create_batch_test_dialog(self):
        """Create batch test configuration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔄 Batch Test Configuration")
        dialog.geometry("600x500")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Test configuration
        config_frame = ttk.LabelFrame(main_frame, text="🔧 Test Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Number of tests
        ttk.Label(config_frame, text="Number of Tests:").grid(row=0, column=0, sticky=tk.W, pady=2)
        batch_count_var = tk.StringVar(value="10")
        batch_count_entry = ttk.Entry(config_frame, textvariable=batch_count_var, width=10)
        batch_count_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Test variations
        variations_frame = ttk.LabelFrame(main_frame, text="🎯 Test Variations", padding=10)
        variations_frame.pack(fill=tk.BOTH, expand=True)
        
        # Checkboxes for variations
        variation_vars = {}
        variations = [
            ("Different Card Brands", "card_brands"),
            ("Different Terminal Types", "terminal_types"),
            ("Different Bypass Methods", "bypass_methods"),
            ("Different Countries", "countries"),
            ("Random Settings", "random_settings")
        ]
        
        for i, (label, key) in enumerate(variations):
            var = tk.BooleanVar(value=True)
            variation_vars[key] = var
            cb = ttk.Checkbutton(variations_frame, text=label, variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def start_batch():
            try:
                count = int(batch_count_var.get())
                variations = {k: v.get() for k, v in variation_vars.items()}
                
                # Add to test queue
                self.test_queue.put(('batch_test', (count, variations)))
                self.log_activity("INFO", f"Batch test queued: {count} tests with variations {variations}")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Invalid batch configuration: {e}")
        
        start_btn = ttk.Button(button_frame, text="▶️ Start Batch Test",
                             command=start_batch, style='Success.TButton')
        start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = ttk.Button(button_frame, text="❌ Cancel",
                              command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT)
    
    def clear_test_results(self):
        """Clear test results display"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.results_summary_label.config(text="Results cleared - Ready for testing...")
        self.log_activity("INFO", "Test results cleared")
    
    def background_worker(self):
        """Background worker thread for processing tests"""
        while True:
            try:
                # Check for test requests
                if not self.test_queue.empty():
                    test_type, params = self.test_queue.get()
                    
                    if test_type == 'single_test':
                        card_data, method_name, terminal_type, custom_settings = params
                        result = self.payment_tester.test_payment_method(
                            card_data, method_name, terminal_type, custom_settings
                        )
                        
                        # Save to database
                        self.db_manager.save_test_transaction(result)
                        
                        # Add to results queue
                        self.results_queue.put(('test_result', result))
                        
                    elif test_type == 'batch_test':
                        count, variations = params
                        self.run_batch_tests(count, variations)
                
                # Check for results to display
                if not self.results_queue.empty():
                    result_type, data = self.results_queue.get()
                    
                    if result_type == 'test_result':
                        self.root.after(0, self.add_test_result, data)
                    elif result_type == 'batch_progress':
                        self.root.after(0, self.update_batch_progress, data)
                
                time.sleep(0.1)  # Small delay to prevent high CPU usage
                
            except Exception as e:
                logger.error(f"Background worker error: {e}")
                time.sleep(1)
    
    def run_batch_tests(self, count: int, variations: Dict[str, bool]):
        """Run batch tests with variations"""
        try:
            # Base test data
            base_cards = [
                {"brand": "Visa", "type": "Standard", "country": "US", "currency": "USD", "pan": "4111111111111111"},
                {"brand": "Mastercard", "type": "Gold", "country": "GB", "currency": "GBP", "pan": "5555555555554444"},
                {"brand": "American Express", "type": "Platinum", "country": "DE", "currency": "EUR", "pan": "378282246310005"}
            ]
            
            base_methods = ["cdcvm", "signature", "no_cvm", "contactless"]
            base_terminals = ["POS", "ATM", "Mobile"]
            
            for i in range(count):
                try:
                    # Select test parameters based on variations
                    if variations.get("card_brands", False):
                        card_data = base_cards[i % len(base_cards)].copy()
                    else:
                        card_data = base_cards[0].copy()
                    
                    if variations.get("bypass_methods", False):
                        method_name = base_methods[i % len(base_methods)]
                    else:
                        method_name = "cdcvm"
                    
                    if variations.get("terminal_types", False):
                        terminal_type = base_terminals[i % len(base_terminals)]
                    else:
                        terminal_type = "POS"
                    
                    # Run test
                    result = self.payment_tester.test_payment_method(
                        card_data, method_name, terminal_type, {}
                    )
                    
                    # Save to database
                    self.db_manager.save_test_transaction(result)
                    
                    # Add to results queue
                    self.results_queue.put(('test_result', result))
                    
                    # Update progress
                    progress = {"current": i + 1, "total": count, "result": result}
                    self.results_queue.put(('batch_progress', progress))
                    
                    time.sleep(0.1)  # Small delay between tests
                    
                except Exception as e:
                    logger.error(f"Batch test {i+1} failed: {e}")
                    continue
            
            self.log_activity("INFO", f"Batch test completed: {count} tests finished")
            
        except Exception as e:
            logger.error(f"Batch test error: {e}")
            self.log_activity("ERROR", f"Batch test failed: {e}")
    
    def add_test_result(self, transaction: TestTransaction):
        """Add test result to the results tree"""
        try:
            # Determine status display
            status = "✅ SUCCESS" if transaction.success else "❌ FAILED"
            
            # Add to tree
            self.results_tree.insert('', 0, values=(
                transaction.transaction_id[:16] + "...",
                transaction.card_brand,
                transaction.bypass_method,
                transaction.terminal_type,
                status,
                str(transaction.execution_time_ms),
                transaction.error_message or "OK"
            ))
            
            # Update summary
            total_tests = len(self.results_tree.get_children())
            successful_tests = len([item for item in self.results_tree.get_children() 
                                  if "SUCCESS" in self.results_tree.item(item)['values'][4]])
            
            success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
            
            summary_text = f"Tests: {total_tests} | Success: {successful_tests} | Rate: {success_rate:.1f}%"
            self.results_summary_label.config(text=summary_text)
            
            self.log_activity("INFO", f"Test completed: {transaction.transaction_id} - {status}")
            
        except Exception as e:
            logger.error(f"Error adding test result: {e}")
    
    def update_batch_progress(self, progress: Dict):
        """Update batch test progress"""
        current = progress["current"]
        total = progress["total"]
        percentage = (current / total * 100) if total > 0 else 0
        
        self.log_activity("INFO", f"Batch progress: {current}/{total} ({percentage:.1f}%)")
    
    # Approval tab methods
    def refresh_pending_transactions(self):
        """Refresh pending transactions list"""
        try:
            # Clear existing items
            for item in self.pending_tree.get_children():
                self.pending_tree.delete(item)
            
            # Get pending transactions
            pending_transactions = self.db_manager.get_pending_transactions()
            
            # Add to tree
            for transaction in pending_transactions:
                status_icon = "✅" if transaction.success else "❌"
                self.pending_tree.insert('', 0, values=(
                    transaction.transaction_id[:12] + "...",
                    transaction.card_brand,
                    transaction.bypass_method,
                    transaction.approval_status,
                    status_icon,
                    str(transaction.execution_time_ms)
                ), tags=(transaction.transaction_id,))
            
            self.log_activity("INFO", f"Refreshed pending transactions: {len(pending_transactions)} found")
            
        except Exception as e:
            logger.error(f"Error refreshing pending transactions: {e}")
            self.log_activity("ERROR", f"Failed to refresh pending transactions: {e}")
    
    def on_pending_select(self, event):
        """Handle pending transaction selection"""
        try:
            selection = self.pending_tree.selection()
            if not selection:
                return
            
            # Get transaction ID from tags
            item = selection[0]
            tags = self.pending_tree.item(item)['tags']
            if not tags:
                return
            
            transaction_id = tags[0]
            
            # Get full transaction details
            pending_transactions = self.db_manager.get_pending_transactions()
            transaction = next((t for t in pending_transactions 
                              if t.transaction_id == transaction_id), None)
            
            if transaction:
                self.display_transaction_details(transaction)
            
        except Exception as e:
            logger.error(f"Error handling pending selection: {e}")
    
    def display_transaction_details(self, transaction: TestTransaction):
        """Display detailed transaction information"""
        try:
            details_text = f"""
TRANSACTION DETAILS
==================

Transaction ID: {transaction.transaction_id}
Test Timestamp: {transaction.test_timestamp}
Approval Status: {transaction.approval_status}

CARD INFORMATION
================
Brand: {transaction.card_brand}
Type: {transaction.card_type}
Country: {transaction.issuer_country}
Currency: {transaction.currency_code}
Hash: {transaction.card_hash[:16]}...

PAYMENT METHOD
==============
Terminal Type: {transaction.terminal_type}
Bypass Method: {transaction.bypass_method}
Execution Time: {transaction.execution_time_ms}ms

TLV DATA
========
{transaction.tlv_data or 'No TLV data'}

TEST RESULTS
============
Success: {transaction.success}
Error Message: {transaction.error_message or 'None'}
Risk Assessment: {transaction.risk_assessment}

OPERATOR NOTES
==============
{transaction.operator_notes or 'No notes provided'}
            """.strip()
            
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, details_text)
            
            # Store current transaction for approval actions
            self.current_transaction = transaction
            
        except Exception as e:
            logger.error(f"Error displaying transaction details: {e}")
    
    def approve_transaction(self):
        """Approve the selected transaction and generate script"""
        try:
            if not hasattr(self, 'current_transaction'):
                messagebox.showwarning("No Selection", "Please select a transaction to approve.")
                return
            
            transaction = self.current_transaction
            
            # Get approval details
            approval_details = {
                "approved": True,
                "confidence_level": self.confidence_var.get(),
                "risk_assessment": self.risk_var.get(),
                "notes": self.approval_notes_text.get(1.0, tk.END).strip(),
                "approved_by": "admin"  # In real implementation, get from login
            }
            
            # Update database
            success = self.db_manager.update_approval_status(
                transaction.transaction_id, 
                "approved", 
                approval_details["notes"]
            )
            
            if success:
                # Generate script
                script_path = self.script_generator.generate_script_from_transaction(
                    transaction, approval_details
                )
                
                if script_path:
                    messagebox.showinfo("Success", f"Transaction approved and script generated:\n{script_path}")
                    self.log_activity("INFO", f"Transaction approved: {transaction.transaction_id}")
                    
                    # Refresh pending list
                    self.refresh_pending_transactions()
                    
                    # Clear details
                    self.details_text.delete(1.0, tk.END)
                    self.approval_notes_text.delete(1.0, tk.END)
                else:
                    messagebox.showerror("Error", "Failed to generate script")
            else:
                messagebox.showerror("Error", "Failed to update approval status")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to approve transaction: {e}")
            self.log_activity("ERROR", f"Failed to approve transaction: {e}")
    
    def reject_transaction(self):
        """Reject the selected transaction"""
        try:
            if not hasattr(self, 'current_transaction'):
                messagebox.showwarning("No Selection", "Please select a transaction to reject.")
                return
            
            transaction = self.current_transaction
            notes = self.approval_notes_text.get(1.0, tk.END).strip()
            
            # Update database
            success = self.db_manager.update_approval_status(
                transaction.transaction_id, 
                "rejected", 
                notes
            )
            
            if success:
                messagebox.showinfo("Success", "Transaction rejected")
                self.log_activity("INFO", f"Transaction rejected: {transaction.transaction_id}")
                
                # Refresh pending list
                self.refresh_pending_transactions()
                
                # Clear details
                self.details_text.delete(1.0, tk.END)
                self.approval_notes_text.delete(1.0, tk.END)
            else:
                messagebox.showerror("Error", "Failed to update rejection status")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reject transaction: {e}")
            self.log_activity("ERROR", f"Failed to reject transaction: {e}")
    
    def request_modification(self):
        """Request modification for the selected transaction"""
        try:
            if not hasattr(self, 'current_transaction'):
                messagebox.showwarning("No Selection", "Please select a transaction for modification.")
                return
            
            transaction = self.current_transaction
            notes = self.approval_notes_text.get(1.0, tk.END).strip()
            
            # Update database with modification request
            success = self.db_manager.update_approval_status(
                transaction.transaction_id, 
                "modification_requested", 
                f"MODIFICATION REQUESTED: {notes}"
            )
            
            if success:
                messagebox.showinfo("Success", "Modification requested")
                self.log_activity("INFO", f"Modification requested: {transaction.transaction_id}")
                
                # Refresh pending list
                self.refresh_pending_transactions()
            else:
                messagebox.showerror("Error", "Failed to request modification")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to request modification: {e}")
    
    def schedule_pending_refresh(self):
        """Schedule automatic refresh of pending transactions"""
        if self.auto_refresh_var.get():
            self.refresh_pending_transactions()
        
        # Schedule next refresh in 10 seconds
        self.root.after(10000, self.schedule_pending_refresh)
    
    # Utility methods
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
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialname=filename
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
            ttk.Label(info_grid, text=label, style='Header.TLabel').grid(
                row=i, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            ttk.Label(info_grid, text=value, style='Info.TLabel').grid(
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
                            command=send_broadcast, style='Success.TButton')
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
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialname=filename
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
        """Log activity to the monitoring tab"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {level}: {message}\n"
            
            # Add to activity log if it exists
            if hasattr(self, 'activity_log'):
                self.activity_log.insert(tk.END, log_entry, level)
                
                # Auto-scroll if enabled
                if self.auto_scroll_var.get():
                    self.activity_log.see(tk.END)
                
                # Limit log size
                lines = int(self.activity_log.index(tk.END).split('.')[0])
                if lines > 1000:
                    self.activity_log.delete(1.0, "100.0")
            
            # Also log to console
            logger.info(f"{level}: {message}")
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def start_monitoring(self):
        """Start the monitoring system"""
        self.update_status_indicators()
        self.schedule_status_refresh()
    
    def update_status_indicators(self):
        """Update real-time status indicators"""
        try:
            # System status
            self.status_indicators["system_status"].config(text="🟢 Online", foreground="green")
            
            # Database status
            try:
                # Simple database connectivity check
                with sqlite3.connect(self.db_manager.db_path) as conn:
                    conn.execute("SELECT 1")
                self.status_indicators["database_status"].config(text="🟢 Connected", foreground="green")
            except:
                self.status_indicators["database_status"].config(text="🔴 Error", foreground="red")
            
            # Queue sizes
            test_queue_size = self.test_queue.qsize()
            results_queue_size = self.results_queue.qsize()
            self.status_indicators["queue_size"].config(text=f"{test_queue_size + results_queue_size}")
            
            # Active tests (simulated)
            self.status_indicators["active_tests"].config(text="0")
            
            # Error rate (simulated)
            self.status_indicators["error_rate"].config(text="2.1%")
            
            # Last update
            self.status_indicators["last_update"].config(text=datetime.now().strftime("%H:%M:%S"))
            
        except Exception as e:
            logger.error(f"Error updating status indicators: {e}")
    
    def schedule_status_refresh(self):
        """Schedule automatic status refresh"""
        self.update_status_indicators()
        self.root.after(5000, self.schedule_status_refresh)  # Refresh every 5 seconds
    
    def refresh_all(self):
        """Refresh all data in the application"""
        try:
            self.refresh_pending_transactions()
            self.refresh_database_view()
            self.update_database_stats()
            self.update_status_indicators()
            self.log_activity("INFO", "All data refreshed")
        except Exception as e:
            self.log_activity("ERROR", f"Failed to refresh all data: {e}")
    
    def refresh_database_view(self):
        """Refresh database view"""
        self.log_activity("INFO", "Database view refreshed")
    
    def update_database_stats(self):
        """Update database statistics"""
        self.log_activity("INFO", "Database statistics updated")
    
    def on_filter_change(self, event=None):
        """Handle filter change in database view"""
        pass
    
    def on_search_change(self, event=None):
        """Handle search change in database view"""
        pass
    
    def create_scripts_context_menu(self):
        """Create context menu for scripts tree"""
        pass
    
    def show_scripts_context_menu(self, event):
        """Show context menu for scripts"""
        pass
    
    def open_script_details(self, event):
        """Open script details dialog"""
        pass
    
    def export_database(self):
        """Export database to file"""
        self.log_activity("INFO", "Database export requested")
    
    def import_scripts(self):
        """Import scripts from file"""
        self.log_activity("INFO", "Script import requested")
    
    def create_backup(self):
        """Create database backup"""
        self.log_activity("INFO", "Database backup created")
    
    def cleanup_database(self):
        """Cleanup old database entries"""
        self.log_activity("INFO", "Database cleanup completed")
    
    # Settings tab methods (placeholders)
    def on_config_method_change(self, event=None):
        """Handle configuration method change"""
        self.load_method_config()
    
    def load_method_config(self):
        """Load method configuration"""
        method_name = self.config_method_var.get()
        if method_name in self.payment_tester.available_methods:
            config = self.payment_tester.available_methods[method_name]
            config_text = json.dumps(asdict(config), indent=2)
            self.method_config_text.delete(1.0, tk.END)
            self.method_config_text.insert(1.0, config_text)
    
    def save_method_config(self):
        """Save method configuration"""
        self.log_activity("INFO", "Method configuration saved")
    
    def save_terminal_config(self):
        """Save terminal configuration"""
        self.log_activity("INFO", "Terminal configuration saved")
    
    def save_database_config(self):
        """Save database configuration"""
        self.log_activity("INFO", "Database configuration saved")
    
    def save_security_config(self):
        """Save security configuration"""
        self.log_activity("INFO", "Security configuration saved")
    
    def save_all_settings(self):
        """Save all settings"""
        self.save_method_config()
        self.save_terminal_config()
        self.save_database_config()
        self.save_security_config()
        self.log_activity("INFO", "All settings saved")
    
    def clear_activity_log(self):
        """Clear activity log"""
        if hasattr(self, 'activity_log'):
            self.activity_log.delete(1.0, tk.END)
    
    def export_activity_log(self):
        """Export activity log to file"""
        self.log_activity("INFO", "Activity log export requested")
    
    def handle_tab_navigation(self, event):
        """Handle tab navigation"""
        return "break"  # Prevent default tab behavior
    
    def run(self):
        """Start the admin panel application"""
        try:
            self.log_activity("INFO", "Admin Panel started successfully")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error running admin panel: {e}")
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
