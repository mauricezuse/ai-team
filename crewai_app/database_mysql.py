"""
MySQL Database Configuration for AI Team
Optimized for Azure Database for MySQL with proper connection pooling
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import time
import logging
from functools import wraps
import os

# Database setup for MySQL
def get_database_url():
    """Get database URL from environment variables"""
    # Check for explicit MySQL configuration
    if all([
        os.getenv('MYSQL_HOST'),
        os.getenv('MYSQL_USERNAME'),
        os.getenv('MYSQL_PASSWORD'),
        os.getenv('MYSQL_DATABASE')
    ]):
        host = os.getenv('MYSQL_HOST')
        port = os.getenv('MYSQL_PORT', '3306')
        username = os.getenv('MYSQL_USERNAME')
        password = os.getenv('MYSQL_PASSWORD')
        database = os.getenv('MYSQL_DATABASE')
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    
    # Fallback to DATABASE_URL
    return os.getenv('DATABASE_URL', 'sqlite:///./ai_team.db')

SQLALCHEMY_DATABASE_URL = get_database_url()

# Determine if we're using MySQL or SQLite
IS_MYSQL = 'mysql' in SQLALCHEMY_DATABASE_URL.lower()

if IS_MYSQL:
    # MySQL configuration with proper connection pooling
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,           # Verify connections before use
        pool_recycle=3600,            # Recycle connections every hour
        pool_size=10,                 # 10 connections in the pool
        max_overflow=20,              # Allow 20 overflow connections
        pool_timeout=30,              # 30 second timeout for getting connection
        pool_reset_on_return='commit', # Reset connection state on return
        echo=False,                   # Disable SQL logging for performance
        connect_args={
            'charset': 'utf8mb4',
            'autocommit': False,
            'sql_mode': 'TRADITIONAL'
        }
    )
else:
    # SQLite configuration (fallback)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 60,
            "isolation_level": None,
        },
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=1,
        max_overflow=0,
        echo=False,
        pool_timeout=30,
        pool_reset_on_return='commit'
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models (same as before, but optimized for MySQL)
class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    jira_story_id = Column(String, index=True)
    jira_story_title = Column(Text)
    jira_story_description = Column(Text)
    status = Column(String, default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    repository_url = Column(String)
    target_branch = Column(String, default="main")
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    error = Column(Text)
    last_heartbeat_at = Column(DateTime)
    heartbeat_stale = Column(Boolean, default=False)

    # Relationships
    conversations = relationship("Conversation", back_populates="workflow", cascade="all, delete-orphan")
    code_files = relationship("CodeFile", back_populates="workflow", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="workflow", cascade="all, delete-orphan")
    collaborations = relationship("Collaboration", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="workflow", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="workflow", cascade="all, delete-orphan")
    diffs = relationship("Diff", back_populates="workflow", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    step = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    agent = Column(String, index=True)
    status = Column(String, default="running", index=True)
    details = Column(Text)
    output = Column(Text)
    prompt = Column(Text)
    llm_calls = Column(JSON, default=list)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(String, default="0.00")

    # Relationships
    workflow = relationship("Workflow", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    llm_calls_rel = relationship("LLMCall", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String, index=True)  # system, user, assistant, tool
    content = Column(Text)  # concise text, large blobs summarized
    artifacts = Column(JSON, default=list)  # array of {type, id, uri, checksum?}
    message_metadata = Column(JSON, default=dict)  # {agent_name, step_name, conversation_id, created_at}
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    conversation = relationship("Conversation", back_populates="messages")

class LLMCall(Base):
    __tablename__ = "llm_calls"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    model = Column(String, index=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(String, default="0.00")
    response_time_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Enhanced fields for governance
    max_tokens = Column(Integer, default=0)
    total_tokens_requested = Column(Integer, default=0)
    status = Column(String, default="success", index=True)  # success, failed, truncated, skipped
    error_code = Column(String)
    truncated_sections = Column(JSON, default=list)  # e.g., ["early_turns", "code_output"]
    prompt_hash = Column(String, index=True)  # sha256 of prompt
    response_hash = Column(String, index=True)  # sha256 of response
    budget_snapshot = Column(JSON, default=dict)  # {prompt_budget_remaining, step_budget_remaining}

    conversation = relationship("Conversation", back_populates="llm_calls_rel")

class CodeFile(Base):
    __tablename__ = "code_files"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    file_path = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="code_files")

class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    agent = Column(String, index=True)
    reason = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False, index=True)

    workflow = relationship("Workflow", back_populates="escalations")

class Collaboration(Base):
    __tablename__ = "collaborations"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    requester = Column(String, index=True)
    target_agent = Column(String, index=True)
    request = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String, default="pending", index=True)

    workflow = relationship("Workflow", back_populates="collaborations")

class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    status = Column(String, default="running", index=True)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    finished_at = Column(DateTime)
    error = Column(Text)

    workflow = relationship("Workflow", back_populates="executions")

class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), index=True)
    number = Column(Integer, index=True)
    title = Column(String)
    body = Column(Text)
    state = Column(String, index=True)
    head_sha = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    closed_at = Column(DateTime)
    merged_at = Column(DateTime)

    workflow = relationship("Workflow", back_populates="pull_requests")
    check_runs = relationship("CheckRun", back_populates="pull_request", cascade="all, delete-orphan")

class CheckRun(Base):
    __tablename__ = "check_runs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), index=True)
    name = Column(String, index=True)
    status = Column(String, index=True)  # queued|in_progress|completed
    conclusion = Column(String, index=True)  # success|failure|neutral|cancelled|timed_out|action_required|skipped
    external_id = Column(String, index=True)
    html_url = Column(String)
    started_at = Column(DateTime, index=True)
    completed_at = Column(DateTime, index=True)

    pull_request = relationship("PullRequest", back_populates="check_runs")

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=True)
    kind = Column(String, index=True)  # test-report|trace|lint|coverage|other
    uri = Column(String, index=True)
    checksum = Column(String, index=True)
    size_bytes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    workflow = relationship("Workflow", back_populates="artifacts")

class Diff(Base):
    __tablename__ = "diffs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    path = Column(String, index=True)
    patch = Column(Text)
    head_sha = Column(String, index=True)
    base_sha = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    workflow = relationship("Workflow", back_populates="diffs")

# Database functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database retry mechanism for handling connection issues
def with_db_retry(max_retries=3, delay=0.1):
    """Decorator to retry database operations on connection errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if any(error in str(e).lower() for error in [
                        "connection", "timeout", "locked", "deadlock"
                    ]) and attempt < max_retries - 1:
                        logging.warning(f"Database error on attempt {attempt + 1}, retrying in {delay}s: {e}")
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        raise
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Safe database session context manager
class SafeDBSession:
    """Context manager for database sessions with retry logic"""
    
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            try:
                if exc_type:
                    self.db.rollback()
                else:
                    self.db.commit()
            except Exception as e:
                logging.error(f"Error in database session cleanup: {e}")
                self.db.rollback()
            finally:
                self.db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def init_database():
    """Initialize the database with tables"""
    create_tables()
    print(f"✅ Database initialized: {SQLALCHEMY_DATABASE_URL.split('@')[0]}@...")

# Print database configuration on import
if __name__ == "__main__":
    print(f"Database URL: {SQLALCHEMY_DATABASE_URL}")
    print(f"Using MySQL: {IS_MYSQL}")
    print(f"Engine: {engine}")
else:
    # Log database configuration
    logging.info(f"Database configured: {'MySQL' if IS_MYSQL else 'SQLite'}")
    logging.info(f"Connection pool size: {engine.pool.size() if hasattr(engine.pool, 'size') else 'N/A'}")
