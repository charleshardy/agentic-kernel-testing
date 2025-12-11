#!/bin/bash
set -e

# Setup script for Linux kernel monitoring automation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Setting up Linux kernel monitoring automation..."

# Check if running as root for cron setup
if [[ $EUID -eq 0 ]]; then
    echo "Warning: Running as root. Cron jobs will be installed system-wide."
    CRON_USER="root"
else
    CRON_USER="$USER"
fi

# Create necessary directories
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/config"

# Make scripts executable
chmod +x "$PROJECT_DIR/scripts/kernel-monitor.py"

# Setup Python environment if needed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Install required Python packages
echo "Installing required Python packages..."
pip3 install --user gitpython smtplib-ssl || {
    echo "Warning: Some packages may already be installed or unavailable"
}

# Setup configuration
echo "Setting up configuration..."
if [[ ! -f "$PROJECT_DIR/config/kernel-monitor.json" ]]; then
    echo "Configuration file not found. Please run 'make kernel-setup' first."
    exit 1
fi

# Create log rotation configuration
cat > "$PROJECT_DIR/config/logrotate-kernel-monitor" << 'EOF'
/path/to/project/logs/kernel-monitor.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 user user
}
EOF

# Replace placeholder path
sed -i "s|/path/to/project|$PROJECT_DIR|g" "$PROJECT_DIR/config/logrotate-kernel-monitor"
sed -i "s|user user|$CRON_USER $CRON_USER|g" "$PROJECT_DIR/config/logrotate-kernel-monitor"

# Create wrapper script for cron
cat > "$PROJECT_DIR/scripts/kernel-monitor-cron.sh" << EOF
#!/bin/bash
# Cron wrapper for kernel monitoring

cd "$PROJECT_DIR"
export PATH="/usr/local/bin:/usr/bin:/bin:\$PATH"

# Log file
LOG_FILE="$PROJECT_DIR/logs/kernel-monitor.log"

# Run monitoring with logging
echo "\$(date): Starting kernel monitoring..." >> "\$LOG_FILE"
python3 "$PROJECT_DIR/scripts/kernel-monitor.py" --days 1 >> "\$LOG_FILE" 2>&1

# Check exit code
if [ \$? -eq 0 ]; then
    echo "\$(date): Kernel monitoring completed successfully" >> "\$LOG_FILE"
else
    echo "\$(date): Kernel monitoring failed" >> "\$LOG_FILE"
fi
EOF

chmod +x "$PROJECT_DIR/scripts/kernel-monitor-cron.sh"

# Setup cron jobs
echo "Setting up cron jobs..."

# Daily monitoring at 9 AM
DAILY_CRON="0 9 * * * $PROJECT_DIR/scripts/kernel-monitor-cron.sh"

# Weekly comprehensive monitoring on Mondays at 8 AM
WEEKLY_CRON="0 8 * * 1 cd $PROJECT_DIR && python3 scripts/kernel-monitor.py --days 7 >> logs/kernel-monitor.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null || true; echo "$DAILY_CRON") | crontab -
(crontab -l 2>/dev/null || true; echo "$WEEKLY_CRON") | crontab -

echo "Cron jobs installed:"
echo "  Daily monitoring: 9:00 AM every day"
echo "  Weekly monitoring: 8:00 AM every Monday"

# Test the setup
echo "Testing kernel monitoring setup..."
if python3 "$PROJECT_DIR/scripts/kernel-monitor.py" --days 1 --email "test@example.com"; then
    echo "✓ Kernel monitoring test successful"
else
    echo "✗ Kernel monitoring test failed"
    echo "Please check the configuration and try again"
    exit 1
fi

echo ""
echo "Kernel monitoring setup completed!"
echo ""
echo "Next steps:"
echo "1. Configure email settings: make kernel-setup"
echo "2. Test monitoring: make kernel-monitor"
echo "3. Check logs: tail -f logs/kernel-monitor.log"
echo ""
echo "Cron jobs are now active and will monitor the Linux kernel automatically."