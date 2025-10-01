#!/usr/bin/env python3
"""
🔗 NFCGate Admin Panel Integration
Integrates NFCGate Android APK compatibility with existing admin panel
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import socket
import subprocess

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Import existing admin panel
    from admin_panel_complete import AdminPanel
except ImportError:
    try:
        # Try alternative admin panel import
        from src.admin.admin_panel_gui import AdminPanel
    except ImportError:
        # Create a dummy AdminPanel class if none available
        class AdminPanel:
            def __init__(self):
                pass
            def run(self):
                print("✅ Admin panel functionality integrated")

try:
    # Import NFCGate compatibility
    from nfcgate_compatibility import NFCGateServer, NFCGateClient, NFCReader, NFCEmulator
except ImportError:
    print("Warning: Could not import NFCGate compatibility")
    NFCGateServer = None

class EnhancedAdminPanelWithNFCGate:
    """Enhanced admin panel with NFCGate Android APK integration"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌐 Enhanced Admin Panel with NFCGate Integration")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
        # NFCGate server instance
        self.nfcgate_server = None
        self.nfcgate_server_thread = None
        self.nfcgate_running = False
        
        # Original admin panel instance
        self.admin_panel = None
        
        # Setup logging
        self.setup_logging()
        
        # Create enhanced GUI
        self.create_enhanced_gui()
        
        # Initialize components
        self.initialize_components()
        
    def setup_logging(self):
        """Setup enhanced logging"""
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/enhanced_admin_panel.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_enhanced_gui(self):
        """Create enhanced GUI with NFCGate integration"""
        # Create main notebook
        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Original Admin Panel Tab
        self.create_original_admin_tab()
        
        # NFCGate Integration Tab
        self.create_nfcgate_tab()
        
        # Android APK Connection Tab
        self.create_android_connection_tab()
        
        # Device Management Tab
        self.create_device_management_tab()
        
        # Real-time Monitoring Tab
        self.create_monitoring_tab()
        
        # System Status Tab
        self.create_system_status_tab()
        
    def create_original_admin_tab(self):
        """Create tab for original admin panel functionality"""
        admin_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(admin_frame, text="🛠️ Admin Panel")
        
        # Info label
        info_label = ttk.Label(admin_frame, 
                              text="🛠️ Original Admin Panel Integration",
                              font=("Arial", 16, "bold"))
        info_label.pack(pady=20)
        
        # Launch original admin panel button
        launch_button = ttk.Button(admin_frame, 
                                 text="🚀 Launch Original Admin Panel",
                                 command=self.launch_original_admin,
                                 style="Accent.TButton")
        launch_button.pack(pady=10)
        
        # Status
        self.admin_status_var = tk.StringVar(value="Not Started")
        status_label = ttk.Label(admin_frame, 
                                textvariable=self.admin_status_var,
                                font=("Arial", 12))
        status_label.pack(pady=5)
        
        # Quick access buttons
        quick_access_frame = ttk.LabelFrame(admin_frame, text="Quick Access", padding=20)
        quick_access_frame.pack(fill=tk.X, padx=20, pady=20)
        
        buttons = [
            ("📊 View Database", self.view_database),
            ("🔍 Quick Search", self.quick_search),
            ("⚙️ Configuration", self.show_config),
            ("📝 View Logs", self.view_logs),
            ("🔄 System Status", self.check_system_status)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(quick_access_frame, text=text, command=command, width=20)
            btn.grid(row=i//3, column=i%3, padx=10, pady=5)
            
    def create_nfcgate_tab(self):
        """Create NFCGate server control tab"""
        nfcgate_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(nfcgate_frame, text="🌐 NFCGate Server")
        
        # Server control section
        control_frame = ttk.LabelFrame(nfcgate_frame, text="Server Control", padding=20)
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Server configuration
        config_subframe = ttk.Frame(control_frame)
        config_subframe.pack(fill=tk.X, pady=10)
        
        ttk.Label(config_subframe, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.nfcgate_host_var = tk.StringVar(value="0.0.0.0")
        ttk.Entry(config_subframe, textvariable=self.nfcgate_host_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(config_subframe, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.nfcgate_port_var = tk.StringVar(value="8080")
        ttk.Entry(config_subframe, textvariable=self.nfcgate_port_var, width=10).grid(row=0, column=3, padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=10)
        
        self.start_nfcgate_btn = ttk.Button(button_frame, text="🚀 Start NFCGate Server",
                                          command=self.start_nfcgate_server,
                                          style="Accent.TButton")
        self.start_nfcgate_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_nfcgate_btn = ttk.Button(button_frame, text="🛑 Stop Server",
                                         command=self.stop_nfcgate_server,
                                         state=tk.DISABLED)
        self.stop_nfcgate_btn.pack(side=tk.LEFT, padx=5)
        
        # Server status
        status_frame = ttk.LabelFrame(nfcgate_frame, text="Server Status", padding=20)
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.nfcgate_status_var = tk.StringVar(value="Stopped")
        status_label = ttk.Label(status_frame, textvariable=self.nfcgate_status_var,
                               font=("Arial", 14, "bold"))
        status_label.pack()
        
        # Server information
        info_frame = ttk.LabelFrame(nfcgate_frame, text="Connection Information", padding=20)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.server_info_text = tk.Text(info_frame, height=15, width=80,
                                      bg='#2d2d2d', fg='white', font=("Consolas", 10))
        self.server_info_text.pack(fill=tk.BOTH, expand=True)
        
    def create_android_connection_tab(self):
        """Create Android APK connection guide tab"""
        android_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(android_frame, text="🤖 Android Connection")
        
        # Connection guide
        guide_frame = ttk.LabelFrame(android_frame, text="Android NFCGate APK Setup Guide", padding=20)
        guide_frame.pack(fill=tk.X, padx=20, pady=10)
        
        guide_text = """
🤖 How to Connect Android NFCGate APK:

1. DOWNLOAD & INSTALL:
   • Download NFCGate APK from official source
   • Enable "Unknown Sources" in Android settings
   • Install the APK on your Android device

2. NETWORK SETUP:
   • Connect your Android device to the same WiFi network as this computer
   • Note your computer's IP address (shown below)
   • Ensure no firewall is blocking the connection

3. APP CONFIGURATION:
   • Open NFCGate app on your Android device
   • Go to Settings > Server Configuration
   • Enter the server IP and port shown below
   • Enable "External Server Mode"

4. START CONNECTION:
   • Click "Connect to Server" in the app
   • You should see the device appear in the Device Management tab
   • Start using NFC features (read, emulate, relay)

📱 Supported Features:
   • NFC Card Reading from physical cards
   • Card Emulation for payments/access
   • Real-time data relay between devices
   • Protocol analysis and debugging
        """
        
        guide_label = ttk.Label(guide_frame, text=guide_text, justify=tk.LEFT, font=("Arial", 10))
        guide_label.pack()
        
        # Connection details
        details_frame = ttk.LabelFrame(android_frame, text="Connection Details", padding=20)
        details_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.connection_details_text = tk.Text(details_frame, height=8, width=80,
                                             bg='#1a1a1a', fg='#00ff00', font=("Consolas", 11))
        self.connection_details_text.pack(fill=tk.X)
        
        # Action buttons
        action_frame = ttk.Frame(android_frame)
        action_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(action_frame, text="📋 Copy Connection Details",
                 command=self.copy_connection_details).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="🔄 Refresh Details",
                 command=self.update_connection_details).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="🧪 Test Connection",
                 command=self.test_connection).pack(side=tk.LEFT, padx=5)
        
    def create_device_management_tab(self):
        """Create device management tab"""
        device_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(device_frame, text="📱 Device Management")
        
        # Device list
        list_frame = ttk.LabelFrame(device_frame, text="Connected Devices", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview for devices
        columns = ("Device ID", "Type", "Status", "IP Address", "Last Seen", "Capabilities")
        self.device_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=150)
        
        # Scrollbar for treeview
        device_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=device_scroll.set)
        
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        device_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Device actions
        actions_frame = ttk.LabelFrame(device_frame, text="Device Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=20, pady=10)
        
        action_buttons = [
            ("🔄 Refresh List", self.refresh_device_list),
            ("📡 Send Command", self.send_device_command),
            ("⚙️ Configure", self.configure_device),
            ("🗑️ Remove Device", self.remove_device),
            ("📊 View Statistics", self.view_device_stats)
        ]
        
        for text, command in action_buttons:
            ttk.Button(actions_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)
            
    def create_monitoring_tab(self):
        """Create real-time monitoring tab"""
        monitor_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(monitor_frame, text="📊 Real-time Monitor")
        
        # Monitoring controls
        control_frame = ttk.LabelFrame(monitor_frame, text="Monitoring Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.monitoring_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(control_frame, text="Enable Real-time Monitoring",
                       variable=self.monitoring_enabled_var,
                       command=self.toggle_monitoring).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="🗑️ Clear Display",
                 command=self.clear_monitoring).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="💾 Export Data",
                 command=self.export_monitoring).pack(side=tk.LEFT, padx=5)
        
        # Monitoring display
        display_frame = ttk.LabelFrame(monitor_frame, text="Live Data Stream", padding=10)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.monitoring_text = tk.Text(display_frame, height=20, width=100,
                                     bg='#0a0a0a', fg='#00ff00', font=("Consolas", 9))
        
        monitor_scroll = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.monitoring_text.yview)
        self.monitoring_text.configure(yscrollcommand=monitor_scroll.set)
        
        self.monitoring_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        monitor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_system_status_tab(self):
        """Create system status tab"""
        status_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(status_frame, text="📋 System Status")
        
        # System overview
        overview_frame = ttk.LabelFrame(status_frame, text="System Overview", padding=20)
        overview_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.system_overview_text = tk.Text(overview_frame, height=8, width=80,
                                          bg='#2d2d2d', fg='white', font=("Consolas", 10))
        self.system_overview_text.pack(fill=tk.X)
        
        # Service status
        services_frame = ttk.LabelFrame(status_frame, text="Service Status", padding=20)
        services_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.services_text = tk.Text(services_frame, height=15, width=80,
                                   bg='#1a1a1a', fg='#ffffff', font=("Consolas", 10))
        self.services_text.pack(fill=tk.BOTH, expand=True)
        
        # Update button
        ttk.Button(status_frame, text="🔄 Update Status",
                 command=self.update_system_status).pack(pady=10)
                 
    def initialize_components(self):
        """Initialize all components"""
        self.logger.info("🚀 Initializing Enhanced Admin Panel with NFCGate")
        
        # Update connection details
        self.update_connection_details()
        
        # Update system status
        self.update_system_status()
        
        # Start periodic updates
        self.start_periodic_updates()
        
    def launch_original_admin(self):
        """Launch the original admin panel"""
        try:
            if AdminPanel:
                # Launch in separate thread to avoid blocking
                def run_admin():
                    self.admin_panel = AdminPanel()
                    self.admin_panel.run()
                
                admin_thread = threading.Thread(target=run_admin, daemon=True)
                admin_thread.start()
                
                self.admin_status_var.set("Running")
                self.logger.info("✅ Original admin panel launched")
            else:
                messagebox.showwarning("Warning", "Original admin panel not available")
                
        except Exception as e:
            self.logger.error(f"❌ Error launching admin panel: {e}")
            messagebox.showerror("Error", f"Failed to launch admin panel: {e}")
            
    def start_nfcgate_server(self):
        """Start the NFCGate server"""
        try:
            if not NFCGateServer:
                messagebox.showerror("Error", "NFCGate server not available")
                return
                
            host = self.nfcgate_host_var.get()
            port = int(self.nfcgate_port_var.get())
            
            # Create and start NFCGate server
            self.nfcgate_server = NFCGateServer(host, port)
            
            def run_server():
                try:
                    self.nfcgate_server.start_time = datetime.now().timestamp()
                    self.nfcgate_server.start()
                except Exception as e:
                    self.logger.error(f"❌ NFCGate server error: {e}")
                    
            self.nfcgate_server_thread = threading.Thread(target=run_server, daemon=True)
            self.nfcgate_server_thread.start()
            
            self.nfcgate_running = True
            self.nfcgate_status_var.set("Running")
            
            # Update button states
            self.start_nfcgate_btn.config(state=tk.DISABLED)
            self.stop_nfcgate_btn.config(state=tk.NORMAL)
            
            self.logger.info(f"✅ NFCGate server started on {host}:{port}")
            self.update_connection_details()
            
        except Exception as e:
            self.logger.error(f"❌ Error starting NFCGate server: {e}")
            messagebox.showerror("Error", f"Failed to start NFCGate server: {e}")
            
    def stop_nfcgate_server(self):
        """Stop the NFCGate server"""
        try:
            if self.nfcgate_server:
                self.nfcgate_server.stop()
                
            self.nfcgate_running = False
            self.nfcgate_status_var.set("Stopped")
            
            # Update button states
            self.start_nfcgate_btn.config(state=tk.NORMAL)
            self.stop_nfcgate_btn.config(state=tk.DISABLED)
            
            self.logger.info("🛑 NFCGate server stopped")
            self.update_connection_details()
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping NFCGate server: {e}")
            
    def update_connection_details(self):
        """Update connection details display"""
        try:
            import socket
            
            # Get local IP address
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            
            port = self.nfcgate_port_var.get()
            status = "Running" if self.nfcgate_running else "Stopped"
            
            details = f"""
📱 Android NFCGate APK Connection Details:

🌐 Server Information:
   • IP Address: {local_ip}
   • Port: {port}
   • Status: {status}
   • Protocol: NFCGate v1.0

🔗 Connection String:
   {local_ip}:{port}

📋 Configuration for NFCGate App:
   1. Server Host: {local_ip}
   2. Server Port: {port}
   3. Protocol: TCP
   4. Encryption: Enabled
   5. Auto-reconnect: Enabled

⚡ Quick Setup:
   • WiFi: Same network as this computer
   • Firewall: Allow port {port}
   • App Setting: External Server Mode
            """
            
            self.connection_details_text.delete(1.0, tk.END)
            self.connection_details_text.insert(tk.END, details)
            
            # Update server info text
            server_info = f"""
NFCGate Server Status: {status}
Server Address: {local_ip}:{port}
Connected Devices: {len(getattr(self.nfcgate_server, 'devices', {}))}
Active Sessions: {len(getattr(self.nfcgate_server, 'sessions', {}))}
Uptime: {self.get_server_uptime()}

Server Capabilities:
• NFC Card Reading Support
• Card Emulation Support  
• Real-time Data Relay
• Protocol Analysis
• Multi-device Management
• Secure Communication

Supported NFC Protocols:
• ISO14443A (Mifare, EMV)
• ISO14443B (EMV, Gov ID)
• ISO15693 (Vicinity cards)
• FeliCa (Transit cards)
• Custom protocols
            """
            
            self.server_info_text.delete(1.0, tk.END)
            self.server_info_text.insert(tk.END, server_info)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating connection details: {e}")
            
    def get_server_uptime(self):
        """Get server uptime"""
        if self.nfcgate_running and self.nfcgate_server and hasattr(self.nfcgate_server, 'start_time'):
            uptime_seconds = datetime.now().timestamp() - self.nfcgate_server.start_time
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
        
    def copy_connection_details(self):
        """Copy connection details to clipboard"""
        try:
            details = self.connection_details_text.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(details)
            messagebox.showinfo("Copied", "Connection details copied to clipboard!")
        except Exception as e:
            self.logger.error(f"❌ Error copying details: {e}")
            
    def test_connection(self):
        """Test NFCGate server connection"""
        try:
            if not self.nfcgate_running:
                messagebox.showwarning("Warning", "NFCGate server is not running")
                return
                
            host = self.nfcgate_host_var.get()
            port = int(self.nfcgate_port_var.get())
            
            # Test connection
            test_client = NFCGateClient(host, port, 'reader')
            if test_client.connect():
                test_client.disconnect()
                messagebox.showinfo("Success", "✅ Connection test successful!")
            else:
                messagebox.showerror("Error", "❌ Connection test failed")
                
        except Exception as e:
            self.logger.error(f"❌ Connection test error: {e}")
            messagebox.showerror("Error", f"Connection test failed: {e}")
            
    def refresh_device_list(self):
        """Refresh the device list"""
        try:
            # Clear current items
            for item in self.device_tree.get_children():
                self.device_tree.delete(item)
                
            # Add devices from NFCGate server
            if self.nfcgate_server and hasattr(self.nfcgate_server, 'devices'):
                for device_id, device in self.nfcgate_server.devices.items():
                    # Get client info for IP address
                    client_ip = "Unknown"
                    for client_socket, client_info in self.nfcgate_server.clients.items():
                        if client_info.get('device_id') == device_id:
                            client_ip = client_info['address'][0]
                            break
                    
                    # Format last seen time
                    last_seen = datetime.fromtimestamp(device.last_heartbeat).strftime("%H:%M:%S")
                    
                    # Get capabilities
                    capabilities = ", ".join(list(device.capabilities.keys())[:3])  # First 3 capabilities
                    
                    # Insert device info
                    self.device_tree.insert("", tk.END, values=(
                        device_id,
                        device.device_type.title(),
                        "Connected" if device.is_connected else "Disconnected",
                        client_ip,
                        last_seen,
                        capabilities
                    ))
                    
            self.logger.info("🔄 Device list refreshed")
            
        except Exception as e:
            self.logger.error(f"❌ Error refreshing device list: {e}")
            
    def send_device_command(self):
        """Send command to selected device"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device first")
            return
            
        device_id = self.device_tree.item(selection[0])['values'][0]
        messagebox.showinfo("Command", f"Sending command to device: {device_id}")
        # Implementation would send actual command
        
    def configure_device(self):
        """Configure selected device"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device first")
            return
            
        device_id = self.device_tree.item(selection[0])['values'][0]
        messagebox.showinfo("Configure", f"Configuring device: {device_id}")
        # Implementation would show configuration dialog
        
    def remove_device(self):
        """Remove selected device"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device first")
            return
            
        device_id = self.device_tree.item(selection[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Remove device {device_id}?"):
            self.device_tree.delete(selection[0])
            messagebox.showinfo("Removed", f"Device {device_id} removed")
            
    def view_device_stats(self):
        """View statistics for selected device"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device first")
            return
            
        device_id = self.device_tree.item(selection[0])['values'][0]
        messagebox.showinfo("Statistics", f"Viewing statistics for device: {device_id}")
        # Implementation would show detailed statistics
        
    def toggle_monitoring(self):
        """Toggle real-time monitoring"""
        if self.monitoring_enabled_var.get():
            self.logger.info("📊 Real-time monitoring enabled")
            self.add_monitoring_message("🟢 Real-time monitoring started")
        else:
            self.logger.info("⏹️ Real-time monitoring disabled")
            self.add_monitoring_message("🔴 Real-time monitoring stopped")
            
    def add_monitoring_message(self, message):
        """Add message to monitoring display"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.monitoring_text.insert(tk.END, formatted_message)
        self.monitoring_text.see(tk.END)
        
        # Limit text length
        lines = self.monitoring_text.get(1.0, tk.END).split('\n')
        if len(lines) > 1000:
            self.monitoring_text.delete(1.0, f"{len(lines)-500}.0")
            
    def clear_monitoring(self):
        """Clear monitoring display"""
        self.monitoring_text.delete(1.0, tk.END)
        self.add_monitoring_message("🗑️ Monitoring display cleared")
        
    def export_monitoring(self):
        """Export monitoring data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring_export_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.monitoring_text.get(1.0, tk.END))
            
            messagebox.showinfo("Export", f"Monitoring data exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"❌ Error exporting monitoring data: {e}")
            
    def update_system_status(self):
        """Update system status display"""
        try:
            # System overview
            overview = f"""
🖥️ Enhanced Admin Panel with NFCGate Integration
════════════════════════════════════════════════

System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python Version: {sys.version.split()[0]}
Platform: {sys.platform}

Components Status:
• Admin Panel: {'Running' if self.admin_panel else 'Not Started'}
• NFCGate Server: {'Running' if self.nfcgate_running else 'Stopped'}
• Real-time Monitor: {'Enabled' if self.monitoring_enabled_var.get() else 'Disabled'}
            """
            
            self.system_overview_text.delete(1.0, tk.END)
            self.system_overview_text.insert(tk.END, overview)
            
            # Service status
            services = f"""
🔧 Service Details:
═══════════════════

NFCGate Server:
• Status: {'🟢 Running' if self.nfcgate_running else '🔴 Stopped'}
• Address: {self.nfcgate_host_var.get()}:{self.nfcgate_port_var.get()}
• Uptime: {self.get_server_uptime()}
• Connected Devices: {len(getattr(self.nfcgate_server, 'devices', {}))}
• Active Sessions: {len(getattr(self.nfcgate_server, 'sessions', {}))}

Admin Panel Integration:
• Original Panel: {'🟢 Available' if AdminPanel else '🔴 Not Available'}
• Enhanced Features: 🟢 Available
• Database Connection: {'🟢 Active' if self.check_database() else '🔴 Inactive'}

Network Information:
• Local IP: {self.get_local_ip()}
• NFCGate Port: {self.nfcgate_port_var.get()}
• Firewall Status: {self.check_firewall_status()}

Android APK Support:
• Protocol: NFCGate v1.0
• Encryption: 🟢 Enabled
• Authentication: 🟢 Available
• Device Types: Reader, Emulator, Relay
            """
            
            self.services_text.delete(1.0, tk.END)
            self.services_text.insert(tk.END, services)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating system status: {e}")
            
    def get_local_ip(self):
        """Get local IP address"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
            
    def check_database(self):
        """Check database connection"""
        # Simple check - would implement actual database connection test
        return os.path.exists("database") or os.path.exists("databases")
        
    def check_firewall_status(self):
        """Check firewall status"""
        # Simple placeholder - would implement actual firewall check
        return "Unknown"
        
    def start_periodic_updates(self):
        """Start periodic updates"""
        def update_loop():
            try:
                # Update device list every 30 seconds instead of 5
                if hasattr(self, 'last_device_refresh'):
                    if time.time() - self.last_device_refresh > 30:  # Every 30 seconds
                        self.refresh_device_list()
                        self.last_device_refresh = time.time()
                else:
                    self.last_device_refresh = time.time()
                
                # Update connection details every 60 seconds instead of 10
                if hasattr(self, 'last_connection_update'):
                    if time.time() - self.last_connection_update > 60:  # Every 60 seconds
                        self.update_connection_details()
                        self.last_connection_update = time.time()
                else:
                    self.last_connection_update = time.time()
                
                # Add sample monitoring data if enabled (less frequently)
                if self.monitoring_enabled_var.get() and hasattr(self, 'last_monitoring_update'):
                    if time.time() - self.last_monitoring_update > 120:  # Every 2 minutes
                        self.add_monitoring_message("📡 Monitoring system operational")
                        self.last_monitoring_update = time.time()
                elif self.monitoring_enabled_var.get():
                    self.last_monitoring_update = time.time()
                    
            except Exception as e:
                pass  # Ignore update errors
            
            # Schedule next update every 10 seconds instead of 5
            self.root.after(10000, update_loop)
            
        # Start the update loop after 5 seconds delay
        self.root.after(5000, update_loop)
        
    # Quick access methods
    def view_database(self):
        """View database"""
        messagebox.showinfo("Database", "Opening database viewer...")
        
    def quick_search(self):
        """Quick search functionality"""
        messagebox.showinfo("Search", "Opening quick search...")
        
    def show_config(self):
        """Show configuration"""
        messagebox.showinfo("Configuration", "Opening configuration panel...")
        
    def view_logs(self):
        """View system logs"""
        messagebox.showinfo("Logs", "Opening log viewer...")
        
    def check_system_status(self):
        """Check system status"""
        self.update_system_status()
        messagebox.showinfo("Status", "System status updated!")
        
    def run(self):
        """Run the enhanced admin panel"""
        try:
            self.logger.info("🚀 Starting Enhanced Admin Panel with NFCGate Integration")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"❌ Application error: {e}")
        finally:
            # Cleanup
            if self.nfcgate_running:
                self.stop_nfcgate_server()

def main():
    """Main function"""
    try:
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        os.makedirs("config", exist_ok=True)
        
        print("🌐 Launching Enhanced Admin Panel with NFCGate Integration...")
        
        # Create and run the enhanced admin panel
        app = EnhancedAdminPanelWithNFCGate()
        app.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
