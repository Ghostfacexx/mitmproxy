#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TLV MASTER UNIFIED LAUNCHER
Ultimate all-in-one launcher for TLV Admin Panel & NFCGate Systems
Quick access to all panels, tools, and comprehensive credit card testing features
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import socket
import time
import platform
import webbrowser
import sqlite3
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path

# Add src to Python path for credit card structures
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import credit card structures
try:
    from credit_card_structures import CreditCardGenerator, CreditCardTypes, EMVTags
    CREDIT_CARD_SUPPORT = True
except ImportError:
    CREDIT_CARD_SUPPORT = False

class MasterUnifiedLauncher:
    """Master launcher for all TLV systems and panels"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("[TARGET] Master TLV Unified Launcher")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Center window
        self.center_window()
        
        # System state
        self.running_processes = []
        self.system_status = {}
        
        # Create GUI
        self.create_gui()
        
        # Initialize status
        self.update_system_status()
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 600
        y = (self.root.winfo_screenheight() // 2) - 400
        self.root.geometry(f"1200x800+{x}+{y}")
        
    def create_gui(self):
        """Create the master launcher GUI"""
        # Title section
        title_frame = tk.Frame(self.root, bg='#1a1a1a')
        title_frame.pack(fill=tk.X, pady=20)
        
        title_label = tk.Label(title_frame,
                              text="[TARGET] MASTER TLV UNIFIED LAUNCHER",
                              font=("Arial", 24, "bold"),
                              fg='#00ff00',
                              bg='#1a1a1a')
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                 text="Ultimate Control Center for Admin Panels, NFCGate & Payment Systems",
                                 font=("Arial", 12),
                                 fg='#cccccc',
                                 bg='#1a1a1a')
        subtitle_label.pack(pady=5)
        
        # Main content with notebook tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create tabs
        self.create_admin_panels_tab()
        self.create_nfcgate_systems_tab()
        self.create_credit_card_tab()
        self.create_testing_tools_tab()
        self.create_system_monitoring_tab()
        self.create_quick_actions_tab()
        
        # Status bar
        self.create_status_bar()
        
    def create_admin_panels_tab(self):
        """Create admin panels tab"""
        admin_frame = ttk.Frame(self.notebook)
        self.notebook.add(admin_frame, text="[ADMIN] Admin Panels")
        
        # Main container
        main_container = ttk.Frame(admin_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_container,
                              text="[ADMIN] Administration Control Panels",
                              font=("Arial", 16, "bold"),
                              fg='#004080')
        title_label.pack(pady=(0, 20))
        
        # Admin panels grid
        panels_frame = tk.Frame(main_container)
        panels_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel 1: Enhanced Admin Panel (GUI)
        panel1_frame = tk.Frame(panels_frame, bg='#e6f3ff', relief=tk.RAISED, bd=3)
        panel1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=20)
        
        tk.Label(panel1_frame, text="🖥️ ENHANCED ADMIN PANEL",
                font=("Arial", 14, "bold"), fg='#004080', bg='#e6f3ff').pack(pady=(0, 10))
        
        tk.Label(panel1_frame, text="• Complete GUI interface with tabs\n• Payment method testing\n• Transaction approval center\n• Database management\n• Connection management\n• Real-time monitoring",
                font=("Arial", 10), fg='#333333', bg='#e6f3ff', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(panel1_frame, text="[LAUNCH] Launch Enhanced Admin Panel",
                 font=("Arial", 11, "bold"), bg='#0066cc', fg='white',
                 padx=20, pady=8, command=self.launch_enhanced_admin_panel).pack(pady=5)
        
        tk.Button(panel1_frame, text="⚙️ Enhanced Launcher",
                 font=("Arial", 10), bg='#4d94ff', fg='white',
                 padx=15, pady=5, command=self.launch_enhanced_launcher).pack(pady=2)
        
        # Panel 2: Complete Admin Panel
        panel2_frame = tk.Frame(panels_frame, bg='#fff0e6', relief=tk.RAISED, bd=3)
        panel2_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=20)
        
        tk.Label(panel2_frame, text="📋 COMPLETE ADMIN PANEL",
                font=("Arial", 14, "bold"), fg='#cc6600', bg='#fff0e6').pack(pady=(0, 10))
        
        tk.Label(panel2_frame, text="• Command-line interface\n• Comprehensive testing suite\n• Database operations\n• Batch processing\n• Report generation\n• Console-based control",
                font=("Arial", 10), fg='#333333', bg='#fff0e6', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(panel2_frame, text="[LAUNCH] Launch Complete Panel",
                 font=("Arial", 11, "bold"), bg='#cc6600', fg='white',
                 padx=20, pady=8, command=self.launch_complete_admin_panel).pack(pady=5)
        
        tk.Button(panel2_frame, text="📋 Standard Launcher",
                 font=("Arial", 10), bg='#ff9933', fg='white',
                 padx=15, pady=5, command=self.launch_admin_launcher).pack(pady=2)
        
        # Panel 3: Online Admin Panel
        panel3_frame = tk.Frame(panels_frame, bg='#f0fff0', relief=tk.RAISED, bd=3)
        panel3_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=20)
        
        tk.Label(panel3_frame, text="🌐 ONLINE ADMIN PANEL",
                font=("Arial", 14, "bold"), fg='#006600', bg='#f0fff0').pack(pady=(0, 10))
        
        tk.Label(panel3_frame, text="• Web-based interface\n• Remote access capability\n• Real-time dashboard\n• Card analysis tools\n• Communication monitoring\n• Browser-based control",
                font=("Arial", 10), fg='#333333', bg='#f0fff0', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(panel3_frame, text="[LAUNCH] Launch Online Panel",
                 font=("Arial", 11, "bold"), bg='#00aa00', fg='white',
                 padx=20, pady=8, command=self.launch_online_admin_panel).pack(pady=5)
        
        tk.Button(panel3_frame, text="🌐 Demo Launcher",
                 font=("Arial", 10), bg='#33cc33', fg='white',
                 padx=15, pady=5, command=self.launch_demo_launcher).pack(pady=2)
        
        # Panel 4: Master Admin Controller
        panel4_frame = tk.Frame(panels_frame, bg='#ffe6f0', relief=tk.RAISED, bd=3)
        panel4_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=20)
        
        tk.Label(panel4_frame, text="🎛️ MASTER CONTROLLER",
                font=("Arial", 14, "bold"), fg='#800040', bg='#ffe6f0').pack(pady=(0, 10))
        
        tk.Label(panel4_frame, text="• Centralized system control\n• All-in-one management\n• Process coordination\n• System orchestration\n• Resource monitoring\n• Advanced automation",
                font=("Arial", 10), fg='#333333', bg='#ffe6f0', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(panel4_frame, text="[LAUNCH] Launch Master Controller",
                 font=("Arial", 11, "bold"), bg='#800040', fg='white',
                 padx=20, pady=8, command=self.launch_master_controller).pack(pady=5)
        
        tk.Button(panel4_frame, text="🎛️ Control Center",
                 font=("Arial", 10), bg='#cc6699', fg='white',
                 padx=15, pady=5, command=self.launch_integrated_control).pack(pady=2)
        
        # Configure grid weights
        panels_frame.grid_columnconfigure(0, weight=1)
        panels_frame.grid_columnconfigure(1, weight=1)
        panels_frame.grid_rowconfigure(0, weight=1)
        panels_frame.grid_rowconfigure(1, weight=1)
        
    def create_nfcgate_systems_tab(self):
        """Create NFCGate systems tab"""
        nfc_frame = ttk.Frame(self.notebook)
        self.notebook.add(nfc_frame, text="📱 NFCGate Systems")
        
        # Main container
        main_container = ttk.Frame(nfc_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_container,
                              text="📱 NFCGate Android APK Integration Systems",
                              font=("Arial", 16, "bold"),
                              fg='#800080')
        title_label.pack(pady=(0, 20))
        
        # Network info
        self.ip_address = self.get_local_ip()
        info_label = tk.Label(main_container,
                             text=f"📡 Your Computer IP: {self.ip_address} | Default NFCGate Port: 8080",
                             font=("Arial", 11), fg='#666666')
        info_label.pack(pady=(0, 20))
        
        # NFCGate systems grid
        nfc_systems_frame = tk.Frame(main_container)
        nfc_systems_frame.pack(fill=tk.BOTH, expand=True)
        
        # System 1: Fixed NFCGate System (Recommended)
        system1_frame = tk.Frame(nfc_systems_frame, bg='#e6ffe6', relief=tk.RAISED, bd=3)
        system1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=20)
        
        tk.Label(system1_frame, text="[FIXED] FIXED SYSTEM (Recommended)",
                font=("Arial", 14, "bold"), fg='#006600', bg='#e6ffe6').pack(pady=(0, 10))
        
        tk.Label(system1_frame, text="[OK] Error-free operation\n[OK] No spam logging\n[OK] Stable connectivity\n[OK] Proper error handling\n[OK] Controlled updates\n[OK] Production ready",
                font=("Arial", 10), fg='#333333', bg='#e6ffe6', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(system1_frame, text="[LAUNCH] Launch Fixed System",
                 font=("Arial", 11, "bold"), bg='#00aa00', fg='white',
                 padx=20, pady=8, command=self.launch_fixed_nfcgate).pack(pady=5)
        
        # System 2: Simple NFCGate Launcher
        system2_frame = tk.Frame(nfc_systems_frame, bg='#e6f0ff', relief=tk.RAISED, bd=3)
        system2_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=20)
        
        tk.Label(system2_frame, text="[TARGET] SIMPLE LAUNCHER",
                font=("Arial", 14, "bold"), fg='#0066cc', bg='#e6f0ff').pack(pady=(0, 10))
        
        tk.Label(system2_frame, text="• Basic NFCGate interface\n• Essential features only\n• Quick start option\n• Minimal configuration\n• Easy setup guide\n• Beginner friendly",
                font=("Arial", 10), fg='#333333', bg='#e6f0ff', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(system2_frame, text="[LAUNCH] Launch Simple System",
                 font=("Arial", 11, "bold"), bg='#0066cc', fg='white',
                 padx=20, pady=8, command=self.launch_simple_nfcgate).pack(pady=5)
        
        # System 3: Complete NFCGate Launcher
        system3_frame = tk.Frame(nfc_systems_frame, bg='#fff0e6', relief=tk.RAISED, bd=3)
        system3_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=20)
        
        tk.Label(system3_frame, text="[TARGET] COMPLETE LAUNCHER",
                font=("Arial", 14, "bold"), fg='#cc6600', bg='#fff0e6').pack(pady=(0, 10))
        
        tk.Label(system3_frame, text="• Professional interface\n• Multiple launch options\n• System testing tools\n• Documentation viewer\n• Android setup guide\n• All features included",
                font=("Arial", 10), fg='#333333', bg='#fff0e6', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(system3_frame, text="[LAUNCH] Launch Complete System",
                 font=("Arial", 11, "bold"), bg='#cc6600', fg='white',
                 padx=20, pady=8, command=self.launch_complete_nfcgate).pack(pady=5)
        
        # System 4: NFCGate Server Only
        system4_frame = tk.Frame(nfc_systems_frame, bg='#f0f0f0', relief=tk.RAISED, bd=3)
        system4_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=20)
        
        tk.Label(system4_frame, text="🌐 SERVER ONLY",
                font=("Arial", 14, "bold"), fg='#666666', bg='#f0f0f0').pack(pady=(0, 10))
        
        tk.Label(system4_frame, text="• Command-line server\n• No GUI interface\n• Advanced users only\n• Direct protocol access\n• Minimal resources\n• Custom integration",
                font=("Arial", 10), fg='#333333', bg='#f0f0f0', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(system4_frame, text="[LAUNCH] Launch Server Only",
                 font=("Arial", 11, "bold"), bg='#666666', fg='white',
                 padx=20, pady=8, command=self.launch_nfcgate_server_only).pack(pady=5)
        
        # Configure grid weights
        nfc_systems_frame.grid_columnconfigure(0, weight=1)
        nfc_systems_frame.grid_columnconfigure(1, weight=1)
        nfc_systems_frame.grid_rowconfigure(0, weight=1)
        nfc_systems_frame.grid_rowconfigure(1, weight=1)
        
    def create_credit_card_tab(self):
        """Create comprehensive credit card testing tab"""
        credit_frame = ttk.Frame(self.notebook)
        self.notebook.add(credit_frame, text="🏦 Credit Cards")
        
        # Main container
        main_container = ttk.Frame(credit_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_container,
                              text="🏦 Comprehensive Credit Card Testing Suite",
                              font=("Arial", 16, "bold"),
                              fg='#006600')
        title_label.pack(pady=(0, 20))
        
        # Feature info
        feature_info = """
✅ Complete Credit Card Support - All Major Brands (Visa, Mastercard, AmEx, Discover, JCB, UnionPay, Diners)
✅ EMV Compliance & Standards - Full EMV 4.4 compliance with proper TLV data structures
✅ TLV Data Analysis - Comprehensive Tag-Length-Value parsing and validation
✅ Track Data Generation - Magnetic stripe track 1 & 2 data with proper encoding
✅ Transaction Simulation - Complete payment processing simulation environment
✅ Security Features - Luhn checksum validation, CVV generation, security codes
✅ Database Integration - SQLite storage for cards, transactions, and test sessions
✅ Testing & Validation - Comprehensive test suites for all payment scenarios
        """
        
        info_label = tk.Label(main_container,
                             text=feature_info,
                             font=("Arial", 10),
                             fg='#333333',
                             justify=tk.LEFT,
                             wraplength=1000)
        info_label.pack(pady=(0, 20))
        
        # Credit card support status
        support_frame = tk.Frame(main_container, bg='#f0f8ff', relief=tk.RAISED, bd=2)
        support_frame.pack(fill=tk.X, pady=(0, 20), padx=20, ipady=10)
        
        if CREDIT_CARD_SUPPORT:
            status_text = "🟢 FULL CREDIT CARD SUPPORT ENABLED"
            status_color = '#006600'
            details_text = "✅ Advanced credit card structures loaded\n✅ Complete EMV compliance available\n✅ All features operational"
        else:
            status_text = "🟡 BASIC CREDIT CARD SUPPORT"
            status_color = '#cc6600'
            details_text = "⚠️ Advanced structures not loaded\n⚠️ Limited EMV support\n⚠️ Basic functionality only"
        
        tk.Label(support_frame, text=status_text,
                font=("Arial", 12, "bold"), fg=status_color, bg='#f0f8ff').pack()
        tk.Label(support_frame, text=details_text,
                font=("Arial", 10), fg='#333333', bg='#f0f8ff', justify=tk.LEFT).pack(pady=(5, 0))
        
        # Credit card tools grid
        tools_frame = tk.Frame(main_container)
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Primary Credit Card Admin Panel
        primary_frame = tk.Frame(tools_frame, bg='#e6ffe6', relief=tk.RAISED, bd=3)
        primary_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=15)
        
        tk.Label(primary_frame, text="🏦 COMPREHENSIVE CREDIT CARD ADMIN PANEL",
                font=("Arial", 14, "bold"), fg='#006600', bg='#e6ffe6').pack(pady=(0, 10))
        
        tk.Label(primary_frame, text="Complete testing environment with card generation, validation, transaction simulation, EMV analysis, and database management",
                font=("Arial", 11), fg='#333333', bg='#e6ffe6', wraplength=800).pack(pady=(0, 10))
        
        tk.Button(primary_frame, text="🚀 Launch Credit Card Admin Panel",
                 font=("Arial", 12, "bold"), bg='#00aa00', fg='white',
                 padx=30, pady=10, command=self.launch_credit_card_admin).pack(pady=5)
        
        # Enhanced RFID Client
        rfid_frame = tk.Frame(tools_frame, bg='#e6f0ff', relief=tk.RAISED, bd=3)
        rfid_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=15)
        
        tk.Label(rfid_frame, text="💳 ENHANCED RFID CLIENT",
                font=("Arial", 14, "bold"), fg='#0066cc', bg='#e6f0ff').pack(pady=(0, 10))
        
        tk.Label(rfid_frame, text="Advanced RFID card reading and writing with credit card support",
                font=("Arial", 10), fg='#333333', bg='#e6f0ff', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(rfid_frame, text="🚀 Launch RFID Client",
                 font=("Arial", 11, "bold"), bg='#0066cc', fg='white',
                 padx=20, pady=8, command=self.launch_enhanced_rfid).pack(pady=5)
        
        # NFCGate Credit Card Compatibility
        nfcgate_cc_frame = tk.Frame(tools_frame, bg='#fff0e6', relief=tk.RAISED, bd=3)
        nfcgate_cc_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=15)
        
        tk.Label(nfcgate_cc_frame, text="🔗 NFCGATE CREDIT CARD",
                font=("Arial", 14, "bold"), fg='#cc6600', bg='#fff0e6').pack(pady=(0, 10))
        
        tk.Label(nfcgate_cc_frame, text="NFCGate compatibility layer with credit card emulation support",
                font=("Arial", 10), fg='#333333', bg='#fff0e6', justify=tk.LEFT).pack(pady=(0, 10))
        
        tk.Button(nfcgate_cc_frame, text="🚀 Launch NFCGate CC",
                 font=("Arial", 11, "bold"), bg='#cc6600', fg='white',
                 padx=20, pady=8, command=self.launch_nfcgate_credit_card).pack(pady=5)
        
        # Credit Card Database Management
        db_cc_frame = tk.Frame(tools_frame, bg='#f0f0f0', relief=tk.RAISED, bd=3)
        db_cc_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew", ipadx=20, ipady=15)
        
        tk.Label(db_cc_frame, text="💾 CREDIT CARD DATABASE MANAGEMENT",
                font=("Arial", 14, "bold"), fg='#666666', bg='#f0f0f0').pack(pady=(0, 10))
        
        tk.Label(db_cc_frame, text="Manage credit card databases, export/import cards, generate reports, and analyze transaction data",
                font=("Arial", 11), fg='#333333', bg='#f0f0f0', justify=tk.LEFT).pack(pady=(0, 10))
        
        button_row = tk.Frame(db_cc_frame, bg='#f0f0f0')
        button_row.pack(pady=5)
        
        tk.Button(button_row, text="📊 Database Stats",
                 font=("Arial", 10, "bold"), bg='#666666', fg='white',
                 padx=15, pady=5, command=self.show_cc_database_stats).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_row, text="📤 Export Cards",
                 font=("Arial", 10, "bold"), bg='#666666', fg='white',
                 padx=15, pady=5, command=self.export_credit_cards).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_row, text="📊 Generate Report",
                 font=("Arial", 10, "bold"), bg='#666666', fg='white',
                 padx=15, pady=5, command=self.generate_cc_report).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        tools_frame.grid_columnconfigure(0, weight=1)
        tools_frame.grid_columnconfigure(1, weight=1)
        tools_frame.grid_rowconfigure(0, weight=0)
        tools_frame.grid_rowconfigure(1, weight=1)
        tools_frame.grid_rowconfigure(2, weight=0)
        
    def create_testing_tools_tab(self):
        """Create testing tools tab"""
        testing_frame = ttk.Frame(self.notebook)
        self.notebook.add(testing_frame, text="🧪 Testing Tools")
        
        # Main container
        main_container = ttk.Frame(testing_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_container,
                              text="🧪 Testing & Validation Tools",
                              font=("Arial", 16, "bold"),
                              fg='#660066')
        title_label.pack(pady=(0, 20))
        
        # Tools grid
        tools_frame = tk.Frame(main_container)
        tools_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tool 1: Admin Panel Tests
        tool1_frame = tk.Frame(tools_frame, bg='#ffe6e6', relief=tk.RAISED, bd=2)
        tool1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", ipadx=15, ipady=15)
        
        tk.Label(tool1_frame, text="🔧 Admin Panel Tests",
                font=("Arial", 12, "bold"), fg='#800000', bg='#ffe6e6').pack(pady=(0, 10))
        
        tk.Button(tool1_frame, text="🧪 Test Admin Panel GUI",
                 bg='#cc0000', fg='white', padx=15, pady=5,
                 command=self.run_admin_panel_test).pack(pady=2)
        
        tk.Button(tool1_frame, text="🧪 Test Enhanced Panel",
                 bg='#ff3333', fg='white', padx=15, pady=5,
                 command=self.run_enhanced_panel_test).pack(pady=2)
        
        tk.Button(tool1_frame, text="🧪 Test Online Panel",
                 bg='#ff6666', fg='white', padx=15, pady=5,
                 command=self.run_online_panel_test).pack(pady=2)
        
        # Tool 2: NFCGate Tests
        tool2_frame = tk.Frame(tools_frame, bg='#e6e6ff', relief=tk.RAISED, bd=2)
        tool2_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew", ipadx=15, ipady=15)
        
        tk.Label(tool2_frame, text="📱 NFCGate Tests",
                font=("Arial", 12, "bold"), fg='#000080', bg='#e6e6ff').pack(pady=(0, 10))
        
        tk.Button(tool2_frame, text="🧪 Test NFCGate Integration",
                 bg='#0000cc', fg='white', padx=15, pady=5,
                 command=self.run_nfcgate_test).pack(pady=2)
        
        tk.Button(tool2_frame, text="🧪 Test Compatibility",
                 bg='#3333ff', fg='white', padx=15, pady=5,
                 command=self.run_compatibility_test).pack(pady=2)
        
        tk.Button(tool2_frame, text="🧪 Test Connections",
                 bg='#6666ff', fg='white', padx=15, pady=5,
                 command=self.run_connection_test).pack(pady=2)
        
        # Tool 3: System Tests
        tool3_frame = tk.Frame(tools_frame, bg='#e6ffe6', relief=tk.RAISED, bd=2)
        tool3_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", ipadx=15, ipady=15)
        
        tk.Label(tool3_frame, text="⚙️ System Tests",
                font=("Arial", 12, "bold"), fg='#008000', bg='#e6ffe6').pack(pady=(0, 10))
        
        tk.Button(tool3_frame, text="🧪 Test Database System",
                 bg='#00cc00', fg='white', padx=15, pady=5,
                 command=self.run_database_test).pack(pady=2)
        
        tk.Button(tool3_frame, text="🧪 Test Geography Integration",
                 bg='#33ff33', fg='white', padx=15, pady=5,
                 command=self.run_geography_test).pack(pady=2)
        
        tk.Button(tool3_frame, text="🧪 Test Setup",
                 bg='#66ff66', fg='white', padx=15, pady=5,
                 command=self.run_setup_test).pack(pady=2)
        
        # Tool 4: Comprehensive Tests
        tool4_frame = tk.Frame(tools_frame, bg='#fff0e6', relief=tk.RAISED, bd=2)
        tool4_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew", ipadx=15, ipady=15)
        
        tk.Label(tool4_frame, text="🔍 Comprehensive Tests",
                font=("Arial", 12, "bold"), fg='#cc6600', bg='#fff0e6').pack(pady=(0, 10))
        
        tk.Button(tool4_frame, text="🧪 Run All Tests",
                 bg='#cc6600', fg='white', padx=15, pady=5,
                 command=self.run_all_tests).pack(pady=2)
        
        tk.Button(tool4_frame, text="🧪 Quick Search Test",
                 bg='#ff9933', fg='white', padx=15, pady=5,
                 command=self.run_quick_search_test).pack(pady=2)
        
        tk.Button(tool4_frame, text="🧪 Automatic DB Creator",
                 bg='#ffcc66', fg='white', padx=15, pady=5,
                 command=self.run_auto_db_test).pack(pady=2)
        
        # Configure grid weights
        tools_frame.grid_columnconfigure(0, weight=1)
        tools_frame.grid_columnconfigure(1, weight=1)
        tools_frame.grid_rowconfigure(0, weight=1)
        tools_frame.grid_rowconfigure(1, weight=1)
        
    def create_system_monitoring_tab(self):
        """Create system monitoring tab"""
        monitoring_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitoring_frame, text="📊 System Monitor")
        
        # Main container
        main_container = ttk.Frame(monitoring_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_container,
                              text="📊 System Status & Monitoring",
                              font=("Arial", 16, "bold"),
                              fg='#004080')
        title_label.pack(pady=(0, 20))
        
        # Status grid
        status_frame = ttk.LabelFrame(main_container, text="🔴 System Status", padding=15)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Create status indicators
        self.status_indicators = {}
        status_grid = tk.Frame(status_frame)
        status_grid.pack(fill=tk.X)
        
        status_items = [
            ("Admin Panel Status", "admin_panel"),
            ("NFCGate System", "nfcgate"),
            ("Database Status", "database"),
            ("Network Status", "network"),
            ("Running Processes", "processes"),
            ("Last Update", "last_update")
        ]
        
        for i, (label, key) in enumerate(status_items):
            row = i // 3
            col = (i % 3) * 2
            
            tk.Label(status_grid, text=f"{label}:", font=("Arial", 10, "bold")).grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5)
            
            self.status_indicators[key] = tk.Label(status_grid, text="⚪ Checking...", 
                                                  font=("Arial", 10))
            self.status_indicators[key].grid(row=row, column=col+1, sticky=tk.W, 
                                           padx=(0, 30), pady=5)
        
        # Process list
        process_frame = ttk.LabelFrame(main_container, text="🔄 Running Processes", padding=15)
        process_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Process treeview
        self.process_tree = ttk.Treeview(process_frame, 
                                        columns=("PID", "Name", "Status", "Started"), 
                                        show="tree headings", height=10)
        
        self.process_tree.heading("#0", text="Process ID")
        self.process_tree.heading("PID", text="System PID")
        self.process_tree.heading("Name", text="Process Name")
        self.process_tree.heading("Status", text="Status")
        self.process_tree.heading("Started", text="Started")
        
        self.process_tree.column("#0", width=100)
        self.process_tree.column("PID", width=80)
        self.process_tree.column("Name", width=200)
        self.process_tree.column("Status", width=100)
        self.process_tree.column("Started", width=120)
        
        process_scrollbar = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, 
                                         command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=process_scrollbar.set)
        
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        process_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons
        control_frame = tk.Frame(main_container)
        control_frame.pack(fill=tk.X)
        
        tk.Button(control_frame, text="🔄 Refresh Status",
                 bg='#0066cc', fg='white', padx=15, pady=5,
                 command=self.update_system_status).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(control_frame, text="🛑 Stop All Processes",
                 bg='#cc0000', fg='white', padx=15, pady=5,
                 command=self.stop_all_processes).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(control_frame, text="📤 Export Logs",
                 bg='#006600', fg='white', padx=15, pady=5,
                 command=self.export_system_logs).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(control_frame, text="🧹 Cleanup System",
                 bg='#cc6600', fg='white', padx=15, pady=5,
                 command=self.cleanup_system).pack(side=tk.RIGHT)
        
    def create_quick_actions_tab(self):
        """Create quick actions tab"""
        actions_frame = ttk.Frame(self.notebook)
        self.notebook.add(actions_frame, text="⚡ Quick Actions")
        
        # Main container
        main_container = ttk.Frame(actions_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_container,
                              text="⚡ Quick Actions & Utilities",
                              font=("Arial", 16, "bold"),
                              fg='#800040')
        title_label.pack(pady=(0, 20))
        
        # Quick actions grid
        actions_grid = tk.Frame(main_container)
        actions_grid.pack(fill=tk.BOTH, expand=True)
        
        # File Operations
        file_frame = ttk.LabelFrame(actions_grid, text="📁 File Operations", padding=15)
        file_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        tk.Button(file_frame, text="📖 View README",
                 bg='#0066cc', fg='white', padx=15, pady=5,
                 command=self.view_readme).pack(fill=tk.X, pady=2)
        
        tk.Button(file_frame, text="📋 View Quick Reference",
                 bg='#0080ff', fg='white', padx=15, pady=5,
                 command=self.view_quick_reference).pack(fill=tk.X, pady=2)
        
        tk.Button(file_frame, text="📊 View Project Status",
                 bg='#3399ff', fg='white', padx=15, pady=5,
                 command=self.view_project_status).pack(fill=tk.X, pady=2)
        
        tk.Button(file_frame, text="🗂️ Open Project Folder",
                 bg='#66b3ff', fg='white', padx=15, pady=5,
                 command=self.open_project_folder).pack(fill=tk.X, pady=2)
        
        # System Operations
        system_frame = ttk.LabelFrame(actions_grid, text="⚙️ System Operations", padding=15)
        system_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        tk.Button(system_frame, text="💾 Install Dependencies",
                 bg='#cc6600', fg='white', padx=15, pady=5,
                 command=self.install_dependencies).pack(fill=tk.X, pady=2)
        
        tk.Button(system_frame, text="🔧 Run Setup",
                 bg='#ff8000', fg='white', padx=15, pady=5,
                 command=self.run_setup).pack(fill=tk.X, pady=2)
        
        tk.Button(system_frame, text="🧹 Clean Cache",
                 bg='#ff9933', fg='white', padx=15, pady=5,
                 command=self.clean_cache).pack(fill=tk.X, pady=2)
        
        tk.Button(system_frame, text="🔄 Restart System",
                 bg='#ffb366', fg='white', padx=15, pady=5,
                 command=self.restart_system).pack(fill=tk.X, pady=2)
        
        # Network Operations
        network_frame = ttk.LabelFrame(actions_grid, text="🌐 Network Operations", padding=15)
        network_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        tk.Button(network_frame, text="📡 Check Network",
                 bg='#006600', fg='white', padx=15, pady=5,
                 command=self.check_network).pack(fill=tk.X, pady=2)
        
        tk.Button(network_frame, text="🔍 Port Scanner",
                 bg='#00cc00', fg='white', padx=15, pady=5,
                 command=self.launch_port_scanner).pack(fill=tk.X, pady=2)
        
        tk.Button(network_frame, text="📊 Network Monitor",
                 bg='#33ff33', fg='white', padx=15, pady=5,
                 command=self.launch_network_monitor).pack(fill=tk.X, pady=2)
        
        tk.Button(network_frame, text="🔗 Connection Test",
                 bg='#66ff66', fg='white', padx=15, pady=5,
                 command=self.test_connections).pack(fill=tk.X, pady=2)
        
        # Development Tools
        dev_frame = ttk.LabelFrame(actions_grid, text="🛠️ Development Tools", padding=15)
        dev_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        tk.Button(dev_frame, text="🔍 Code Search",
                 bg='#800080', fg='white', padx=15, pady=5,
                 command=self.launch_code_search).pack(fill=tk.X, pady=2)
        
        tk.Button(dev_frame, text="📝 Edit Config",
                 bg='#cc00cc', fg='white', padx=15, pady=5,
                 command=self.edit_config).pack(fill=tk.X, pady=2)
        
        tk.Button(dev_frame, text="🔧 Debug Tools",
                 bg='#ff33ff', fg='white', padx=15, pady=5,
                 command=self.launch_debug_tools).pack(fill=tk.X, pady=2)
        
        tk.Button(dev_frame, text="📊 Performance Monitor",
                 bg='#ff66ff', fg='white', padx=15, pady=5,
                 command=self.launch_performance_monitor).pack(fill=tk.X, pady=2)
        
        # Configure grid weights
        actions_grid.grid_columnconfigure(0, weight=1)
        actions_grid.grid_columnconfigure(1, weight=1)
        actions_grid.grid_rowconfigure(0, weight=1)
        actions_grid.grid_rowconfigure(1, weight=1)
        
    def create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = tk.Frame(self.root, bg='#333333', height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        # Status text
        self.status_var = tk.StringVar(value="🎯 Master Unified Launcher Ready - All systems available")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               bg='#333333', fg='#cccccc', font=("Arial", 9))
        status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # System info
        system_info = f"🖥️ {platform.system()} | 📡 IP: {self.get_local_ip()} | ⏰ {datetime.now().strftime('%H:%M:%S')}"
        info_label = tk.Label(status_frame, text=system_info,
                             bg='#333333', fg='#999999', font=("Arial", 8))
        info_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
    def get_local_ip(self):
        """Get local IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
            
    # Admin Panel Launch Methods
    def launch_enhanced_admin_panel(self):
        """Launch enhanced admin panel directly"""
        try:
            self.status_var.set("🚀 Launching Enhanced Admin Panel...")
            self.root.update()
            
            if os.path.exists("src/admin/admin_panel_gui.py"):
                def run_panel():
                    try:
                        process = subprocess.Popen([sys.executable, "src/admin/admin_panel_gui.py"])
                        self.running_processes.append(("Enhanced Admin Panel", process))
                    except Exception as e:
                        self.status_var.set(f"❌ Error launching panel: {e}")
                
                threading.Thread(target=run_panel, daemon=True).start()
                self.status_var.set("✅ Enhanced Admin Panel launched!")
                messagebox.showinfo("Success", "Enhanced Admin Panel launched successfully!")
            else:
                messagebox.showerror("Error", "Enhanced admin panel file not found!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch enhanced admin panel: {e}")
            
    def launch_enhanced_launcher(self):
        """Launch enhanced admin panel launcher"""
        self.launch_file("enhanced_admin_panel_launcher.py", "Enhanced Admin Launcher")
        
    def launch_complete_admin_panel(self):
        """Launch complete admin panel"""
        self.launch_file("admin_panel_complete.py", "Complete Admin Panel")
        
    def launch_admin_launcher(self):
        """Launch standard admin launcher"""
        self.launch_file("admin_panel_launcher.py", "Admin Panel Launcher")
        
    def launch_online_admin_panel(self):
        """Launch online admin panel"""
        self.launch_file("online_admin_panel.py", "Online Admin Panel")
        
    def launch_demo_launcher(self):
        """Launch demo launcher"""
        self.launch_file("enhanced_admin_panel_demo.py", "Demo Launcher")
        
    def launch_master_controller(self):
        """Launch master controller"""
        self.launch_file("master_admin_controller.py", "Master Controller")
        
    def launch_integrated_control(self):
        """Launch integrated control system"""
        self.launch_file("integrated_control_system.py", "Integrated Control")
        
    # NFCGate Launch Methods
    def launch_fixed_nfcgate(self):
        """Launch fixed NFCGate system"""
        self.launch_file("fixed_nfcgate_system.py", "Fixed NFCGate System")
        
    def launch_simple_nfcgate(self):
        """Launch simple NFCGate launcher"""
        self.launch_file("simple_nfcgate_launcher.py", "Simple NFCGate")
        
    def launch_complete_nfcgate(self):
        """Launch complete NFCGate launcher"""
        self.launch_file("complete_nfcgate_launcher.py", "Complete NFCGate")
        
    def launch_nfcgate_server_only(self):
        """Launch NFCGate server only"""
        try:
            self.status_var.set("🌐 Starting NFCGate server...")
            self.root.update()
            
            if os.path.exists("nfcgate_compatibility.py"):
                def run_server():
                    try:
                        cmd = [sys.executable, "nfcgate_compatibility.py", "--mode", "server", "--port", "8080"]
                        process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
                        self.running_processes.append(("NFCGate Server", process))
                    except Exception as e:
                        self.status_var.set(f"❌ Error: {e}")
                
                threading.Thread(target=run_server, daemon=True).start()
                self.status_var.set(f"✅ NFCGate server started on {self.get_local_ip()}:8080")
                messagebox.showinfo("Server Started", f"NFCGate server started on {self.get_local_ip()}:8080")
            else:
                messagebox.showerror("Error", "NFCGate compatibility file not found!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start NFCGate server: {e}")
            
    # Credit Card Testing Methods
    def launch_credit_card_admin(self):
        """Launch comprehensive credit card admin panel"""
        self.launch_file("comprehensive_credit_card_admin.py", "Credit Card Admin Panel")
        
    def launch_enhanced_rfid(self):
        """Launch enhanced RFID client with credit card support"""
        self.launch_file("enhanced_rfid_client.py", "Enhanced RFID Client")
        
    def launch_nfcgate_credit_card(self):
        """Launch NFCGate compatibility with credit card support"""
        self.launch_file("nfcgate_compatibility.py", "NFCGate Credit Card Support")
        
    def show_cc_database_stats(self):
        """Show credit card database statistics"""
        try:
            db_path = Path(__file__).parent / "database" / "credit_cards.db"
            
            if not db_path.exists():
                messagebox.showinfo("Database Info", "Credit card database not found. Generate cards first.")
                return
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get statistics
                cursor.execute("SELECT COUNT(*) FROM credit_cards")
                total_cards = cursor.fetchone()[0]
                
                cursor.execute("SELECT card_type, COUNT(*) FROM credit_cards GROUP BY card_type")
                card_type_stats = cursor.fetchall()
                
                cursor.execute("SELECT COUNT(*) FROM transactions")
                total_transactions = cursor.fetchone()[0]
                
                # Format message
                stats_message = f"📊 Credit Card Database Statistics\n\n"
                stats_message += f"Total Cards: {total_cards}\n"
                stats_message += f"Total Transactions: {total_transactions}\n\n"
                stats_message += "Card Type Distribution:\n"
                
                for card_type, count in card_type_stats:
                    percentage = (count / total_cards * 100) if total_cards > 0 else 0
                    stats_message += f"• {card_type}: {count} ({percentage:.1f}%)\n"
                
                messagebox.showinfo("Database Statistics", stats_message)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get database statistics: {e}")
    
    def export_credit_cards(self):
        """Export credit cards to file"""
        try:
            db_path = Path(__file__).parent / "database" / "credit_cards.db"
            
            if not db_path.exists():
                messagebox.showinfo("Export Info", "Credit card database not found. Generate cards first.")
                return
            
            # Get export file location
            export_file = filedialog.asksaveasfilename(
                title="Export Credit Cards",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )
            
            if not export_file:
                return
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM credit_cards")
                cards = cursor.fetchall()
                
                # Export as JSON
                if export_file.endswith('.json'):
                    export_data = {
                        'export_timestamp': datetime.now().isoformat(),
                        'total_cards': len(cards),
                        'cards': []
                    }
                    
                    for card in cards:
                        card_data = {
                            'id': card[0],
                            'uid': card[1],
                            'card_type': card[2],
                            'masked_pan': card[4],
                            'expiry_date': card[5],
                            'created_at': card[11],
                            'usage_count': card[14]
                        }
                        export_data['cards'].append(card_data)
                    
                    with open(export_file, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2)
                
                messagebox.showinfo("Export Success", f"Exported {len(cards)} cards to {export_file}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export cards: {e}")
    
    def generate_cc_report(self):
        """Generate credit card testing report"""
        try:
            db_path = Path(__file__).parent / "database" / "credit_cards.db"
            
            if not db_path.exists():
                messagebox.showinfo("Report Info", "Credit card database not found. Generate cards first.")
                return
            
            # Get report file location
            report_file = filedialog.asksaveasfilename(
                title="Save Credit Card Report",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("HTML files", "*.html"),
                    ("All files", "*.*")
                ]
            )
            
            if not report_file:
                return
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Generate comprehensive report
                report_content = f"CREDIT CARD TESTING REPORT\n"
                report_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_content += f"{'='*60}\n\n"
                
                # Card statistics
                cursor.execute("SELECT COUNT(*) FROM credit_cards")
                total_cards = cursor.fetchone()[0]
                
                cursor.execute("SELECT card_type, COUNT(*) FROM credit_cards GROUP BY card_type")
                card_stats = cursor.fetchall()
                
                report_content += f"CARD STATISTICS\n"
                report_content += f"-" * 30 + "\n"
                report_content += f"Total Cards: {total_cards}\n\n"
                
                for card_type, count in card_stats:
                    percentage = (count / total_cards * 100) if total_cards > 0 else 0
                    report_content += f"{card_type}: {count} ({percentage:.1f}%)\n"
                
                report_content += f"\n"
                
                # Transaction statistics
                cursor.execute("SELECT COUNT(*) FROM transactions")
                total_transactions = cursor.fetchone()[0]
                
                if total_transactions > 0:
                    cursor.execute("SELECT status, COUNT(*) FROM transactions GROUP BY status")
                    transaction_stats = cursor.fetchall()
                    
                    report_content += f"TRANSACTION STATISTICS\n"
                    report_content += f"-" * 30 + "\n"
                    report_content += f"Total Transactions: {total_transactions}\n\n"
                    
                    for status, count in transaction_stats:
                        percentage = (count / total_transactions * 100) if total_transactions > 0 else 0
                        report_content += f"{status.capitalize()}: {count} ({percentage:.1f}%)\n"
                
                # Feature support
                report_content += f"\nFEATURE SUPPORT\n"
                report_content += f"-" * 30 + "\n"
                report_content += f"Credit Card Structures: {'✅ Enabled' if CREDIT_CARD_SUPPORT else '❌ Basic Mode'}\n"
                report_content += f"EMV Compliance: {'✅ Full Support' if CREDIT_CARD_SUPPORT else '❌ Limited'}\n"
                report_content += f"Database Integration: ✅ Active\n"
                
                # Save report
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                messagebox.showinfo("Report Generated", f"Credit card report saved to {report_file}")
                
        except Exception as e:
            messagebox.showerror("Report Error", f"Failed to generate report: {e}")
            
    # Testing Methods
    def run_admin_panel_test(self):
        """Run admin panel GUI test"""
        self.launch_file("test_admin_panel_gui.py", "Admin Panel Test")
        
    def run_enhanced_panel_test(self):
        """Run enhanced panel test"""
        self.launch_file("test_enhanced_admin_panel.py", "Enhanced Panel Test")
        
    def run_online_panel_test(self):
        """Run online panel test"""
        self.launch_file("test_online_admin_demo.py", "Online Panel Test")
        
    def run_nfcgate_test(self):
        """Run NFCGate integration test"""
        self.launch_file("test_nfcgate_integration.py", "NFCGate Test")
        
    def run_compatibility_test(self):
        """Run compatibility test"""
        self.launch_file("test_comprehensive_compatibility.py", "Compatibility Test")
        
    def run_connection_test(self):
        """Run connection management test"""
        self.launch_file("test_connection_management.py", "Connection Test")
        
    def run_database_test(self):
        """Run database system test"""
        self.launch_file("test_database_system.py", "Database Test")
        
    def run_geography_test(self):
        """Run geography integration test"""
        self.launch_file("test_geography_integration.py", "Geography Test")
        
    def run_setup_test(self):
        """Run setup test"""
        self.launch_file("test_setup.py", "Setup Test")
        
    def run_all_tests(self):
        """Run all tests"""
        try:
            self.status_var.set("🧪 Running comprehensive test suite...")
            test_files = [
                "test_admin_panel_gui.py",
                "test_enhanced_admin_panel.py", 
                "test_nfcgate_integration.py",
                "test_database_system.py"
            ]
            
            for test_file in test_files:
                if os.path.exists(test_file):
                    self.launch_file(test_file, f"Test: {test_file}")
                    time.sleep(1)  # Small delay between tests
                    
            self.status_var.set("✅ All tests launched!")
            messagebox.showinfo("Tests Started", f"Launched {len(test_files)} test suites!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run tests: {e}")
            
    def run_quick_search_test(self):
        """Run quick search test"""
        self.launch_file("test_quick_search.py", "Quick Search Test")
        
    def run_auto_db_test(self):
        """Run automatic database creator test"""
        self.launch_file("test_automatic_db_creator.py", "Auto DB Test")
        
    # Utility Methods
    def launch_file(self, filename: str, display_name: str):
        """Generic file launcher"""
        try:
            if os.path.exists(filename):
                self.status_var.set(f"🚀 Launching {display_name}...")
                self.root.update()
                
                def run_file():
                    try:
                        process = subprocess.Popen([sys.executable, filename])
                        self.running_processes.append((display_name, process))
                    except Exception as e:
                        self.status_var.set(f"❌ Error: {e}")
                
                threading.Thread(target=run_file, daemon=True).start()
                self.status_var.set(f"✅ {display_name} launched!")
                messagebox.showinfo("Success", f"{display_name} launched successfully!")
            else:
                messagebox.showerror("Error", f"{filename} not found!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {display_name}: {e}")
            
    def update_system_status(self):
        """Update system status indicators"""
        try:
            # Check admin panel status
            admin_running = any("admin" in name.lower() for name, _ in self.running_processes)
            self.status_indicators["admin_panel"].config(
                text="🟢 Running" if admin_running else "🔴 Stopped",
                fg="green" if admin_running else "red"
            )
            
            # Check NFCGate status
            nfc_running = any("nfc" in name.lower() for name, _ in self.running_processes)
            self.status_indicators["nfcgate"].config(
                text="🟢 Running" if nfc_running else "🔴 Stopped",
                fg="green" if nfc_running else "red"
            )
            
            # Check database status
            db_exists = os.path.exists("databases") or os.path.exists("database")
            self.status_indicators["database"].config(
                text="🟢 Available" if db_exists else "🟡 Not found",
                fg="green" if db_exists else "orange"
            )
            
            # Check network status
            self.status_indicators["network"].config(
                text=f"🟢 {self.get_local_ip()}",
                fg="green"
            )
            
            # Update process count
            self.status_indicators["processes"].config(
                text=f"🔄 {len(self.running_processes)} active",
                fg="blue"
            )
            
            # Update timestamp
            self.status_indicators["last_update"].config(
                text=f"⏰ {datetime.now().strftime('%H:%M:%S')}",
                fg="gray"
            )
            
            # Update process tree
            self.update_process_tree()
            
        except Exception as e:
            print(f"Status update error: {e}")
            
    def update_process_tree(self):
        """Update process tree view"""
        try:
            # Clear existing items
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
            
            # Add current processes
            for i, (name, process) in enumerate(self.running_processes):
                try:
                    status = "Running" if process.poll() is None else "Finished"
                    pid = process.pid if hasattr(process, 'pid') else "N/A"
                    
                    self.process_tree.insert('', 'end', 
                                           text=f"Process_{i+1}",
                                           values=(pid, name, status, datetime.now().strftime('%H:%M:%S')))
                except:
                    continue
                    
        except Exception as e:
            print(f"Process tree update error: {e}")
            
    def stop_all_processes(self):
        """Stop all running processes"""
        try:
            if not self.running_processes:
                messagebox.showinfo("No Processes", "No running processes to stop.")
                return
                
            if messagebox.askyesno("Confirm", f"Stop all {len(self.running_processes)} running processes?"):
                stopped_count = 0
                for name, process in self.running_processes:
                    try:
                        if process.poll() is None:  # Process is still running
                            process.terminate()
                            stopped_count += 1
                    except:
                        continue
                
                self.running_processes.clear()
                self.update_system_status()
                messagebox.showinfo("Success", f"Stopped {stopped_count} processes.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop processes: {e}")
            
    def export_system_logs(self):
        """Export system logs"""
        messagebox.showinfo("Export Logs", "Log export feature would be implemented here.")
        
    def cleanup_system(self):
        """Cleanup system files"""
        try:
            if messagebox.askyesno("Confirm Cleanup", "Clean temporary files and cache?"):
                # Clean __pycache__ directories
                for root, dirs, files in os.walk("."):
                    if "__pycache__" in dirs:
                        shutil.rmtree(os.path.join(root, "__pycache__"))
                
                messagebox.showinfo("Success", "System cleanup completed!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Cleanup failed: {e}")
            
    # Quick Actions Methods
    def view_readme(self):
        """View README file"""
        try:
            readme_files = ["README.md", "README_NFCGATE.md", "README.txt"]
            for readme in readme_files:
                if os.path.exists(readme):
                    if platform.system() == "Windows":
                        os.startfile(readme)
                    else:
                        subprocess.run(["xdg-open", readme])
                    return
            messagebox.showwarning("Not Found", "No README file found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open README: {e}")
            
    def view_quick_reference(self):
        """View quick reference"""
        self.view_file("ADMIN_PANEL_QUICK_REFERENCE.md")
        
    def view_project_status(self):
        """View project status"""
        self.view_file("PROJECT_STATUS_FINAL.md")
        
    def open_project_folder(self):
        """Open project folder in file explorer"""
        try:
            if platform.system() == "Windows":
                os.startfile(".")
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "."])
            else:  # Linux
                subprocess.run(["xdg-open", "."])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
            
    def view_file(self, filename: str):
        """View a specific file"""
        try:
            if os.path.exists(filename):
                if platform.system() == "Windows":
                    os.startfile(filename)
                else:
                    subprocess.run(["xdg-open", filename])
            else:
                messagebox.showwarning("Not Found", f"{filename} not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open {filename}: {e}")
            
    def install_dependencies(self):
        """Install system dependencies"""
        try:
            self.status_var.set("💾 Installing dependencies...")
            
            def install():
                try:
                    if os.path.exists("install.py"):
                        subprocess.run([sys.executable, "install.py"])
                    else:
                        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                    self.status_var.set("✅ Dependencies installed!")
                except Exception as e:
                    self.status_var.set(f"❌ Install failed: {e}")
                    
            threading.Thread(target=install, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install dependencies: {e}")
            
    def run_setup(self):
        """Run system setup"""
        self.launch_file("install.py", "System Setup")
        
    def clean_cache(self):
        """Clean system cache"""
        self.cleanup_system()
        
    def restart_system(self):
        """Restart launcher system"""
        try:
            if messagebox.askyesno("Restart", "Restart the Master Unified Launcher?"):
                self.stop_all_processes()
                self.root.quit()
                subprocess.Popen([sys.executable, __file__])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart: {e}")
            
    def check_network(self):
        """Check network connectivity"""
        try:
            self.status_var.set("📡 Checking network...")
            
            # Test local network
            local_ip = self.get_local_ip()
            
            # Test internet connectivity
            try:
                response = socket.create_connection(("8.8.8.8", 53), timeout=3)
                response.close()
                internet_status = "✅ Connected"
            except:
                internet_status = "❌ No internet"
            
            messagebox.showinfo("Network Status", 
                              f"Local IP: {local_ip}\n"
                              f"Internet: {internet_status}\n"
                              f"System: {platform.system()}")
            
            self.status_var.set(f"📡 Network check complete - IP: {local_ip}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Network check failed: {e}")
            
    def launch_port_scanner(self):
        """Launch port scanner utility"""
        messagebox.showinfo("Port Scanner", "Port scanner utility would be launched here.")
        
    def launch_network_monitor(self):
        """Launch network monitor"""
        messagebox.showinfo("Network Monitor", "Network monitoring tool would be launched here.")
        
    def test_connections(self):
        """Test system connections"""
        self.run_connection_test()
        
    def launch_code_search(self):
        """Launch code search tool"""
        self.launch_file("demo_quick_search.py", "Code Search Tool")
        
    def edit_config(self):
        """Edit system configuration"""
        try:
            config_files = ["config.py", "unified_config_system.py", "config.json"]
            for config in config_files:
                if os.path.exists(config):
                    self.view_file(config)
                    return
            messagebox.showwarning("Not Found", "No configuration file found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open config: {e}")
            
    def launch_debug_tools(self):
        """Launch debugging tools"""
        messagebox.showinfo("Debug Tools", "Debug tools would be launched here.")
        
    def launch_performance_monitor(self):
        """Launch performance monitor"""
        messagebox.showinfo("Performance Monitor", "Performance monitoring would be launched here.")
        
    def run(self):
        """Run the master launcher"""
        try:
            # Schedule periodic status updates
            def update_status_periodically():
                self.update_system_status()
                self.root.after(10000, update_status_periodically)  # Update every 10 seconds
                
            update_status_periodically()
            
            # Start the GUI
            self.root.mainloop()
            
        except Exception as e:
            print(f"Master launcher error: {e}")

def main():
    """Main function"""
    try:
        print("Starting Master TLV Unified Launcher...")
        print("=" * 60)
        print("Ultimate control center for all TLV systems")
        print("Admin panels, NFCGate, testing tools & more")
        print("Quick access to all features in one place")
        print("=" * 60)
        
        # Create and run launcher
        launcher = MasterUnifiedLauncher()
        launcher.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Master launcher interrupted by user")
    except Exception as e:
        print(f"❌ Master launcher failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
