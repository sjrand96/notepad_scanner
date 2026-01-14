"""
Notion API client for creating pages with bulleted lists.
"""
import requests
import os
from backend.config import NOTION_TOKEN, NOTION_API_URL


def parse_markdown_to_notion_blocks(markdown_text):
    """
    Parse markdown-style text (headers and bulleted lists) into Notion API block format.
    
    Supports:
    - Headers: ### Header text (converted to heading_3)
    - Bulleted lists with proper nesting (up to 3 levels)
    
    Args:
        markdown_text: String containing markdown-style content (headers and bullets)
    
    Returns:
        List of top-level Notion block objects (with nested children properly structured)
    """
    lines = markdown_text.strip().split('\n')
    top_level_blocks = []
    parent_stack = []
    
    for line in lines:
        line = line.rstrip()
        if not line.strip():
            continue
        
        if line.strip().startswith('###'):
            parent_stack = []
            header_text = line.strip()[3:].strip()
            
            if header_text:
                header_block = {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": { "content": header_text }
                            }
                        ]
                    }
                }
                top_level_blocks.append(header_block)
            continue
        
        original_indent = len(line) - len(line.lstrip())
        indent_level = original_indent // 2
        if indent_level > 3:
            indent_level = 3
        
        content = line.lstrip('- ').lstrip('* ').strip()
        if not content:
            continue
        
        block = {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": { "content": content }
                    }
                ]
            }
        }
        
        while parent_stack and parent_stack[-1][0] >= indent_level:
            parent_stack.pop()
        
        if indent_level == 0:
            top_level_blocks.append(block)
            parent_stack = [(0, block)]
        else:
            if parent_stack:
                parent_indent, parent_block = parent_stack[-1]
                
                if "children" not in parent_block["bulleted_list_item"]:
                    parent_block["bulleted_list_item"]["children"] = []
                
                parent_block["bulleted_list_item"]["children"].append(block)
                parent_stack.append((indent_level, block))
            else:
                top_level_blocks.append(block)
                parent_stack = [(indent_level, block)]
    
    return top_level_blocks


def create_page_with_bulleted_list(database_id, title, bulleted_text, notion_token=None):
    """
    Create a Notion page with headers and bulleted lists.
    
    Args:
        database_id: Notion database ID
        title: Title for the page
        bulleted_text: Markdown-style text (can include headers ### and bullets)
        notion_token: Notion API token (optional, uses NOTION_TOKEN from config if not provided)
    
    Returns:
        Response JSON from Notion API
    """
    token = notion_token or NOTION_TOKEN
    if not token:
        raise ValueError("Notion token not provided and NOTION_TOKEN environment variable not set")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    
    children = parse_markdown_to_notion_blocks(bulleted_text)
    
    url = f"{NOTION_API_URL}/pages"
    
    payload = {
        "parent": { "database_id": database_id },
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": { "content": title }
                    }
                ]
            }
        },
        "children": children
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
