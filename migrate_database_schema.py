#!/usr/bin/env python3
"""
Database migration script to add missing columns to llm_calls table.
Run this when the server is stopped to avoid database lock issues.
"""

import sqlite3
import os

def migrate_database():
    """Add missing columns to llm_calls table"""
    db_path = 'ai_team.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current columns
        cursor.execute("PRAGMA table_info(llm_calls)")
        columns = [row[1] for row in cursor.fetchall()]
        print('Current columns:', columns)
        
        # Add missing columns if they don't exist
        missing_columns = [
            ('max_tokens', 'INTEGER DEFAULT 0'),
            ('total_tokens_requested', 'INTEGER DEFAULT 0'),
            ('status', 'VARCHAR DEFAULT "success"'),
            ('error_code', 'VARCHAR'),
            ('truncated_sections', 'JSON DEFAULT "[]"'),
            ('prompt_hash', 'VARCHAR'),
            ('response_hash', 'VARCHAR'),
            ('budget_snapshot', 'JSON DEFAULT "{}"')
        ]
        
        for column_name, column_type in missing_columns:
            if column_name not in columns:
                print(f'Adding column: {column_name}')
                cursor.execute(f'ALTER TABLE llm_calls ADD COLUMN {column_name} {column_type}')
            else:
                print(f'Column {column_name} already exists')
        
        conn.commit()
        print('Database migration completed successfully')
        
    except Exception as e:
        print(f'Error during migration: {e}')
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
