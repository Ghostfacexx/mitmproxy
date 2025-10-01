#!/usr/bin/env python3
"""
NFCGate MITM Troubleshooting Tool
Diagnoses and fixes common connection issues
"""

import socket
import subprocess
import sys
import time
import json
import logging
import psutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NFCGateTroubleshooter:
    def __init__(self):
        self.config_file = "config.json"
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Config file not found, using defaults")
            return {
                "server": {"listen_port": 8080, "target_host": "127.0.0.1", "target_port": 5566},
                "security": {"allowed_ips": ["77.85.97.37", "127.0.0.1"]}
            }
    
    def check_port_availability(self, host: str, port: int) -> bool:
        """Check if a port is available for binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, port))
                return True
        except OSError:
            return False
    
    def check_port_listening(self, host: str, port: int) -> bool:
        """Check if a service is listening on a port"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                result = s.connect_ex((host, port))
                return result == 0
        except:
            return False
    
    def find_process_using_port(self, port: int) -> list:
        """Find processes using a specific port"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                connections = proc.connections('tcp') if hasattr(proc, 'connections') else []
                for conn in connections:
                    if conn.laddr and conn.laddr.port == port:
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'port': port
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
                pass
        return processes
    
    def check_firewall_rules(self) -> dict:
        """Check Windows firewall rules for the ports"""
        try:
            # Check if ports are blocked by firewall
            listen_port = self.config["server"]["listen_port"]
            target_port = self.config["server"]["target_port"]
            
            # On Windows, check firewall rules
            if sys.platform == "win32":
                try:
                    # Check inbound rules
                    cmd = f'netsh advfirewall firewall show rule name=all | findstr "{listen_port}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    firewall_blocking = "Block" in result.stdout
                    
                    return {
                        "firewall_checked": True,
                        "potentially_blocking": firewall_blocking,
                        "recommendation": "Check Windows Firewall settings" if firewall_blocking else "Firewall OK"
                    }
                except:
                    return {"firewall_checked": False, "error": "Could not check firewall"}
            
            return {"firewall_checked": False, "platform": sys.platform}
        except Exception as e:
            return {"error": str(e)}
    
    def check_network_connectivity(self) -> dict:
        """Check network connectivity to external IPs"""
        results = {}
        allowed_ips = self.config.get("security", {}).get("allowed_ips", [])
        
        for ip in allowed_ips:
            if ip == "127.0.0.1":
                continue
                
            try:
                # Try to connect to the IP (basic connectivity test)
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((ip, 80))  # Try HTTP port
                sock.close()
                latency = time.time() - start_time
                
                results[ip] = {
                    "reachable": result == 0,
                    "latency_ms": round(latency * 1000, 2),
                    "note": "Basic connectivity test"
                }
            except Exception as e:
                results[ip] = {"error": str(e)}
        
        return results
    
    def diagnose_connection_refused(self) -> dict:
        """Diagnose 'Connection refused' errors"""
        target_host = self.config["server"]["target_host"]
        target_port = self.config["server"]["target_port"]
        
        diagnosis = {
            "target": f"{target_host}:{target_port}",
            "issues": [],
            "recommendations": []
        }
        
        # Check if target port is listening
        if not self.check_port_listening(target_host, target_port):
            diagnosis["issues"].append(f"NFCGate service not listening on {target_host}:{target_port}")
            diagnosis["recommendations"].append("Start NFCGate service or use mock mode")
        
        # Check for port conflicts
        processes = self.find_process_using_port(target_port)
        if processes:
            diagnosis["issues"].append(f"Port {target_port} in use by: {processes}")
        
        # Check if we can bind to listen port
        listen_port = self.config["server"]["listen_port"]
        if not self.check_port_availability("0.0.0.0", listen_port):
            diagnosis["issues"].append(f"Cannot bind to listen port {listen_port}")
            diagnosis["recommendations"].append(f"Kill process using port {listen_port} or use different port")
        
        return diagnosis
    
    def suggest_fixes(self) -> list:
        """Suggest fixes for common issues"""
        fixes = []
        
        # Check if NFCGate service is running
        target_host = self.config["server"]["target_host"]
        target_port = self.config["server"]["target_port"]
        
        if not self.check_port_listening(target_host, target_port):
            fixes.append({
                "issue": "NFCGate service not running",
                "fix": "Enable mock mode in config.json or start actual NFCGate service",
                "command": "python nfcgate_mitm.py # Will auto-start mock service"
            })
        
        # Check for port conflicts
        listen_port = self.config["server"]["listen_port"]
        processes = self.find_process_using_port(listen_port)
        if processes:
            for proc in processes:
                fixes.append({
                    "issue": f"Port {listen_port} in use by {proc['name']} (PID: {proc['pid']})",
                    "fix": f"Kill process or change port",
                    "command": f"taskkill /PID {proc['pid']} /F"
                })
        
        # Network connectivity issues
        connectivity = self.check_network_connectivity()
        for ip, result in connectivity.items():
            if "error" in result or not result.get("reachable", False):
                fixes.append({
                    "issue": f"Cannot reach {ip}",
                    "fix": "Check network connectivity or firewall settings",
                    "command": f"ping {ip}"
                })
        
        return fixes
    
    def run_full_diagnosis(self):
        """Run complete diagnostic check"""
        print("?? NFCGate MITM Troubleshooting Report")
        print("=" * 50)
        
        # 1. Port Status
        print("\n?? Port Status:")
        listen_port = self.config["server"]["listen_port"]
        target_port = self.config["server"]["target_port"]
        target_host = self.config["server"]["target_host"]
        
        print(f"  Listen Port {listen_port}: {'? Available' if self.check_port_availability('0.0.0.0', listen_port) else '? In Use'}")
        print(f"  Target {target_host}:{target_port}: {'? Listening' if self.check_port_listening(target_host, target_port) else '? Not Listening'}")
        
        # 2. Process Check
        print(f"\n?? Processes using port {listen_port}:")
        processes = self.find_process_using_port(listen_port)
        if processes:
            for proc in processes:
                print(f"  - {proc['name']} (PID: {proc['pid']})")
        else:
            print("  None found")
        
        # 3. Connection Refused Diagnosis
        print(f"\n?? Connection Refused Analysis:")
        diagnosis = self.diagnose_connection_refused()
        if diagnosis["issues"]:
            for issue in diagnosis["issues"]:
                print(f"  ? {issue}")
        else:
            print("  ? No obvious issues detected")
        
        # 4. Network Connectivity
        print(f"\n?? Network Connectivity:")
        connectivity = self.check_network_connectivity()
        for ip, result in connectivity.items():
            if "error" in result:
                print(f"  ? {ip}: {result['error']}")
            elif result.get("reachable"):
                print(f"  ? {ip}: Reachable ({result['latency_ms']}ms)")
            else:
                print(f"  ?? {ip}: Not reachable")
        
        # 5. Firewall Check
        print(f"\n??? Firewall Check:")
        firewall = self.check_firewall_rules()
        if firewall.get("firewall_checked"):
            if firewall.get("potentially_blocking"):
                print(f"  ?? Firewall may be blocking traffic")
            else:
                print(f"  ? Firewall appears OK")
        else:
            print(f"  ?? Could not check firewall automatically")
        
        # 6. Suggested Fixes
        print(f"\n?? Suggested Fixes:")
        fixes = self.suggest_fixes()
        if fixes:
            for i, fix in enumerate(fixes, 1):
                print(f"  {i}. {fix['issue']}")
                print(f"     Fix: {fix['fix']}")
                print(f"     Command: {fix['command']}")
                print()
        else:
            print("  ? No obvious issues to fix")
        
        # 7. Quick Fix Commands
        print(f"\n? Quick Fix Commands:")
        print(f"  Kill processes on port {listen_port}:")
        print(f"    netstat -ano | findstr :{listen_port}")
        print(f"    taskkill /PID <PID> /F")
        print(f"  \n  Start in mock mode:")
        print(f"    python nfcgate_mitm.py")
        print(f"  \n  Test connectivity:")
        print(f"    telnet {target_host} {target_port}")

def main():
    """Main function"""
    troubleshooter = NFCGateTroubleshooter()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "ports":
            # Quick port check
            config = troubleshooter.config
            listen_port = config["server"]["listen_port"]
            target_port = config["server"]["target_port"]
            target_host = config["server"]["target_host"]
            
            print(f"Listen port {listen_port}: {'Available' if troubleshooter.check_port_availability('0.0.0.0', listen_port) else 'In Use'}")
            print(f"Target {target_host}:{target_port}: {'Listening' if troubleshooter.check_port_listening(target_host, target_port) else 'Not Listening'}")
            
        elif command == "fix":
            # Apply automatic fixes
            fixes = troubleshooter.suggest_fixes()
            print(f"Found {len(fixes)} potential fixes:")
            for i, fix in enumerate(fixes, 1):
                print(f"{i}. {fix['issue']}")
                apply = input(f"Apply fix? (y/N): ").strip().lower()
                if apply == 'y':
                    try:
                        subprocess.run(fix['command'], shell=True, check=True)
                        print("? Fix applied")
                    except subprocess.CalledProcessError as e:
                        print(f"? Fix failed: {e}")
        else:
            print("Usage: python troubleshoot.py [ports|fix]")
    else:
        # Full diagnosis
        troubleshooter.run_full_diagnosis()

if __name__ == "__main__":
    main()