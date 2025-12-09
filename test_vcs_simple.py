#!/usr/bin/env python3
"""Simple test to check VCS integration."""

import sys
import traceback

try:
    print("Testing imports...")
    from integration.vcs_models import VCSEvent, VCSProvider, EventType
    print("✓ vcs_models imported")
    
    from integration.webhook_parser import WebhookParser
    print("✓ webhook_parser imported")
    
    from integration.vcs_client import VCSClient
    print("✓ vcs_client imported")
    
    from integration.vcs_integration import VCSIntegration
    print("✓ vcs_integration imported")
    
    print("\nTesting basic functionality...")
    integration = VCSIntegration()
    print("✓ VCSIntegration instantiated")
    
    # Test handler registration
    handler_called = []
    def test_handler(event):
        handler_called.append(event)
    
    integration.register_event_handler(EventType.PUSH, test_handler)
    print("✓ Handler registered")
    
    print("\nAll basic tests passed!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
