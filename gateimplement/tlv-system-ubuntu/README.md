# TLV Credit Card System - Ubuntu Server Package

## Quick Start

1. **Extract and Deploy:**
   ```bash
   unzip tlv-system-ubuntu.zip
   cd tlv-system-ubuntu
   ./deploy.sh
   ```

2. **Access the System:**
   - Admin Panel: http://YOUR_SERVER_IP:5000
   - NFCGate Server: YOUR_SERVER_IP:8080

## What's Included

- Complete TLV credit card system source code
- Ubuntu server deployment scripts
- Systemd service configurations
- Nginx reverse proxy configuration
- Automated installation and setup
- Comprehensive documentation

## Requirements

- Ubuntu 20.04+ (22.04 recommended)
- 2GB RAM minimum (4GB recommended)
- 10GB free disk space
- Internet connection for dependencies

## Support

- See `UBUNTU_DEPLOYMENT_GUIDE.md` for detailed instructions
- Check logs: `sudo journalctl -u tlv-nfcgate -u tlv-admin -f`
- Status check: `sudo systemctl status tlv-nfcgate tlv-admin`

## Features

✅ Complete credit card system with EMV support
✅ NFCGate Android integration
✅ Real-time transaction monitoring
✅ Relay mode and MITM capabilities
✅ Web-based admin panel
✅ Database learning system
✅ Professional Ubuntu deployment
