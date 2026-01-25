import hashlib
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os


@dataclass
class ReportSection:
    """Represents a section in the report."""

    title: str
    content: str
    level: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "content": self.content, "level": self.level}


@dataclass
class ReportData:
    """Container for all data needed to generate a report."""

    sample_name: str
    sample_id: str
    reference_name: str
    reference_id: str
    analysis_date: str
    analysis_time: str
    operator_name: str
    software_version: str
    overall_status: str
    coverage_percentage: float
    total_variants: int
    critical_variants: int
    variants: List[Dict[str, Any]] = field(default_factory=list)
    effects: List[Dict[str, Any]] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sample_description: str = ""
    instrument_name: str = ""
    run_id: str = ""
    comments: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_name": self.sample_name,
            "sample_id": self.sample_id,
            "reference_name": self.reference_name,
            "reference_id": self.reference_id,
            "analysis_date": self.analysis_date,
            "analysis_time": self.analysis_time,
            "operator_name": self.operator_name,
            "software_version": self.software_version,
            "overall_status": self.overall_status,
            "coverage_percentage": self.coverage_percentage,
            "total_variants": self.total_variants,
            "critical_variants": self.critical_variants,
            "variants": self.variants,
            "effects": self.effects,
            "failures": self.failures,
            "warnings": self.warnings,
            "sample_description": self.sample_description,
            "instrument_name": self.instrument_name,
            "run_id": self.run_id,
            "comments": self.comments,
        }


class ReportGenerator:
    """Generates regulatory-compliant PDF reports."""

    def __init__(self, output_dir: str = "."):
        """Initialize the report generator.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self, data: ReportData, output_filename: str = None) -> str:
        """Generate a PDF report.

        Args:
            data: ReportData containing all report information
            output_filename: Optional output filename

        Returns:
            Path to generated PDF file
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.lib import colors

        if output_filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_sample_name = "".join(
                c if c.isalnum() else "_" for c in data.sample_name
            )
            output_filename = f"QC_Report_{safe_sample_name}_{timestamp}.pdf"

        output_path = os.path.join(self.output_dir, output_filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=20,
            alignment=1,
        )

        header_style = ParagraphStyle(
            "Header",
            parent=styles["Heading2"],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.darkblue,
        )

        normal_style = ParagraphStyle(
            "Normal", parent=styles["Normal"], fontSize=10, spaceAfter=6
        )

        story = []

        story.append(
            Paragraph("NucleoQC - Biologics Quality Control Report", title_style)
        )
        story.append(Spacer(1, 12))

        story.append(Paragraph("1. Sample Information", header_style))
        sample_info = [
            ["Sample Name:", data.sample_name],
            ["Sample ID:", data.sample_id],
            ["Description:", data.sample_description or "N/A"],
            ["Instrument:", data.instrument_name or "N/A"],
            ["Run ID:", data.run_id or "N/A"],
        ]

        t = Table(sample_info, colWidths=[2 * inch, 4 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.darkblue),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 12))

        story.append(Paragraph("2. Reference Sequence", header_style))
        ref_info = [
            ["Reference Name:", data.reference_name],
            ["Reference ID:", data.reference_id],
        ]

        t = Table(ref_info, colWidths=[2 * inch, 4 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.darkblue),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 12))

        story.append(Paragraph("3. Analysis Results", header_style))

        status_color = colors.green if data.overall_status == "PASS" else colors.red
        result_info = [
            [
                "Overall Status:",
                Paragraph(f"<b>{data.overall_status}</b>", normal_style),
            ],
            ["Coverage:", f"{data.coverage_percentage:.1f}%"],
            ["Total Variants:", str(data.total_variants)],
            ["Critical Variants:", str(data.critical_variants)],
        ]

        t = Table(result_info, colWidths=[2 * inch, 4 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.darkblue),
                    ("TEXTCOLOR", (0, 1), (0, 1), status_color),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 12))

        if data.variants:
            story.append(Paragraph("4. Variant Details", header_style))

            variant_headers = ["Position", "Ref", "Alt", "Type", "Quality", "Impact"]
            variant_data = []

            for v in data.variants[:20]:
                variant_data.append(
                    [
                        str(v.get("position", "N/A")),
                        v.get("ref_base", "-"),
                        v.get("alt_base", "-"),
                        v.get("variant_type", "N/A"),
                        f"{v.get('quality_score', 0):.1f}",
                        v.get("is_critical", False) and "CRITICAL" or "Low",
                    ]
                )

            if variant_data:
                t = Table(
                    [variant_headers] + variant_data,
                    colWidths=[
                        1 * inch,
                        0.8 * inch,
                        0.8 * inch,
                        1.2 * inch,
                        1 * inch,
                        1 * inch,
                    ],
                )
                t.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )
                story.append(t)
                story.append(Spacer(1, 12))

        if data.failures:
            story.append(Paragraph("5. QC Failures", header_style))
            for failure in data.failures:
                story.append(Paragraph(f"• {failure}", normal_style))
            story.append(Spacer(1, 12))

        if data.warnings:
            story.append(Paragraph("6. Warnings", header_style))
            for warning in data.warnings:
                story.append(Paragraph(f"• {warning}", normal_style))
            story.append(Spacer(1, 12))

        story.append(Paragraph("7. Audit Information", header_style))

        current_time = datetime.datetime.now().isoformat()
        report_hash = self._generate_report_hash(data, current_time)

        audit_info = [
            ["Analysis Date:", data.analysis_date],
            ["Analysis Time:", data.analysis_time],
            ["Operator:", data.operator_name],
            ["Software Version:", data.software_version],
            ["Report Generated:", current_time],
            ["Report Hash:", report_hash[:32] + "..."],
        ]

        t = Table(audit_info, colWidths=[2 * inch, 4 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.darkblue),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 24))

        story.append(Paragraph("QA Approval", header_style))
        story.append(Spacer(1, 24))
        approval_table = Table(
            [
                ["Name:", "", "Signature:", ""],
                ["Date:", "", "", ""],
            ],
            colWidths=[1.5 * inch, 2 * inch, 1.5 * inch, 2 * inch],
        )
        approval_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(approval_table)

        doc.build(story)

        return output_path

    def _generate_report_hash(self, data: ReportData, timestamp: str) -> str:
        """Generate a hash for report integrity verification.

        Args:
            data: ReportData used to generate the report
            timestamp: Timestamp of report generation

        Returns:
            SHA-256 hash string
        """
        content = f"{data.to_dict()}{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()

    def generate_summary_report(
        self, results: List[Dict[str, Any]], output_filename: str = None
    ) -> str:
        """Generate a summary report for multiple samples.

        Args:
            results: List of analysis results
            output_filename: Optional output filename

        Returns:
            Path to generated PDF file
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.lib import colors

        if output_filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"QC_Summary_Report_{timestamp}.pdf"

        output_path = os.path.join(self.output_dir, output_filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=20,
            alignment=1,
        )

        story = []

        story.append(Paragraph("NucleoQC - Batch Analysis Summary", title_style))
        story.append(Spacer(1, 12))

        story.append(Paragraph(f"Total Samples: {len(results)}", styles["Normal"]))
        passed = sum(1 for r in results if r.get("overall_status") == "PASS")
        story.append(
            Paragraph(
                f"Passed: {passed} | Failed: {len(results) - passed}", styles["Normal"]
            )
        )
        story.append(Spacer(1, 12))

        headers = ["Sample", "Status", "Coverage", "Variants", "Critical"]
        table_data = []

        for r in results:
            status = r.get("overall_status", "UNKNOWN")
            table_data.append(
                [
                    r.get("sample_name", "N/A"),
                    status,
                    f"{r.get('coverage_percentage', 0):.1f}%",
                    str(r.get("total_variants", 0)),
                    str(r.get("critical_variants", 0)),
                ]
            )

        t = Table(
            [headers] + table_data,
            colWidths=[2 * inch, 1 * inch, 1.2 * inch, 1 * inch, 1 * inch],
        )
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )

        story.append(t)

        doc.build(story)

        return output_path
