#!/usr/bin/env python3
"""
NucleoQC - Biologics Quality Control Suite

An open-source desktop application for Sanger sequencing analysis
and variant detection in biopharmaceutical manufacturing.
"""

import sys
import os


def main():
    """Main entry point for NucleoQC application."""
    from gui.main_window import MainWindow
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("NucleoQC")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
