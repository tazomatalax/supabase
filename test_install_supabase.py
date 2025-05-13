#!/usr/bin/env python3
"""
test_install_supabase.py

Unit tests for the Supabase installation script.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from install_supabase import (
    run_command, 
    clone_supabase_repo, 
    prepare_env_file, 
    verify_docker_installation,
    verify_docker_compose_installation
)


class TestInstallSupabase(unittest.TestCase):
    """Test cases for the Supabase installation script."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        # Save original working directory
        self.original_cwd = os.getcwd()
        # Change to temp directory
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Change back to original directory
        os.chdir(self.original_cwd)
        # Remove temp directory
        shutil.rmtree(self.temp_dir)
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test run_command with successful execution."""
        # Setup
        mock_result = MagicMock()
        mock_result.stdout = "Command output"
        mock_run.return_value = mock_result
        
        # Execute
        result = run_command(["echo", "test"])
        
        # Verify
        mock_run.assert_called_once()
        self.assertEqual(result, mock_result)
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test run_command with failed execution."""
        # Setup - make subprocess.run raise CalledProcessError
        mock_error = subprocess.CalledProcessError(1, ["test"])
        mock_error.stdout = ""
        mock_error.stderr = "Error"
        mock_run.side_effect = mock_error
        
        # Execute and verify
        with self.assertRaises(subprocess.CalledProcessError):
            run_command(["test"])
    
    @patch('os.chdir')
    @patch('install_supabase.run_command')
    @patch('pathlib.Path.exists')
    def test_clone_supabase_repo_new(self, mock_exists, mock_run_command, mock_chdir):
        """Test cloning a new Supabase repository."""
        # Setup
        mock_exists.return_value = False
        
        # Execute
        clone_supabase_repo("test_repo")
        
        # Verify
        self.assertEqual(mock_run_command.call_count, 4)
        self.assertEqual(mock_chdir.call_count, 2)
    
    @patch('os.chdir')
    @patch('install_supabase.run_command')
    @patch('pathlib.Path.exists')
    def test_clone_supabase_repo_existing(self, mock_exists, mock_run_command, mock_chdir):
        """Test updating an existing Supabase repository."""
        # Setup
        mock_exists.return_value = True
        
        # Execute
        clone_supabase_repo("test_repo")
        
        # Verify
        mock_run_command.assert_called_once()
        self.assertEqual(mock_chdir.call_count, 2)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @patch('shutil.copyfile')
    @patch('builtins.open', unittest.mock.mock_open())
    def test_prepare_env_file_existing_source(self, mock_copyfile, mock_mkdir, mock_exists):
        """Test preparing environment file with existing source file."""
        # Setup
        mock_exists.return_value = True
        
        # Execute
        prepare_env_file("source.env", "target.env")
        
        # Verify
        mock_copyfile.assert_called_once()
        mock_mkdir.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', unittest.mock.mock_open())
    def test_prepare_env_file_no_source(self, mock_mkdir, mock_exists):
        """Test preparing environment file without source file."""
        # Setup
        mock_exists.return_value = False
        
        # Execute
        prepare_env_file("source.env", "target.env")
        
        # Verify
        mock_mkdir.assert_called_once()
    
    @patch('install_supabase.run_command')
    def test_verify_docker_installation_success(self, mock_run_command):
        """Test successful Docker installation verification."""
        # Execute
        result = verify_docker_installation()
        
        # Verify
        self.assertEqual(mock_run_command.call_count, 2)
        self.assertTrue(result)
    
    @patch('install_supabase.run_command')
    def test_verify_docker_installation_failure(self, mock_run_command):
        """Test failed Docker installation verification."""
        # Setup
        mock_run_command.side_effect = subprocess.CalledProcessError(1, ["docker"])
        
        # Execute
        result = verify_docker_installation()
        
        # Verify
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()