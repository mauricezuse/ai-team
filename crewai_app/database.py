import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import time
import logging
from functools import wraps

# Database setup - MySQL Configuration
MYSQL_HOST = os.environ.get("MYSQL_HOST", "ai-team-mysql-f8eioxb8.mysql.database.azure.com")
MYSQL_USER = os.environ.get("MYSQL_USER", "ai_team_admin")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "AiTeam2024!SecureMySQL")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "ai_team")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")

# Use DATABASE_URL if available, otherwise construct from individual components
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?ssl_disabled=false&ssl_verify_cert=true&ssl_verify_identity=true"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,         # Connection pool size for MySQL
    max_overflow=20,      # Allow overflow connections
    pool_recycle=300,     # Recycle connections every 5 minutes
    pool_pre_ping=True,   # Verify connections before use
    echo=False,           # Disable SQL logging for performance
    pool_timeout=30,      # 30 second timeout for getting connection from pool
    connect_args={
        "charset": "utf8mb4",
        "autocommit": False,
        "ssl_disabled": False,
        "ssl_verify_cert": True,
        "ssl_verify_identity": True
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    jira_story_id = Column(String(255), unique=True, index=True)
    jira_story_title = Column(String(500))
    jira_story_description = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    repository_url = Column(String(500))
    target_branch = Column(String(100), default="main")
    
    # Enhanced status tracking fields
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    error = Column(Text)
    last_heartbeat_at = Column(DateTime)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="workflow", cascade="all, delete-orphan")
    code_files = relationship("CodeFile", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="workflow", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="workflow", cascade="all, delete-orphan")
    diffs = relationship("Diff", back_populates="workflow", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    step = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent = Column(String(100))
    status = Column(String(50), default="pending")
    details = Column(Text)
    output = Column(Text)
    prompt = Column(Text)
    
    # LLM call tracking
    llm_calls = Column(JSON, default=list)  # Store array of LLM call objects
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(String(20), default="0.00")
    
    # Relationships
    workflow = relationship("Workflow", back_populates="conversations")
    escalations = relationship("Escalation", back_populates="conversation", cascade="all, delete-orphan")
    collaborations = relationship("Collaboration", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class CodeFile(Base):
    __tablename__ = "code_files"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    filename = Column(String(255))
    file_path = Column(String(500))
    file_content = Column(Text)
    file_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="code_files")
    conversation = relationship("Conversation")

class Escalation(Base):
    __tablename__ = "escalations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    from_agent = Column(String(100))
    to_agent = Column(String(100))
    reason = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="escalations")

class Collaboration(Base):
    __tablename__ = "collaborations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    from_agent = Column(String(100))
    to_agent = Column(String(100))
    request_type = Column(String(100))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="collaborations")

class LLMCall(Base):
    __tablename__ = "llm_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    model = Column(String(100))  # e.g., "gpt-4", "gpt-3.5-turbo"
    # Token usage and limits
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    max_tokens = Column(Integer, default=0)
    total_tokens_requested = Column(Integer, default=0)
    # Latency and status
    response_time_ms = Column(Integer, default=0)
    status = Column(String(50), default="success")  # success|failed|truncated|skipped
    error_code = Column(String(50))
    # Truncation and governance
    truncated_sections = Column(JSON)  # list of truncated parts/quotas applied
    prompt_hash = Column(String(64))
    response_hash = Column(String(64))
    budget_snapshot = Column(JSON)  # {prompt_budget_remaining, step_budget_remaining}
    # Costing
    cost = Column(String(20), default="0.00")
    timestamp = Column(DateTime, default=datetime.utcnow)
    request_data = Column(JSON)  # Store the full request for debugging
    response_data = Column(JSON)  # Store the full response for debugging
    
    # Relationships
    conversation = relationship("Conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String(20))  # system|user|assistant|tool
    content = Column(Text)  # concise text (long blobs should be summarized/linked)
    artifacts = Column(JSON, default=list)  # array of {type,id,uri,checksum?}
    message_metadata = Column(JSON, default=dict)  # {agent_name, step_name, conversation_id, created_at}
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class Execution(Base):
    __tablename__ = "executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    status = Column(String(50), default="pending")  # pending|running|completed|failed
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    total_calls = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(String(20), default="0.00")
    avg_latency_ms = Column(Integer, default=0)
    models = Column(JSON, default=list)  # list of models used
    meta = Column(JSON, default=dict)  # prompt/config hashes, flags, etc.
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")

class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    pr_number = Column(Integer, index=True)
    url = Column(String(500))
    title = Column(String(255))
    state = Column(String(20))  # open|closed|merged
    head_branch = Column(String(100))
    base_branch = Column(String(100))
    head_sha = Column(String(40))
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    merged_at = Column(DateTime)

    # Relationships
    workflow = relationship("Workflow", back_populates="pull_requests")
    check_runs = relationship("CheckRun", back_populates="pull_request", cascade="all, delete-orphan")

class CheckRun(Base):
    __tablename__ = "check_runs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), index=True)
    name = Column(String(255))
    status = Column(String(20))  # queued|in_progress|completed
    conclusion = Column(String(30))  # success|failure|neutral|cancelled|timed_out|action_required|skipped
    external_id = Column(String(100))
    html_url = Column(String(500))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    pull_request = relationship("PullRequest", back_populates="check_runs")

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=True)
    kind = Column(String(50))  # test-report|trace|lint|coverage|other
    uri = Column(String(500))
    checksum = Column(String(64))
    size_bytes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="artifacts")

class Diff(Base):
    __tablename__ = "diffs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    path = Column(String(500))
    patch = Column(Text)  # unified diff
    head_sha = Column(String(40))
    base_sha = Column(String(40))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="diffs")

# Database functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database retry mechanism for handling lock errors
def with_db_retry(max_retries=3, delay=0.1):
    """Decorator to retry database operations on lock errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        logging.warning(f"Database lock error on attempt {attempt + 1}, retrying in {delay}s: {e}")
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
    Base.metadata.create_all(bind=engine)

def init_database():
    create_tables()
    # Add some sample data if needed
    db = SessionLocal()
    try:
        # Check if we have any workflows
        if db.query(Workflow).count() == 0:
            # Create sample workflows
            sample_workflows = [
                {
                    "name": "NEGISHI-178: Federation-aware agents",
                    "jira_story_id": "NEGISHI-178",
                    "jira_story_title": "Implement federation-aware agents that can collaborate across different environments",
                    "jira_story_description": "Create a system where AI agents can work together across different environments and share information securely.",
                    "status": "completed",
                    "repository_url": "https://github.com/mauricezuse/negishi-freelancing",
                    "target_branch": "main"
                },
                {
                    "name": "NEGISHI-175: Intelligent code modifications",
                    "jira_story_id": "NEGISHI-175", 
                    "jira_story_title": "Implement intelligent code modifications that can automatically improve code quality",
                    "jira_story_description": "Develop an AI-powered system that can analyze code and suggest or implement improvements automatically.",
                    "status": "completed",
                    "repository_url": "https://github.com/mauricezuse/negishi-freelancing",
                    "target_branch": "main"
                }
            ]
            
            for workflow_data in sample_workflows:
                workflow = Workflow(**workflow_data)
                db.add(workflow)
            
            db.commit()
    finally:
        db.close()
