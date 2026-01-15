# Virtual Environment Guide

## Why Use Virtual Environments?

Virtual environments are isolated Python environments that keep your project dependencies separate from system-wide packages. This prevents conflicts and ensures reproducible builds.

## The Problem: System Python vs Virtual Environment

### System Python (`python3`)
- **Location:** `/usr/bin/python3`
- **Packages:** `/usr/lib/python3.12/site-packages/` and `~/.local/lib/python3.12/site-packages/`
- **Scope:** Shared across your entire system
- **Issues:** 
  - May lack project-specific packages (like `email-validator`)
  - Installing packages requires `sudo` or affects all projects
  - Version conflicts between different projects

### Virtual Environment Python (`venv/bin/python`)
- **Location:** `venv/bin/python` (in your project directory)
- **Packages:** `venv/lib/python3.12/site-packages/` (project-specific)
- **Scope:** Isolated to this project only
- **Benefits:**
  - All project dependencies installed and isolated
  - No conflicts with other projects
  - Reproducible environment for all developers

## Common Error: ModuleNotFoundError

If you see this error:
```
ModuleNotFoundError: No module named 'email_validator'
ImportError: email-validator is not installed, run `pip install 'pydantic[email]'`
```

**Cause:** You're using system Python (`python3`) instead of the virtual environment.

**Solution:** Use one of the three methods below.

## Three Ways to Use the Virtual Environment

### Method 1: Activate the Virtual Environment (Recommended for Development)

```bash
# Activate the virtual environment
source venv/bin/activate

# Your prompt will change to show (venv)
(venv) user@host:~/project$

# Now you can use 'python' and 'pip' normally
python -m api.server
pip install some-package

# When done, deactivate
deactivate
```

**Pros:**
- Most convenient for interactive development
- Use `python` and `pip` without full paths
- Clear visual indicator (prompt shows `(venv)`)

**Cons:**
- Must remember to activate in each new terminal
- Can forget which environment is active

### Method 2: Use Full Path to Virtual Environment Python

```bash
# Run Python from venv directly
venv/bin/python -m api.server

# Install packages with venv pip
venv/bin/pip install some-package
```

**Pros:**
- Explicit and clear which Python you're using
- Works in any terminal without activation
- Good for scripts and automation

**Cons:**
- More typing
- Longer commands

### Method 3: Use Convenience Scripts (Recommended for Running Services)

```bash
# Use the provided startup script
./start-api.sh

# The script automatically uses venv/bin/python
```

**Pros:**
- Simplest to use
- Automatically uses correct Python
- Can include additional setup/checks

**Cons:**
- Requires creating wrapper scripts
- Less flexible for ad-hoc commands

## Setup Instructions

### Creating a Virtual Environment

```bash
# Create virtual environment (only needed once)
python3 -m venv venv

# This creates a venv/ directory with:
# - venv/bin/python (Python interpreter)
# - venv/bin/pip (Package installer)
# - venv/lib/python3.12/site-packages/ (Installed packages)
```

### Installing Dependencies

```bash
# Method 1: With activated venv
source venv/bin/activate
pip install -r requirements.txt

# Method 2: Using full path
venv/bin/pip install -r requirements.txt
```

### Verifying Your Environment

```bash
# Check which Python you're using
which python
# Should show: /path/to/project/venv/bin/python (if activated)
# Or: /usr/bin/python3 (if not activated - WRONG!)

# Check if email-validator is installed
venv/bin/python -c "import email_validator; print('✅ email-validator installed')"

# List installed packages
venv/bin/pip list
```

## Best Practices

### ✅ DO:
- Always use the virtual environment for project work
- Activate venv when doing interactive development
- Use `venv/bin/python` in scripts and automation
- Add `venv/` to `.gitignore` (already done)
- Document venv usage in README and scripts

### ❌ DON'T:
- Use system Python (`python3`) for running the project
- Install project dependencies globally with `sudo pip`
- Commit the `venv/` directory to git
- Mix packages between system and venv

## Troubleshooting

### "Command not found: python"
**Problem:** Virtual environment not activated, and `python` isn't in PATH.

**Solution:** Either activate venv or use `python3` to create venv:
```bash
python3 -m venv venv
source venv/bin/activate
```

### "ModuleNotFoundError" even with venv activated
**Problem:** Dependencies not installed in venv.

**Solution:** Install dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied: ./start-api.sh"
**Problem:** Script not executable.

**Solution:** Make it executable:
```bash
chmod +x start-api.sh
./start-api.sh
```

### Venv created with wrong Python version
**Problem:** Created venv with Python 3.8 but need 3.10+.

**Solution:** Delete and recreate with correct version:
```bash
rm -rf venv
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## IDE Integration

### VS Code
Add to `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

### PyCharm
1. File → Settings → Project → Python Interpreter
2. Click gear icon → Add
3. Select "Existing environment"
4. Choose `venv/bin/python`

### Vim/Neovim
Add to your project's `.vim/` or use a plugin like `vim-virtualenv`.

## Additional Resources

- [Python venv documentation](https://docs.python.org/3/library/venv.html)
- [Real Python: Virtual Environments Primer](https://realpython.com/python-virtual-environments-a-primer/)
- [Python Packaging User Guide](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)

## Quick Reference

| Task | Command |
|------|---------|
| Create venv | `python3 -m venv venv` |
| Activate venv | `source venv/bin/activate` |
| Deactivate venv | `deactivate` |
| Install packages | `pip install -r requirements.txt` |
| Run with venv | `venv/bin/python script.py` |
| Check Python path | `which python` |
| List packages | `pip list` |
| Start API server | `./start-api.sh` |

---

**Remember:** When in doubt, use `./start-api.sh` or `venv/bin/python` to ensure you're using the correct environment!
