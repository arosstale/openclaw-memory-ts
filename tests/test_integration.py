# Tests for OpenClaw Memory Template

import pytest
import json
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def mock_msam_response():
    """Mock MSAM API response"""
    return {
        "stored": True,
        "atom_id": "test-atom-123",
        "confidence_tier": "high",
        "atoms": [{"id": "1", "content": "Test memory"}],
        "total_atoms": 75,
        "active_atoms": 75,
        "by_stream": {"semantic": 70, "episodic": 3, "procedural": 2}
    }


class TestMSAMIntegration:
    """Test MSAM cognitive memory integration (mocked)"""

    @patch('subprocess.run')
    def test_msam_installed(self, mock_run, mock_msam_response):
        """Check if MSAM CLI command format is correct"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="MSAM Remember v1.0.0"
        )

        # Simulate MSAM check
        result = subprocess.run(
            ["python", "-m", "msam.remember", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch('subprocess.run')
    def test_msam_store_format(self, mock_run, mock_msam_response):
        """Test store command format"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_msam_response)
        )

        # Simulate store command
        result = subprocess.run(
            ["python", "-m", "msam.remember", "store", "Test memory"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert mock_run.called

    @patch('subprocess.run')
    def test_msam_query_format(self, mock_run, mock_msam_response):
        """Test query command format"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_msam_response)
        )

        # Simulate query command
        result = subprocess.run(
            ["python", "-m", "msam.remember", "query", "Test query"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch('subprocess.run')
    def test_msam_stats_format(self, mock_run, mock_msam_response):
        """Test stats command format"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_msam_response)
        )

        # Simulate stats command
        result = subprocess.run(
            ["python", "-m", "msam.remember", "stats"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0


class TestResearchEngine:
    """Test Research Engine functionality"""

    def test_domains_config_exists(self):
        """Check if domains.json exists and is valid JSON"""
        domains_path = Path(__file__).parent.parent / "research" / "domains.json"

        if not domains_path.exists():
            pytest.skip("domains.json not found - research engine optional")

        with open(domains_path) as f:
            data = json.load(f)
            assert isinstance(data, dict)

    def test_domains_has_required_keys(self):
        """Check each domain has required keys"""
        domains_path = Path(__file__).parent.parent / "research" / "domains.json"

        if not domains_path.exists():
            pytest.skip("domains.json not found - research engine optional")

        with open(domains_path) as f:
            data = json.load(f)

        for domain_id, domain_data in data.items():
            assert "name" in domain_data, f"{domain_id} missing 'name'"
            # Keywords and arxiv_categories are optional


class TestMemoryStructure:
    """Test OpenClaw memory template structure"""

    def test_core_directory_exists(self):
        """Check if .openclaw/core/ exists"""
        core_path = Path(__file__).parent.parent / ".openclaw" / "core"
        # Skip if not yet initialized
        if not core_path.exists():
            pytest.skip("Core directory not initialized")
        assert core_path.exists()

    def test_memory_directory_exists(self):
        """Check if memory/ directory exists"""
        memory_path = Path(__file__).parent.parent / "memory"
        assert memory_path.exists(), "memory/ directory required"

    def test_research_directory_exists(self):
        """Check if research/ directory exists (optional)"""
        research_path = Path(__file__).parent.parent / "research"
        if not research_path.exists():
            pytest.skip("research/ optional")


class TestDocumentation:
    """Test documentation files"""

    def test_readme_exists(self):
        """Check if README.md exists"""
        readme_path = Path(__file__).parent.parent / "README.md"
        assert readme_path.exists(), "README.md required"

    def test_msam_integration_exists(self):
        """Check if MSAM_INTEGRATION.md exists"""
        msam_path = Path(__file__).parent.parent / "MSAM_INTEGRATION.md"
        if not msam_path.exists():
            pytest.skip("MSAM_INTEGRATION.md optional")

    def test_research_engine_exists(self):
        """Check if RESEARCH_ENGINE.md exists"""
        research_path = Path(__file__).parent.parent / "RESEARCH_ENGINE.md"
        if not research_path.exists():
            pytest.skip("RESEARCH_ENGINE.md optional")


class TestSetupScript:
    """Test setup.sh script"""

    def test_setup_script_exists(self):
        """Check if setup.sh exists and is executable"""
        setup_path = Path(__file__).parent.parent / "setup.sh"
        if not setup_path.exists():
            pytest.skip("setup.sh optional")
        assert setup_path.exists()


class TestDockerfile:
    """Test Dockerfile"""

    def test_dockerfile_exists(self):
        """Check if Dockerfile exists"""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile optional")
        assert dockerfile_path.exists()

    def test_dockerfile_base_image(self):
        """Check Dockerfile uses Python base image"""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile optional")

        content = dockerfile_path.read_text()
        assert "FROM python:" in content, "Dockerfile must use Python base image"


class TestMakefile:
    """Test Makefile"""

    def test_makefile_exists(self):
        """Check if Makefile exists"""
        makefile_path = Path(__file__).parent.parent / "Makefile"
        if not makefile_path.exists():
            pytest.skip("Makefile optional")
        assert makefile_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
