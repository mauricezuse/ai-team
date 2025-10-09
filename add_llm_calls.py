#!/usr/bin/env python3
"""
Script to add sample LLM call data to existing conversations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crewai_app.database import get_db, Conversation, LLMCall
from datetime import datetime
import json

def add_sample_llm_calls():
    """Add sample LLM call data to existing conversations"""
    
    # Get database session
    db = next(get_db())
    
    # Get workflow 12 (NEGISHI-165)
    conversations = db.query(Conversation).filter(Conversation.workflow_id == 12).all()
    
    print(f"Found {len(conversations)} conversations to update")
    
    # Sample LLM call data for different agents (using actual database agent names)
    sample_llm_calls = {
        'pm': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 150,
                'completion_tokens': 200,
                'total_tokens': 350,
                'cost': '0.0105',
                'response_time_ms': 1200,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a Product Manager analyzing user stories...'},
                        {'role': 'user', 'content': 'Analyze the NEGISHI-165 story requirements...'}
                    ]
                },
                'response_data': {
                    'content': '''## Story Analysis: NEGISHI-165 - Job Offer Viewing and Acceptance

### Requirements Breakdown:

**Primary Requirements:**
1. **Job Offer Visibility**: Freelancers must be able to view available job offers in their dashboard
2. **Job Offer Details**: Display comprehensive job information including:
   - Job title and description
   - Client information and rating
   - Budget range and payment terms
   - Project timeline and deadlines
   - Required skills and experience level
3. **Acceptance Workflow**: Enable freelancers to accept job offers with one-click functionality
4. **Communication Integration**: Direct link to communication system for client interaction

**Stakeholders Identified:**
- **Primary Users**: Freelancers seeking job opportunities
- **Secondary Users**: Clients posting job offers
- **System Administrators**: Managing job offer lifecycle
- **Support Team**: Handling acceptance issues and disputes

**User Stories Created:**

**As a Freelancer, I want to:**
- View all available job offers in my dashboard
- Filter job offers by skills, budget, and location
- See detailed job information before accepting
- Accept job offers with a single click
- Access communication tools directly from job offers
- Track my application and acceptance history

**As a Client, I want to:**
- Post job offers that are visible to qualified freelancers
- Receive notifications when freelancers accept my offers
- Communicate directly with accepted freelancers
- Manage the hiring process through the platform

**Technical Requirements:**
- Real-time job offer updates
- Secure payment integration
- Mobile-responsive design
- Notification system for new offers
- Integration with existing communication platform

**Success Metrics:**
- Time from job posting to acceptance
- Freelancer engagement with job offers
- Client satisfaction with hiring process
- Platform revenue from successful matches''',
                    'usage': {'prompt_tokens': 150, 'completion_tokens': 200, 'total_tokens': 350}
                }
            }
        ],
        'architect': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 200,
                'completion_tokens': 300,
                'total_tokens': 500,
                'cost': '0.0150',
                'response_time_ms': 1800,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a Solution Architect designing system architecture...'},
                        {'role': 'user', 'content': 'Create a comprehensive implementation plan...'}
                    ]
                },
                'response_data': {
                    'content': '''## Implementation Plan: Job Offer System Architecture

### System Architecture Overview:

**Frontend Components:**
1. **JobOfferDashboard**: Main component for displaying job offers
2. **JobOfferCard**: Individual job offer display with accept button
3. **JobOfferFilters**: Filtering by skills, budget, location
4. **CommunicationLink**: Direct integration with messaging system

**Backend Services:**
1. **JobOfferService**: CRUD operations for job offers
2. **AcceptanceService**: Handle job offer acceptance workflow
3. **NotificationService**: Send alerts for new offers and acceptances
4. **CommunicationService**: Integration with messaging platform

**Database Schema:**
```sql
-- Job Offers Table
CREATE TABLE job_offers (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    budget_min DECIMAL(10,2),
    budget_max DECIMAL(10,2),
    required_skills TEXT[],
    deadline TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Job Acceptances Table
CREATE TABLE job_acceptances (
    id UUID PRIMARY KEY,
    job_offer_id UUID REFERENCES job_offers(id),
    freelancer_id UUID REFERENCES users(id),
    accepted_at TIMESTAMP DEFAULT NOW(),
    communication_thread_id UUID
);
```

**API Endpoints:**
- `GET /api/job-offers` - List available job offers
- `GET /api/job-offers/{id}` - Get specific job offer details
- `POST /api/job-offers/{id}/accept` - Accept a job offer
- `GET /api/job-offers/my-accepted` - Get freelancer's accepted offers

**Integration Points:**
- **Payment System**: Stripe integration for secure transactions
- **Communication Platform**: Direct messaging integration
- **Notification System**: Real-time alerts via WebSocket
- **User Management**: Integration with existing user profiles

**Security Considerations:**
- JWT authentication for all endpoints
- Rate limiting on acceptance endpoints
- Input validation and sanitization
- Audit logging for all job offer actions

**Performance Optimizations:**
- Redis caching for frequently accessed job offers
- Database indexing on client_id, status, and created_at
- Pagination for large job offer lists
- CDN for job offer images and documents''',
                    'usage': {'prompt_tokens': 200, 'completion_tokens': 300, 'total_tokens': 500}
                }
            }
        ],
        'developer': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 180,
                'completion_tokens': 250,
                'total_tokens': 430,
                'cost': '0.0129',
                'response_time_ms': 1500,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a Backend Developer implementing APIs...'},
                        {'role': 'user', 'content': 'Implement the backend functionality for job offers...'}
                    ]
                },
                'response_data': {
                    'content': '''## Backend Implementation: Job Offer API Endpoints

### Implemented API Endpoints:

**1. Job Offer Listing Endpoint:**
```python
@app.get("/api/job-offers")
async def get_job_offers(
    skip: int = 0,
    limit: int = 20,
    skills: Optional[str] = None,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get paginated list of available job offers with filtering"""
    query = db.query(JobOffer).filter(JobOffer.status == "active")
    
    if skills:
        query = query.filter(JobOffer.required_skills.contains(skills.split(",")))
    if budget_min:
        query = query.filter(JobOffer.budget_max >= budget_min)
    if budget_max:
        query = query.filter(JobOffer.budget_min <= budget_max)
    
    offers = query.offset(skip).limit(limit).all()
    return {"offers": offers, "total": query.count()}
```

**2. Job Offer Details Endpoint:**
```python
@app.get("/api/job-offers/{offer_id}")
async def get_job_offer_details(offer_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific job offer"""
    offer = db.query(JobOffer).filter(JobOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Job offer not found")
    
    return {
        "id": offer.id,
        "title": offer.title,
        "description": offer.description,
        "budget_range": {"min": offer.budget_min, "max": offer.budget_max},
        "required_skills": offer.required_skills,
        "deadline": offer.deadline,
        "client_info": {
            "id": offer.client_id,
            "rating": get_client_rating(offer.client_id),
            "completed_projects": get_client_project_count(offer.client_id)
        }
    }
```

**3. Job Offer Acceptance Endpoint:**
```python
@app.post("/api/job-offers/{offer_id}/accept")
async def accept_job_offer(
    offer_id: str,
    freelancer_id: str,
    db: Session = Depends(get_db)
):
    """Accept a job offer and create communication thread"""
    # Check if offer is still available
    offer = db.query(JobOffer).filter(JobOffer.id == offer_id).first()
    if not offer or offer.status != "active":
        raise HTTPException(status_code=400, detail="Job offer no longer available")
    
    # Create acceptance record
    acceptance = JobAcceptance(
        job_offer_id=offer_id,
        freelancer_id=freelancer_id,
        accepted_at=datetime.utcnow()
    )
    db.add(acceptance)
    
    # Update offer status
    offer.status = "accepted"
    offer.accepted_by = freelancer_id
    
    # Create communication thread
    thread_id = create_communication_thread(offer.client_id, freelancer_id, offer_id)
    acceptance.communication_thread_id = thread_id
    
    # Send notifications
    send_notification(offer.client_id, "Job offer accepted", f"Your job offer '{offer.title}' has been accepted")
    send_notification(freelancer_id, "Job offer accepted", f"You have successfully accepted the job offer")
    
    db.commit()
    return {"status": "accepted", "communication_thread_id": thread_id}
```

**4. Database Models:**
```python
class JobOffer(Base):
    __tablename__ = "job_offers"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    budget_min = Column(Numeric(10, 2))
    budget_max = Column(Numeric(10, 2))
    required_skills = Column(ARRAY(String))
    deadline = Column(DateTime)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_by = Column(UUID, ForeignKey("users.id"))

class JobAcceptance(Base):
    __tablename__ = "job_acceptances"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    job_offer_id = Column(UUID, ForeignKey("job_offers.id"), nullable=False)
    freelancer_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    accepted_at = Column(DateTime, default=datetime.utcnow)
    communication_thread_id = Column(UUID)
```

**5. Error Handling and Validation:**
- Input validation for all endpoints
- Rate limiting on acceptance endpoint (max 5 per minute)
- Duplicate acceptance prevention
- Comprehensive error messages
- Audit logging for all actions

**6. Security Features:**
- JWT token validation for all endpoints
- User authorization checks
- SQL injection prevention
- XSS protection for text fields
- CORS configuration for frontend integration''',
                    'usage': {'prompt_tokens': 180, 'completion_tokens': 250, 'total_tokens': 430}
                }
            }
        ],
        'frontend': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 160,
                'completion_tokens': 220,
                'total_tokens': 380,
                'cost': '0.0114',
                'response_time_ms': 1400,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a Frontend Developer creating user interfaces...'},
                        {'role': 'user', 'content': 'Implement the user interface for job offer viewing...'}
                    ]
                },
                'response_data': {
                    'content': 'I have created the frontend components for job offer display...',
                    'usage': {'prompt_tokens': 160, 'completion_tokens': 220, 'total_tokens': 380}
                }
            }
        ],
        'tester': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 140,
                'completion_tokens': 180,
                'total_tokens': 320,
                'cost': '0.0096',
                'response_time_ms': 1100,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a QA Tester creating comprehensive tests...'},
                        {'role': 'user', 'content': 'Create tests for the job offer functionality...'}
                    ]
                },
                'response_data': {
                    'content': 'I have created comprehensive test cases covering...',
                    'usage': {'prompt_tokens': 140, 'completion_tokens': 180, 'total_tokens': 320}
                }
            }
        ]
    }
    
    for conversation in conversations:
        print(f"Updating conversation: {conversation.step} ({conversation.agent})")
        
        # Get sample LLM calls for this agent
        agent_calls = sample_llm_calls.get(conversation.agent, [])
        
        if agent_calls:
            # Update conversation with LLM call data
            conversation.llm_calls = agent_calls
            conversation.total_tokens_used = sum(call['total_tokens'] for call in agent_calls)
            conversation.total_cost = f"{sum(float(call['cost']) for call in agent_calls):.4f}"
            
            # Create LLMCall records
            for call_data in agent_calls:
                llm_call = LLMCall(
                    conversation_id=conversation.id,
                    model=call_data['model'],
                    prompt_tokens=call_data['prompt_tokens'],
                    completion_tokens=call_data['completion_tokens'],
                    total_tokens=call_data['total_tokens'],
                    cost=call_data['cost'],
                    response_time_ms=call_data['response_time_ms'],
                    request_data=call_data['request_data'],
                    response_data=call_data['response_data']
                )
                db.add(llm_call)
            
            print(f"  Added {len(agent_calls)} LLM calls, {conversation.total_tokens_used} tokens, ${conversation.total_cost}")
    
    # Commit changes
    db.commit()
    print("LLM call data added successfully!")

if __name__ == "__main__":
    add_sample_llm_calls()
