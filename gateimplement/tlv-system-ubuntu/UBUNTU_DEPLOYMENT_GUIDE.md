# 🐧 TLV Credit Card System - Ubuntu Server Deployment Guide

## 📋 **Quick Start**

### **1. Upload and Extract**
```bash
# Upload tlv-system-ubuntu.zip to your Ubuntu server
scp tlv-system-ubuntu.zip user@your-server:/tmp/

# On Ubuntu server, extract and deploy
cd /tmp
unzip tlv-system-ubuntu.zip
cd tlv-system
chmod +x ubuntu-deploy.sh
./ubuntu-deploy.sh
```

### **2. Start the System**
```bash
# Start all services
sudo /opt/tlv-system/tlv-start.sh

# Check status
sudo /opt/tlv-system/tlv-status.sh
```

### **3. Access the System**
- **Admin Panel:** http://YOUR_SERVER_IP:5000
- **NFCGate Server:** YOUR_SERVER_IP:8080

---

## 🛠️ **System Requirements**

### **Ubuntu Server Version**
- Ubuntu 20.04 LTS or newer
- Ubuntu 22.04 LTS (recommended)
- Ubuntu 24.04 LTS (latest)

### **Minimum Hardware**
- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 10GB free space
- **CPU:** 2 cores minimum
- **Network:** Internet connection for installation

### **Required Packages** (auto-installed)
- Python 3.8+
- Nginx (optional, for reverse proxy)
- SQLite3
- OpenSSL

---

## 📦 **Installation Methods**

### **Method 1: Automated Deployment (Recommended)**
```bash
# Extract and run deployment script
unzip tlv-system-ubuntu.zip
cd tlv-system
sudo ./ubuntu-deploy.sh
```

### **Method 2: Manual Installation**
```bash
# Extract files
unzip tlv-system-ubuntu.zip
cd tlv-system

# Run installation script
chmod +x ubuntu-install.sh
./ubuntu-install.sh

# Deploy as service
sudo ./ubuntu-deploy.sh
```

---

## ⚙️ **System Services**

### **Systemd Services Created**
- `tlv-nfcgate.service` - NFCGate server for Android connections
- `tlv-admin.service` - Web admin panel interface

### **Service Management**
```bash
# Start services
sudo systemctl start tlv-nfcgate tlv-admin

# Stop services  
sudo systemctl stop tlv-nfcgate tlv-admin

# Enable auto-start on boot
sudo systemctl enable tlv-nfcgate tlv-admin

# Check status
sudo systemctl status tlv-nfcgate tlv-admin

# View logs
sudo journalctl -u tlv-nfcgate -f
sudo journalctl -u tlv-admin -f
```

---

## 🌐 **Network Configuration**

### **Firewall Setup**
```bash
# Allow required ports
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443  
sudo ufw allow 5000
sudo ufw allow 8080
sudo ufw enable
```

### **Port Usage**
- **5000** - Admin Panel (HTTP)
- **8080** - NFCGate Server (TCP)
- **80** - Nginx Proxy (optional)
- **22** - SSH Access

### **Nginx Configuration** (Optional)
The system includes Nginx configuration for:
- Reverse proxy for admin panel
- SSL termination support
- Static file serving
- Load balancing capability

---

## 📁 **Directory Structure**

```
/opt/tlv-system/                 # Main installation directory
├── venv/                        # Python virtual environment
├── src/                         # Source code
├── config/                      # Configuration files
├── logs/                        # Application logs
├── database/                    # Database files
├── ubuntu-config/               # Ubuntu-specific configs
├── tlv-start.sh                 # Start script
├── tlv-stop.sh                  # Stop script
├── tlv-status.sh               # Status script
└── tlv-logs.sh                 # Log viewer script

/var/log/tlv-system/            # System logs
├── nfcgate.log                 # NFCGate server logs
├── admin.log                   # Admin panel logs
└── error.log                   # Error logs

/etc/tlv-system/                # Configuration files
├── mitm_config.json            # MITM configuration
├── proxy_config.json           # Proxy settings
└── unified_config.json         # Unified system config
```

---

## 🔧 **Management Scripts**

### **Start System**
```bash
sudo /opt/tlv-system/tlv-start.sh
```

### **Stop System**
```bash
sudo /opt/tlv-system/tlv-stop.sh
```

### **Check Status**
```bash
sudo /opt/tlv-system/tlv-status.sh
```

### **View Logs**
```bash
sudo /opt/tlv-system/tlv-logs.sh
```

---

## 📱 **Android NFCGate Setup**

### **1. Install NFCGate APK**
- Download NFCGate APK from official source
- Install on Android device with NFC capability

### **2. Configure Connection**
- Open NFCGate app
- Go to Settings → Connection
- Set Server Host: `YOUR_UBUNTU_SERVER_IP`
- Set Server Port: `8080`
- Enable "External Server Mode"

### **3. Connect to Server**
- Tap "Connect to Server" in NFCGate app
- Verify connection in Admin Panel → Device Management

---

## 🛡️ **Security Configuration**

### **Service Security**
- Services run as non-root user `tlv`
- Restricted filesystem access
- Private temp directories
- No new privileges allowed

### **Network Security**
- UFW firewall configuration
- Rate limiting (via Nginx)
- SSL/TLS support ready
- Security headers configured

### **File Permissions**
```bash
# Check file permissions
ls -la /opt/tlv-system/
ls -la /var/log/tlv-system/

# Fix permissions if needed
sudo chown -R tlv:tlv /opt/tlv-system
sudo chown -R tlv:tlv /var/log/tlv-system
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Service Won't Start**
```bash
# Check service status
sudo systemctl status tlv-nfcgate
sudo systemctl status tlv-admin

# Check logs
sudo journalctl -u tlv-nfcgate --since "10 minutes ago"
sudo journalctl -u tlv-admin --since "10 minutes ago"

# Restart services
sudo systemctl restart tlv-nfcgate tlv-admin
```

#### **Port Already in Use**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :5000
sudo netstat -tulpn | grep :8080

# Kill process if needed
sudo fuser -k 5000/tcp
sudo fuser -k 8080/tcp
```

#### **Permission Issues**
```bash
# Fix ownership
sudo chown -R tlv:tlv /opt/tlv-system
sudo chown -R tlv:tlv /var/log/tlv-system

# Fix permissions
sudo chmod -R 755 /opt/tlv-system
sudo chmod 644 /var/log/tlv-system/*
```

#### **Android Connection Issues**
- Verify server IP address and port
- Check firewall allows port 8080
- Ensure Android and server on same network
- Check NFCGate server logs for connection attempts

### **Log Locations**
- **System logs:** `sudo journalctl -u tlv-nfcgate -u tlv-admin`
- **Application logs:** `/var/log/tlv-system/`
- **Nginx logs:** `/var/log/nginx/`
- **UFW logs:** `/var/log/ufw.log`

---

## 🚀 **Performance Tuning**

### **System Optimization**
```bash
# Increase file limits for high-traffic scenarios
echo "tlv soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "tlv hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize network settings
echo "net.core.somaxconn = 65536" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### **Database Optimization**
- SQLite databases are optimized for concurrent access
- Automatic vacuum and optimization enabled
- WAL mode for better concurrent performance

---

## 🔄 **Updates and Maintenance**

### **Update System**
```bash
# Stop services
sudo /opt/tlv-system/tlv-stop.sh

# Backup current installation
sudo cp -r /opt/tlv-system /opt/tlv-system.backup

# Extract new version
cd /tmp
unzip tlv-system-ubuntu-new.zip
cd tlv-system
sudo ./ubuntu-deploy.sh

# Start services
sudo /opt/tlv-system/tlv-start.sh
```

### **Backup System**
```bash
# Create backup
sudo tar -czf tlv-system-backup-$(date +%Y%m%d).tar.gz \
    /opt/tlv-system \
    /var/log/tlv-system \
    /etc/tlv-system

# Restore backup
sudo tar -xzf tlv-system-backup-YYYYMMDD.tar.gz -C /
```

---

## ✅ **Verification Checklist**

After installation, verify:

- [ ] Services are running: `sudo systemctl status tlv-nfcgate tlv-admin`
- [ ] Admin panel accessible: http://SERVER_IP:5000
- [ ] NFCGate server listening: `sudo netstat -tulpn | grep :8080`
- [ ] Firewall configured: `sudo ufw status`
- [ ] Logs being written: `ls -la /var/log/tlv-system/`
- [ ] Android device can connect to NFCGate server
- [ ] Admin panel shows connected devices

---

## 📞 **Support**

### **Log Collection for Support**
```bash
# Collect system information
sudo /opt/tlv-system/tlv-status.sh > system-info.txt
sudo journalctl -u tlv-nfcgate -u tlv-admin --since "1 hour ago" > service-logs.txt
sudo dmesg | tail -100 > system-logs.txt

# Package for support
tar -czf tlv-support-info.tar.gz system-info.txt service-logs.txt system-logs.txt
```

**The TLV Credit Card System is now ready for production use on Ubuntu Server!** 🎉
