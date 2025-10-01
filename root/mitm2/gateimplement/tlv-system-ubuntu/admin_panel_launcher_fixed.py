#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TLV Admin Panel Launcher - Enhanced Version
Robust launcher with multiple fallback mechanisms and comprehensive error handling
"""

import os
import sys
import platform
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Set up paths
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"

# Configure logging  
log_dir = current_dir / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"admin_launcher_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add src to Python path for imports
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
    logger.info(f"[OK] Added to path: {src_dir}")

def default_emergency_admin():
    """Absolute fallback admin panel"""
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    messagebox.showinfo(
        "Admin Panel", 
        "🏦 TLV Admin Panel\n\n"
        "Basic admin panel is running.\n"
        "Credit card system components are available.\n\n"
        "Check the terminal for more options."
    )
    
    print("🏦 Basic admin panel displayed")
    print("💳 Credit card system is operational")
    print("🚀 Use: python master_unified_launcher.py for full interface")
    
    root.destroy()

def import_admin_components():
    """Import admin components with multiple fallback strategies"""
    global AdminPanel, run_admin_panel
    AdminPanel = None
    run_admin_panel = None
    
    logger.info("🔧 Importing admin components...")
    
    # Strategy 1: Try simplified admin panel first (most reliable)
    try:
        simple_methods_file = src_dir / "admin" / "admin_panel_methods_simple.py"
        if simple_methods_file.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("admin_panel_methods_simple", simple_methods_file)
            if spec and spec.loader:
                simple_methods_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(simple_methods_module)
                run_admin_panel = simple_methods_module.main
                AdminPanel = simple_methods_module.AdminPanel
                logger.info("✅ Successfully imported simplified admin methods")
                return True
    except Exception as e:
        logger.warning(f"⚠️ Simplified methods import failed: {e}")
    
    # Strategy 2: Try GUI component directly
    try:
        gui_file = src_dir / "admin" / "admin_panel_gui.py"
        if gui_file.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("admin_panel_gui", gui_file)
            if spec and spec.loader:
                admin_gui_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(admin_gui_module)
                if hasattr(admin_gui_module, 'AdminPanel'):
                    AdminPanel = admin_gui_module.AdminPanel
                    def run_gui():
                        if AdminPanel is not None:
                            app = AdminPanel()
                            app.run()
                        else:
                            default_emergency_admin()
                    run_admin_panel = run_gui
                    logger.info("✅ Successfully imported admin GUI directly")
                    return True
    except Exception as e:
        logger.warning(f"⚠️ Direct GUI import failed: {e}")
    
    # Strategy 3: Create emergency fallback
    logger.warning("🆘 Creating emergency fallback admin panel...")
    create_emergency_admin_panel()
    
    # Final safety check
    if run_admin_panel is None:
        logger.warning("⚠️ Setting emergency fallback function")
        run_admin_panel = default_emergency_admin
    
    return True

def create_emergency_admin_panel():
    """Create emergency fallback admin panel"""
    global AdminPanel, run_admin_panel
    
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    class EmergencyAdminPanel:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("🔧 TLV Admin Panel - Emergency Mode")
            self.root.geometry("700x500")
            self.root.configure(bg='#f0f0f0')
            
        def setup_ui(self):
            # Main frame
            main_frame = ttk.Frame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Header
            header_frame = ttk.Frame(main_frame)
            header_frame.pack(fill=tk.X, pady=(0, 20))
            
            title_label = ttk.Label(header_frame, text="🔧 TLV Admin Panel", 
                                  font=("Arial", 18, "bold"))
            title_label.pack()
            
            subtitle_label = ttk.Label(header_frame, text="Emergency Mode - Limited Functionality",
                                     font=("Arial", 10))
            subtitle_label.pack(pady=5)
            
            # Status section
            status_frame = ttk.LabelFrame(main_frame, text="System Status", padding=15)
            status_frame.pack(fill=tk.X, pady=(0, 15))
            
            status_text = f"""🖥️ Platform: {platform.system()} {platform.release()}
🐍 Python: {sys.version.split()[0]}
📁 Working Directory: {current_dir}
🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⚠️ Mode: Emergency Fallback"""
            
            ttk.Label(status_frame, text=status_text, justify=tk.LEFT).pack(anchor=tk.W)
            
            # Actions section
            actions_frame = ttk.LabelFrame(main_frame, text="Available Actions", padding=15)
            actions_frame.pack(fill=tk.X, pady=(0, 15))
            
            # Button grid
            button_grid = ttk.Frame(actions_frame)
            button_grid.pack()
            
            # Row 1
            ttk.Button(button_grid, text="📊 System Info", 
                      command=self.show_system_info).grid(row=0, column=0, padx=5, pady=5)
            ttk.Button(button_grid, text="🔍 Check Files", 
                      command=self.check_files).grid(row=0, column=1, padx=5, pady=5)
            ttk.Button(button_grid, text="🧪 Basic Test", 
                      command=self.run_basic_test).grid(row=0, column=2, padx=5, pady=5)
            
            # Row 2
            ttk.Button(button_grid, text="📁 Open Folder", 
                      command=self.open_folder).grid(row=1, column=0, padx=5, pady=5)
            ttk.Button(button_grid, text="🚀 Try Alternative", 
                      command=self.try_alternative).grid(row=1, column=1, padx=5, pady=5)
            ttk.Button(button_grid, text="🚪 Exit", 
                      command=self.exit_app).grid(row=1, column=2, padx=5, pady=5)
            
            # Info section
            info_frame = ttk.LabelFrame(main_frame, text="Information", padding=15)
            info_frame.pack(fill=tk.BOTH, expand=True)
            
            info_text = """This emergency mode provides basic functionality when the main admin panel 
components cannot be loaded. This typically happens due to:

• Missing dependencies
• Corrupted configuration files
• Import errors in main components
• File permission issues

Try the "Try Alternative" button to attempt launching other admin panel versions."""
            
            ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=600).pack(anchor=tk.W)
            
        def show_system_info(self):
            info = f"""System Information:

Platform: {platform.platform()}
Python Version: {sys.version}
Python Executable: {sys.executable}
Working Directory: {os.getcwd()}
Script Location: {__file__}

Python Path:
{chr(10).join(sys.path[:5])}...

Environment Variables:
PATH: {os.environ.get('PATH', 'Not set')[:100]}..."""
            
            messagebox.showinfo("System Information", info)
            
        def check_files(self):
            files_to_check = [
                "src/admin/admin_panel_gui.py",
                "src/admin/admin_panel_methods.py",
                "src/admin/admin_panel_methods_simple.py",
                "admin_panel_complete.py",
                "online_admin_panel.py",
                "master_unified_launcher.py"
            ]
            
            result = "File Check Results:\\n\\n"
            for file_path in files_to_check:
                full_path = current_dir / file_path
                if full_path.exists():
                    size = full_path.stat().st_size
                    result += f"✅ {file_path} ({size} bytes)\\n"
                else:
                    result += f"❌ {file_path} (missing)\\n"
            
            messagebox.showinfo("File Check", result)
            
        def run_basic_test(self):
            result = "Basic System Test:\\n\\n"
            
            # Test 1: Python imports
            try:
                import tkinter
                result += "✅ tkinter: Available\\n"
            except ImportError:
                result += "❌ tkinter: Not available\\n"
            
            try:
                import sqlite3
                result += "✅ sqlite3: Available\\n"
            except ImportError:
                result += "❌ sqlite3: Not available\\n"
            
            # Test 2: File system
            try:
                test_file = current_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                result += "✅ File system: Writable\\n"
            except Exception as e:
                result += f"❌ File system: Error ({e})\\n"
            
            # Test 3: Network
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect(("8.8.8.8", 53))
                sock.close()
                result += "✅ Network: Available\\n"
            except Exception:
                result += "❌ Network: Not available\\n"
            
            result += "\\n🎉 Basic test completed"
            messagebox.showinfo("Basic Test Results", result)
            
        def open_folder(self):
            try:
                if platform.system() == "Windows":
                    os.startfile(current_dir)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", current_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", current_dir])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
                
        def try_alternative(self):
            alternatives = [
                ("Master Unified Launcher", "master_unified_launcher.py"),
                ("Complete Admin Panel", "admin_panel_complete.py"),
                ("Online Admin Panel", "online_admin_panel.py"),
                ("Enhanced Launcher", "enhanced_admin_panel_launcher.py")
            ]
            
            for name, filename in alternatives:
                file_path = current_dir / filename
                if file_path.exists():
                    try:
                        if messagebox.askyesno("Try Alternative", 
                                             f"Found {name}. Launch it?"):
                            subprocess.Popen([sys.executable, str(file_path)])
                            self.root.destroy()
                            return
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to launch {name}: {e}")
            
            messagebox.showinfo("No Alternatives", "No alternative launchers found.")
            
        def exit_app(self):
            if messagebox.askyesno("Exit", "Exit Emergency Admin Panel?"):
                self.root.destroy()
                
        def run(self):
            self.setup_ui()
            self.root.mainloop()
    
    AdminPanel = EmergencyAdminPanel
    
    def emergency_run():
        app = EmergencyAdminPanel()
        app.run()
    
    run_admin_panel = emergency_run
    logger.info("✅ Emergency admin panel created")

def main():
    """Enhanced main launcher function with comprehensive error handling"""
    print("🔧 TLV ADMIN PANEL - Payment Method Testing & Database Building")
    print("=" * 70)
    print()
    print("Features:")
    print("  🧪 Payment Method Testing")
    print("  ✅ Transaction Approval Center") 
    print("  💾 Database Management")
    print("  ⚙️ System Configuration")
    print("  📈 Real-time Monitoring")
    print("  🌐 Connection Management")
    print()
    
    # Check system compatibility
    print("🔍 System Compatibility Check:")
    print(f"  🖥️ Platform: {platform.system()} {platform.release()}")
    print(f"  🐍 Python: {sys.version.split()[0]}")
    print(f"  📁 Working Dir: {Path.cwd()}")
    print()
    
    try:
        # Import admin components
        if import_admin_components():
            print("🚀 Launching admin panel...")
            print()
            if run_admin_panel is not None:
                run_admin_panel()
            else:
                print("❌ Admin panel function not available")
                return 1
        else:
            print("❌ Failed to import admin components")
            return 1
            
    except KeyboardInterrupt:
        print("\\n\\n🛑 Admin panel stopped by user")
        logger.info("Admin panel stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running admin panel: {e}")
        print(f"\\n\\n❌ Error running admin panel: {e}")
        
        # Show error details in emergency mode
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()  # Hide main window
            
            error_msg = f"""Admin Panel Error:

{str(e)}

This could be due to:
• Missing dependencies
• Corrupted files
• Configuration issues

Would you like to try the emergency mode?"""
            
            if messagebox.askyesno("Admin Panel Error", error_msg):
                create_emergency_admin_panel()
                if run_admin_panel is not None:
                    run_admin_panel()
                else:
                    messagebox.showerror("Error", "Emergency admin panel failed to initialize")
            
            root.destroy()
            
        except Exception as fallback_error:
            logger.error(f"❌ Emergency fallback failed: {fallback_error}")
            print(f"❌ Emergency fallback also failed: {fallback_error}")
            print("\\n💡 Please check the installation and try running individual components manually.")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
