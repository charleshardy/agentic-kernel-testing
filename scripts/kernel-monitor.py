#!/usr/bin/env python3
"""
Linux Kernel Change Monitor

This script monitors the Linux kernel repository for significant changes
and sends email notifications about major feature updates.
"""

import os
import sys
import subprocess
import smtplib
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class KernelChangeMonitor:
    """Monitor Linux kernel repository for significant changes."""
    
    def __init__(self, repo_url: str = "https://github.com/torvalds/linux.git"):
        self.repo_url = repo_url
        self.repo_dir = Path("./linux-kernel")
        self.config_file = Path("./config/kernel-monitor.json")
        
        # Major subsystems to monitor
        self.major_subsystems = {
            'arch/': 'Architecture-specific code',
            'drivers/': 'Device drivers',
            'fs/': 'Filesystems',
            'kernel/': 'Core kernel',
            'mm/': 'Memory management',
            'net/': 'Networking',
            'security/': 'Security subsystem',
            'sound/': 'Sound subsystem',
            'crypto/': 'Cryptographic API',
            'block/': 'Block layer',
            'init/': 'Kernel initialization',
            'ipc/': 'Inter-process communication',
            'lib/': 'Library routines',
            'scripts/': 'Build scripts',
            'tools/': 'Kernel tools',
            'Documentation/': 'Documentation'
        }
        
        # Keywords that indicate major features
        self.major_feature_keywords = [
            'new driver', 'new filesystem', 'new architecture',
            'major rewrite', 'significant improvement', 'performance boost',
            'security enhancement', 'vulnerability fix', 'CVE',
            'new subsystem', 'API change', 'ABI change',
            'memory management', 'scheduler', 'networking stack',
            'virtualization', 'container', 'namespace',
            'lockdown', 'hardening', 'mitigation'
        ]
    
    def setup_repository(self) -> bool:
        """Clone or update the Linux kernel repository."""
        try:
            if not self.repo_dir.exists():
                print(f"Cloning Linux kernel repository to {self.repo_dir}")
                result = subprocess.run([
                    'git', 'clone', '--depth', '100', self.repo_url, str(self.repo_dir)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    print(f"Failed to clone repository: {result.stderr}")
                    return False
            else:
                print("Updating Linux kernel repository")
                result = subprocess.run([
                    'git', 'fetch', 'origin', 'master'
                ], cwd=self.repo_dir, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    print(f"Failed to fetch updates: {result.stderr}")
                    return False
                
                # Reset to latest
                subprocess.run([
                    'git', 'reset', '--hard', 'origin/master'
                ], cwd=self.repo_dir, capture_output=True, text=True)
            
            return True
            
        except subprocess.TimeoutExpired:
            print("Git operation timed out")
            return False
        except Exception as e:
            print(f"Error setting up repository: {e}")
            return False
    
    def get_recent_commits(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get commits from the last N days."""
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Get commit log with detailed information
            result = subprocess.run([
                'git', 'log', 
                f'--since={since_date}',
                '--pretty=format:%H|%an|%ae|%ad|%s',
                '--date=iso',
                '--name-status'
            ], cwd=self.repo_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Failed to get commit log: {result.stderr}")
                return []
            
            commits = []
            current_commit = None
            
            for line in result.stdout.split('\n'):
                if '|' in line and len(line.split('|')) == 5:
                    # New commit line
                    if current_commit:
                        commits.append(current_commit)
                    
                    parts = line.split('|')
                    current_commit = {
                        'sha': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4],
                        'files': []
                    }
                elif line.strip() and current_commit:
                    # File change line
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        current_commit['files'].append({
                            'status': parts[0],
                            'path': parts[1]
                        })
            
            if current_commit:
                commits.append(current_commit)
            
            return commits
            
        except Exception as e:
            print(f"Error getting recent commits: {e}")
            return []
    
    def analyze_commit_significance(self, commit: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if a commit represents a major feature update."""
        significance = {
            'is_major': False,
            'score': 0,
            'reasons': [],
            'subsystems': [],
            'type': 'minor'
        }
        
        message = commit['message'].lower()
        files = commit.get('files', [])
        
        # Check for major feature keywords in commit message
        for keyword in self.major_feature_keywords:
            if keyword in message:
                significance['score'] += 10
                significance['reasons'].append(f"Contains keyword: {keyword}")
        
        # Check for subsystem involvement
        affected_subsystems = set()
        for file_info in files:
            file_path = file_info['path']
            for subsystem, description in self.major_subsystems.items():
                if file_path.startswith(subsystem):
                    affected_subsystems.add(subsystem)
                    significance['subsystems'].append(description)
        
        # Score based on number of affected subsystems
        if len(affected_subsystems) > 3:
            significance['score'] += 15
            significance['reasons'].append(f"Affects {len(affected_subsystems)} major subsystems")
        elif len(affected_subsystems) > 1:
            significance['score'] += 8
        
        # Check for large number of files changed
        if len(files) > 50:
            significance['score'] += 12
            significance['reasons'].append(f"Large changeset: {len(files)} files")
        elif len(files) > 20:
            significance['score'] += 6
        
        # Check for new files (potential new features)
        new_files = [f for f in files if f['status'] == 'A']
        if len(new_files) > 10:
            significance['score'] += 10
            significance['reasons'].append(f"Adds {len(new_files)} new files")
        
        # Check for architecture-specific changes
        if any(f['path'].startswith('arch/') for f in files):
            arch_files = [f for f in files if f['path'].startswith('arch/')]
            if len(arch_files) > 5:
                significance['score'] += 8
                significance['reasons'].append("Significant architecture changes")
        
        # Check for security-related changes
        security_indicators = ['cve', 'security', 'vulnerability', 'exploit', 'mitigation']
        if any(indicator in message for indicator in security_indicators):
            significance['score'] += 15
            significance['reasons'].append("Security-related change")
        
        # Determine significance level
        if significance['score'] >= 25:
            significance['is_major'] = True
            significance['type'] = 'major'
        elif significance['score'] >= 15:
            significance['type'] = 'significant'
        elif significance['score'] >= 8:
            significance['type'] = 'moderate'
        
        return significance
    
    def generate_email_content(self, major_commits: List[Dict[str, Any]]) -> str:
        """Generate email content for major kernel changes."""
        if not major_commits:
            return None
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; }}
                .commit {{ margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .commit-header {{ font-weight: bold; color: #2c3e50; }}
                .commit-meta {{ color: #7f8c8d; font-size: 0.9em; }}
                .reasons {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; }}
                .subsystems {{ background-color: #e8f5e8; padding: 10px; margin: 10px 0; }}
                .files {{ font-family: monospace; font-size: 0.8em; max-height: 200px; overflow-y: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Linux Kernel Major Changes Report</h2>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p>Found {len(major_commits)} significant changes in the last 7 days</p>
            </div>
        """
        
        for commit in major_commits:
            significance = commit.get('significance', {})
            
            html_content += f"""
            <div class="commit">
                <div class="commit-header">
                    {commit['message'][:100]}{'...' if len(commit['message']) > 100 else ''}
                </div>
                <div class="commit-meta">
                    <strong>Commit:</strong> {commit['sha'][:12]}<br>
                    <strong>Author:</strong> {commit['author']} &lt;{commit['email']}&gt;<br>
                    <strong>Date:</strong> {commit['date']}<br>
                    <strong>Significance:</strong> {significance.get('type', 'unknown').title()} (Score: {significance.get('score', 0)})
                </div>
                
                {f'<div class="reasons"><strong>Why this matters:</strong><ul>{"".join(f"<li>{reason}</li>" for reason in significance.get("reasons", []))}</ul></div>' if significance.get('reasons') else ''}
                
                {f'<div class="subsystems"><strong>Affected Subsystems:</strong><ul>{"".join(f"<li>{subsystem}</li>" for subsystem in set(significance.get("subsystems", [])))}</ul></div>' if significance.get('subsystems') else ''}
                
                <div class="files">
                    <strong>Changed Files ({len(commit.get('files', []))}):</strong><br>
                    {'<br>'.join(f"{f['status']} {f['path']}" for f in commit.get('files', [])[:20])}
                    {f'<br>... and {len(commit.get("files", [])) - 20} more files' if len(commit.get('files', [])) > 20 else ''}
                </div>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
    
    def send_email(self, content: str, recipient: str = "le.liu@windriver.com") -> bool:
        """Send email notification."""
        try:
            # Load email configuration
            config = self.load_config()
            smtp_config = config.get('smtp', {})
            
            if not smtp_config:
                print("No SMTP configuration found. Email content saved to file instead.")
                output_file = Path(f"kernel-changes-{datetime.now().strftime('%Y%m%d')}.html")
                with open(output_file, 'w') as f:
                    f.write(content)
                print(f"Email content saved to: {output_file}")
                return True
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Linux Kernel Major Changes - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = smtp_config.get('from_email', 'kernel-monitor@example.com')
            msg['To'] = recipient
            
            # Add HTML content
            html_part = MIMEText(content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_config['host'], smtp_config.get('port', 587)) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                if smtp_config.get('username') and smtp_config.get('password'):
                    server.login(smtp_config['username'], smtp_config['password'])
                
                server.send_message(msg)
            
            print(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            # Save content to file as fallback
            output_file = Path(f"kernel-changes-{datetime.now().strftime('%Y%m%d')}.html")
            with open(output_file, 'w') as f:
                f.write(content)
            print(f"Email content saved to: {output_file}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return {}
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def run_analysis(self, days: int = 7) -> bool:
        """Run the complete analysis workflow."""
        print("Starting Linux kernel change analysis...")
        
        # Setup repository
        if not self.setup_repository():
            print("Failed to setup repository")
            return False
        
        # Get recent commits
        print(f"Analyzing commits from the last {days} days...")
        commits = self.get_recent_commits(days)
        
        if not commits:
            print("No recent commits found")
            return False
        
        print(f"Found {len(commits)} commits to analyze")
        
        # Analyze significance
        major_commits = []
        for commit in commits:
            significance = self.analyze_commit_significance(commit)
            commit['significance'] = significance
            
            if significance['is_major'] or significance['type'] in ['significant', 'major']:
                major_commits.append(commit)
        
        print(f"Found {len(major_commits)} significant commits")
        
        if not major_commits:
            print("No major changes detected")
            return True
        
        # Generate and send email
        email_content = self.generate_email_content(major_commits)
        if email_content:
            return self.send_email(email_content)
        
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor Linux kernel for major changes')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--email', type=str, default='le.liu@windriver.com', help='Email recipient')
    parser.add_argument('--setup-config', action='store_true', help='Setup email configuration')
    
    args = parser.parse_args()
    
    monitor = KernelChangeMonitor()
    
    if args.setup_config:
        # Interactive configuration setup
        config = monitor.load_config()
        
        print("Setting up email configuration...")
        smtp_config = config.get('smtp', {})
        
        smtp_config['host'] = input(f"SMTP Host [{smtp_config.get('host', 'smtp.gmail.com')}]: ") or smtp_config.get('host', 'smtp.gmail.com')
        smtp_config['port'] = int(input(f"SMTP Port [{smtp_config.get('port', 587)}]: ") or smtp_config.get('port', 587))
        smtp_config['use_tls'] = input(f"Use TLS [y/N]: ").lower().startswith('y')
        smtp_config['username'] = input(f"Username [{smtp_config.get('username', '')}]: ") or smtp_config.get('username', '')
        smtp_config['password'] = input("Password (leave empty to skip): ") or smtp_config.get('password', '')
        smtp_config['from_email'] = input(f"From Email [{smtp_config.get('from_email', '')}]: ") or smtp_config.get('from_email', '')
        
        config['smtp'] = smtp_config
        monitor.save_config(config)
        print("Configuration saved!")
        return
    
    # Run analysis
    success = monitor.run_analysis(args.days)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()