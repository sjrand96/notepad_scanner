"""
Unit tests for notion_client module.

These tests use mocking to avoid making real API calls.
The pytest-mock plugin provides the 'mocker' fixture for easy mocking.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from backend.notion_client import (
    parse_markdown_to_notion_blocks,
    upload_image_to_notion,
    create_page_with_bulleted_list
)


@pytest.mark.unit
class TestParseMarkdownToNotionBlocks:
    """Tests for markdown parsing function."""
    
    def test_parse_simple_bullets(self):
        """Test parsing simple bulleted list."""
        markdown = "- First item\n- Second item\n- Third item"
        
        blocks = parse_markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 3
        assert all(block["type"] == "bulleted_list_item" for block in blocks)
        assert blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "First item"
    
    def test_parse_nested_bullets(self):
        """Test parsing nested bullets."""
        markdown = "- Parent item\n  - Child item 1\n  - Child item 2"
        
        blocks = parse_markdown_to_notion_blocks(markdown)
        
        # Should have 1 top-level block with children
        assert len(blocks) == 1
        assert "children" in blocks[0]["bulleted_list_item"]
        assert len(blocks[0]["bulleted_list_item"]["children"]) == 2
    
    def test_parse_header(self):
        """Test parsing header."""
        markdown = "### My Header\n- Item under header"
        
        blocks = parse_markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 2
        assert blocks[0]["type"] == "heading_3"
        assert blocks[0]["heading_3"]["rich_text"][0]["text"]["content"] == "My Header"
        assert blocks[1]["type"] == "bulleted_list_item"
    
    def test_parse_empty_string(self):
        """Test that empty string returns empty list."""
        blocks = parse_markdown_to_notion_blocks("")
        assert blocks == []
    
    def test_parse_with_blank_lines(self):
        """Test that blank lines are ignored."""
        markdown = "- Item 1\n\n- Item 2\n\n\n- Item 3"
        
        blocks = parse_markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 3


@pytest.mark.unit
class TestUploadImageToNotion:
    """Tests for image upload function (requires mocking)."""
    
    def test_upload_image_success(self, mocker, temp_image_file):
        """Test successful image upload with mocked API calls."""
        # Mock the requests.post calls
        mock_post = mocker.patch('backend.notion_client.requests.post')
        
        # First call: create file upload object
        create_response = Mock()
        create_response.status_code = 200
        create_response.json.return_value = {"id": "file_upload_123"}
        
        # Second call: upload file content
        upload_response = Mock()
        upload_response.status_code = 200
        
        # Configure mock to return different responses for each call
        mock_post.side_effect = [create_response, upload_response]
        
        # Call the function
        file_upload_id = upload_image_to_notion(temp_image_file, notion_token="test_token")
        
        # Verify the result
        assert file_upload_id == "file_upload_123"
        
        # Verify requests.post was called twice
        assert mock_post.call_count == 2
    
    def test_upload_image_create_fails(self, mocker, temp_image_file):
        """Test that function raises exception when file creation fails."""
        mock_post = mocker.patch('backend.notion_client.requests.post')
        
        # Mock failed response
        failed_response = Mock()
        failed_response.status_code = 400
        failed_response.text = "Bad request"
        mock_post.return_value = failed_response
        
        # Should raise an exception
        with pytest.raises(Exception, match="File creation failed"):
            upload_image_to_notion(temp_image_file, notion_token="test_token")
    
    def test_upload_image_no_token(self, mocker, temp_image_file):
        """Test that function raises ValueError when no token provided."""
        # Mock the NOTION_TOKEN from config to be None (simulates no env var)
        mocker.patch('backend.notion_client.NOTION_TOKEN', None)
        
        with pytest.raises(ValueError, match="Notion token not provided"):
            upload_image_to_notion(temp_image_file, notion_token=None)


@pytest.mark.unit
class TestCreatePageWithBulletedList:
    """Tests for Notion page creation function."""
    
    def test_create_page_without_image(self, mocker):
        """Test creating a page without an image."""
        # Mock requests.post
        mock_post = mocker.patch('backend.notion_client.requests.post')
        mock_response = Mock()
        mock_response.json.return_value = {"id": "page_123"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Call the function
        result = create_page_with_bulleted_list(
            database_id="test_db",
            title="Test Page",
            bulleted_text="- Item 1\n- Item 2",
            notion_token="test_token",
            image_path=None
        )
        
        assert result["id"] == "page_123"
        assert mock_post.call_count == 1
    
    def test_create_page_with_image(self, mocker, temp_image_file):
        """Test creating a page with an image."""
        # Mock upload_image_to_notion
        mock_upload = mocker.patch('backend.notion_client.upload_image_to_notion')
        mock_upload.return_value = "file_upload_123"
        
        # Mock requests.post for page creation
        mock_post = mocker.patch('backend.notion_client.requests.post')
        mock_response = Mock()
        mock_response.json.return_value = {"id": "page_456"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Call the function
        result = create_page_with_bulleted_list(
            database_id="test_db",
            title="Test Page",
            bulleted_text="- Item 1",
            notion_token="test_token",
            image_path=temp_image_file
        )
        
        # Verify upload was called
        mock_upload.assert_called_once()
        
        # Verify page was created
        assert result["id"] == "page_456"
        
        # Verify the page creation payload includes header and image blocks
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert len(payload['children']) >= 2
        # Second to last block should be heading_2
        assert payload['children'][-2]['type'] == 'heading_2'
        assert payload['children'][-2]['heading_2']['rich_text'][0]['text']['content'] == 'Source Photo:'
        # Last block should be an image
        assert payload['children'][-1]['type'] == 'image'
