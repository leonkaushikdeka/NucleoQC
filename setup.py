from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nucleoqc",
    version="1.0.0",
    author="NucleoQC Contributors",
    description="Open-Source Biologics Quality Control Suite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nucleoqc/nucleoqc",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=[
        "biopython>=1.81",
        "matplotlib>=3.7.0",
        "reportlab>=4.0.0",
        "PyQt6>=6.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nucleoqc=nucleoqc:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Desktop Environment :: GUI",
    ],
    keywords="bioinformatics, sequencing, quality-control, sanger, ab1, genetics",
    project_urls={
        "Bug Reports": "https://github.com/nucleoqc/nucleoqc/issues",
        "Source": "https://github.com/nucleoqc/nucleoqc",
        "Documentation": "https://nucleoqc.readthedocs.io/",
    },
)
