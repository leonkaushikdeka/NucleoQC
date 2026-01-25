import struct
import os
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict, Any
from enum import IntEnum


class AB1Error(Exception):
    """Base exception for AB1 parsing errors."""

    pass


class InvalidAB1FileError(AB1Error):
    """Raised when file is not a valid AB1 file."""

    pass


class UnsupportedVersionError(AB1Error):
    """Raised when AB1 version is not supported."""

    pass


class DataItemTag(IntEnum):
    """AB1 data item tags."""

    RAW_DATA = 1
    WAVELENGTH_INFO = 2
    PROCESSING_INFO = 3
    SAMPLE_NAME = 4
    SAMPLE_DESCRIPTION = 5
    MACHINE_NAME = 6
    USER_NAME = 7
    RUN_START_TIME = 8
    RUN_END_TIME = 9
    INSTRUMENT_NAME = 10
    INSTRUMENT_TYPE = 11
    INSTRUMENT_SERIAL = 12
    RUN_NAME = 13
    RUN_ID = 14
    PROVENANCE = 15
    ANALYSIS = 16
    COLORMODEL = 17
    DYE_PRIMER_FILE = 18
    DYE_SET_NAME = 19
    MISMATCH_Info = 20
    BASE_CALLING = 21
    CAP_NUM_OF_LAMBDAS = 22
    SCAN_RANGE = 23
    DATA_OFFSET = 24
    DATA_LENGTH = 25
    NUM_ELEMENTS = 26
    FIRST_PEAK_LOCATION = 27
    MAX_PEAK_LOCATION = 28
    MIN_PEAK_LOCATION = 29
    NUM_BASE_CALLS = 30
    BASECALL_1 = 31
    BASECALL_2_NT = 32
    BASECALL_2 = 33
    PROBABLE_SEQUENCE = 34
    QUALITY_VALUES = 35
    SPACING = 36
    PROFILE_TYPE = 37
    COMMENT = 38
    CHANNEL_COUNT = 39
    WELL_NAME = 40


@dataclass
class ChromatogramData:
    """Container for parsed chromatogram data."""

    sequence: str
    confidence_scores: List[int]
    positions_a: List[float]
    positions_t: List[float]
    positions_c: List[float]
    positions_g: List[float]
    peak_positions: List[int]

    def get_coverage(self) -> int:
        """Return the number of bases called."""
        return len(self.sequence)

    def get_average_quality(self) -> float:
        """Return average Phred quality score."""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)


@dataclass
class AB1Metadata:
    """Container for AB1 file metadata."""

    sample_name: str
    sample_description: str
    machine_name: str
    user_name: str
    run_start_time: Optional[str]
    run_end_time: Optional[str]
    instrument_name: str
    instrument_type: str
    instrument_serial: str
    run_name: str
    run_id: str
    dye_set_name: str
    well_name: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "sample_name": self.sample_name,
            "sample_description": self.sample_description,
            "machine_name": self.machine_name,
            "user_name": self.user_name,
            "run_start_time": self.run_start_time,
            "run_end_time": self.run_end_time,
            "instrument_name": self.instrument_name,
            "instrument_type": self.instrument_type,
            "instrument_serial": self.instrument_serial,
            "run_name": self.run_name,
            "run_id": self.run_id,
            "dye_set_name": self.dye_set_name,
            "well_name": self.well_name,
        }


class AB1Parser:
    """Parser for AB1 (Sanger sequencing) binary files."""

    MAGIC = b"ABIF"
    SUPPORTED_VERSIONS = [(1, 0), (1, 1)]

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._file_size = 0
        self._version = (0, 0)
        self._directory_offset = 0
        self._directory_entry_count = 0
        self._data_items: Dict[int, Tuple[int, int, Any]] = {}
        self._parsed = False

    def parse(self) -> Tuple[ChromatogramData, AB1Metadata]:
        """Parse the AB1 file and return chromatogram data and metadata.

        Returns:
            Tuple of (ChromatogramData, AB1Metadata)

        Raises:
            AB1Error: If parsing fails
        """
        if not os.path.exists(self.file_path):
            raise AB1Error(f"File not found: {self.file_path}")

        self._file_size = os.path.getsize(self.file_path)

        with open(self.file_path, "rb") as f:
            self._parse_header(f)
            self._parse_directory(f)
            chromatogram = self._extract_chromatogram_data()
            metadata = self._extract_metadata()

        self._parsed = True
        return chromatogram, metadata

    def _parse_header(self, f) -> None:
        """Parse the AB1 file header."""
        magic = f.read(4)
        if magic != self.MAGIC:
            raise InvalidAB1FileError(
                f"Invalid magic number. Expected {self.MAGIC!r}, got {magic!r}"
            )

        self._version = struct.unpack(">HH", f.read(4))
        if self._version not in self.SUPPORTED_VERSIONS:
            raise UnsupportedVersionError(
                f"Unsupported AB1 version: {self._version}. "
                f"Supported versions: {self.SUPPORTED_VERSIONS}"
            )

        self._directory_offset = struct.unpack(">I", f.read(4))[0]
        self._directory_entry_count = struct.unpack(">H", f.read(2))[0]
        f.read(2)

    def _parse_directory(self, f) -> None:
        """Parse the AB1 directory structure."""
        f.seek(self._directory_offset)

        for _ in range(self._directory_entry_count):
            tag = struct.unpack(">H", f.read(2))[0]
            element_type = struct.unpack(">H", f.read(2))[0]
            element_count = struct.unpack(">I", f.read(4))[0]
            data_size = struct.unpack(">I", f.read(4))[0]
            data_offset = struct.unpack(">I", f.read(4))[0]
            f.read(4)

            if data_size <= 4:
                data = f.read(data_size)
                self._data_items[tag] = (element_type, element_count, data)
            else:
                self._data_items[tag] = (element_type, element_count, data_offset)

    def _get_string_data(self, tag: DataItemTag) -> str:
        """Extract string data from a directory entry."""
        if tag not in self._data_items:
            return ""

        element_type, element_count, data = self._data_items[tag]

        if isinstance(data, int):
            with open(self.file_path, "rb") as f:
                f.seek(data)
                raw_data = f.read(element_count)
        else:
            raw_data = data

        return raw_data.rstrip(b"\x00").decode("utf-8", errors="replace")

    def _get_int_data(self, tag: DataItemTag) -> int:
        """Extract integer data from a directory entry."""
        if tag not in self._data_items:
            return 0

        element_type, element_count, data = self._data_items[tag]

        if isinstance(data, int):
            with open(self.file_path, "rb") as f:
                f.seek(data)
                raw_data = f.read(element_count)
        else:
            raw_data = data

        if len(raw_data) >= 4:
            return struct.unpack(">I", raw_data[:4])[0]
        return 0

    def _get_float_array(self, tag: DataItemTag) -> List[float]:
        """Extract float array from a directory entry."""
        if tag not in self._data_items:
            return []

        element_type, element_count, data = self._data_items[tag]

        if isinstance(data, int):
            with open(self.file_path, "rb") as f:
                f.seek(data)
                raw_data = f.read(element_count * 4)
        else:
            raw_data = data

        return [
            struct.unpack(">f", raw_data[i : i + 4])[0]
            for i in range(0, len(raw_data), 4)
        ]

    def _extract_chromatogram_data(self) -> ChromatogramData:
        """Extract chromatogram data from the AB1 file."""
        base_calls_tag = DataItemTag.BASECALL_1
        quality_tag = DataItemTag.QUALITY_VALUES

        base_calls = self._get_string_data(base_calls_tag)

        num_bases = len(base_calls)
        if num_bases == 0:
            return ChromatogramData(
                sequence="",
                confidence_scores=[],
                positions_a=[],
                positions_t=[],
                positions_c=[],
                positions_g=[],
                peak_positions=[],
            )

        raw_data_tag = DataItemTag.RAW_DATA
        if raw_data_tag not in self._data_items:
            return ChromatogramData(
                sequence=base_calls,
                confidence_scores=[0] * num_bases,
                positions_a=[],
                positions_t=[],
                positions_c=[],
                positions_g=[],
                peak_positions=list(range(num_bases)),
            )

        element_type, element_count, data_offset = self._data_items[raw_data_tag]

        with open(self.file_path, "rb") as f:
            f.seek(data_offset)
            raw_data = f.read(element_count * 4)

        num_channels = 4
        samples_per_channel = element_count // num_channels
        trace_data = [
            struct.unpack(">f", raw_data[i : i + 4])[0]
            for i in range(0, len(raw_data), 4)
        ]

        positions_a = trace_data[0:samples_per_channel]
        positions_t = trace_data[samples_per_channel : 2 * samples_per_channel]
        positions_c = trace_data[2 * samples_per_channel : 3 * samples_per_channel]
        positions_g = trace_data[3 * samples_per_channel : 4 * samples_per_channel]

        num_calls = self._get_int_data(DataItemTag.NUM_BASE_CALLS)
        peak_positions = list(range(num_calls))

        quality_data = self._get_float_array(quality_tag)
        confidence_scores = (
            [int(q * 255) for q in quality_data[:num_bases]]
            if quality_data
            else [0] * num_bases
        )

        return ChromatogramData(
            sequence=base_calls,
            confidence_scores=confidence_scores,
            positions_a=positions_a,
            positions_t=positions_t,
            positions_c=positions_c,
            positions_g=positions_g,
            peak_positions=peak_positions,
        )

    def _extract_metadata(self) -> AB1Metadata:
        """Extract metadata from the AB1 file."""
        return AB1Metadata(
            sample_name=self._get_string_data(DataItemTag.SAMPLE_NAME),
            sample_description=self._get_string_data(DataItemTag.SAMPLE_DESCRIPTION),
            machine_name=self._get_string_data(DataItemTag.MACHINE_NAME),
            user_name=self._get_string_data(DataItemTag.USER_NAME),
            run_start_time=self._get_string_data(DataItemTag.RUN_START_TIME),
            run_end_time=self._get_string_data(DataItemTag.RUN_END_TIME),
            instrument_name=self._get_string_data(DataItemTag.INSTRUMENT_NAME),
            instrument_type=self._get_string_data(DataItemTag.INSTRUMENT_TYPE),
            instrument_serial=self._get_string_data(DataItemTag.INSTRUMENT_SERIAL),
            run_name=self._get_string_data(DataItemTag.RUN_NAME),
            run_id=self._get_string_data(DataItemTag.RUN_ID),
            dye_set_name=self._get_string_data(DataItemTag.DYE_SET_NAME),
            well_name=self._get_string_data(DataItemTag.WELL_NAME),
        )

    @property
    def is_parsed(self) -> bool:
        """Check if the file has been parsed."""
        return self._parsed

    def get_raw_trace_data(self) -> Dict[str, List[float]]:
        """Get raw trace data for visualization."""
        chromatogram, _ = self.parse()
        return {
            "A": chromatogram.positions_a,
            "T": chromatogram.positions_t,
            "C": chromatogram.positions_c,
            "G": chromatogram.positions_g,
        }
