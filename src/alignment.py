from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Align import PairwiseAligner
import re


@dataclass
class AlignmentResult:
    """Container for alignment results."""

    query_sequence: str
    target_sequence: str
    aligned_query: str
    aligned_target: str
    score: float
    query_start: int
    query_end: int
    target_start: int
    target_end: int
    coverage: float

    def get_mismatches(self) -> List[Tuple[int, str, str]]:
        """Get list of mismatches between aligned sequences.

        Returns:
            List of (position, query_base, target_base) tuples
        """
        mismatches = []
        for i, (q, t) in enumerate(zip(self.aligned_query, self.aligned_target)):
            if q != t and q != "-" and t != "-":
                mismatches.append((i, q, t))
        return mismatches

    def get_gaps(self) -> List[Tuple[int, str]]:
        """Get list of gaps in the alignment.

        Returns:
            List of (position, sequence_with_gap) tuples
        """
        gaps = []
        for i, (q, t) in enumerate(zip(self.aligned_query, self.aligned_target)):
            if q == "-" or t == "-":
                gaps.append((i, q if q != "-" else t))
        return gaps


@dataclass
class ReferenceSequence:
    """Container for reference sequence information."""

    id: str
    name: str
    description: str
    sequence: str
    features: List[Dict[str, Any]]

    @property
    def length(self) -> int:
        """Return the length of the reference sequence."""
        return len(self.sequence)

    def extract_region(self, start: int, end: int) -> str:
        """Extract a region from the reference sequence.

        Args:
            start: Start position (0-based)
            end: End position (exclusive)

        Returns:
            Extracted sequence region
        """
        return self.sequence[start:end]


class GenBankParser:
    """Parser for GenBank reference files."""

    @staticmethod
    def parse(file_path: str) -> ReferenceSequence:
        """Parse a GenBank file and extract reference information.

        Args:
            file_path: Path to the GenBank file

        Returns:
            ReferenceSequence object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        try:
            record = SeqIO.read(file_path, "gb")
        except FileNotFoundError:
            raise FileNotFoundError(f"GenBank file not found: {file_path}")
        except ValueError:
            raise ValueError(f"Invalid GenBank format in file: {file_path}")

        features = []
        for feature in record.features:
            feature_dict = {
                "type": feature.type,
                "location": str(feature.location),
                "qualifiers": dict(feature.qualifiers),
            }
            features.append(feature_dict)

        return ReferenceSequence(
            id=record.id,
            name=record.name,
            description=record.description,
            sequence=str(record.seq),
            features=features,
        )

    @staticmethod
    def parse_from_string(gb_string: str) -> ReferenceSequence:
        """Parse a GenBank file from a string.

        Args:
            gb_string: GenBank file content as string

        Returns:
            ReferenceSequence object
        """
        from io import StringIO

        record = SeqIO.read(StringIO(gb_string), "gb")

        features = []
        for feature in record.features:
            feature_dict = {
                "type": feature.type,
                "location": str(feature.location),
                "qualifiers": dict(feature.qualifiers),
            }
            features.append(feature_dict)

        return ReferenceSequence(
            id=record.id,
            name=record.name,
            description=record.description,
            sequence=str(record.seq),
            features=features,
        )


class SequenceAligner:
    """Sequence aligner using semi-global alignment."""

    def __init__(
        self,
        match_score: float = 2.0,
        mismatch_score: float = -1.0,
        gap_score: float = -2.0,
        gap_extension_score: float = -0.5,
    ):
        """Initialize the aligner with scoring parameters.

        Args:
            match_score: Score for matching bases
            mismatch_score: Score for mismatching bases
            gap_score: Score for opening a gap
            gap_extension_score: Score for extending a gap
        """
        self.aligner = PairwiseAligner()
        self.aligner.mode = "global"
        self.aligner.match_score = match_score
        self.aligner.mismatch_score = mismatch_score
        self.aligner.open_gap_score = gap_score
        self.aligner.extend_gap_score = gap_extension_score

    def align(
        self,
        query_sequence: str,
        target_sequence: str,
        target_start: int = 0,
        target_end: Optional[int] = None,
    ) -> AlignmentResult:
        """Align a query sequence to a target sequence.

        Args:
            query_sequence: The query sequence (from AB1 data)
            target_sequence: The target sequence (from GenBank)
            target_start: Start position in target for partial alignment
            target_end: End position in target (None for full length)

        Returns:
            AlignmentResult object
        """
        if target_end is None:
            target_end = len(target_sequence)

        target_region = target_sequence[target_start:target_end]

        alignments = self.aligner.align(target_region, query_sequence)

        if not alignments:
            return AlignmentResult(
                query_sequence=query_sequence,
                target_sequence=target_region,
                aligned_query=query_sequence,
                aligned_target=target_region,
                score=0.0,
                query_start=0,
                query_end=len(query_sequence),
                target_start=target_start,
                target_end=target_end,
                coverage=0.0,
            )

        best_alignment = alignments[0]

        aligned_target = str(best_alignment[0])
        aligned_query = str(best_alignment[1])

        query_len = len(query_sequence)
        target_len = len(target_region)

        coverage = min(query_len, target_len) / max(query_len, target_len) * 100

        return AlignmentResult(
            query_sequence=query_sequence,
            target_sequence=target_region,
            aligned_query=aligned_query,
            aligned_target=aligned_target,
            score=best_alignment.score,
            query_start=0,
            query_end=query_len,
            target_start=target_start,
            target_end=target_end,
            coverage=coverage,
        )

    def find_best_match(
        self,
        query_sequence: str,
        target_sequences: List[str],
        target_starts: List[int] = None,
    ) -> Tuple[int, AlignmentResult]:
        """Find the best matching target region for a query sequence.

        Args:
            query_sequence: The query sequence
            target_sequences: List of target sequences to search
            target_starts: Starting positions for each target (optional)

        Returns:
            Tuple of (best_target_index, AlignmentResult)
        """
        if target_starts is None:
            target_starts = [0] * len(target_sequences)

        best_score = float("-inf")
        best_index = -1
        best_result = None

        for i, target in enumerate(target_sequences):
            start = target_starts[i] if i < len(target_starts) else 0
            result = self.align(query_sequence, target, target_start=start)

            if result.score > best_score:
                best_score = result.score
                best_index = i
                best_result = result

        return best_index, best_result


class ContigAssembler:
    """Assembles overlapping sequencing reads into contigs."""

    def __init__(self, min_overlap: int = 20, min_identity: float = 0.95):
        """Initialize the assembler.

        Args:
            min_overlap: Minimum overlap between reads
            min_identity: Minimum identity for overlap alignment
        """
        self.min_overlap = min_overlap
        self.min_identity = min_identity
        self.aligner = SequenceAligner(
            match_score=1.0, mismatch_score=-1.0, gap_score=-2.0
        )

    def assemble(
        self, sequences: List[Tuple[str, int]]
    ) -> Tuple[str, List[Tuple[int, str, str]]]:
        """Assemble sequences into a consensus contig.

        Args:
            sequences: List of (sequence, direction) tuples

        Returns:
            Tuple of (consensus_sequence, variant_positions)
        """
        if not sequences:
            return "", []

        processed_seqs = []
        for seq, direction in sequences:
            if direction == -1:
                seq = str(Seq(seq).reverse_complement())
            processed_seqs.append(seq)

        consensus = self._greedy_assemble(processed_seqs)

        return consensus, []

    def _greedy_assemble(self, sequences: List[str]) -> str:
        """Perform greedy assembly of sequences.

        Args:
            sequences: List of sequences to assemble

        Returns:
            Consensus sequence
        """
        if len(sequences) == 1:
            return sequences[0]

        sorted_seqs = sorted(sequences, key=len, reverse=True)
        consensus = sorted_seqs[0]

        for seq in sorted_seqs[1:]:
            overlap = self._find_overlap(consensus, seq)
            if overlap >= self.min_overlap:
                consensus = consensus + seq[overlap:]
            else:
                overlap = self._find_overlap(seq, consensus)
                if overlap >= self.min_overlap:
                    consensus = seq + consensus[overlap:]
                else:
                    pass

        return consensus

    def _find_overlap(self, seq1: str, seq2: str) -> int:
        """Find the overlap length between end of seq1 and start of seq2.

        Args:
            seq1: First sequence
            seq2: Second sequence

        Returns:
            Overlap length
        """
        max_overlap = min(len(seq1), len(seq2), 100)

        for overlap in range(max_overlap, self.min_overlap - 1, -1):
            if seq1[-overlap:] == seq2[:overlap]:
                return overlap

        return 0
