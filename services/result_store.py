import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class ResultStore:
    """Service for persistently storing job results using SQLite."""

    def __init__(self, db_path: str | Path = "data/music_suite.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def close(self):
        """
        Close the result store. 
        As connections are context-managed, this serves as a clean termination hook.
        """
        pass
        
    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    source_type TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    result_files TEXT,
                    metadata TEXT
                )
            ''')
            conn.commit()

    def store_completed(self, job_id: str, title: str, source_type: str, result_files: List[str], metadata: Dict[str, Any] = None):
        """Store a successfully completed job."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO jobs 
                (id, title, source_type, status, created_at, completed_at, result_files, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id, title, source_type, "COMPLETED", 
                datetime.now().isoformat(), datetime.now().isoformat(),
                json.dumps(result_files), json.dumps(metadata or {})
            ))
            conn.commit()

    def store_failed(self, job_id: str, title: str, source_type: str, error_message: str, metadata: Dict[str, Any] = None):
        """Store a failed job."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO jobs 
                (id, title, source_type, status, created_at, completed_at, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id, title, source_type, "FAILED", 
                datetime.now().isoformat(), datetime.now().isoformat(),
                error_message, json.dumps(metadata or {})
            ))
            conn.commit()

    def retrieve_history(self) -> List[Dict[str, Any]]:
        """Retrieve all historical jobs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM jobs ORDER BY completed_at DESC')
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data['result_files'] = json.loads(data['result_files']) if data['result_files'] else []
                data['metadata'] = json.loads(data['metadata']) if data['metadata'] else {}
                results.append(data)
            return results

    def delete_record(self, job_id: str):
        """Delete a historical job record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
            conn.commit()

    def clear_all_records(self):
        """Delete all historical job records."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM jobs')
            conn.commit()

