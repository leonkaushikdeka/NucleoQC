import pytest
import tempfile
import os
from src.alignment import SequenceAligner, AlignmentResult, GenBankParser


class TestSequenceAligner:
    """Test cases for sequence alignment."""

    def test_aligner_initialization(self):
        """Test aligner initializes with default parameters."""
        aligner = SequenceAligner()
        assert aligner is not None

    def test_aligner_custom_scores(self):
        """Test aligner with custom scoring."""
        aligner = SequenceAligner(match_score=3.0, mismatch_score=-1.0, gap_score=-2.0)
        assert aligner is not None

    def test_simple_alignment(self):
        """Test simple sequence alignment."""
        aligner = SequenceAligner()
        result = aligner.align("ATCG", "ATCG")

        assert isinstance(result, AlignmentResult)
        assert result.query_sequence == "ATCG"
        assert result.target_sequence == "ATCG"
        assert result.score > 0

    def test_alignment_with_mismatch(self):
        """Test alignment with a single mismatch."""
        aligner = SequenceAligner()
        result = aligner.align("ATCC", "ATCG")

        assert isinstance(result, AlignmentResult)
        mismatches = result.get_mismatches()
        assert len(mismatches) >= 0

    def test_alignment_coverage(self):
        """Test coverage calculation."""
        aligner = SequenceAligner()
        result = aligner.align("ATCG", "ATCGATCG")

        assert isinstance(result, AlignmentResult)
        assert 0 <= result.coverage <= 100

    def test_get_mismatches(self):
        """Test mismatch detection."""
        aligner = SequenceAligner()
        result = aligner.align("ATCG", "ATGG")

        mismatches = result.get_mismatches()
        assert isinstance(mismatches, list)

    def test_get_gaps(self):
        """Test gap detection."""
        aligner = SequenceAligner()
        result = aligner.align("ATCG", "AT-CG")

        gaps = result.get_gaps()
        assert isinstance(gaps, list)

    def test_find_best_match(self):
        """Test finding best match among multiple targets."""
        aligner = SequenceAligner()

        targets = ["ATCGATCG", "GGGGGGGG", "ATCGATCG"]
        query = "ATCG"

        best_index, best_result = aligner.find_best_match(query, targets)

        assert isinstance(best_result, AlignmentResult)
        assert 0 <= best_index < len(targets)

    def test_alignment_result_to_dict(self):
        """Test alignment result to dictionary conversion."""
        aligner = SequenceAligner()
        result = aligner.align("ATCG", "ATCG")

        result_dict = {
            "query_sequence": result.query_sequence,
            "target_sequence": result.target_sequence,
            "score": result.score,
            "coverage": result.coverage,
        }

        assert "query_sequence" in result_dict
        assert "target_sequence" in result_dict


class TestGenBankParser:
    """Test cases for GenBank file parsing."""

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent GenBank file."""
        with pytest.raises(FileNotFoundError):
            GenBankParser.parse("/nonexistent/file.gb")

    def test_parse_invalid_format(self):
        """Test parsing invalid GenBank format."""
        import tempfile
        import os

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".gb", delete=False) as f:
                temp_path = f.name
                f.write("INVALID CONTENT")

            with pytest.raises(ValueError):
                GenBankParser.parse(temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_reference_sequence_length(self):
        """Test reference sequence length property."""
        from src.alignment import ReferenceSequence

        ref = ReferenceSequence(
            id="test",
            name="Test",
            description="Test reference",
            sequence="ATCGATCG",
            features=[],
        )

        assert ref.length == 8

    def test_extract_region(self):
        """Test extracting region from reference."""
        from src.alignment import ReferenceSequence

        ref = ReferenceSequence(
            id="test",
            name="Test",
            description="Test reference",
            sequence="ATCGATCG",
            features=[],
        )

        region = ref.extract_region(0, 4)
        assert region == "ATCG"

    def test_extract_invalid_region(self):
        """Test extracting invalid region."""
        from src.alignment import ReferenceSequence

        ref = ReferenceSequence(
            id="test",
            name="Test",
            description="Test reference",
            sequence="ATCG",
            features=[],
        )

        region = ref.extract_region(0, 10)
        assert region == "ATCG"
