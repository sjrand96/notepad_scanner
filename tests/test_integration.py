"""
Integration tests for end-to-end workflows.

These tests verify that multiple components work together correctly.
They are marked as 'integration' and may be slower than unit tests.
"""
import pytest
import os
from unittest.mock import Mock, patch
from backend.image_processor import crop_to_fixed_roi


@pytest.mark.integration
class TestFixedRoiWorkflow:
    """Test fixed-ROI crop workflow (simulates capture -> crop -> ready for OCR)."""

    def test_crop_full_frame_then_roi(self, sample_image):
        """Capture-sized frame cropped with ROI 0,0,0,0 gives full frame."""
        img = sample_image
        if img.shape[0] < 10 or img.shape[1] < 10:
            img = __import__("numpy").zeros((100, 100, 3), dtype=__import__("numpy").uint8)
        cropped = crop_to_fixed_roi(img, 0, 0, 0, 0)
        assert cropped is not None
        assert cropped.size > 0
        assert len(cropped.shape) == 3

    def test_crop_subregion(self, sample_image):
        """Cropped subregion has correct shape and is contiguous."""
        import numpy as np
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        cropped = crop_to_fixed_roi(img, 50, 50, 100, 80)
        assert cropped is not None
        assert cropped.shape == (80, 100, 3)
        assert cropped.size > 0


@pytest.mark.integration
class TestUserToNotionWorkflow:
    """Test user management integrated with Notion workflow."""
    
    def test_user_lookup_and_notion_config(self, temp_users_file, temp_dir, monkeypatch):
        """
        Integration test: Load user and verify Notion credentials are accessible.
        
        This simulates the workflow when a user starts a session.
        """
        from backend import user_manager
        
        # Mock paths
        monkeypatch.setattr(user_manager, "USERS_FILE", temp_users_file)
        monkeypatch.setattr(user_manager, "DATA_DIR", temp_dir)
        
        # Step 1: List available users
        users = user_manager.list_users()
        assert len(users) > 0, "Should have users available"
        
        # Step 2: Get specific user
        user_id = users[0]
        user = user_manager.get_user(user_id)
        
        assert user is not None, "Should retrieve user"
        assert "notion_token" in user, "User should have Notion token field"
        assert "notion_database_id" in user, "User should have database ID field"
        
        # Step 3: Verify credentials are present (simulating session creation)
        notion_token = user.get("notion_token")
        notion_db_id = user.get("notion_database_id")
        
        assert notion_token, "Token should be present"
        assert notion_db_id, "Database ID should be present"


@pytest.mark.integration
@pytest.mark.slow
def test_full_markdown_to_notion_blocks(sample_users):
    """
    Integration test: Parse complex markdown and verify block structure.
    
    This tests the complete markdown parsing workflow with various elements.
    """
    from backend.notion_client import parse_markdown_to_notion_blocks
    
    complex_markdown = """### Meeting Notes

- Main topic 1
  - Subtopic 1.1
  - Subtopic 1.2
    - Deep subtopic 1.2.1
- Main topic 2
  - Subtopic 2.1

### Action Items

- Task 1
- Task 2
  - Task 2 details"""
    
    blocks = parse_markdown_to_notion_blocks(complex_markdown)
    
    # Verify structure
    assert len(blocks) > 0, "Should have blocks"
    
    # Count headers
    headers = [b for b in blocks if b["type"] == "heading_3"]
    assert len(headers) == 2, "Should have 2 headers"
    
    # Count top-level bullets
    bullets = [b for b in blocks if b["type"] == "bulleted_list_item"]
    assert len(bullets) > 0, "Should have bullet points"
    
    # Verify nested structure exists
    has_nested = any(
        "children" in b["bulleted_list_item"] 
        for b in blocks if b["type"] == "bulleted_list_item"
    )
    assert has_nested, "Should have nested bullets"
