import os
import unittest
from dotenv import load_dotenv
from experiments.notion_example import (
    create_page_with_bulleted_list,
    parse_markdown_to_notion_blocks,
    NOTION_TOKEN,
    DATABASE_ID
)

load_dotenv()


class TestNotionAPI(unittest.TestCase):
    """Unit tests for Notion API integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        # Verify environment variables are set
        if not NOTION_TOKEN:
            raise ValueError("NOTION_TOKEN environment variable not set")
        if not DATABASE_ID:
            raise ValueError("DATABASE_ID environment variable not set")
    
    def test_parse_bulleted_list_simple(self):
        """Test parsing a simple bulleted list."""
        text = """- First bullet
- Second bullet
- Third bullet"""
        
        blocks = parse_markdown_to_notion_blocks(text)
        
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0]["type"], "bulleted_list_item")
        self.assertEqual(
            blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"],
            "First bullet"
        )
        self.assertEqual(
            blocks[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"],
            "Second bullet"
        )
        self.assertEqual(
            blocks[2]["bulleted_list_item"]["rich_text"][0]["text"]["content"],
            "Third bullet"
        )
    
    def test_parse_bulleted_list_with_sub_bullets(self):
        """Test parsing a bulleted list with sub-bullets."""
        text = """- Main bullet 1
  - Sub-bullet 1.1
  - Sub-bullet 1.2
- Main bullet 2
  - Sub-bullet 2.1
    - Nested sub-bullet"""
        
        blocks = parse_markdown_to_notion_blocks(text)
        
        self.assertGreater(len(blocks), 0)
        self.assertEqual(blocks[0]["type"], "bulleted_list_item")
        # Verify first main bullet
        self.assertEqual(
            blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"],
            "Main bullet 1"
        )
    
    def test_parse_bulleted_list_empty_lines(self):
        """Test parsing handles empty lines correctly."""
        text = """- First bullet

- Second bullet
- Third bullet"""
        
        blocks = parse_markdown_to_notion_blocks(text)
        
        # Should skip empty lines
        self.assertEqual(len(blocks), 3)
    
    def test_create_page_with_bulleted_list(self):
        """Test creating a Notion page with a bulleted list."""
        placeholder_bullets = """- First placeholder bullet point
- Second placeholder bullet point
  - Sub-bullet for second point
- Third placeholder bullet point
  - Sub-bullet for third point
    - Nested sub-bullet"""
        
        title = "Test Page - Bulleted List"
        
        try:
            result = create_page_with_bulleted_list(title, placeholder_bullets)
            
            # Verify page was created successfully
            self.assertIn("id", result)
            self.assertEqual(
                result["properties"]["Name"]["title"][0]["text"]["content"],
                title
            )
            
            # Store page ID for potential cleanup
            self.page_id = result["id"]
            print(f"\n✓ Successfully created page with ID: {result['id']}")
            
        except Exception as e:
            self.fail(f"Failed to create page: {str(e)}")
    
    def test_create_page_with_simple_bullets(self):
        """Test creating a page with a simple bulleted list."""
        simple_bullets = """- Item one
- Item two
- Item three"""
        
        title = "Test Page - Simple Bullets"
        
        try:
            result = create_page_with_bulleted_list(title, simple_bullets)
            
            self.assertIn("id", result)
            self.assertEqual(
                result["properties"]["Name"]["title"][0]["text"]["content"],
                title
            )
            print(f"\n✓ Successfully created simple bullet page with ID: {result['id']}")
            
        except Exception as e:
            self.fail(f"Failed to create page: {str(e)}")
    
    def test_parse_markdown_with_headers(self):
        """Test parsing markdown with headers and bullets."""
        text = """### Section One
- First bullet
  - Sub-bullet
- Second bullet
### Section Two
- Third bullet"""
        
        blocks = parse_markdown_to_notion_blocks(text)
        
        # Should have 2 headers and bullets
        self.assertGreater(len(blocks), 2)
        
        # First block should be a header
        self.assertEqual(blocks[0]["type"], "heading_3")
        self.assertEqual(
            blocks[0]["heading_3"]["rich_text"][0]["text"]["content"],
            "Section One"
        )
        
        # Second block should be a bullet
        self.assertEqual(blocks[1]["type"], "bulleted_list_item")
    
    def test_create_page_with_headers_and_bullets(self):
        """Test creating a page with headers and bulleted lists."""
        text_with_headers = """### Important Section
- Main point one
  - Sub-point with details
- Main point two
### Another Section
- Point in second section"""
        
        title = "Test Page - Headers and Bullets"
        
        try:
            result = create_page_with_bulleted_list(title, text_with_headers)
            
            self.assertIn("id", result)
            self.assertEqual(
                result["properties"]["Name"]["title"][0]["text"]["content"],
                title
            )
            print(f"\n✓ Successfully created page with headers and bullets: {result['id']}")
            
        except Exception as e:
            self.fail(f"Failed to create page: {str(e)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

