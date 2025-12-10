#!/usr/bin/env python3
"""API server startup script."""

import uvicorn
import argparse
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings


def main():
    """Start the API server."""
    parser = argparse.ArgumentParser(description="Start the Agentic AI Testing System API server")
    parser.add_argument("--host", default=None, help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log-level", default=None, help="Log level (debug, info, warning, error)")
    
    args = parser.parse_args()
    
    # Load settings
    settings = get_settings()
    
    # Override settings with command line arguments
    host = args.host or settings.api.host
    port = args.port or settings.api.port
    reload = args.reload or settings.api.debug
    log_level = args.log_level or ("debug" if args.debug else "info")
    
    print(f"Starting Agentic AI Testing System API server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug mode: {reload}")
    print(f"Log level: {log_level}")
    print(f"Documentation: http://{host}:{port}/docs")
    print(f"Health check: http://{host}:{port}/api/v1/health")
    
    try:
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nShutting down API server...")
    except Exception as e:
        print(f"Failed to start API server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()