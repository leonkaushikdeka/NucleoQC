import sqlite3
import json
import hashlib
import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import os


class AuditDatabaseError(Exception):
    """Base exception for audit database errors."""

    pass


class DatabaseNotFoundError(AuditDatabaseError):
    """Raised when database file doesn't exist."""

    pass


@dataclass
class AuditEntry:
    """Represents an audit trail entry."""

    id: Optional[int]
    sample_name: str
    sample_id: str
    reference_name: str
    reference_id: str
    operator_name: str
    analysis_timestamp: str
    overall_status: str
    coverage_percentage: float
    total_variants: int
    critical_variants: int
    variants_json: str
    effects_json: str
    report_path: Optional[str]
    data_hash: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditDatabase:
    """SQLite database for audit trail management."""

    def __init__(self, db_path: str = "nucleoqc_audit.db"):
        """Initialize the audit database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialize the database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_name TEXT NOT NULL,
                    sample_id TEXT NOT NULL,
                    reference_name TEXT NOT NULL,
                    reference_id TEXT NOT NULL,
                    operator_name TEXT NOT NULL,
                    analysis_timestamp TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    coverage_percentage REAL NOT NULL,
                    total_variants INTEGER NOT NULL,
                    critical_variants INTEGER NOT NULL,
                    variants_json TEXT,
                    effects_json TEXT,
                    report_path TEXT,
                    data_hash TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_imports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_entry_id INTEGER,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (audit_entry_id) REFERENCES audit_entries (id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sample_name 
                ON audit_entries(sample_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analysis_timestamp 
                ON audit_entries(analysis_timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_overall_status 
                ON audit_entries(overall_status)
            """)

    def log_analysis(
        self,
        sample_name: str,
        sample_id: str,
        reference_name: str,
        reference_id: str,
        operator_name: str,
        overall_status: str,
        coverage_percentage: float,
        total_variants: int,
        critical_variants: int,
        variants: List[Dict[str, Any]],
        effects: List[Dict[str, Any]],
        report_path: Optional[str] = None,
        notes: str = "",
    ) -> int:
        """Log an analysis result to the audit trail.

        Args:
            sample_name: Name of the sample
            sample_id: Unique identifier for the sample
            reference_name: Name of the reference sequence
            reference_id: Identifier for the reference
            operator_name: Name of the operator
            overall_status: PASS or FAIL
            coverage_percentage: Coverage achieved
            total_variants: Total variants found
            critical_variants: Critical variants count
            variants: List of variant dictionaries
            effects: List of effect analysis dictionaries
            report_path: Path to generated report
            notes: Additional notes

        Returns:
            ID of the created audit entry
        """
        variants_json = json.dumps(variants, default=str)
        effects_json = json.dumps(effects, default=str)

        data_content = f"{sample_name}{sample_id}{reference_name}{reference_id}{variants_json}{effects_json}"
        data_hash = hashlib.sha256(data_content.encode()).hexdigest()

        timestamp = datetime.datetime.now().isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO audit_entries (
                    sample_name, sample_id, reference_name, reference_id,
                    operator_name, analysis_timestamp, overall_status,
                    coverage_percentage, total_variants, critical_variants,
                    variants_json, effects_json, report_path, data_hash, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    sample_name,
                    sample_id,
                    reference_name,
                    reference_id,
                    operator_name,
                    timestamp,
                    overall_status,
                    coverage_percentage,
                    total_variants,
                    critical_variants,
                    variants_json,
                    effects_json,
                    report_path,
                    data_hash,
                    notes,
                ),
            )

            return cursor.lastrowid

    def log_file_import(
        self, audit_entry_id: int, file_path: str, file_type: str, file_hash: str
    ) -> int:
        """Log a file import to the audit trail.

        Args:
            audit_entry_id: ID of the associated audit entry
            file_path: Path to the imported file
            file_type: Type of file (ab1, genbank, etc.)
            file_hash: Hash of the file contents

        Returns:
            ID of the created file import entry
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO file_imports (
                    audit_entry_id, file_path, file_type, file_hash
                ) VALUES (?, ?, ?, ?)
            """,
                (audit_entry_id, file_path, file_type, file_hash),
            )

            return cursor.lastrowid

    def get_audit_entry(self, entry_id: int) -> Optional[AuditEntry]:
        """Retrieve an audit entry by ID.

        Args:
            entry_id: ID of the audit entry

        Returns:
            AuditEntry object or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM audit_entries WHERE id = ?", (entry_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            return AuditEntry(
                id=row["id"],
                sample_name=row["sample_name"],
                sample_id=row["sample_id"],
                reference_name=row["reference_name"],
                reference_id=row["reference_id"],
                operator_name=row["operator_name"],
                analysis_timestamp=row["analysis_timestamp"],
                overall_status=row["overall_status"],
                coverage_percentage=row["coverage_percentage"],
                total_variants=row["total_variants"],
                critical_variants=row["critical_variants"],
                variants_json=row["variants_json"],
                effects_json=row["effects_json"],
                report_path=row["report_path"],
                data_hash=row["data_hash"],
                notes=row["notes"],
            )

    def get_audit_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        status_filter: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> List[AuditEntry]:
        """Retrieve audit entries with optional filters.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            status_filter: Filter by status (PASS/FAIL)
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)

        Returns:
            List of AuditEntry objects
        """
        query = "SELECT * FROM audit_entries WHERE 1=1"
        params = []

        if status_filter:
            query += " AND overall_status = ?"
            params.append(status_filter)

        if start_date:
            query += " AND analysis_timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND analysis_timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY analysis_timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            entries = []
            for row in cursor.fetchall():
                entries.append(
                    AuditEntry(
                        id=row["id"],
                        sample_name=row["sample_name"],
                        sample_id=row["sample_id"],
                        reference_name=row["reference_name"],
                        reference_id=row["reference_id"],
                        operator_name=row["operator_name"],
                        analysis_timestamp=row["analysis_timestamp"],
                        overall_status=row["overall_status"],
                        coverage_percentage=row["coverage_percentage"],
                        total_variants=row["total_variants"],
                        critical_variants=row["critical_variants"],
                        variants_json=row["variants_json"],
                        effects_json=row["effects_json"],
                        report_path=row["report_path"],
                        data_hash=row["data_hash"],
                        notes=row["notes"],
                    )
                )

            return entries

    def search_audit_entries(
        self, search_term: str, limit: int = 50
    ) -> List[AuditEntry]:
        """Search audit entries by sample name or ID.

        Args:
            search_term: Term to search for
            limit: Maximum results

        Returns:
            List of matching AuditEntry objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM audit_entries 
                WHERE sample_name LIKE ? OR sample_id LIKE ?
                ORDER BY analysis_timestamp DESC
                LIMIT ?
            """,
                (f"%{search_term}%", f"%{search_term}%", limit),
            )

            entries = []
            for row in cursor.fetchall():
                entries.append(
                    AuditEntry(
                        id=row["id"],
                        sample_name=row["sample_name"],
                        sample_id=row["sample_id"],
                        reference_name=row["reference_name"],
                        reference_id=row["reference_id"],
                        operator_name=row["operator_name"],
                        analysis_timestamp=row["analysis_timestamp"],
                        overall_status=row["overall_status"],
                        coverage_percentage=row["coverage_percentage"],
                        total_variants=row["total_variants"],
                        critical_variants=row["critical_variants"],
                        variants_json=row["variants_json"],
                        effects_json=row["effects_json"],
                        report_path=row["report_path"],
                        data_hash=row["data_hash"],
                        notes=row["notes"],
                    )
                )

            return entries

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit trail statistics.

        Returns:
            Dictionary with statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM audit_entries")
            total_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM audit_entries WHERE overall_status = 'PASS'"
            )
            pass_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM audit_entries WHERE overall_status = 'FAIL'"
            )
            fail_count = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(coverage_percentage) FROM audit_entries")
            avg_coverage = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT DATE(analysis_timestamp) as date, COUNT(*) as count
                FROM audit_entries
                GROUP BY DATE(analysis_timestamp)
                ORDER BY date DESC
                LIMIT 7
            """)
            recent_activity = [
                {"date": row["date"], "count": row["count"]}
                for row in cursor.fetchall()
            ]

            return {
                "total_analyses": total_count,
                "passed": pass_count,
                "failed": fail_count,
                "pass_rate": (pass_count / total_count * 100) if total_count > 0 else 0,
                "average_coverage": avg_coverage,
                "recent_activity": recent_activity,
            }

    def verify_integrity(self, entry_id: int) -> Tuple[bool, str]:
        """Verify the integrity of an audit entry.

        Args:
            entry_id: ID of the audit entry

        Returns:
            Tuple of (is_valid, message)
        """
        entry = self.get_audit_entry(entry_id)
        if entry is None:
            return False, "Audit entry not found"

        data_content = f"{entry.sample_name}{entry.sample_id}{entry.reference_name}{entry.reference_id}{entry.variants_json}{entry.effects_json}"
        expected_hash = hashlib.sha256(data_content.encode()).hexdigest()

        if entry.data_hash == expected_hash:
            return True, "Data integrity verified"
        else:
            return False, "Data integrity check failed - entry may have been modified"

    def export_audit_log(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        """Export audit log entries for compliance reporting.

        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)

        Returns:
            List of audit entry dictionaries
        """
        query = "SELECT * FROM audit_entries WHERE 1=1"
        params = []

        if start_date:
            query += " AND analysis_timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND analysis_timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY analysis_timestamp ASC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            entries = []
            for row in cursor.fetchall():
                entry = {
                    "id": row["id"],
                    "sample_name": row["sample_name"],
                    "sample_id": row["sample_id"],
                    "reference_name": row["reference_name"],
                    "reference_id": row["reference_id"],
                    "operator_name": row["operator_name"],
                    "analysis_timestamp": row["analysis_timestamp"],
                    "overall_status": row["overall_status"],
                    "coverage_percentage": row["coverage_percentage"],
                    "total_variants": row["total_variants"],
                    "critical_variants": row["critical_variants"],
                    "variants": json.loads(row["variants_json"] or "[]"),
                    "effects": json.loads(row["effects_json"] or "[]"),
                    "report_path": row["report_path"],
                    "data_hash": row["data_hash"],
                    "notes": row["notes"],
                }
                entries.append(entry)

            return entries

    def delete_entry(self, entry_id: int) -> bool:
        """Delete an audit entry (for admin use only).

        Args:
            entry_id: ID of the entry to delete

        Returns:
            True if deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM file_imports WHERE audit_entry_id = ?", (entry_id,)
            )
            cursor.execute("DELETE FROM audit_entries WHERE id = ?", (entry_id,))

            return cursor.rowcount > 0
