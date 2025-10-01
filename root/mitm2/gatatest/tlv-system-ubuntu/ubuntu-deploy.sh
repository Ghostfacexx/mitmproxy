#!/bin/bash
# Ubuntu Server Deployment Script
# This script sets up the TLV system as a proper Ubuntu service

set -e  # Exit on any error

echo "🐧 TLV Credit Card System - Ubuntu Server Deployment"
echo "===================================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root directly"
   echo "Please run as regular user with sudo privileges"
   exit 1
fi

# Variables
INSTALL_DIR="/opt/tlv-system"
SERVICE_USER="tlv"
SERVICE_GROUP="tlv"

# Create service user
echo "👤 Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd --system --home "$INSTALL_DIR" --shell /bin/bash --group "$SERVICE_GROUP" "$SERVICE_USER" || true
fi

# Create installation directory
echo "📁 Creating installation directory..."
sudo mkdir -p "$INSTALL_DIR"
sudo mkdir -p /var/log/tlv-system
sudo mkdir -p /etc/tlv-system

# Copy files to installation directory
echo "📋 Copying system files..."
sudo cp -r . "$INSTALL_DIR/"
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" /var/log/tlv-system

# Set up Python environment
echo "🐍 Setting up Python environment..."
sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && python3 -m venv venv"
sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && source venv/bin/activate && pip install --upgrade pip"

# Install requirements
echo "📦 Installing Python packages..."
if [ -f "$INSTALL_DIR/requirements-ubuntu.txt" ]; then
    sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && source venv/bin/activate && pip install -r requirements-ubuntu.txt"
else
    sudo -u "$SERVICE_USER" bash -c "cd $INSTALL_DIR && source venv/bin/activate && pip install flask flask-socketio cryptography requests protobuf psutil"
fi

# Set up systemd services
echo "⚙️ Setting up systemd services..."
sudo cp ubuntu-config/tlv-nfcgate.service /etc/systemd/system/
sudo cp ubuntu-config/tlv-admin.service /etc/systemd/system/

# Update service files with correct paths
sudo sed -i "s|/opt/tlv-system|$INSTALL_DIR|g" /etc/systemd/system/tlv-nfcgate.service
sudo sed -i "s|/opt/tlv-system|$INSTALL_DIR|g" /etc/systemd/system/tlv-admin.service
sudo sed -i "s|User=tlv|User=$SERVICE_USER|g" /etc/systemd/system/tlv-nfcgate.service
sudo sed -i "s|User=tlv|User=$SERVICE_USER|g" /etc/systemd/system/tlv-admin.service
sudo sed -i "s|Group=tlv|Group=$SERVICE_GROUP|g" /etc/systemd/system/tlv-nfcgate.service
sudo sed -i "s|Group=tlv|Group=$SERVICE_GROUP|g" /etc/systemd/system/tlv-admin.service

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable tlv-nfcgate.service
sudo systemctl enable tlv-admin.service

# Set up Nginx (if installed)
if command -v nginx &> /dev/null; then
    echo "🌐 Configuring Nginx..."
    sudo cp ubuntu-config/nginx-tlv.conf /etc/nginx/sites-available/tlv
    sudo ln -sf /etc/nginx/sites-available/tlv /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
fi

# Create management scripts
echo "📝 Creating management scripts..."
cat > "$INSTALL_DIR/tlv-start.sh" << 'EOF'
#!/bin/bash
echo "🚀 Starting TLV Credit Card System..."
sudo systemctl start tlv-nfcgate
sudo systemctl start tlv-admin
sleep 2
echo "✅ System started!"
./tlv-status.sh
EOF

cat > "$INSTALL_DIR/tlv-stop.sh" << 'EOF'
#!/bin/bash
echo "🛑 Stopping TLV Credit Card System..."
sudo systemctl stop tlv-nfcgate
sudo systemctl stop tlv-admin
echo "✅ System stopped!"
EOF

cat > "$INSTALL_DIR/tlv-status.sh" << 'EOF'
#!/bin/bash
echo "📊 TLV Credit Card System Status"
echo "================================"
echo "NFCGate Service: $(systemctl is-active tlv-nfcgate)"
echo "Admin Service: $(systemctl is-active tlv-admin)"
if command -v nginx &> /dev/null; then
    echo "Nginx: $(systemctl is-active nginx)"
fi
echo ""
echo "🌐 Access Information:"
IP=$(hostname -I | awk '{print $1}')
echo "Server IP: $IP"
echo "Admin Panel: http://$IP:5000"
echo "NFCGate Server: $IP:8080"
if command -v nginx &> /dev/null; then
    echo "Nginx Proxy: http://$IP"
fi
echo ""
echo "📁 Important Paths:"
echo "System Directory: /opt/tlv-system"
echo "Logs: /var/log/tlv-system"
echo "Config: /etc/tlv-system"
EOF

cat > "$INSTALL_DIR/tlv-logs.sh" << 'EOF'
#!/bin/bash
echo "📋 TLV System Logs"
echo "=================="
echo ""
echo "🔍 Choose log to view:"
echo "1. NFCGate Service"
echo "2. Admin Service" 
echo "3. System Logs"
echo "4. All Logs (live)"
read -p "Enter choice (1-4): " choice

case $choice in
    1) sudo journalctl -u tlv-nfcgate -f ;;
    2) sudo journalctl -u tlv-admin -f ;;
    3) sudo journalctl -u tlv-nfcgate -u tlv-admin --since "1 hour ago" ;;
    4) sudo journalctl -u tlv-nfcgate -u tlv-admin -f ;;
    *) echo "Invalid choice" ;;
esac
EOF

# Make scripts executable
sudo chmod +x "$INSTALL_DIR"/*.sh
sudo chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"/*.sh

# Set up log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/tlv-system > /dev/null << 'EOF'
/var/log/tlv-system/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 tlv tlv
    postrotate
        systemctl reload tlv-nfcgate tlv-admin || true
    endscript
}
EOF

# Final permissions check
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" /var/log/tlv-system
sudo chmod -R 755 "$INSTALL_DIR"
sudo chmod 644 /var/log/tlv-system/* 2>/dev/null || true

echo ""
echo "✅ Ubuntu deployment completed successfully!"
echo ""
echo "🚀 Management Commands:"
echo "  Start:  $INSTALL_DIR/tlv-start.sh"
echo "  Stop:   $INSTALL_DIR/tlv-stop.sh" 
echo "  Status: $INSTALL_DIR/tlv-status.sh"
echo "  Logs:   $INSTALL_DIR/tlv-logs.sh"
echo ""
echo "🌐 Access URLs:"
IP=$(hostname -I | awk '{print $1}')
echo "  Admin Panel: http://$IP:5000"
echo "  NFCGate Server: $IP:8080"
echo ""
echo "📋 Next Steps:"
echo "1. Run: $INSTALL_DIR/tlv-start.sh"
echo "2. Check status: $INSTALL_DIR/tlv-status.sh"
echo "3. Configure firewall for ports 5000 and 8080"
echo "4. Connect Android NFCGate APK to server"
echo ""
