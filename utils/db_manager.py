import sqlite3
import os
import json
from datetime import datetime
import pandas as pd

class DatabaseManager:
    """
    Manages SQLite database for Market Rover.
    Handles persistence for user profiles and portfolios.
    """
    def __init__(self, db_path="data/market_rover.db"):
        self.db_path = db_path
        self._ensure_data_dir()
        self._init_db()

    def _ensure_data_dir(self):
        dirname = os.path.dirname(self.db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # User Profiles Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    username TEXT PRIMARY KEY,
                    persona TEXT,
                    scores TEXT,  -- JSON string
                    brands TEXT,  -- JSON string
                    last_updated TIMESTAMP
                )
            """)
            
            # Portfolios Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    portfolio_name TEXT,
                    data TEXT,  -- JSON string of portfolio records
                    last_updated TIMESTAMP,
                    UNIQUE(username, portfolio_name)
                )
            """)
            conn.commit()

    # --- User Profile Operations ---

    def save_user_profile(self, username, persona, scores, brands=None):
        """Saves or updates a user profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_profiles (username, persona, scores, brands, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    persona=excluded.persona,
                    scores=excluded.scores,
                    brands=excluded.brands,
                    last_updated=excluded.last_updated
            """, (
                username, 
                persona, 
                json.dumps(scores), 
                json.dumps(brands) if brands else None, 
                datetime.now().isoformat()
            ))
            conn.commit()

    def get_user_profile(self, username):
        """Retrieves a user profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return {
                    "username": row[0],
                    "persona": row[1],
                    "scores": json.loads(row[2]) if row[2] else {},
                    "brands": json.loads(row[3]) if row[3] else [],
                    "last_updated": row[4]
                }
            return None

    # --- Portfolio Operations ---

    def save_portfolio(self, username, portfolio_name, df_records):
        """Saves or updates a portfolio."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO portfolios (username, portfolio_name, data, last_updated)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(username, portfolio_name) DO UPDATE SET
                    data=excluded.data,
                    last_updated=excluded.last_updated
            """, (
                username, 
                portfolio_name, 
                json.dumps(df_records), 
                datetime.now().isoformat()
            ))
            conn.commit()

    def get_portfolio(self, username, portfolio_name):
        """Retrieves a portfolio as records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data FROM portfolios 
                WHERE username = ? AND portfolio_name = ?
            """, (username, portfolio_name))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def get_portfolio_names(self, username):
        """Returns a list of portfolio names for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT portfolio_name FROM portfolios WHERE username = ?", (username,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def delete_portfolio(self, username, portfolio_name):
        """Deletes a portfolio."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM portfolios 
                WHERE username = ? AND portfolio_name = ?
            """, (username, portfolio_name))
            conn.commit()
            return cursor.rowcount > 0
