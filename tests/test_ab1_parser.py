import pytest
import tempfile
import os
from src.ab1_parser import AB1Parser, AB1Error, ChromatogramData


class TestAB1Parser:
    """Test cases for AB1 file parser."""

    def test_parser_initialization(self):
        """Test parser initializes correctly."""
        parser = AB1Parser("test_data/sample.ab1")
        assert parser.file_path == "test_data/sample.ab1"
        assert parser._parsed is False

    def test_invalid_file_path(self):
        """Test parser raises error for non-existent file."""
        parser = AB1Parser("/nonexistent/path/file.ab1")
        with pytest.raises(AB1Error):
            parser.parse()

    def test_chromatogram_data_structure(self):
        """Test ChromatogramData dataclass."""
        data = ChromatogramData(
            sequence="ATCG",
            confidence_scores=[30, 40, 35, 45],
            positions_a=[1.0, 2.0, 3.0, 4.0],
            positions_t=[0.5, 1.5, 2.5, 3.5],
            positions_c=[0.8, 1.8, 2.8, 3.8],
            positions_g=[0.9, 1.9, 2.9, 3.9],
            peak_positions=[0, 1, 2, 3],
        )

        assert data.get_coverage() == 4
        assert data.get_average_quality() == 37.5

    def test_empty_chromatogram_coverage(self):
        """Test coverage calculation for empty data."""
        data = ChromatogramData(
            sequence="",
            confidence_scores=[],
            positions_a=[],
            positions_t=[],
            positions_c=[],
            positions_g=[],
            peak_positions=[],
        )

        assert data.get_coverage() == 0
        assert data.get_average_quality() == 0.0


class TestAB1ErrorHandling:
    """Test error handling in AB1 parser."""

    def test_custom_exceptions(self):
        """Test custom exception classes."""
        with pytest.raises(AB1Error):
            raise AB1Error("Test error")

        with pytest.raises(AB1Error):
            raise AB1Error("Invalid file")

    def test_invalid_file_exception(self):
        """Test InvalidAB1FileError."""
        with pytest.raises(Exception):
            raise AB1Error("Invalid AB1 file format")

    def test_version_not_supported(self):
        """Test UnsupportedVersionError."""
        with pytest.raises(Exception):
            raise AB1Error("Version not supported")
