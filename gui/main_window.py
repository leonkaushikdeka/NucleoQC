import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QStatusBar,
    QToolBar,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QFrame,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NucleoQC - Biologics Quality Control Suite")
        self.setMinimumSize(1200, 800)

        self.current_reference = None
        self.current_ab1_files = []
        self.analysis_results = []

        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QHBoxLayout(header_frame)

        title_label = QLabel("NucleoQC")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Biologics Quality Control Suite")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: gray;")
        header_layout.addWidget(subtitle_label)

        header_layout.addStretch()

        self.version_label = QLabel("v1.0.0")
        self.version_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.version_label)

        main_layout.addWidget(header_frame)

        input_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        reference_group = QGroupBox("Reference Sequence")
        reference_layout = QVBoxLayout(reference_group)

        self.reference_path_label = QLabel("No reference selected")
        self.reference_path_label.setWordWrap(True)
        self.reference_path_label.setStyleSheet("color: gray; font-style: italic;")
        reference_layout.addWidget(self.reference_path_label)

        reference_btn_layout = QHBoxLayout()
        self.btn_load_reference = QPushButton("Load GenBank File")
        self.btn_load_reference.clicked.connect(self._load_reference)
        reference_btn_layout.addWidget(self.btn_load_reference)
        reference_layout.addLayout(reference_btn_layout)

        left_layout.addWidget(reference_group)

        ab1_group = QGroupBox("Sequencing Data (AB1)")
        ab1_layout = QVBoxLayout(ab1_group)

        self.ab1_files_label = QLabel("No AB1 files selected")
        self.ab1_files_label.setWordWrap(True)
        self.ab1_files_label.setStyleSheet("color: gray; font-style: italic;")
        ab1_layout.addWidget(self.ab1_files_label)

        ab1_btn_layout = QHBoxLayout()
        self.btn_load_ab1 = QPushButton("Load AB1 Files")
        self.btn_load_ab1.clicked.connect(self._load_ab1_files)
        ab1_btn_layout.addWidget(self.btn_load_ab1)

        self.btn_clear_ab1 = QPushButton("Clear")
        self.btn_clear_ab1.clicked.connect(self._clear_ab1_files)
        ab1_btn_layout.addWidget(self.btn_clear_ab1)

        ab1_layout.addLayout(ab1_btn_layout)

        self.ab1_count_label = QLabel("0 files loaded")
        self.ab1_count_label.setStyleSheet("color: gray;")
        ab1_layout.addWidget(self.ab1_count_label)

        left_layout.addWidget(ab1_group)

        operator_group = QGroupBox("Operator Information")
        operator_layout = QVBoxLayout(operator_group)

        operator_layout.addWidget(QLabel("Operator Name:"))
        self.operator_name_input = QLineEdit()
        operator_layout.addWidget(self.operator_name_input)

        operator_layout.addWidget(QLabel("Sample ID:"))
        self.sample_id_input = QLineEdit()
        operator_layout.addWidget(self.sample_id_input)

        left_layout.addWidget(operator_group)

        left_layout.addStretch()

        input_splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels(
            [
                "Sample",
                "Status",
                "Coverage",
                "Variants",
                "Critical",
                "Position",
                "Ref",
                "Alt",
            ]
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        results_layout.addWidget(self.results_table)

        right_layout.addWidget(results_group)

        button_layout = QHBoxLayout()

        self.btn_analyze = QPushButton("Run Analysis")
        self.btn_analyze.clicked.connect(self._run_analysis)
        self.btn_analyze.setEnabled(False)
        button_layout.addWidget(self.btn_analyze)

        self.btn_generate_report = QPushButton("Generate Report")
        self.btn_generate_report.clicked.connect(self._generate_report)
        self.btn_generate_report.setEnabled(False)
        button_layout.addWidget(self.btn_generate_report)

        button_layout.addStretch()

        right_layout.addLayout(button_layout)

        input_splitter.addWidget(right_panel)

        input_splitter.setSizes([300, 900])
        main_layout.addWidget(input_splitter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    def _init_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        load_ref_action = QAction("Load Reference...", self)
        load_ref_action.setShortcut("Ctrl+R")
        load_ref_action.triggered.connect(self._load_reference)
        file_menu.addAction(load_ref_action)

        load_ab1_action = QAction("Load AB1 Files...", self)
        load_ab1_action.setShortcut("Ctrl+O")
        load_ab1_action.triggered.connect(self._load_ab1_files)
        file_menu.addAction(load_ab1_action)

        file_menu.addSeparator()

        generate_report_action = QAction("Generate Report...", self)
        generate_report_action.setShortcut("Ctrl+P")
        generate_report_action.triggered.connect(self._generate_report)
        file_menu.addAction(generate_report_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")

        view_history_action = QAction("Analysis History...", self)
        view_history_action.triggered.connect(self._view_history)
        view_menu.addAction(view_history_action)

        tools_menu = menubar.addMenu("Tools")

        export_action = QAction("Export Audit Log...", self)
        export_action.triggered.connect(self._export_audit_log)
        tools_menu.addAction(export_action)

        help_menu = menubar.addMenu("Help")

        about_action = QAction("About NucleoQC...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        documentation_action = QAction("Documentation", self)
        documentation_action.triggered.connect(self._show_documentation)
        help_menu.addAction(documentation_action)

    def _init_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        load_ref_action = QAction("Reference", self)
        load_ref_action.triggered.connect(self._load_reference)
        toolbar.addAction(load_ref_action)

        load_ab1_action = QAction("AB1 Files", self)
        load_ab1_action.triggered.connect(self._load_ab1_files)
        toolbar.addAction(load_ab1_action)

        toolbar.addSeparator()

        analyze_action = QAction("Analyze", self)
        analyze_action.triggered.connect(self._run_analysis)
        toolbar.addAction(analyze_action)

        toolbar.addSeparator()

        report_action = QAction("Report", self)
        report_action.triggered.connect(self._generate_report)
        toolbar.addAction(report_action)

    def _init_statusbar(self):
        self.statusBar().showMessage("Ready")

    def _load_reference(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select GenBank Reference File",
            "",
            "GenBank Files (*.gb *.gbk);;All Files (*)",
        )

        if file_path:
            self.current_reference = file_path
            filename = os.path.basename(file_path)
            self.reference_path_label.setText(filename)
            self.reference_path_label.setStyleSheet("")
            self._update_analysis_button()

    def _load_ab1_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select AB1 Files", "", "AB1 Files (*.ab1);;All Files (*)"
        )

        if file_paths:
            self.current_ab1_files.extend(file_paths)
            self._update_ab1_display()
            self._update_analysis_button()

    def _clear_ab1_files(self):
        self.current_ab1_files = []
        self._update_ab1_display()
        self._update_analysis_button()

    def _update_ab1_display(self):
        if not self.current_ab1_files:
            self.ab1_files_label.setText("No AB1 files selected")
            self.ab1_files_label.setStyleSheet("color: gray; font-style: italic;")
            self.ab1_count_label.setText("0 files loaded")
        else:
            if len(self.current_ab1_files) <= 3:
                file_list = ", ".join(
                    os.path.basename(f) for f in self.current_ab1_files
                )
            else:
                file_list = ", ".join(
                    os.path.basename(f) for f in self.current_ab1_files[:3]
                )
                file_list += f" and {len(self.current_ab1_files) - 3} more"
            self.ab1_files_label.setText(file_list)
            self.ab1_files_label.setStyleSheet("")
            self.ab1_count_label.setText(f"{len(self.current_ab1_files)} files loaded")

    def _update_analysis_button(self):
        has_reference = self.current_reference is not None
        has_ab1_files = len(self.current_ab1_files) > 0
        self.btn_analyze.setEnabled(has_reference and has_ab1_files)

    def _run_analysis(self):
        if not self.current_reference or not self.current_ab1_files:
            QMessageBox.warning(
                self, "Warning", "Please load reference and AB1 files first."
            )
            return

        operator = self.operator_name_input.text().strip()
        if not operator:
            QMessageBox.warning(self, "Warning", "Please enter operator name.")
            return

        self.statusBar().showMessage("Running analysis...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(10)
        QApplication.processEvents()

        try:
            from src.ab1_parser import AB1Parser
            from src.alignment import GenBankParser, SequenceAligner
            from src.variant_caller import VariantCaller, ConstructVerifier
            from src.audit_db import AuditDatabase

            ref_data = GenBankParser.parse(self.current_reference)
            aligner = SequenceAligner()
            variant_caller = VariantCaller()
            verifier = ConstructVerifier()
            db = AuditDatabase()

            self.progress_bar.setValue(30)
            QApplication.processEvents()

            results = []
            for i, ab1_path in enumerate(self.current_ab1_files):
                progress = 30 + int((i + 1) / len(self.current_ab1_files) * 50)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()

                parser = AB1Parser(ab1_path)
                chromatogram, metadata = parser.parse()

                result = aligner.align(
                    chromatogram.sequence,
                    ref_data.sequence,
                    target_start=0,
                    target_end=min(
                        len(ref_data.sequence), len(chromatogram.sequence) + 100
                    ),
                )

                variant_result = variant_caller.run_analysis(
                    result.aligned_query,
                    result.aligned_target,
                    target_start=result.target_start,
                    ref_sequence=ref_data.sequence,
                    quality_scores=chromatogram.confidence_scores,
                )

                verification = verifier.verify(variant_result, result.coverage)

                results.append(
                    {
                        "file_path": ab1_path,
                        "metadata": metadata,
                        "chromatogram": chromatogram,
                        "alignment": result,
                        "variant_result": variant_result,
                        "verification": verification,
                    }
                )

            self.progress_bar.setValue(90)
            QApplication.processEvents()

            for r in results:
                db.log_analysis(
                    sample_name=r["metadata"].sample_name
                    or os.path.basename(r["file_path"]),
                    sample_id=self.sample_id_input.text().strip() or "N/A",
                    reference_name=ref_data.name,
                    reference_id=ref_data.id,
                    operator_name=operator,
                    overall_status=r["verification"]["status"],
                    coverage_percentage=r["verification"]["coverage"],
                    total_variants=r["variant_result"].total_variants,
                    critical_variants=r["verification"]["critical_variants"],
                    variants=[v.to_dict() for v in r["variant_result"].variants],
                    effects=[e.to_dict() for e in r["variant_result"].effects],
                )

            self.analysis_results = results
            self._update_results_table()

            self.btn_generate_report.setEnabled(True)

            self.progress_bar.setValue(100)
            self.statusBar().showMessage(
                f"Analysis complete. {len(results)} samples processed."
            )

        except Exception as e:
            self.statusBar().showMessage("Analysis failed")
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")

        finally:
            self.progress_bar.setVisible(False)

    def _update_results_table(self):
        self.results_table.setRowCount(0)

        for result in self.analysis_results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            sample_name = result["metadata"].sample_name or os.path.basename(
                result["file_path"]
            )
            status = result["verification"]["status"]
            coverage = result["verification"]["coverage"]
            total_variants = result["variant_result"].total_variants
            critical = result["verification"]["critical_variants"]

            variants_info = result["variant_result"].variants
            if variants_info:
                first_variant = variants_info[0]
                pos = first_variant.position
                ref = first_variant.ref_base
                alt = first_variant.alt_base
            else:
                pos = "-"
                ref = "-"
                alt = "-"

            self.results_table.setItem(row, 0, QTableWidgetItem(sample_name))

            status_item = QTableWidgetItem(status)
            if status == "PASS":
                status_item.setBackground(Qt.GlobalColor.lightGreen)
            else:
                status_item.setBackground(Qt.GlobalColor.lightCoral)
            self.results_table.setItem(row, 1, status_item)

            self.results_table.setItem(row, 2, QTableWidgetItem(f"{coverage:.1f}%"))
            self.results_table.setItem(row, 3, QTableWidgetItem(str(total_variants)))

            critical_item = QTableWidgetItem(str(critical))
            if critical > 0:
                critical_item.setBackground(Qt.GlobalColor.lightCoral)
            self.results_table.setItem(row, 4, critical_item)

            self.results_table.setItem(row, 5, QTableWidgetItem(str(pos)))
            self.results_table.setItem(row, 6, QTableWidgetItem(ref))
            self.results_table.setItem(row, 7, QTableWidgetItem(alt))

    def _generate_report(self):
        if not self.analysis_results:
            QMessageBox.warning(self, "Warning", "No analysis results to report.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "", "PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            try:
                from src.report_generator import ReportGenerator, ReportData
                import datetime

                generator = ReportGenerator()

                first_result = self.analysis_results[0]
                ref_data = (
                    first_result["alignment"].target_sequence
                    if hasattr(first_result["alignment"], "target_sequence")
                    else "Reference"
                )

                sample_name = first_result["metadata"].sample_name or "Sample"
                sample_id = self.sample_id_input.text().strip() or "N/A"

                now = datetime.datetime.now()

                all_variants = []
                all_effects = []
                all_failures = []
                all_warnings = []

                for result in self.analysis_results:
                    all_variants.extend(
                        [v.to_dict() for v in result["variant_result"].variants]
                    )
                    all_effects.extend(
                        [e.to_dict() for e in result["variant_result"].effects]
                    )
                    all_failures.extend(result["verification"].get("failures", []))
                    for effect in result["variant_result"].effects:
                        if effect.impact == "MODERATE":
                            all_warnings.append(
                                f"Position {effect.variant.position}: {effect.effect.value}"
                            )

                data = ReportData(
                    sample_name=sample_name,
                    sample_id=sample_id,
                    reference_name=ref_data[:50] if len(ref_data) > 50 else ref_data,
                    reference_id="Reference",
                    analysis_date=now.strftime("%Y-%m-%d"),
                    analysis_time=now.strftime("%H:%M:%S"),
                    operator_name=self.operator_name_input.text().strip(),
                    software_version="1.0.0",
                    overall_status="PASS"
                    if all(r["verification"]["passed"] for r in self.analysis_results)
                    else "FAIL",
                    coverage_percentage=sum(
                        r["verification"]["coverage"] for r in self.analysis_results
                    )
                    / len(self.analysis_results),
                    total_variants=sum(
                        r["variant_result"].total_variants
                        for r in self.analysis_results
                    ),
                    critical_variants=sum(
                        r["verification"]["critical_variants"]
                        for r in self.analysis_results
                    ),
                    variants=all_variants,
                    effects=all_effects,
                    failures=all_failures,
                    warnings=all_warnings,
                    sample_description=first_result["metadata"].sample_description
                    or "",
                    instrument_name=first_result["metadata"].instrument_name or "",
                    run_id=first_result["metadata"].run_id or "",
                )

                output_path = generator.generate_report(data, file_path)

                QMessageBox.information(
                    self, "Success", f"Report saved to: {output_path}"
                )
                self.statusBar().showMessage(f"Report saved to {output_path}")

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to generate report: {str(e)}"
                )

    def _view_history(self):
        QMessageBox.information(
            self, "Analysis History", "History view not implemented in this version."
        )

    def _export_audit_log(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Audit Log",
            "",
            "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)",
        )

        if file_path:
            try:
                from src.audit_db import AuditDatabase

                db = AuditDatabase()
                entries = db.export_audit_log()

                import json

                with open(file_path, "w") as f:
                    json.dump(entries, f, indent=2)

                QMessageBox.information(
                    self, "Success", f"Audit log exported to: {file_path}"
                )

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to export audit log: {str(e)}"
                )

    def _show_about(self):
        QMessageBox.about(
            self,
            "About NucleoQC",
            "<h3>NucleoQC v1.0.0</h3>"
            "<p>Biologics Quality Control Suite</p>"
            "<p>Open-source software for Sanger sequencing analysis "
            "and variant detection in biopharmaceutical manufacturing.</p>"
            "<p>© 2024 NucleoQC Contributors</p>",
        )

    def _show_documentation(self):
        QMessageBox.information(
            self, "Documentation", "Documentation not available in this version."
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
