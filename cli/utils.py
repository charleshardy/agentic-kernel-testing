"""Utility functions for CLI operations."""

import logging
import sys
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

import click
from api.client import AgenticTestingClient, APIError


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    # Reduce noise from requests library
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_client(ctx: click.Context) -> AgenticTestingClient:
    """Get API client with configuration from context."""
    # Ensure context object exists
    if ctx.obj is None:
        ctx.obj = {}
    
    # Get API URL
    api_url = ctx.obj.get('api_url')
    if not api_url:
        settings = ctx.obj.get('settings')
        if settings:
            api_url = f"http://{settings.api.host}:{settings.api.port}"
        else:
            api_url = "http://localhost:8000"
    
    # Create client
    client = AgenticTestingClient(base_url=api_url)
    
    # Set API key if provided
    api_key = ctx.obj.get('api_key')
    if api_key:
        client.session.headers['Authorization'] = f'Bearer {api_key}'
    
    return client


def get_debug_mode(ctx: click.Context) -> bool:
    """Safely get debug mode from context."""
    return ctx.obj.get('debug', False) if ctx.obj else False


def handle_api_error(error: Exception, debug: bool = False):
    """Handle API errors with user-friendly messages."""
    if isinstance(error, APIError):
        click.echo(f"❌ API Error: {error}", err=True)
        if debug and hasattr(error, 'response_data') and error.response_data:
            click.echo(f"Response data: {json.dumps(error.response_data, indent=2)}", err=True)
    else:
        click.echo(f"❌ Error: {error}", err=True)
        if debug:
            import traceback
            click.echo(traceback.format_exc(), err=True)
    
    sys.exit(1)


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_bytes(bytes_count: int) -> str:
    """Format bytes in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f}{unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f}PB"


def format_percentage(value: float) -> str:
    """Format percentage value."""
    return f"{value * 100:.1f}%"


def print_table(headers: List[str], rows: List[List[str]], max_width: int = 120):
    """Print a formatted table."""
    if not rows:
        click.echo("No data to display")
        return
    
    # Calculate column widths
    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Adjust for max width
    total_width = sum(col_widths) + len(headers) * 3 - 1
    if total_width > max_width:
        # Reduce widths proportionally
        reduction = (total_width - max_width) / len(col_widths)
        col_widths = [max(10, int(w - reduction)) for w in col_widths]
    
    # Print header
    header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    click.echo(header_row)
    click.echo("-" * len(header_row))
    
    # Print rows
    for row in rows:
        formatted_row = []
        for i, (cell, width) in enumerate(zip(row, col_widths)):
            cell_str = str(cell)
            if len(cell_str) > width:
                cell_str = cell_str[:width-3] + "..."
            formatted_row.append(cell_str.ljust(width))
        
        click.echo(" | ".join(formatted_row))


def print_json(data: Any, indent: int = 2):
    """Print data as formatted JSON."""
    click.echo(json.dumps(data, indent=indent, default=str))


def print_yaml(data: Any):
    """Print data as formatted YAML."""
    click.echo(yaml.dump(data, default_flow_style=False))


def confirm_action(message: str, default: bool = False) -> bool:
    """Confirm an action with the user."""
    return click.confirm(message, default=default)


def prompt_for_input(message: str, default: str = None, hide_input: bool = False) -> str:
    """Prompt user for input."""
    return click.prompt(message, default=default, hide_input=hide_input)


def select_from_list(items: List[str], message: str = "Select an option") -> str:
    """Let user select from a list of options."""
    if not items:
        raise ValueError("No items to select from")
    
    if len(items) == 1:
        return items[0]
    
    click.echo(f"\n{message}:")
    for i, item in enumerate(items, 1):
        click.echo(f"  {i}. {item}")
    
    while True:
        try:
            choice = click.prompt("Enter choice", type=int)
            if 1 <= choice <= len(items):
                return items[choice - 1]
            else:
                click.echo(f"Please enter a number between 1 and {len(items)}")
        except (ValueError, click.Abort):
            click.echo("Invalid input. Please enter a number.")


def load_config_file(file_path: str) -> Dict[str, Any]:
    """Load configuration from file."""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    with open(path, 'r') as f:
        if path.suffix.lower() in ['.yml', '.yaml']:
            return yaml.safe_load(f)
        elif path.suffix.lower() == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {path.suffix}")


def save_config_file(data: Dict[str, Any], file_path: str, format: str = 'yaml'):
    """Save configuration to file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        if format.lower() in ['yml', 'yaml']:
            yaml.dump(data, f, default_flow_style=False)
        elif format.lower() == 'json':
            json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


def validate_test_type(test_type: str) -> str:
    """Validate test type."""
    valid_types = ['unit', 'integration', 'fuzz', 'performance', 'security']
    if test_type not in valid_types:
        raise click.BadParameter(f"Test type must be one of: {', '.join(valid_types)}")
    return test_type


def validate_architecture(arch: str) -> str:
    """Validate architecture."""
    valid_archs = ['x86_64', 'arm64', 'riscv64', 'arm']
    if arch not in valid_archs:
        raise click.BadParameter(f"Architecture must be one of: {', '.join(valid_archs)}")
    return arch


def parse_key_value_pairs(ctx, param, value) -> Dict[str, str]:
    """Parse key=value pairs from command line."""
    if not value:
        return {}
    
    result = {}
    for pair in value:
        if '=' not in pair:
            raise click.BadParameter(f"Invalid key=value pair: {pair}")
        
        key, val = pair.split('=', 1)
        result[key.strip()] = val.strip()
    
    return result


def format_test_status(status: str) -> str:
    """Format test status with color."""
    status_colors = {
        'passed': 'green',
        'failed': 'red',
        'running': 'yellow',
        'queued': 'blue',
        'cancelled': 'magenta',
        'timeout': 'red',
        'error': 'red'
    }
    
    color = status_colors.get(status.lower(), 'white')
    return click.style(status.upper(), fg=color)


def format_risk_level(risk: str) -> str:
    """Format risk level with color."""
    risk_colors = {
        'low': 'green',
        'medium': 'yellow',
        'high': 'red',
        'critical': 'red'
    }
    
    color = risk_colors.get(risk.lower(), 'white')
    return click.style(risk.upper(), fg=color)


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def paginate_results(items: List[Any], page_size: int = 20) -> List[List[Any]]:
    """Paginate a list of items."""
    pages = []
    for i in range(0, len(items), page_size):
        pages.append(items[i:i + page_size])
    return pages


def display_paginated_results(items: List[Any], page_size: int = 20, formatter=None):
    """Display paginated results with navigation."""
    if not items:
        click.echo("No results to display")
        return
    
    pages = paginate_results(items, page_size)
    current_page = 0
    
    while True:
        # Display current page
        click.clear()
        click.echo(f"Page {current_page + 1} of {len(pages)} ({len(items)} total items)")
        click.echo("=" * 50)
        
        page_items = pages[current_page]
        if formatter:
            for item in page_items:
                formatter(item)
        else:
            for item in page_items:
                click.echo(item)
        
        # Navigation
        click.echo("\n" + "=" * 50)
        options = []
        if current_page > 0:
            options.append("p) Previous page")
        if current_page < len(pages) - 1:
            options.append("n) Next page")
        options.extend(["q) Quit", "g) Go to page"])
        
        click.echo(" | ".join(options))
        
        choice = click.prompt("Choice", default="q").lower()
        
        if choice == 'q':
            break
        elif choice == 'n' and current_page < len(pages) - 1:
            current_page += 1
        elif choice == 'p' and current_page > 0:
            current_page -= 1
        elif choice == 'g':
            try:
                page_num = click.prompt("Page number", type=int)
                if 1 <= page_num <= len(pages):
                    current_page = page_num - 1
                else:
                    click.echo(f"Invalid page number. Must be between 1 and {len(pages)}")
                    click.pause()
            except (ValueError, click.Abort):
                click.echo("Invalid page number")
                click.pause()