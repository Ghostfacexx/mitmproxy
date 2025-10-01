#!/bin/bash

# TLV System Ubuntu Deployment Script
echo "🐧 TLV System - Ubuntu Server Deployment"
echo "========================================"

# Check if running as root for system deployment
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root - will deploy as system service"
    DEPLOY_MODE="system"
else
    echo "👤 Running as user - checking sudo access..."
    if sudo -n true 2>/dev/null; then
        echo "✅ Sudo access available"
        DEPLOY_MODE="system"
    else
        echo "❌ No sudo access - will deploy in user mode"
        DEPLOY_MODE="user"
    fi
fi

# Make scripts executable
chmod +x ubuntu-install.sh
chmod +x ubuntu-deploy.sh

if [ "$DEPLOY_MODE" = "system" ]; then
    echo "🚀 Starting system deployment..."
    ./ubuntu-install.sh
    sudo ./ubuntu-deploy.sh
else
    echo "👤 Starting user deployment..."
    ./ubuntu-install.sh --user
    ./ubuntu-deploy.sh --user
fi

echo "✅ Deployment complete!"
echo ""
echo "🌐 Access Points:"
echo "   Admin Panel: http://localhost:5000"
echo "   NFCGate Server: localhost:8080"
echo ""
echo "📊 Management Commands:"
echo "   Status: sudo systemctl status tlv-nfcgate tlv-admin"
echo "   Logs: sudo journalctl -u tlv-nfcgate -u tlv-admin -f"
echo "   Start: sudo systemctl start tlv-nfcgate tlv-admin"
echo "   Stop: sudo systemctl stop tlv-nfcgate tlv-admin"
