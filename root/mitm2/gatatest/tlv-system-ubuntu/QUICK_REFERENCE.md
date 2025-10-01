# Quick Reference - NFC Proxy Commands

## ⚡ **Start the Proxy Server**

### PowerShell (Recommended)

```powershell
# Use dot-slash prefix for local files
.\run.ps1

# OR use ampersand for direct Python execution
& ".venv\Scripts\python.exe" main.py
```bash

### Command Prompt

```cmd
# Direct execution in CMD
.\run.bat

# OR activate environment first
.venv\Scripts\activate
python main.py
```text

## 🧪 **Run Tests**

### PowerShell

```powershell
.\test.ps1
# or  
& ".venv\Scripts\python.exe" test_setup.py
```text

### Command Prompt

```cmd
.\test.bat
# or
.venv\Scripts\python.exe test_setup.py
```bash

## 🔧 **Common Issues & Solutions**

### PowerShell: "not recognized as cmdlet"

**Problem**: `run.bat` not found
**Solution**: Use `.\run.bat` (with dot-slash prefix)

### PowerShell: "Unexpected token"

**Problem**: `"path" main.py` syntax error
**Solution**: Use `& "path" main.py` (with ampersand)

### Python: "No module named"

**Problem**: Missing dependencies
**Solution**: Run `& ".venv\Scripts\python.exe" -m pip install pycryptodome protobuf`

## 📊 **Server Status**

When running, check:

- **TCP Server**: `localhost:8081` (NFCGate clients)
- **HTTP Server**: `localhost:8082` (Web clients)  
- **Status API**: `http://localhost:8082/status`

## 🛑 **Stop the Server**

Press `Ctrl+C` in the terminal window

## 📁 **Important Files**

- **`config/proxy_config.json`**: Server settings
- **`config/mitm_config.json`**: MITM behavior
- **`logs/nfcgate_proxy.log`**: Main log file
- **`keys/private.pem`**: RSA private key

---
*For detailed documentation, see `README.md` and `DEVELOPMENT.md`*
