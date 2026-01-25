from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class VariantType(Enum):
    """Types of genetic variants."""

    SNP = "SNP"
    INSERTION = "INSERTION"
    DELETION = "DELETION"
    MIXED = "MIXED"


class VariantEffect(Enum):
    """Effects of variants on protein sequence."""

    SYNONYMOUS = "SYNONYMOUS"
    MISSENSE = "MISSENSE"
    NONSENSE = "NONSENSE"
    FRAMESHIFT = "FRAMESHIFT"
    INFRAME_INSERTION = "INFRAME_INSERTION"
    INFRAME_DELETION = "INFRAME_DELETION"
    UPSTREAM = "UPSTREAM"
    DOWNSTREAM = "DOWNSTREAM"
    INTRONIC = "INTRONIC"
    INTERGENIC = "INTERGENIC"


@dataclass
class Variant:
    """Represents a genetic variant."""

    position: int
    ref_base: str
    alt_base: str
    variant_type: VariantType
    quality_score: float
    coverage: int
    frequency: float

    @property
    def is_critical(self) -> bool:
        """Check if variant is critical for QC purposes."""
        return self.variant_type in [VariantType.INSERTION, VariantType.DELETION]

    def to_dict(self) -> Dict[str, Any]:
        """Convert variant to dictionary."""
        return {
            "position": self.position,
            "ref_base": self.ref_base,
            "alt_base": self.alt_base,
            "variant_type": self.variant_type.value,
            "quality_score": self.quality_score,
            "coverage": self.coverage,
            "frequency": self.frequency,
            "is_critical": self.is_critical,
        }


@dataclass
class VariantEffectResult:
    """Result of variant effect analysis."""

    variant: Variant
    effect: VariantEffect
    codon_change: Optional[str]
    amino_acid_change: Optional[Tuple[str, str]]
    protein_position: Optional[int]
    impact: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "effect": self.effect.value,
            "codon_change": self.codon_change,
            "amino_acid_change": self.amino_acid_change,
            "protein_position": self.protein_position,
            "impact": self.impact,
        }
        result.update(self.variant.to_dict())
        return result


@dataclass
class VariantCallResult:
    """Container for complete variant calling results."""

    variants: List[Variant]
    effects: List[VariantEffectResult]
    passed_quality_check: bool
    overall_status: str
    coverage_percentage: float
    total_variants: int
    critical_variants: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "variants": [v.to_dict() for v in self.variants],
            "effects": [e.to_dict() for e in self.effects],
            "passed_quality_check": self.passed_quality_check,
            "overall_status": self.overall_status,
            "coverage_percentage": self.coverage_percentage,
            "total_variants": self.total_variants,
            "critical_variants": self.critical_variants,
        }


class CodonTable:
    """Standard genetic codon table."""

    CODON_MAP = {
        "TTT": "F",
        "TTC": "F",
        "TTA": "L",
        "TTG": "L",
        "TCT": "S",
        "TCC": "S",
        "TCA": "S",
        "TCG": "S",
        "TAT": "Y",
        "TAC": "Y",
        "TAA": "*",
        "TAG": "*",
        "TGT": "C",
        "TGC": "C",
        "TGA": "*",
        "TGG": "W",
        "CTT": "L",
        "CTC": "L",
        "CTA": "L",
        "CTG": "L",
        "CCT": "P",
        "CCC": "P",
        "CCA": "P",
        "CCG": "P",
        "CAT": "H",
        "CAC": "H",
        "CAA": "Q",
        "CAG": "Q",
        "CGT": "R",
        "CGC": "R",
        "CGA": "R",
        "CGG": "R",
        "ATT": "I",
        "ATC": "I",
        "ATA": "I",
        "ATG": "M",
        "ACT": "T",
        "ACC": "T",
        "ACA": "T",
        "ACG": "T",
        "AAT": "N",
        "AAC": "N",
        "AAA": "K",
        "AAG": "K",
        "AGT": "S",
        "AGC": "S",
        "AGA": "R",
        "AGG": "R",
        "GTT": "V",
        "GTC": "V",
        "GTA": "V",
        "GTG": "V",
        "GCT": "A",
        "GCC": "A",
        "GCA": "A",
        "GCG": "A",
        "GAT": "D",
        "GAC": "D",
        "GAA": "E",
        "GAG": "E",
        "GGT": "G",
        "GGC": "G",
        "GGA": "G",
        "GGG": "G",
    }

    @classmethod
    def translate_codon(cls, codon: str) -> str:
        """Translate a codon to an amino acid.

        Args:
            codon: Three-letter codon string

        Returns:
            Amino acid letter or '*' for stop codon
        """
        codon = codon.upper()
        return cls.CODON_MAP.get(codon, "X")

    @classmethod
    def is_synonymous(cls, ref_codon: str, alt_codon: str) -> bool:
        """Check if two codons encode the same amino acid.

        Args:
            ref_codon: Reference codon
            alt_codon: Alternate codon

        Returns:
            True if synonymous
        """
        return cls.translate_codon(ref_codon) == cls.translate_codon(alt_codon)


class VariantCaller:
    """Identifies and analyzes variants in sequencing data."""

    def __init__(
        self,
        min_quality: float = 20.0,
        min_coverage: int = 10,
        min_frequency: float = 0.2,
    ):
        """Initialize the variant caller.

        Args:
            min_quality: Minimum quality score for variant call
            min_coverage: Minimum coverage at variant position
            min_frequency: Minimum variant frequency for calling
        """
        self.min_quality = min_quality
        self.min_coverage = min_coverage
        self.min_frequency = min_frequency

    def call_variants(
        self,
        aligned_query: str,
        aligned_target: str,
        target_start: int = 0,
        quality_scores: Optional[List[int]] = None,
    ) -> List[Variant]:
        """Call variants from aligned sequences.

        Args:
            aligned_query: Aligned query sequence
            aligned_target: Aligned target sequence
            target_start: Starting position in target
            quality_scores: Quality scores for each base

        Returns:
            List of Variant objects
        """
        variants = []

        for i, (q_base, t_base) in enumerate(zip(aligned_query, aligned_target)):
            if q_base == t_base:
                continue

            if q_base == "-" and t_base != "-":
                variants.append(
                    Variant(
                        position=target_start + i,
                        ref_base=t_base,
                        alt_base="-",
                        variant_type=VariantType.DELETION,
                        quality_score=quality_scores[i] if quality_scores else 0,
                        coverage=0,
                        frequency=1.0,
                    )
                )
            elif q_base != "-" and t_base == "-":
                variants.append(
                    Variant(
                        position=target_start + i,
                        ref_base="-",
                        alt_base=q_base,
                        variant_type=VariantType.INSERTION,
                        quality_score=quality_scores[i] if quality_scores else 0,
                        coverage=0,
                        frequency=1.0,
                    )
                )
            elif q_base != "-" and t_base != "-":
                variants.append(
                    Variant(
                        position=target_start + i,
                        ref_base=t_base,
                        alt_base=q_base,
                        variant_type=VariantType.SNP,
                        quality_score=quality_scores[i] if quality_scores else 0,
                        coverage=0,
                        frequency=1.0,
                    )
                )

        return variants

    def analyze_effects(
        self,
        variants: List[Variant],
        ref_sequence: str,
        protein_sequence: Optional[str] = None,
    ) -> List[VariantEffectResult]:
        """Analyze the effects of variants on protein sequence.

        Args:
            variants: List of variants
            ref_sequence: Reference DNA sequence
            protein_sequence: Reference protein sequence (optional)

        Returns:
            List of VariantEffectResult objects
        """
        effects = []

        for variant in variants:
            effect = self._analyze_single_variant(
                variant, ref_sequence, protein_sequence
            )
            effects.append(effect)

        return effects

    def _analyze_single_variant(
        self,
        variant: Variant,
        ref_sequence: str,
        protein_sequence: Optional[str] = None,
    ) -> VariantEffectResult:
        """Analyze the effect of a single variant.

        Args:
            variant: The variant to analyze
            ref_sequence: Reference DNA sequence
            protein_sequence: Reference protein sequence

        Returns:
            VariantEffectResult object
        """
        codon_pos = (variant.position // 3) * 3
        codon_end = min(codon_pos + 3, len(ref_sequence))

        if variant.variant_type == VariantType.SNP:
            if codon_end - codon_pos == 3:
                ref_codon = ref_sequence[codon_pos:codon_end]
                ref_aa = CodonTable.translate_codon(ref_codon)

                alt_codon_list = list(ref_codon)
                alt_codon_list[variant.position % 3] = variant.alt_base
                alt_codon = "".join(alt_codon_list)
                alt_aa = CodonTable.translate_codon(alt_codon)

                if ref_aa == alt_aa:
                    effect = VariantEffect.SYNONYMOUS
                    impact = "LOW"
                elif alt_aa == "*":
                    effect = VariantEffect.NONSENSE
                    impact = "HIGH"
                else:
                    effect = VariantEffect.MISSENSE
                    impact = "MODERATE"

                return VariantEffectResult(
                    variant=variant,
                    effect=effect,
                    codon_change=f"{ref_codon}>{alt_codon}",
                    amino_acid_change=(ref_aa, alt_aa),
                    protein_position=(codon_pos // 3) + 1,
                    impact=impact,
                )
            else:
                return VariantEffectResult(
                    variant=variant,
                    effect=VariantEffect.INTRONIC,
                    codon_change=None,
                    amino_acid_change=None,
                    protein_position=None,
                    impact="LOW",
                )

        elif variant.variant_type == VariantType.INSERTION:
            if (codon_end - codon_pos) % 3 == 0:
                return VariantEffectResult(
                    variant=variant,
                    effect=VariantEffect.INFRAME_INSERTION,
                    codon_change=None,
                    amino_acid_change=None,
                    protein_position=(codon_pos // 3) + 1,
                    impact="MODERATE",
                )
            else:
                return VariantEffectResult(
                    variant=variant,
                    effect=VariantEffect.FRAMESHIFT,
                    codon_change=None,
                    amino_acid_change=None,
                    protein_position=(codon_pos // 3) + 1,
                    impact="HIGH",
                )

        elif variant.variant_type == VariantType.DELETION:
            if (codon_end - codon_pos) % 3 == 0:
                return VariantEffectResult(
                    variant=variant,
                    effect=VariantEffect.INFRAME_DELETION,
                    codon_change=None,
                    amino_acid_change=None,
                    protein_position=(codon_pos // 3) + 1,
                    impact="MODERATE",
                )
            else:
                return VariantEffectResult(
                    variant=variant,
                    effect=VariantEffect.FRAMESHIFT,
                    codon_change=None,
                    amino_acid_change=None,
                    protein_position=(codon_pos // 3) + 1,
                    impact="HIGH",
                )

        return VariantEffectResult(
            variant=variant,
            effect=VariantEffect.INTRONIC,
            codon_change=None,
            amino_acid_change=None,
            protein_position=None,
            impact="LOW",
        )

    def run_analysis(
        self,
        aligned_query: str,
        aligned_target: str,
        target_start: int = 0,
        ref_sequence: Optional[str] = None,
        quality_scores: Optional[List[int]] = None,
    ) -> VariantCallResult:
        """Run complete variant calling analysis.

        Args:
            aligned_query: Aligned query sequence
            aligned_target: Aligned target sequence
            target_start: Starting position in target
            ref_sequence: Full reference sequence
            quality_scores: Quality scores for query bases

        Returns:
            VariantCallResult object
        """
        variants = self.call_variants(
            aligned_query, aligned_target, target_start, quality_scores
        )

        effects = self.analyze_effects(variants, ref_sequence or aligned_target)

        critical_count = sum(1 for e in effects if e.impact == "HIGH")

        passed = critical_count == 0

        status = "PASS" if passed else "FAIL"

        coverage = (
            (len(aligned_query) / len(aligned_target) * 100) if aligned_target else 0
        )

        return VariantCallResult(
            variants=variants,
            effects=effects,
            passed_quality_check=passed,
            overall_status=status,
            coverage_percentage=coverage,
            total_variants=len(variants),
            critical_variants=critical_count,
        )


class ConstructVerifier:
    """Verifies construct integrity for QC purposes."""

    def __init__(
        self, min_coverage: float = 95.0, allowed_variants: Optional[List[int]] = None
    ):
        """Initialize the verifier.

        Args:
            min_coverage: Minimum coverage percentage required
            allowed_variants: List of variant positions that are allowed
        """
        self.min_coverage = min_coverage
        self.allowed_variants = allowed_variants or []
        self.variant_caller = VariantCaller()

    def verify(
        self, result: VariantCallResult, coverage: Optional[float] = None
    ) -> Dict[str, Any]:
        """Verify construct and return QC decision.

        Args:
            result: VariantCallResult from analysis
            coverage: Coverage percentage (overrides result value)

        Returns:
            Dictionary with verification decision
        """
        actual_coverage = (
            coverage if coverage is not None else result.coverage_percentage
        )

        failures = []

        if actual_coverage < self.min_coverage:
            failures.append(
                f"Coverage too low: {actual_coverage:.1f}% < {self.min_coverage}%"
            )

        critical_variants = [e for e in result.effects if e.impact == "HIGH"]
        if critical_variants:
            for cv in critical_variants:
                if cv.variant.position not in self.allowed_variants:
                    failures.append(
                        f"Critical variant at position {cv.variant.position}: "
                        f"{cv.effect.value}"
                    )

        passed = len(failures) == 0

        return {
            "passed": passed,
            "status": "PASS" if passed else "FAIL",
            "coverage": actual_coverage,
            "failures": failures,
            "total_variants": result.total_variants,
            "critical_variants": len(critical_variants),
            "warnings": [e for e in result.effects if e.impact == "MODERATE"],
        }
