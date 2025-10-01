#!/usr/bin/env python3
"""
🚀 NFCGate Launcher - Complete System Launcher
Full-featured launcher for NFCGate Android APK integration with configuration and monitoring.
"""

import sys
import os
import time
import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from nfcgate_compatibility import NFCGateServer, NFCGateClient
    from nfcgate_admin_integration import app as admin_app
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all NFCGate modules are available")
    sys.exit(1)

class NFCGateLauncher:
    """Full-featured NFCGate system launcher with GUI."""
    
    def __init__(self):
        self.server = None
        self.server_thread = None
        self.running = False
        
        # Configuration
        self.config = {
            'server_host': '0.0.0.0',
            'server_port': 8080,
            'max_clients': 50,
            'enable_logging': True,
            'auto_start': False,
            'encryption_enabled': True
        }
        
        self.setup_gui()
        self.load_config()
    
    def setup_gui(self):
        """Set up the launcher GUI."""
        self.root = tk.Tk()
        self.root.title("🚀 NFCGate Launcher - Complete System Control")
        self.root.geometry("800x700")
        self.root.configure(bg='#2c3e50')
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='#34495e')
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Title frame
        title_frame = tk.Frame(self.root, bg='#2c3e50')
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(
            title_frame,
            text="🚀 NFCGate Complete System Launcher",
            font=('Arial', 18, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Full Android NFCGate APK Integration with Admin Panel",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        subtitle_label.pack()
        
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Server Control Tab
        self.create_server_tab()
        
        # Configuration Tab
        self.create_config_tab()
        
        # Device Management Tab
        self.create_device_tab()
        
        # System Status Tab
        self.create_status_tab()
        
        # Android Setup Tab
        self.create_android_tab()
    
    def create_server_tab(self):
        """Create server control tab."""
        server_frame = ttk.Frame(self.notebook)
        self.notebook.add(server_frame, text="🌐 Server Control")
        
        # Server status
        status_frame = ttk.LabelFrame(server_frame, text="Server Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="🔴 Server Stopped",
            font=('Arial', 12, 'bold'),
            fg='red'
        )
        self.status_label.pack()
        
        # Control buttons
        button_frame = tk.Frame(status_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = tk.Button(
            button_frame,
            text="🚀 Start NFCGate Server",
            command=self.start_server,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(
            button_frame,
            text="🛑 Stop Server",
            command=self.stop_server,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.restart_button = tk.Button(
            button_frame,
            text="🔄 Restart",
            command=self.restart_server,
            bg='#f39c12',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        )
        self.restart_button.pack(side=tk.LEFT, padx=5)
        
        # Server info
        info_frame = ttk.LabelFrame(server_frame, text="Server Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.server_info = tk.Text(info_frame, height=8, bg='#ecf0f1', font=('Courier', 10))
        self.server_info.pack(fill=tk.BOTH, expand=True)
        
        self.update_server_info()
    
    def create_config_tab(self):
        """Create configuration tab."""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Configuration")
        
        # Server configuration
        server_config_frame = ttk.LabelFrame(config_frame, text="Server Configuration", padding=10)
        server_config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Host
        tk.Label(server_config_frame, text="Server Host:").grid(row=0, column=0, sticky=tk.W)
        self.host_entry = tk.Entry(server_config_frame, width=20)
        self.host_entry.insert(0, self.config['server_host'])
        self.host_entry.grid(row=0, column=1, padx=5)
        
        # Port
        tk.Label(server_config_frame, text="Server Port:").grid(row=1, column=0, sticky=tk.W)
        self.port_entry = tk.Entry(server_config_frame, width=20)
        self.port_entry.insert(0, str(self.config['server_port']))
        self.port_entry.grid(row=1, column=1, padx=5)
        
        # Max clients
        tk.Label(server_config_frame, text="Max Clients:").grid(row=2, column=0, sticky=tk.W)
        self.max_clients_entry = tk.Entry(server_config_frame, width=20)
        self.max_clients_entry.insert(0, str(self.config['max_clients']))
        self.max_clients_entry.grid(row=2, column=1, padx=5)
        
        # Options
        options_frame = ttk.LabelFrame(config_frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.logging_var = tk.BooleanVar(value=self.config['enable_logging'])
        tk.Checkbutton(options_frame, text="Enable Logging", variable=self.logging_var).pack(anchor=tk.W)
        
        self.auto_start_var = tk.BooleanVar(value=self.config['auto_start'])
        tk.Checkbutton(options_frame, text="Auto Start Server", variable=self.auto_start_var).pack(anchor=tk.W)
        
        self.encryption_var = tk.BooleanVar(value=self.config['encryption_enabled'])
        tk.Checkbutton(options_frame, text="Enable Encryption", variable=self.encryption_var).pack(anchor=tk.W)
        
        # Save button
        save_button = tk.Button(
            config_frame,
            text="💾 Save Configuration",
            command=self.save_config,
            bg='#3498db',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        )
        save_button.pack(pady=10)
    
    def create_device_tab(self):
        """Create device management tab."""
        device_frame = ttk.Frame(self.notebook)
        self.notebook.add(device_frame, text="📱 Device Management")
        
        # Connected devices
        devices_frame = ttk.LabelFrame(device_frame, text="Connected Devices", padding=10)
        devices_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Device list
        columns = ('Device ID', 'IP Address', 'Type', 'Status', 'Connected')
        self.device_tree = ttk.Treeview(devices_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=100)
        
        device_scrollbar = ttk.Scrollbar(devices_frame, orient=tk.VERTICAL, command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=device_scrollbar.set)
        
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        device_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Device controls
        device_controls_frame = tk.Frame(device_frame)
        device_controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        refresh_devices_button = tk.Button(
            device_controls_frame,
            text="🔄 Refresh Devices",
            command=self.refresh_devices,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        refresh_devices_button.pack(side=tk.LEFT, padx=5)
        
        disconnect_device_button = tk.Button(
            device_controls_frame,
            text="🔌 Disconnect Selected",
            command=self.disconnect_device,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        disconnect_device_button.pack(side=tk.LEFT, padx=5)
    
    def create_status_tab(self):
        """Create system status tab."""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="📊 System Status")
        
        # System info
        system_info_frame = ttk.LabelFrame(status_frame, text="System Information", padding=10)
        system_info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.system_info = tk.Text(system_info_frame, height=6, bg='#ecf0f1', font=('Courier', 10))
        self.system_info.pack(fill=tk.BOTH, expand=True)
        
        # Live log
        log_frame = ttk.LabelFrame(status_frame, text="Live System Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, bg='black', fg='green', font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls_frame = tk.Frame(status_frame)
        log_controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        clear_log_button = tk.Button(
            log_controls_frame,
            text="🗑️ Clear Log",
            command=self.clear_log,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 10)
        )
        clear_log_button.pack(side=tk.LEFT, padx=5)
        
        save_log_button = tk.Button(
            log_controls_frame,
            text="💾 Save Log",
            command=self.save_log,
            bg='#3498db',
            fg='white',
            font=('Arial', 10)
        )
        save_log_button.pack(side=tk.LEFT, padx=5)
        
        self.update_system_info()
    
    def create_android_tab(self):
        """Create Android setup guide tab."""
        android_frame = ttk.Frame(self.notebook)
        self.notebook.add(android_frame, text="📱 Android Setup")
        
        # Setup guide
        guide_frame = ttk.LabelFrame(android_frame, text="NFCGate Android APK Setup Guide", padding=10)
        guide_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        setup_text = """
📱 ANDROID NFCGATE APK SETUP GUIDE

🔧 STEP 1: Install NFCGate APK
• Download NFCGate APK from official source
• Enable "Install from unknown sources" in Android settings
• Install the APK on your Android device

🌐 STEP 2: Network Configuration
• Connect your Android device to the same WiFi network as this computer
• Note your computer's IP address (shown in System Status tab)
• Ensure no firewall is blocking port 8080

📱 STEP 3: Configure NFCGate App
• Open NFCGate app on Android
• Go to Settings → Connection
• Set Server Host: [Your Computer IP]
• Set Server Port: 8080
• Enable "External Server Mode"

🔗 STEP 4: Connect to Server
• Start the NFCGate server using the Server Control tab
• In NFCGate app, tap "Connect to Server"
• Verify connection in Device Management tab

🧪 STEP 5: Test NFC Operations
• Use "Read Card" to read NFC cards
• Use "Emulate Card" to emulate payment cards
• Monitor real-time data in System Status tab

✅ TROUBLESHOOTING:
• Check firewall settings if connection fails
• Verify both devices are on same network
• Restart server if connection issues persist
• Check system log for detailed error messages
        """
        
        setup_display = scrolledtext.ScrolledText(
            guide_frame,
            wrap=tk.WORD,
            bg='#f8f9fa',
            font=('Arial', 10),
            height=25
        )
        setup_display.insert(tk.END, setup_text)
        setup_display.config(state=tk.DISABLED)
        setup_display.pack(fill=tk.BOTH, expand=True)
    
    def start_server(self):
        """Start the NFCGate server."""
        if self.running:
            self.log_message("⚠️ Server is already running")
            return
        
        try:
            host = self.host_entry.get() or '0.0.0.0'
            port = int(self.port_entry.get() or 8080)
            
            self.server = NFCGateServer(host=host, port=port)
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            
            self.running = True
            self.status_label.config(text="🟢 Server Running", fg='green')
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            self.log_message(f"🚀 NFCGate server started on {host}:{port}")
            self.update_server_info()
            
        except Exception as e:
            self.log_message(f"❌ Failed to start server: {e}")
            messagebox.showerror("Server Error", f"Failed to start server: {e}")
    
    def stop_server(self):
        """Stop the NFCGate server."""
        if not self.running:
            self.log_message("⚠️ Server is not running")
            return
        
        try:
            if self.server:
                self.server.stop()
            
            self.running = False
            self.status_label.config(text="🔴 Server Stopped", fg='red')
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            self.log_message("🛑 NFCGate server stopped")
            self.update_server_info()
            
        except Exception as e:
            self.log_message(f"❌ Error stopping server: {e}")
    
    def restart_server(self):
        """Restart the NFCGate server."""
        self.log_message("🔄 Restarting server...")
        self.stop_server()
        time.sleep(1)
        self.start_server()
    
    def run_server(self):
        """Run the server in background thread."""
        try:
            if self.server:
                self.server.start()
        except Exception as e:
            self.log_message(f"❌ Server error: {e}")
            self.running = False
            self.root.after(0, lambda: self.status_label.config(text="🔴 Server Error", fg='red'))
    
    def refresh_devices(self):
        """Refresh the device list."""
        # Clear existing items
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # Add sample devices (in real implementation, get from server)
        if self.running and self.server:
            # Get connected devices from server
            devices = getattr(self.server, 'connected_devices', {})
            for device_id, device_info in devices.items():
                self.device_tree.insert('', tk.END, values=(
                    device_id,
                    device_info.get('ip', 'Unknown'),
                    device_info.get('type', 'Android'),
                    device_info.get('status', 'Connected'),
                    device_info.get('connected_time', 'Now')
                ))
        
        self.log_message("🔄 Device list refreshed")
    
    def disconnect_device(self):
        """Disconnect selected device."""
        selected = self.device_tree.selection()
        if selected:
            device_id = self.device_tree.item(selected[0])['values'][0]
            self.log_message(f"🔌 Disconnecting device: {device_id}")
            # In real implementation, disconnect device from server
            self.refresh_devices()
    
    def update_server_info(self):
        """Update server information display."""
        info = f"""
🌐 Server Configuration:
   Host: {self.config['server_host']}
   Port: {self.config['server_port']}
   Max Clients: {self.config['max_clients']}
   Encryption: {'Enabled' if self.config['encryption_enabled'] else 'Disabled'}
   
📊 Server Status:
   Running: {'Yes' if self.running else 'No'}
   Connected Devices: {len(getattr(self.server, 'connected_devices', {}))}
   Uptime: {'Running' if self.running else 'Stopped'}
   
🔧 Features:
   ✅ Android NFCGate APK Support
   ✅ Real-time NFC Operations
   ✅ Multi-device Support
   ✅ Session Management
   ✅ Live Monitoring
        """
        
        self.server_info.delete(1.0, tk.END)
        self.server_info.insert(tk.END, info)
    
    def update_system_info(self):
        """Update system information display."""
        import socket
        import platform
        
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            hostname = "Unknown"
            local_ip = "Unknown"
        
        info = f"""
💻 System Information:
   Platform: {platform.system()} {platform.release()}
   Hostname: {hostname}
   Local IP: {local_ip}
   Python: {platform.python_version()}
   
🔧 NFCGate Integration:
   Status: Ready
   Admin Panel: Available
   Test Suite: Available
        """
        
        self.system_info.delete(1.0, tk.END)
        self.system_info.insert(tk.END, info)
    
    def log_message(self, message):
        """Add message to log display."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear the log display."""
        self.log_text.delete(1.0, tk.END)
        self.log_message("📝 Log cleared")
    
    def save_log(self):
        """Save log to file."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_file = f"logs/nfcgate_launcher_{timestamp}.log"
            
            os.makedirs("logs", exist_ok=True)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            
            self.log_message(f"💾 Log saved to {log_file}")
            messagebox.showinfo("Log Saved", f"Log saved to {log_file}")
            
        except Exception as e:
            self.log_message(f"❌ Failed to save log: {e}")
            messagebox.showerror("Save Error", f"Failed to save log: {e}")
    
    def load_config(self):
        """Load configuration from file."""
        try:
            config_file = "config/nfcgate_launcher.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
                self.log_message("⚙️ Configuration loaded")
        except Exception as e:
            self.log_message(f"⚠️ Could not load config: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        try:
            # Update config from GUI
            self.config['server_host'] = self.host_entry.get()
            self.config['server_port'] = int(self.port_entry.get())
            self.config['max_clients'] = int(self.max_clients_entry.get())
            self.config['enable_logging'] = self.logging_var.get()
            self.config['auto_start'] = self.auto_start_var.get()
            self.config['encryption_enabled'] = self.encryption_var.get()
            
            # Save to file
            os.makedirs("config", exist_ok=True)
            config_file = "config/nfcgate_launcher.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            
            self.log_message("💾 Configuration saved")
            self.update_server_info()
            messagebox.showinfo("Config Saved", "Configuration saved successfully!")
            
        except Exception as e:
            self.log_message(f"❌ Failed to save config: {e}")
            messagebox.showerror("Save Error", f"Failed to save configuration: {e}")
    
    def run(self):
        """Run the launcher."""
        self.log_message("🚀 NFCGate Launcher started")
        
        # Auto-start server if configured
        if self.config['auto_start']:
            self.log_message("🔄 Auto-starting server...")
            self.root.after(1000, self.start_server)
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log_message("🛑 Launcher stopped by user")
        finally:
            if self.running:
                self.stop_server()

def main():
    """Main function."""
    print("🚀 Starting NFCGate Complete System Launcher...")
    print("=" * 60)
    print("Full-featured launcher for NFCGate Android APK integration")
    print("Includes server control, device management, and monitoring")
    print("=" * 60)
    
    try:
        launcher = NFCGateLauncher()
        launcher.run()
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
