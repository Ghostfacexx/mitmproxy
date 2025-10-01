#!/usr/bin/env python3
"""
🌐 NFCGate Android APK Integration System
Complete integration between Android NFCGate APK and existing admin panel
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import socket
import subprocess
import sys
import os

# Import our NFCGate compatibility system
from nfcgate_compatibility import NFCGateServer, NFCGateClient, NFCReader, NFCEmulator, NFCDevice

class NFCGateControlPanel:
    """Control panel for NFCGate Android APK integration"""
    
    def __init__(self, parent_window=None):
        self.parent = parent_window
        self.window = tk.Toplevel(parent_window) if parent_window else tk.Tk()
        self.window.title("🌐 NFCGate Android APK Integration")
        self.window.geometry("1200x800")
        self.window.configure(bg='#1e1e1e')
        
        # NFCGate server
        self.nfcgate_server = None
        self.server_thread = None
        self.server_running = False
        
        # Connected devices
        self.connected_devices = {}
        self.device_sessions = {}
        
        # Message queues for thread communication
        self.update_queue = queue.Queue()
        
        # Setup logging
        self.setup_logging()
        
        # Create GUI
        self.create_gui()
        
        # Start update loop
        self.update_loop()
        
    def setup_logging(self):
        """Setup logging for NFCGate operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/nfcgate_integration.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_gui(self):
        """Create the NFCGate control panel GUI"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Server Control Tab
        self.create_server_tab()
        
        # Device Management Tab
        self.create_device_tab()
        
        # Android APK Connection Tab
        self.create_android_tab()
        
        # Data Monitoring Tab
        self.create_monitoring_tab()
        
        # Configuration Tab
        self.create_config_tab()
        
        # Logs Tab
        self.create_logs_tab()
        
    def create_server_tab(self):
        """Create server control tab"""
        server_frame = ttk.Frame(self.notebook)
        self.notebook.add(server_frame, text="🖥️ Server Control")
        
        # Server status section
        status_frame = ttk.LabelFrame(server_frame, text="Server Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.server_status_var = tk.StringVar(value="Stopped")
        self.server_status_label = ttk.Label(status_frame, textvariable=self.server_status_var, 
                                           font=("Arial", 14, "bold"))
        self.server_status_label.pack(pady=5)
        
        # Server configuration
        config_frame = ttk.LabelFrame(server_frame, text="Server Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Host and port
        ttk.Label(config_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.host_var = tk.StringVar(value="0.0.0.0")
        self.host_entry = ttk.Entry(config_frame, textvariable=self.host_var, width=20)
        self.host_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(config_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.port_var = tk.StringVar(value="8080")
        self.port_entry = ttk.Entry(config_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=0, column=3, padx=5)
        
        # Control buttons
        control_frame = ttk.Frame(server_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="🚀 Start Server", 
                                     command=self.start_server, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="🛑 Stop Server", 
                                    command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.restart_button = ttk.Button(control_frame, text="🔄 Restart Server", 
                                       command=self.restart_server, state=tk.DISABLED)
        self.restart_button.pack(side=tk.LEFT, padx=5)
        
        # Server statistics
        stats_frame = ttk.LabelFrame(server_frame, text="Server Statistics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=10, width=80,
                                                  bg='#2d2d2d', fg='white', font=("Consolas", 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
    def create_device_tab(self):
        """Create device management tab"""
        device_frame = ttk.Frame(self.notebook)
        self.notebook.add(device_frame, text="📱 Devices")
        
        # Device list
        list_frame = ttk.LabelFrame(device_frame, text="Connected Devices", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Device tree view
        columns = ("Device ID", "Type", "Status", "Last Seen", "IP Address", "Capabilities")
        self.device_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=150)
        
        device_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=device_scroll.set)
        
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        device_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Device actions
        actions_frame = ttk.LabelFrame(device_frame, text="Device Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(actions_frame, text="📡 Send Test Data", 
                 command=self.send_test_data).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(actions_frame, text="⚙️ Configure Device", 
                 command=self.configure_device).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(actions_frame, text="🔄 Refresh Devices", 
                 command=self.refresh_devices).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(actions_frame, text="🗑️ Remove Device", 
                 command=self.remove_device).pack(side=tk.LEFT, padx=5)
        
    def create_android_tab(self):
        """Create Android APK connection tab"""
        android_frame = ttk.Frame(self.notebook)
        self.notebook.add(android_frame, text="🤖 Android APK")
        
        # Connection instructions
        instructions_frame = ttk.LabelFrame(android_frame, text="Connection Instructions", padding=10)
        instructions_frame.pack(fill=tk.X, padx=10, pady=5)
        
        instructions_text = """
🤖 How to connect Android NFCGate APK:

1. Install NFCGate APK on your Android device
2. Enable Developer Options and USB Debugging
3. Connect your device to the same network as this server
4. In NFCGate app, go to Settings > Server Configuration
5. Enter the server IP address and port (shown below)
6. Enable "Connect to External Server" option
7. Start NFC operations in the app

📱 Supported Operations:
• NFC Card Reading
• Card Emulation
• Data Relay
• Real-time Monitoring
        """
        
        instructions_label = ttk.Label(instructions_frame, text=instructions_text, 
                                     justify=tk.LEFT, font=("Arial", 10))
        instructions_label.pack()
        
        # Connection details
        details_frame = ttk.LabelFrame(android_frame, text="Connection Details", padding=10)
        details_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Server address info
        ttk.Label(details_frame, text="Server Address:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.server_address_var = tk.StringVar()
        self.server_address_label = ttk.Label(details_frame, textvariable=self.server_address_var, 
                                            font=("Arial", 12, "bold"), foreground="blue")
        self.server_address_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Button(details_frame, text="📋 Copy Address", 
                 command=self.copy_server_address).grid(row=0, column=2, padx=5)
        
        # QR Code for easy setup
        qr_frame = ttk.LabelFrame(android_frame, text="QR Code Setup", padding=10)
        qr_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(qr_frame, text="📱 Generate QR Code", 
                 command=self.generate_qr_code).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(qr_frame, text="Scan with NFCGate app for automatic configuration").pack(side=tk.LEFT, padx=10)
        
        # Android device status
        android_status_frame = ttk.LabelFrame(android_frame, text="Android Device Status", padding=10)
        android_status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.android_status_text = scrolledtext.ScrolledText(android_status_frame, height=15, width=80,
                                                           bg='#2d2d2d', fg='white', font=("Consolas", 10))
        self.android_status_text.pack(fill=tk.BOTH, expand=True)
        
    def create_monitoring_tab(self):
        """Create data monitoring tab"""
        monitoring_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitoring_frame, text="📊 Monitoring")
        
        # Real-time data display
        data_frame = ttk.LabelFrame(monitoring_frame, text="Real-time NFC Data", padding=10)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.data_text = scrolledtext.ScrolledText(data_frame, height=20, width=100,
                                                 bg='#1a1a1a', fg='#00ff00', font=("Consolas", 9))
        self.data_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        control_frame = ttk.Frame(monitoring_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.monitoring_var = tk.BooleanVar()
        ttk.Checkbutton(control_frame, text="Enable Real-time Monitoring", 
                       variable=self.monitoring_var, command=self.toggle_monitoring).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="🗑️ Clear Data", 
                 command=self.clear_monitoring_data).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="💾 Export Data", 
                 command=self.export_monitoring_data).pack(side=tk.LEFT, padx=5)
        
    def create_config_tab(self):
        """Create configuration tab"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Configuration")
        
        # NFCGate server settings
        server_settings_frame = ttk.LabelFrame(config_frame, text="Server Settings", padding=10)
        server_settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Timeout settings
        ttk.Label(server_settings_frame, text="Client Timeout (seconds):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.timeout_var = tk.StringVar(value="30")
        ttk.Entry(server_settings_frame, textvariable=self.timeout_var, width=10).grid(row=0, column=1, padx=5)
        
        # Max clients
        ttk.Label(server_settings_frame, text="Max Clients:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.max_clients_var = tk.StringVar(value="50")
        ttk.Entry(server_settings_frame, textvariable=self.max_clients_var, width=10).grid(row=1, column=1, padx=5)
        
        # Protocol settings
        protocol_frame = ttk.LabelFrame(config_frame, text="Protocol Settings", padding=10)
        protocol_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Supported protocols
        self.protocol_vars = {}
        protocols = ["ISO14443A", "ISO14443B", "ISO15693", "FELICA", "MIFARE"]
        
        for i, protocol in enumerate(protocols):
            var = tk.BooleanVar(value=True)
            self.protocol_vars[protocol] = var
            ttk.Checkbutton(protocol_frame, text=protocol, variable=var).grid(row=i//3, column=i%3, sticky=tk.W, padx=5)
        
        # Security settings
        security_frame = ttk.LabelFrame(config_frame, text="Security Settings", padding=10)
        security_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.encryption_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(security_frame, text="Enable Message Encryption", 
                       variable=self.encryption_var).pack(anchor=tk.W, padx=5)
        
        self.auth_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(security_frame, text="Require Device Authentication", 
                       variable=self.auth_var).pack(anchor=tk.W, padx=5)
        
        # Save configuration
        ttk.Button(config_frame, text="💾 Save Configuration", 
                 command=self.save_config).pack(pady=10)
        
    def create_logs_tab(self):
        """Create logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📝 Logs")
        
        # Log display
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=25, width=120,
                                                 bg='#0a0a0a', fg='#ffffff', font=("Consolas", 9))
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log controls
        log_controls = ttk.Frame(logs_frame)
        log_controls.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_controls, text="🗑️ Clear Logs", 
                 command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(log_controls, text="💾 Export Logs", 
                 command=self.export_logs).pack(side=tk.LEFT, padx=5)
        
        # Log level filter
        ttk.Label(log_controls, text="Level:").pack(side=tk.LEFT, padx=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_controls, textvariable=self.log_level_var, 
                                     values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                     width=10, state="readonly")
        log_level_combo.pack(side=tk.LEFT, padx=5)
        
    def start_server(self):
        """Start the NFCGate server"""
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())
            
            # Create NFCGate server
            self.nfcgate_server = NFCGateServer(host, port)
            
            # Start server in separate thread
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            
            self.server_running = True
            self.server_status_var.set("Running")
            
            # Update server address
            self.update_server_address()
            
            # Update button states
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.restart_button.config(state=tk.NORMAL)
            
            self.log_message("✅ NFCGate server started successfully")
            
        except Exception as e:
            self.log_message(f"❌ Failed to start server: {e}")
            messagebox.showerror("Error", f"Failed to start server: {e}")
            
    def run_server(self):
        """Run the NFCGate server"""
        try:
            self.nfcgate_server.start()
        except Exception as e:
            self.log_message(f"❌ Server error: {e}")
            
    def stop_server(self):
        """Stop the NFCGate server"""
        try:
            if self.nfcgate_server:
                self.nfcgate_server.stop()
                
            self.server_running = False
            self.server_status_var.set("Stopped")
            
            # Update button states
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)
            
            self.log_message("🛑 NFCGate server stopped")
            
        except Exception as e:
            self.log_message(f"❌ Error stopping server: {e}")
            
    def restart_server(self):
        """Restart the NFCGate server"""
        self.log_message("🔄 Restarting NFCGate server...")
        self.stop_server()
        time.sleep(1)
        self.start_server()
        
    def update_server_address(self):
        """Update server address display"""
        try:
            # Get local IP address
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            
            address = f"{local_ip}:{self.port_var.get()}"
            self.server_address_var.set(address)
            
        except Exception as e:
            self.server_address_var.set(f"localhost:{self.port_var.get()}")
            
    def copy_server_address(self):
        """Copy server address to clipboard"""
        try:
            address = self.server_address_var.get()
            self.window.clipboard_clear()
            self.window.clipboard_append(address)
            messagebox.showinfo("Copied", f"Server address copied to clipboard: {address}")
        except Exception as e:
            self.log_message(f"❌ Error copying address: {e}")
            
    def generate_qr_code(self):
        """Generate QR code for NFCGate app configuration"""
        try:
            # Create configuration for QR code
            config = {
                "server_host": self.server_address_var.get().split(':')[0],
                "server_port": int(self.port_var.get()),
                "protocol": "nfcgate",
                "encryption": self.encryption_var.get(),
                "auto_connect": True
            }
            
            # You would implement QR code generation here
            # For now, just show the configuration
            config_text = json.dumps(config, indent=2)
            messagebox.showinfo("QR Code Configuration", f"Configuration for QR code:\n\n{config_text}")
            
        except Exception as e:
            self.log_message(f"❌ Error generating QR code: {e}")
            
    def refresh_devices(self):
        """Refresh device list"""
        try:
            # Clear current device list
            for item in self.device_tree.get_children():
                self.device_tree.delete(item)
            
            # Update with current devices
            if self.nfcgate_server and hasattr(self.nfcgate_server, 'devices'):
                for device_id, device in self.nfcgate_server.devices.items():
                    # Get client info
                    client_info = None
                    for client_socket, info in self.nfcgate_server.clients.items():
                        if info.get('device_id') == device_id:
                            client_info = info
                            break
                    
                    # Format device info
                    status = "Connected" if device.is_connected else "Disconnected"
                    last_seen = datetime.fromtimestamp(device.last_heartbeat).strftime("%H:%M:%S")
                    ip_address = client_info['address'][0] if client_info else "Unknown"
                    capabilities = ", ".join(device.capabilities.keys())
                    
                    self.device_tree.insert("", tk.END, values=(
                        device_id, device.device_type, status, last_seen, ip_address, capabilities
                    ))
            
            self.log_message("🔄 Device list refreshed")
            
        except Exception as e:
            self.log_message(f"❌ Error refreshing devices: {e}")
            
    def send_test_data(self):
        """Send test data to selected device"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device first")
            return
        
        device_id = self.device_tree.item(selection[0])['values'][0]
        
        # Create test data
        test_data = {
            "type": "test",
            "message": "Hello from NFCGate Control Panel",
            "timestamp": datetime.now().isoformat(),
            "test_data": "0123456789ABCDEF"
        }
        
        self.log_message(f"📡 Sending test data to device {device_id}")
        # Implementation would send data to the specific device
        
    def configure_device(self):
        """Configure selected device"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device first")
            return
        
        device_id = self.device_tree.item(selection[0])['values'][0]
        self.log_message(f"⚙️ Configuring device {device_id}")
        
        # Create device configuration dialog
        config_window = tk.Toplevel(self.window)
        config_window.title(f"Configure Device: {device_id}")
        config_window.geometry("400x300")
        
        # Add configuration options here
        ttk.Label(config_window, text="Device Configuration", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(config_window, text="Feature coming soon...").pack(pady=20)
        
    def remove_device(self):
        """Remove selected device"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device first")
            return
        
        device_id = self.device_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Confirm", f"Remove device {device_id}?"):
            # Implementation would remove the device
            self.device_tree.delete(selection[0])
            self.log_message(f"🗑️ Device {device_id} removed")
            
    def toggle_monitoring(self):
        """Toggle real-time monitoring"""
        if self.monitoring_var.get():
            self.log_message("📊 Real-time monitoring enabled")
            # Start monitoring thread
        else:
            self.log_message("⏹️ Real-time monitoring disabled")
            # Stop monitoring thread
            
    def clear_monitoring_data(self):
        """Clear monitoring data display"""
        self.data_text.delete(1.0, tk.END)
        self.log_message("🗑️ Monitoring data cleared")
        
    def export_monitoring_data(self):
        """Export monitoring data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nfcgate_monitoring_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(self.data_text.get(1.0, tk.END))
            
            self.log_message(f"💾 Monitoring data exported to {filename}")
            messagebox.showinfo("Export Complete", f"Data exported to {filename}")
            
        except Exception as e:
            self.log_message(f"❌ Error exporting data: {e}")
            
    def save_config(self):
        """Save configuration"""
        try:
            config = {
                "server": {
                    "host": self.host_var.get(),
                    "port": self.port_var.get(),
                    "timeout": self.timeout_var.get(),
                    "max_clients": self.max_clients_var.get()
                },
                "protocols": {proto: var.get() for proto, var in self.protocol_vars.items()},
                "security": {
                    "encryption": self.encryption_var.get(),
                    "authentication": self.auth_var.get()
                }
            }
            
            with open("config/nfcgate_config.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            self.log_message("💾 Configuration saved")
            messagebox.showinfo("Success", "Configuration saved successfully")
            
        except Exception as e:
            self.log_message(f"❌ Error saving configuration: {e}")
            
    def clear_logs(self):
        """Clear logs display"""
        self.logs_text.delete(1.0, tk.END)
        
    def export_logs(self):
        """Export logs"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nfcgate_logs_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(self.logs_text.get(1.0, tk.END))
            
            messagebox.showinfo("Export Complete", f"Logs exported to {filename}")
            
        except Exception as e:
            self.log_message(f"❌ Error exporting logs: {e}")
            
    def log_message(self, message: str):
        """Log message to both console and GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to logs tab
        self.logs_text.insert(tk.END, formatted_message)
        self.logs_text.see(tk.END)
        
        # Add to monitoring if enabled
        if hasattr(self, 'monitoring_var') and self.monitoring_var.get():
            self.data_text.insert(tk.END, formatted_message)
            self.data_text.see(tk.END)
        
        # Console logging
        print(formatted_message.strip())
        
    def update_loop(self):
        """Main update loop for GUI"""
        try:
            # Process any queued updates
            while not self.update_queue.empty():
                update_func = self.update_queue.get_nowait()
                update_func()
                
            # Update server statistics
            if self.server_running and self.nfcgate_server:
                self.update_server_stats()
                
            # Refresh device list periodically
            if hasattr(self, 'last_device_refresh'):
                if time.time() - self.last_device_refresh > 5:  # Every 5 seconds
                    self.refresh_devices()
                    self.last_device_refresh = time.time()
            else:
                self.last_device_refresh = time.time()
                
        except Exception as e:
            pass  # Ignore update errors
            
        # Schedule next update
        self.window.after(1000, self.update_loop)
        
    def update_server_stats(self):
        """Update server statistics display"""
        try:
            if not self.nfcgate_server:
                return
                
            stats = {
                "Status": "Running" if self.server_running else "Stopped",
                "Connected Devices": len([d for d in self.nfcgate_server.devices.values() if d.is_connected]),
                "Total Devices": len(self.nfcgate_server.devices),
                "Active Sessions": len(self.nfcgate_server.sessions),
                "Total Clients": len(self.nfcgate_server.clients),
                "Server Address": self.server_address_var.get(),
                "Uptime": f"{time.time() - getattr(self.nfcgate_server, 'start_time', time.time()):.0f}s"
            }
            
            stats_text = "\n".join([f"{key}: {value}" for key, value in stats.items()])
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, stats_text)
            
        except Exception as e:
            pass  # Ignore stats update errors

def main():
    """Main function"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # Create and run the NFCGate control panel
    app = NFCGateControlPanel()
    
    try:
        app.window.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")

if __name__ == "__main__":
    main()
