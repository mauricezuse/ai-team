#!/usr/bin/env python3
"""
Migration script to add LLM call tracking columns to the database
"""
import sqlite3
import json

def migrate_database():
    """Add LLM call tracking columns to existing database"""
    
    # Connect to the database
    conn = sqlite3.connect('ai_team.db')
    cursor = conn.cursor()
    
    try:
        # Add new columns to conversations table
        print("Adding LLM call tracking columns to conversations table...")
        
        # Add llm_calls column (JSON)
        cursor.execute("ALTER TABLE conversations ADD COLUMN llm_calls TEXT DEFAULT '[]'")
        print("Added llm_calls column")
        
        # Add total_tokens_used column
        cursor.execute("ALTER TABLE conversations ADD COLUMN total_tokens_used INTEGER DEFAULT 0")
        print("Added total_tokens_used column")
        
        # Add total_cost column
        cursor.execute("ALTER TABLE conversations ADD COLUMN total_cost TEXT DEFAULT '0.00'")
        print("Added total_cost column")
        
        # Create llm_calls table
        print("Creating llm_calls table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                model TEXT,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost TEXT DEFAULT '0.00',
                response_time_ms INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                request_data TEXT,
                response_data TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """)
        print("Created llm_calls table")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Columns already exist, skipping...")
        else:
            print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
