"""
Unit tests for user_manager module.

These tests use temporary files to avoid interfering with real user data.
We use the temp_dir fixture to create isolated test environments.
"""
import pytest
import os
import json
from unittest.mock import patch
from backend import user_manager


@pytest.mark.unit
class TestUserManager:
    """Tests for user management functions."""
    
    def test_load_users_creates_default_file(self, temp_dir, monkeypatch):
        """Test that load_users creates a default users file if it doesn't exist."""
        # Set up environment variables (both users need token and database ID per schema)
        monkeypatch.setenv("SPENCER_NOTION_TOKEN", "test_token_spencer")
        monkeypatch.setenv("SPENCER_NOTION_DATABASE_ID", "test_db_spencer")
        monkeypatch.setenv("CELESTE_NOTION_TOKEN", "test_token_celeste")
        monkeypatch.setenv("CELESTE_NOTION_DATABASE_ID", "test_db_celeste")
        
        # Mock the paths to use our temp directory
        users_file = os.path.join(temp_dir, "users.json")
        monkeypatch.setattr(user_manager, "USERS_FILE", users_file)
        monkeypatch.setattr(user_manager, "DATA_DIR", temp_dir)
        
        # Load users (should create default file)
        users = user_manager.load_users()
        
        # Verify the file was created
        assert os.path.exists(users_file), "users.json should be created"
        
        # Verify it has expected users
        assert "spencer" in users
        assert "celeste" in users
        assert users["spencer"]["name"] == "Spencer"
        assert users["spencer"]["notion_token"] == "test_token_spencer"
    
    def test_load_users_reads_existing_file(self, temp_users_file, temp_dir, monkeypatch):
        """Test that load_users correctly reads an existing users file."""
        # Mock the paths
        monkeypatch.setattr(user_manager, "USERS_FILE", temp_users_file)
        monkeypatch.setattr(user_manager, "DATA_DIR", temp_dir)
        
        users = user_manager.load_users()
        
        assert "test_user_1" in users
        assert "test_user_2" in users
        assert users["test_user_1"]["name"] == "Test User 1"
        assert users["test_user_1"]["notion_token"] == "test_token_1"
    
    def test_save_users(self, temp_dir, monkeypatch):
        """Test that save_users correctly writes to file."""
        users_file = os.path.join(temp_dir, "users.json")
        monkeypatch.setattr(user_manager, "USERS_FILE", users_file)
        monkeypatch.setattr(user_manager, "DATA_DIR", temp_dir)
        
        test_users = {
            "user1": {
                "name": "User One",
                "notion_token": "token1",
                "notion_database_id": "db1"
            }
        }
        
        user_manager.save_users(test_users)
        
        # Verify file was created and contains correct data
        assert os.path.exists(users_file)
        with open(users_file, 'r') as f:
            saved_users = json.load(f)
        
        assert saved_users == test_users
    
    def test_get_user_returns_correct_user(self, temp_users_file, temp_dir, monkeypatch):
        """Test that get_user returns the correct user profile."""
        monkeypatch.setattr(user_manager, "USERS_FILE", temp_users_file)
        monkeypatch.setattr(user_manager, "DATA_DIR", temp_dir)
        
        user = user_manager.get_user("test_user_1")
        
        assert user is not None
        assert user["name"] == "Test User 1"
        assert user["notion_token"] == "test_token_1"
    
    def test_get_user_returns_none_for_nonexistent_user(self, temp_users_file, temp_dir, monkeypatch):
        """Test that get_user returns None for a user that doesn't exist."""
        monkeypatch.setattr(user_manager, "USERS_FILE", temp_users_file)
        monkeypatch.setattr(user_manager, "DATA_DIR", temp_dir)
        
        user = user_manager.get_user("nonexistent_user")
        
        assert user is None
    
    def test_list_users_returns_all_user_ids(self, temp_users_file, temp_dir, monkeypatch):
        """Test that list_users returns all user IDs."""
        monkeypatch.setattr(user_manager, "USERS_FILE", temp_users_file)
        monkeypatch.setattr(user_manager, "DATA_DIR", temp_dir)
        
        user_ids = user_manager.list_users()
        
        assert len(user_ids) == 2
        assert "test_user_1" in user_ids
        assert "test_user_2" in user_ids
    
    def test_load_users_handles_corrupted_file(self, temp_dir, monkeypatch):
        """Test that load_users handles corrupted JSON gracefully."""
        # Create a corrupted JSON file
        users_file = os.path.join(temp_dir, "users.json")
        with open(users_file, 'w') as f:
            f.write("{ this is not valid json }")
        
        monkeypatch.setattr(user_manager, "USERS_FILE", users_file)
        monkeypatch.setattr(user_manager, "DATA_DIR", temp_dir)
        
        users = user_manager.load_users()
        
        # Should return empty dict instead of crashing
        assert users == {}
