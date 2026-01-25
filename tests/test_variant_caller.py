import pytest
from src.variant_caller import (
    VariantCaller,
    Variant,
    VariantType,
    VariantEffect,
    CodonTable,
    ConstructVerifier,
    VariantCallResult,
    VariantEffectResult,
)


class TestVariant:
    """Test cases for Variant dataclass."""

    def test_variant_creation(self):
        """Test variant creation."""
        variant = Variant(
            position=100,
            ref_base="A",
            alt_base="G",
            variant_type=VariantType.SNP,
            quality_score=30.0,
            coverage=50,
            frequency=1.0,
        )

        assert variant.position == 100
        assert variant.ref_base == "A"
        assert variant.alt_base == "G"
        assert variant.variant_type == VariantType.SNP

    def test_variant_is_critical(self):
        """Test critical variant detection."""
        snp_variant = Variant(
            position=100,
            ref_base="A",
            alt_base="G",
            variant_type=VariantType.SNP,
            quality_score=30.0,
            coverage=50,
            frequency=1.0,
        )
        assert snp_variant.is_critical is False

        insertion_variant = Variant(
            position=100,
            ref_base="-",
            alt_base="T",
            variant_type=VariantType.INSERTION,
            quality_score=30.0,
            coverage=50,
            frequency=1.0,
        )
        assert insertion_variant.is_critical is True

    def test_variant_to_dict(self):
        """Test variant to dictionary conversion."""
        variant = Variant(
            position=100,
            ref_base="A",
            alt_base="G",
            variant_type=VariantType.SNP,
            quality_score=30.0,
            coverage=50,
            frequency=1.0,
        )

        variant_dict = variant.to_dict()
        assert variant_dict["position"] == 100
        assert variant_dict["variant_type"] == "SNP"
        assert variant_dict["is_critical"] is False


class TestCodonTable:
    """Test cases for genetic codon table."""

    def test_translate_codon_phenylalanine(self):
        """Test phenylalanine codons."""
        assert CodonTable.translate_codon("TTT") == "F"
        assert CodonTable.translate_codon("TTC") == "F"

    def test_translate_codon_leucine(self):
        """Test leucine codons."""
        assert CodonTable.translate_codon("TTA") == "L"
        assert CodonTable.translate_codon("TTG") == "L"

    def test_translate_codon_stop_codons(self):
        """Test stop codons."""
        assert CodonTable.translate_codon("TAA") == "*"
        assert CodonTable.translate_codon("TAG") == "*"
        assert CodonTable.translate_codon("TGA") == "*"

    def test_is_synonymous_same(self):
        """Test synonymous mutation detection - same amino acid."""
        assert CodonTable.is_synonymous("TTT", "TTC") is True

    def test_is_synonymous_different(self):
        """Test synonymous mutation detection - different amino acids."""
        assert CodonTable.is_synonymous("TTT", "ATG") is False

    def test_translate_known_sequence(self):
        """Test translation of known sequence."""
        codon = "ATG"
        amino_acid = CodonTable.translate_codon(codon)
        assert amino_acid == "M"


class TestVariantCaller:
    """Test cases for variant calling functionality."""

    def test_caller_initialization(self):
        """Test variant caller initialization."""
        caller = VariantCaller()
        assert caller.min_quality == 20.0
        assert caller.min_coverage == 10
        assert caller.min_frequency == 0.2

    def test_caller_custom_parameters(self):
        """Test variant caller with custom parameters."""
        caller = VariantCaller(min_quality=30.0, min_coverage=20, min_frequency=0.3)
        assert caller.min_quality == 30.0

    def test_call_no_variants(self):
        """Test variant calling with identical sequences."""
        caller = VariantCaller()
        variants = caller.call_variants("ATCG", "ATCG", target_start=0)

        assert isinstance(variants, list)
        assert len(variants) == 0

    def test_call_snp_variant(self):
        """Test SNP variant detection."""
        caller = VariantCaller()
        variants = caller.call_variants("ATGG", "ATCG", target_start=0)

        assert len(variants) > 0
        assert any(v.variant_type == VariantType.SNP for v in variants)

    def test_call_insertion_variant(self):
        """Test insertion variant detection."""
        caller = VariantCaller()
        variants = caller.call_variants("ATGCG", "ATCG", target_start=0)

        assert len(variants) > 0

    def test_call_deletion_variant(self):
        """Test deletion variant detection."""
        caller = VariantCaller()
        variants = caller.call_variants("ATG", "ATCG", target_start=0)

        assert len(variants) > 0

    def test_run_analysis(self):
        """Test complete analysis workflow."""
        caller = VariantCaller()
        result = caller.run_analysis("ATCG", "ATCG", target_start=0)

        assert result.total_variants == 0
        assert result.passed_quality_check is True
        assert result.overall_status == "PASS"

    def test_run_analysis_with_variants(self):
        """Test analysis with variants."""
        caller = VariantCaller()
        result = caller.run_analysis("ATGG", "ATCG", target_start=0)

        assert result.total_variants >= 0
        assert isinstance(result.coverage_percentage, float)

    def test_analyze_effects(self):
        """Test variant effect analysis."""
        caller = VariantCaller()

        variant = Variant(
            position=1,
            ref_base="C",
            alt_base="G",
            variant_type=VariantType.SNP,
            quality_score=30.0,
            coverage=50,
            frequency=1.0,
        )

        effects = caller.analyze_effects([variant], "ATCGATCG")

        assert len(effects) == 1
        assert effects[0].effect in [VariantEffect.SYNONYMOUS, VariantEffect.MISSENSE]


class TestConstructVerifier:
    """Test cases for construct verification."""

    def test_verifier_initialization(self):
        """Test verifier initialization."""
        verifier = ConstructVerifier()
        assert verifier.min_coverage == 95.0

    def test_verifier_custom_parameters(self):
        """Test verifier with custom parameters."""
        verifier = ConstructVerifier(min_coverage=80.0, allowed_variants=[100, 200])
        assert verifier.min_coverage == 80.0
        assert 100 in verifier.allowed_variants

    def test_verify_pass(self):
        """Test verification passing."""
        from src.variant_caller import VariantCallResult

        result = VariantCallResult(
            variants=[],
            effects=[],
            passed_quality_check=True,
            overall_status="PASS",
            coverage_percentage=98.0,
            total_variants=0,
            critical_variants=0,
        )

        verifier = ConstructVerifier()
        verification = verifier.verify(result, coverage=98.0)

        assert verification["passed"] is True
        assert verification["status"] == "PASS"

    def test_verify_low_coverage(self):
        """Test verification with low coverage."""
        from src.variant_caller import VariantCallResult

        result = VariantCallResult(
            variants=[],
            effects=[],
            passed_quality_check=True,
            overall_status="PASS",
            coverage_percentage=50.0,
            total_variants=0,
            critical_variants=0,
        )

        verifier = ConstructVerifier()
        verification = verifier.verify(result, coverage=50.0)

        assert verification["passed"] is False
        assert "Coverage too low" in verification["failures"][0]

    def test_verify_with_allowed_variants(self):
        """Test verification with allowed critical variants."""
        from src.variant_caller import (
            VariantCallResult,
            VariantEffectResult,
            Variant,
            VariantType,
        )

        variant = Variant(
            position=100,
            ref_base="A",
            alt_base="G",
            variant_type=VariantType.SNP,
            quality_score=30.0,
            coverage=50,
            frequency=1.0,
        )

        effect_result = VariantEffectResult(
            variant=variant,
            effect=VariantEffect.NONSENSE,
            codon_change="ATG>TGG",
            amino_acid_change=("M", "W"),
            protein_position=1,
            impact="HIGH",
        )

        result = VariantCallResult(
            variants=[variant],
            effects=[effect_result],
            passed_quality_check=False,
            overall_status="FAIL",
            coverage_percentage=99.0,
            total_variants=1,
            critical_variants=1,
        )

        verifier = ConstructVerifier(allowed_variants=[100])
        verification = verifier.verify(result, coverage=99.0)

        assert verification["passed"] is True
