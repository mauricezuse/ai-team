from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./ai_team.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    jira_story_id = Column(String, unique=True, index=True)
    jira_story_title = Column(String)
    jira_story_description = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    repository_url = Column(String)
    target_branch = Column(String, default="main")
    
    # Relationships
    conversations = relationship("Conversation", back_populates="workflow", cascade="all, delete-orphan")
    code_files = relationship("CodeFile", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    step = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent = Column(String)
    status = Column(String, default="pending")
    details = Column(Text)
    output = Column(Text)
    prompt = Column(Text)
    
    # LLM call tracking
    llm_calls = Column(JSON, default=list)  # Store array of LLM call objects
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(String, default="0.00")
    
    # Relationships
    workflow = relationship("Workflow", back_populates="conversations")
    escalations = relationship("Escalation", back_populates="conversation", cascade="all, delete-orphan")
    collaborations = relationship("Collaboration", back_populates="conversation", cascade="all, delete-orphan")

class CodeFile(Base):
    __tablename__ = "code_files"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    filename = Column(String)
    file_path = Column(String)
    file_content = Column(Text)
    file_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="code_files")
    conversation = relationship("Conversation")

class Escalation(Base):
    __tablename__ = "escalations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    from_agent = Column(String)
    to_agent = Column(String)
    reason = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="escalations")

class Collaboration(Base):
    __tablename__ = "collaborations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    from_agent = Column(String)
    to_agent = Column(String)
    request_type = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="collaborations")

class LLMCall(Base):
    __tablename__ = "llm_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    model = Column(String)  # e.g., "gpt-4", "gpt-3.5-turbo"
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(String, default="0.00")
    response_time_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    request_data = Column(JSON)  # Store the full request for debugging
    response_data = Column(JSON)  # Store the full response for debugging
    
    # Relationships
    conversation = relationship("Conversation")

class Execution(Base):
    __tablename__ = "executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    status = Column(String, default="pending")  # pending|running|completed|failed
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    total_calls = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(String, default="0.00")
    avg_latency_ms = Column(Integer, default=0)
    models = Column(JSON, default=list)  # list of models used
    meta = Column(JSON, default=dict)  # prompt/config hashes, flags, etc.
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")

# Database functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
