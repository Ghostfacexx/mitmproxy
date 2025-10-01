# 🔧 ADMIN PANEL GUI - QUICK REFERENCE

## 🚀 Launch Commands

### Recommended (Auto-install dependencies)

```bash
python enhanced_admin_panel_launcher.py
```bash

### Direct Launch

```bash
python src/admin/admin_panel_gui.py
```bash

### Test First

```bash
python test_connection_management.py
```bash

---

## 📊 GUI Features

| Tab | Icon | Purpose |
|-----|------|---------|
| Payment Testing | 🧪 | Test payment methods and cards |
| Approval Center | ✅ | Review and approve transactions |
| Database Manager | 💾 | Browse scripts and results |
| **Connections** | **🌐** | **Manage IP connections, sessions & rooms** |
| Settings | ⚙️ | Configure system settings |
| Monitoring | 📊 | View logs and system status |

---

## 🌐 NEW: Connection Management Features

### Connect to Server

1. Go to **Connections** tab
2. Enter target IP address (e.g., 127.0.0.1)
3. Enter port number (e.g., 5000)
4. Click **"🔗 Connect"**
5. Monitor connection status (🟢 Connected / 🔴 Disconnected)

### Verify IP Connection

1. Enter IP address in target field
2. Click **"✅ Verify IP"**
3. View comprehensive report:
   - DNS resolution check
   - Ping connectivity test
   - Port scanning results
   - Network information
4. Save verification report if needed

### Create Client Rooms

1. Ensure connection is established
2. Enter room name (unique identifier)
3. Select room type:
   - **Payment Testing** - For transaction testing
   - **Admin Panel** - Administrative access
   - **Monitoring** - System monitoring
   - **Debugging** - Development/troubleshooting
   - **Private** - Restricted access
4. Set max clients (1-100)
5. Click **"➕ Create Room"**

### Network Diagnostic Tools

- **📡 Ping IP** - Test basic connectivity
- **🔍 Port Scan** - Discover available services (configurable range)
- **🗺️ Trace Route** - Analyze network path to target
- **🔄 Refresh** - Update connection information
- **📢 Broadcast** - Send messages to connected clients
- **📤 Export** - Save connection logs and reports

---

## 🎯 Quick Actions

### Run a Payment Test

1. Go to **Payment Testing** tab
2. Select card brand (Visa, Mastercard, etc.)
3. Choose payment method (CDCVM, Signature, etc.)
4. Click **"🧪 Run Single Test"**

### Approve Transaction

1. Go to **Approval Center** tab
2. Select pending transaction
3. Set confidence level and risk
4. Click **"✅ Approve & Generate Script"**

### Manage Connections

1. Go to **Connections** tab
2. Connect to target server
3. Create rooms for different client types
4. Monitor active sessions and clients
5. Use network tools for diagnostics

### Export Data

1. Go to **Database Manager** tab
2. Click **"📤 Export Database"**
3. Choose file location
4. Save as JSON

---

## 🔧 Configuration

### Connection Settings

- **Default IP**: 127.0.0.1 (localhost)
- **Default Port**: 5000
- **Connection Timeout**: 10 seconds
- **Auto-refresh**: Every 10 seconds

### Room Types Available

- **Payment Testing** - Transaction testing and validation
- **Admin Panel** - Administrative access and control
- **Monitoring** - System monitoring and logging
- **Debugging** - Development and troubleshooting
- **Private** - Restricted access rooms

### Payment Methods Available

- **CDCVM** - Consumer Device Cardholder Verification
- **Signature** - Signature Verification
- **No CVM** - No Cardholder Verification
- **PIN** - PIN Verification
- **Contactless** - Contactless Payment

### Terminal Types

- **POS** - Point of Sale
- **ATM** - Automated Teller Machine
- **Mobile** - Mobile Payment Terminal
- **Transit** - Public Transport Terminal
- **Contactless** - Contactless Reader

---

## 📁 File Locations

- **Database:** `database/admin_panel.db`
- **Generated Scripts:** `generated_scripts/`
- **Connection Logs:** `connection_log_YYYYMMDD_HHMMSS.json`
- **IP Verification Reports:** `ip_verification_IP_YYYYMMDD_HHMMSS.txt`
- **Backups:** `backups/`
- **Config Files:** `config/`

---

## ⚠️ Troubleshooting

### GUI Won't Start

1. Run: `python enhanced_admin_panel_launcher.py`
2. Check dependencies are installed
3. Verify Tkinter is available

### Connection Issues

1. Verify IP address format (use ✅ Verify IP)
2. Check port accessibility
3. Ensure target server is running
4. Check firewall settings

### Database Issues

1. Check `database/` folder exists
2. Verify write permissions
3. Try running as administrator

### Import Errors

1. Install missing packages: `pip install flask flask-socketio`
2. Check Python version (3.6+ required)
3. Verify file paths are correct

---

## 🌐 Connection Management Workflow

### 1. Initial Setup

```text
Enter IP → Enter Port → Click Connect → Verify Connection
```text

### 2. Session Management

```text
Connection Established → Session Created → Monitor Status
```text

### 3. Room Creation

```text
Name Room → Select Type → Set Max Clients → Create Room
```text

### 4. Client Management

```bash
Monitor Clients → View Details → Manage Access → Broadcast Messages
```text

### 5. Network Diagnostics

```text
Ping Test → Port Scan → Trace Route → Export Results
```text

---

## 🎉 Status: ✅ FULLY OPERATIONAL

All components tested and working correctly:

- ✅ Connection management with IP confirmation
- ✅ Session tracking and monitoring
- ✅ Multiple room types for different clients
- ✅ Real-time status indicators
- ✅ Network diagnostic tools
- ✅ Export and logging capabilities
