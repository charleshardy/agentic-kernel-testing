#!/usr/bin/env python3
"""
Script to update Confluence page ID 274793107 with the latest content.
Requires confluence-python library: pip install atlassian-python-api
"""

import os
from atlassian import Confluence
import markdown

def update_confluence_page():
    # Configuration - Set these environment variables
    confluence_url = os.getenv('CONFLUENCE_URL')  # e.g., 'https://yourcompany.atlassian.net'
    username = os.getenv('CONFLUENCE_USERNAME')
    api_token = os.getenv('CONFLUENCE_API_TOKEN')  # or password
    
    if not all([confluence_url, username, api_token]):
        print("❌ Missing required environment variables:")
        print("   CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN")
        return False
    
    # Initialize Confluence connection
    confluence = Confluence(
        url=confluence_url,
        username=username,
        password=api_token,
        cloud=True  # Set to False for Confluence Server
    )
    
    # Read the confluence page content
    try:
        with open('docs/confluence-page-content.md', 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print("❌ Could not find docs/confluence-page-content.md")
        return False
    
    # Extract just the content (skip the header comments)
    lines = markdown_content.split('\n')
    content_start = 0
    for i, line in enumerate(lines):
        if line.startswith('# Agentic AI Testing System'):
            content_start = i
            break
    
    clean_content = '\n'.join(lines[content_start:])
    
    # Convert Markdown to HTML (Confluence storage format)
    html_content = markdown.markdown(clean_content, extensions=['tables', 'fenced_code'])
    
    # Page details
    page_id = 274793107
    page_title = "Agentic AI Testing System for Linux Kernel and BSP"
    
    try:
        # Get current page to get version number
        current_page = confluence.get_page_by_id(page_id, expand='version')
        current_version = current_page['version']['number']
        
        # Update the page
        result = confluence.update_page(
            page_id=page_id,
            title=page_title,
            body=html_content,
            parent_id=None,
            type='page',
            representation='storage',
            minor_edit=False,
            version_comment='Updated to Production Ready v1.0.0 status - All 50 tasks complete'
        )
        
        print(f"✅ Successfully updated Confluence page {page_id}")
        print(f"   New version: {current_version + 1}")
        print(f"   Page URL: {confluence_url}/pages/viewpage.action?pageId={page_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Confluence page: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Updating Confluence Page ID 274793107...")
    print("📄 Content: Agentic AI Testing System - Production Ready v1.0.0")
    print()
    
    success = update_confluence_page()
    
    if success:
        print("\n🎉 Confluence page updated successfully!")
        print("📋 The page now shows the complete production-ready status")
        print("✅ All 50 tasks completed with 100% requirement coverage")
    else:
        print("\n❌ Failed to update Confluence page")
        print("💡 Try the manual update method instead")
