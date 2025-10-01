#!/bin/bash
# Ubuntu Server Installation Script for TLV Credit Card System
# Run this script on Ubuntu Server to set up the complete system

echo "🚀 TLV Credit Card System - Ubuntu Server Installation"
echo "======================================================"

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3 and pip
echo "🐍 Installing Python 3 and dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install system dependencies
echo "📚 Installing system dependencies..."
sudo apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    sqlite3 \
    curl \
    wget \
    unzip \
    git \
    nginx \
    supervisor

# Create virtual environment
echo "🔧 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up directories with proper permissions
echo "📁 Setting up directories..."
sudo mkdir -p /var/log/tlv-system
sudo mkdir -p /etc/tlv-system
sudo chown -R $USER:$USER /var/log/tlv-system
sudo chown -R $USER:$USER /etc/tlv-system

# Copy configuration files
echo "⚙️ Setting up configuration..."
cp -r config/* /etc/tlv-system/ 2>/dev/null || echo "No config files to copy"

# Set up systemd services
echo "🔧 Setting up systemd services..."
sudo cp ubuntu-config/tlv-nfcgate.service /etc/systemd/system/
sudo cp ubuntu-config/tlv-admin.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable services
echo "🔄 Enabling services..."
sudo systemctl enable tlv-nfcgate.service
sudo systemctl enable tlv-admin.service

# Set up Nginx configuration
echo "🌐 Configuring Nginx..."
sudo cp ubuntu-config/nginx-tlv.conf /etc/nginx/sites-available/tlv
sudo ln -sf /etc/nginx/sites-available/tlv /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Set up firewall
echo "🛡️ Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8080
sudo ufw allow 5000
sudo ufw --force enable

# Create startup script
echo "📝 Creating startup script..."
cat > start-tlv-system.sh << 'EOF'
#!/bin/bash
cd /opt/tlv-system
source venv/bin/activate
echo "🚀 Starting TLV Credit Card System..."
sudo systemctl start tlv-nfcgate
sudo systemctl start tlv-admin
echo "✅ System started successfully!"
echo "🌐 Admin Panel: http://$(hostname -I | awk '{print $1}'):5000"
echo "📱 NFCGate Server: $(hostname -I | awk '{print $1}'):8080"
EOF

chmod +x start-tlv-system.sh

# Create stop script
cat > stop-tlv-system.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping TLV Credit Card System..."
sudo systemctl stop tlv-nfcgate
sudo systemctl stop tlv-admin
echo "✅ System stopped successfully!"
EOF

chmod +x stop-tlv-system.sh

# Create status script
cat > status-tlv-system.sh << 'EOF'
#!/bin/bash
echo "📊 TLV Credit Card System Status"
echo "================================"
echo "NFCGate Server: $(sudo systemctl is-active tlv-nfcgate)"
echo "Admin Panel: $(sudo systemctl is-active tlv-admin)"
echo "Nginx: $(sudo systemctl is-active nginx)"
echo ""
echo "🌐 Network Information:"
echo "Server IP: $(hostname -I | awk '{print $1}')"
echo "Admin Panel: http://$(hostname -I | awk '{print $1}'):5000"
echo "NFCGate Server: $(hostname -I | awk '{print $1}'):8080"
echo ""
echo "📁 Log Files:"
echo "NFCGate: /var/log/tlv-system/nfcgate.log"
echo "Admin: /var/log/tlv-system/admin.log"
echo "System: journalctl -u tlv-nfcgate -u tlv-admin"
EOF

chmod +x status-tlv-system.sh

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🚀 To start the system:"
echo "   ./start-tlv-system.sh"
echo ""
echo "📊 To check status:"
echo "   ./status-tlv-system.sh"
echo ""
echo "🛑 To stop the system:"
echo "   ./stop-tlv-system.sh"
echo ""
echo "🌐 Access URLs (after starting):"
echo "   Admin Panel: http://$(hostname -I | awk '{print $1}'):5000"
echo "   NFCGate Server: $(hostname -I | awk '{print $1}'):8080"
echo ""
