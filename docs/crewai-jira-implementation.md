```

---

## Agent Collaboration Patterns

### Pattern 1: Sequential Collaboration

```
Story Analysis → Architecture Review → Implementation → Testing → Validation
     (PO)              (Arch)              (Dev)         (QA)      (Validator)
```

**When to use**: Standard feature implementation with clear dependencies

**Example Flow**:
1. PO analyzes story and creates requirements document
2. Architect reviews codebase and creates implementation plan
3. Developer implements based on plan
4. Test Engineer writes and runs tests
5. QA Validator verifies AC are met

### Pattern 2: Iterative Collaboration (with Feedback Loops)

```
Developer → Code Reviewer → Developer (if changes needed)
              ↓ (approved)
         Test Engineer
              ↓
         QA Validator → Developer (if issues found)
```

**When to use**: When quality issues are detecte# CrewAI Jira Story Implementation Guide

## Autonomous Development Team for Jira Stories

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Agent Roles & Responsibilities](#agent-roles--responsibilities)
4. [Workflow Orchestration](#workflow-orchestration)
5. [Configuration](#configuration)
6. [Agent Collaboration Patterns](#agent-collaboration-patterns)
7. [Quality Control Mechanisms](#quality-control-mechanisms)
8. [Escalation & Feedback Loops](#escalation--feedback-loops)
9. [Hallucination Detection](#hallucination-detection)
10. [Implementation](#implementation)
11. [Testing & Validation](#testing--validation)

---

## Overview

This system implements an autonomous development team that takes Jira stories and implements them end-to-end, including:

- Cloning repositories
- Analyzing existing codebase
- Implementing features
- Writing tests
- Code review
- Creating pull requests
- Validating against acceptance criteria

### Key Features

✅ **Autonomous Development**: Full feature implementation from story to PR  
✅ **Intelligent Collaboration**: Agents work together with feedback loops  
✅ **Quality Gates**: Multiple validation checkpoints  
✅ **Hallucination Detection**: AI output validation mechanisms  
✅ **Escalation Paths**: Human intervention when needed  
✅ **Repository Management**: Safe cloning and branching  

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Jira Integration                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Story Fetch  │  │  AC Parser   │  │  Status Updates      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Durable Functions Orchestrator                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              Workflow State Machine                    │     │
│  │                                                        │     │
│  │  1. Story Analysis     → Quality Gate 1               │     │
│  │  2. Repository Setup   → Validation                   │     │
│  │  3. Codebase Analysis  → Quality Gate 2               │     │
│  │  4. Implementation     → Code Review Loop             │     │
│  │  5. Testing            → Quality Gate 3               │     │
│  │  6. Validation         → AC Verification              │     │
│  │  7. PR Creation        → Human Review                 │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Collaboration Layer                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Product    │─────→│  Architect   │─────→│   Developer  │  │
│  │    Owner     │      │   Reviewer   │      │    Agent     │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                      │                      │         │
│         │                      ▼                      ▼         │
│         │              ┌──────────────┐      ┌──────────────┐  │
│         └─────────────→│Code Reviewer │      │Test Engineer │  │
│                        │    Agent     │      │    Agent     │  │
│                        └──────────────┘      └──────────────┘  │
│                                │                      │         │
│                                ▼                      ▼         │
│                        ┌──────────────┐      ┌──────────────┐  │
│                        │  QA Agent    │      │  DevOps      │  │
│                        │  (Validator) │      │  Agent       │  │
│                        └──────────────┘      └──────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │        Hallucination Detection & Feedback Loop          │    │
│  │  • Output validation • Fact checking • Reality testing  │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Repository Management Layer                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Git Clone    │  │Branch Manager│  │  PR Creator          │  │
│  │ (/repos/)    │  │              │  │  (GitHub/Azure)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Quality Control & Escalation                  │
├─────────────────────────────────────────────────────────────────┤
│  • Automated Tests         • Code Quality Metrics               │
│  • AC Verification         • Security Scanning                  │
│  • Human Escalation        • Rollback Mechanisms                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Roles & Responsibilities

### 1. Product Owner Agent

**Role**: Story Analyst & Requirements Guardian

**Responsibilities**:
- Parse Jira story and extract requirements
- Break down acceptance criteria into testable conditions
- Clarify ambiguities (or escalate)
- Validate final implementation against AC
- Approve/reject implementation

**Configuration**:
```yaml
product_owner:
  name: "Product Owner Agent"
  model: "gpt-4"
  temperature: 0.3  # Low temperature for consistency
  tools:
    - jira_reader
    - acceptance_criteria_parser
    - requirements_validator
  
  system_prompt: |
    You are an experienced Product Owner who ensures that implementations 
    meet business requirements. You are meticulous about acceptance criteria 
    and user value. You escalate when requirements are unclear.
  
  escalation_triggers:
    - ambiguous_requirements
    - conflicting_acceptance_criteria
    - missing_business_context
  
  validation_checklist:
    - all_ac_testable
    - clear_definition_of_done
    - no_technical_jargon_in_ac
```

### 2. Architect Reviewer Agent

**Role**: Codebase Guardian & Technical Advisor

**Responsibilities**:
- Analyze existing codebase structure
- Identify patterns and conventions
- Recommend implementation approach
- Ensure architectural consistency
- Review for technical debt

**Configuration**:
```yaml
architect_reviewer:
  name: "Architect Reviewer Agent"
  model: "gpt-4"
  temperature: 0.2
  tools:
    - codebase_analyzer
    - dependency_checker
    - pattern_detector
    - architectural_diagram_generator
  
  system_prompt: |
    You are a Senior Software Architect who reviews codebases and ensures 
    new implementations follow existing patterns and best practices. You 
    identify potential issues early and guide developers toward maintainable 
    solutions.
  
  analysis_areas:
    - code_structure
    - design_patterns
    - naming_conventions
    - dependency_management
    - testing_patterns
    - error_handling_patterns
  
  output_format:
    - architecture_overview
    - implementation_recommendations
    - files_to_modify
    - new_files_to_create
    - potential_risks
```

### 3. Developer Agent

**Role**: Code Implementation Specialist

**Responsibilities**:
- Implement features based on architect's guidance
- Follow existing code patterns
- Write clean, maintainable code
- Handle edge cases
- Create necessary files

**Configuration**:
```yaml
developer:
  name: "Developer Agent"
  model: "gpt-4"
  temperature: 0.4  # Slightly creative for problem-solving
  tools:
    - file_reader
    - file_writer
    - code_executor
    - dependency_installer
    - git_operations
  
  system_prompt: |
    You are a Senior Software Developer who writes production-quality code. 
    You follow the codebase conventions, implement features correctly, and 
    handle edge cases. You ask for clarification when requirements are unclear.
  
  coding_principles:
    - DRY (Don't Repeat Yourself)
    - SOLID principles
    - Clean code practices
    - Defensive programming
    - Error handling
  
  max_file_size: 500  # lines per file
  max_complexity: 10   # cyclomatic complexity
  
  feedback_loop:
    max_iterations: 3
    review_after_each_iteration: true
```

### 4. Test Engineer Agent

**Role**: Quality Assurance & Test Coverage

**Responsibilities**:
- Write unit tests
- Write integration tests
- Ensure test coverage > 80%
- Test edge cases
- Validate against acceptance criteria

**Configuration**:
```yaml
test_engineer:
  name: "Test Engineer Agent"
  model: "gpt-4"
  temperature: 0.3
  tools:
    - test_framework_runner
    - coverage_analyzer
    - test_generator
    - mock_generator
  
  system_prompt: |
    You are a QA Engineer who writes comprehensive tests. You think about 
    edge cases, error conditions, and ensure code is thoroughly tested. 
    You write clear, maintainable test code.
  
  test_requirements:
    min_coverage: 80
    test_types:
      - unit_tests
      - integration_tests
      - edge_case_tests
      - error_condition_tests
  
  test_naming_convention: "test_<functionality>_<condition>_<expected_result>"
```

### 5. Code Reviewer Agent

**Role**: Code Quality Guardian

**Responsibilities**:
- Review code for quality
- Check for security issues
- Ensure style consistency
- Validate against best practices
- Request changes if needed

**Configuration**:
```yaml
code_reviewer:
  name: "Code Reviewer Agent"
  model: "gpt-4"
  temperature: 0.2
  tools:
    - static_analysis_runner
    - security_scanner
    - code_style_checker
    - complexity_analyzer
  
  system_prompt: |
    You are a meticulous Code Reviewer who ensures high code quality. You 
    check for bugs, security issues, performance problems, and style violations. 
    You provide constructive feedback with specific examples.
  
  review_checklist:
    - code_correctness
    - security_vulnerabilities
    - performance_issues
    - code_style_consistency
    - test_coverage
    - documentation
    - error_handling
  
  quality_gates:
    - no_critical_security_issues
    - no_hardcoded_secrets
    - complexity_under_threshold
    - style_compliance: 95%
  
  feedback_format:
    - issue_severity: [critical, major, minor, suggestion]
    - line_number
    - description
    - suggested_fix
```

### 6. QA Validator Agent

**Role**: Acceptance Criteria Validator

**Responsibilities**:
- Validate all AC are met
- Run end-to-end tests
- Verify business logic
- Check for regressions
- Final approval/rejection

**Configuration**:
```yaml
qa_validator:
  name: "QA Validator Agent"
  model: "gpt-4"
  temperature: 0.1  # Very low - needs to be objective
  tools:
    - test_runner
    - ac_validator
    - regression_tester
    - integration_tester
  
  system_prompt: |
    You are a QA Validator who verifies that implementations meet all 
    acceptance criteria. You are thorough, objective, and detail-oriented. 
    You reject implementations that don't fully meet requirements.
  
  validation_process:
    - run_all_tests
    - validate_each_ac
    - check_for_regressions
    - verify_edge_cases
    - final_approval_decision
  
  approval_criteria:
    - all_tests_passing: true
    - all_ac_met: true
    - no_regressions: true
    - code_review_approved: true
```

### 7. DevOps Agent

**Role**: CI/CD & Deployment Specialist

**Responsibilities**:
- Create feature branches
- Commit changes
- Create pull requests
- Run CI/CD pipelines
- Monitor deployment

**Configuration**:
```yaml
devops:
  name: "DevOps Agent"
  model: "gpt-4"
  temperature: 0.1
  tools:
    - git_operations
    - github_api
    - azure_devops_api
    - ci_cd_runner
  
  system_prompt: |
    You are a DevOps Engineer who manages code deployment. You follow 
    branching strategies, create clean commits, and ensure CI/CD passes.
  
  git_workflow:
    branch_naming: "feature/JIRA-{story_id}-{short-description}"
    commit_convention: "conventional_commits"
    pr_template: true
  
  pr_requirements:
    - descriptive_title
    - link_to_jira
    - summary_of_changes
    - testing_notes
    - screenshots_if_ui
```

---

## Workflow Orchestration

### Main Orchestration Flow

```python
def jira_story_orchestrator(context: df.DurableOrchestrationContext):
    """
    Main orchestrator for implementing a Jira story
    """
    story_input = context.get_input()
    workflow_id = context.instance_id
    jira_story_id = story_input['jira_story_id']
    
    try:
        # ========================================
        # PHASE 1: Story Analysis & Planning
        # ========================================
        context.set_custom_status({
            "phase": "story_analysis",
            "progress": 5,
            "current_agent": "product_owner"
        })
        
        # 1.1: Fetch story from Jira
        story_details = yield context.call_activity(
            'fetch_jira_story',
            jira_story_id
        )
        
        # 1.2: Product Owner analyzes story
        story_analysis = yield context.call_activity(
            'product_owner_analyze_story',
            story_details
        )
        
        # Quality Gate 1: Check if story is clear
        if story_analysis['requires_clarification']:
            # Escalate to human
            yield context.call_activity(
                'escalate_to_human',
                {
                    'reason': 'ambiguous_requirements',
                    'details': story_analysis['clarifications_needed']
                }
            )
            # Wait for human input
            clarification = yield context.wait_for_external_event(
                'requirements_clarified'
            )
            story_analysis = yield context.call_activity(
                'product_owner_reanalyze_story',
                {'story': story_details, 'clarification': clarification}
            )
        
        # ========================================
        # PHASE 2: Repository Setup
        # ========================================
        context.set_custom_status({
            "phase": "repository_setup",
            "progress": 15,
            "current_agent": "devops"
        })
        
        # 2.1: Clone repository to /repos/
        repo_setup = yield context.call_activity(
            'clone_repository',
            {
                'repo_url': story_details['repository_url'],
                'branch': story_details.get('base_branch', 'main'),
                'clone_path': f'/repos/{jira_story_id}'
            }
        )
        
        # 2.2: Create feature branch
        branch_created = yield context.call_activity(
            'create_feature_branch',
            {
                'repo_path': repo_setup['repo_path'],
                'branch_name': f"feature/{jira_story_id}",
                'base_branch': story_details.get('base_branch', 'main')
            }
        )
        
        # ========================================
        # PHASE 3: Codebase Analysis
        # ========================================
        context.set_custom_status({
            "phase": "codebase_analysis",
            "progress": 25,
            "current_agent": "architect"
        })
        
        # 3.1: Architect reviews codebase
        codebase_analysis = yield context.call_activity(
            'architect_review_codebase',
            {
                'repo_path': repo_setup['repo_path'],
                'story_requirements': story_analysis['requirements'],
                'files_to_analyze': repo_setup['relevant_files']
            }
        )
        
        # Quality Gate 2: Validate architecture recommendations
        architecture_validation = yield context.call_activity(
            'validate_architecture_plan',
            codebase_analysis
        )
        
        if not architecture_validation['is_valid']:
            # Feedback loop: Ask architect to revise
            codebase_analysis = yield context.call_activity(
                'architect_revise_plan',
                {
                    'original_plan': codebase_analysis,
                    'validation_feedback': architecture_validation['feedback']
                }
            )
        
        # ========================================
        # PHASE 4: Implementation (with feedback loops)
        # ========================================
        context.set_custom_status({
            "phase": "implementation",
            "progress": 40,
            "current_agent": "developer"
        })
        
        implementation_approved = False
        implementation_iteration = 0
        max_iterations = 3
        
        while not implementation_approved and implementation_iteration < max_iterations:
            implementation_iteration += 1
            
            # 4.1: Developer implements feature
            implementation = yield context.call_activity(
                'developer_implement_feature',
                {
                    'repo_path': repo_setup['repo_path'],
                    'architecture_plan': codebase_analysis,
                    'requirements': story_analysis['requirements'],
                    'iteration': implementation_iteration
                }
            )
            
            # 4.2: Check for hallucinations
            hallucination_check = yield context.call_activity(
                'detect_hallucinations',
                {
                    'implementation': implementation,
                    'original_requirements': story_analysis['requirements'],
                    'codebase_context': codebase_analysis
                }
            )
            
            if hallucination_check['hallucinations_detected']:
                # Feedback to developer with specific issues
                context.set_custom_status({
                    "phase": "implementation_revision",
                    "issue": "hallucinations_detected",
                    "iteration": implementation_iteration
                })
                continue  # Retry implementation
            
            # 4.3: Code Review
            code_review = yield context.call_activity(
                'code_reviewer_review',
                {
                    'implementation': implementation,
                    'standards': codebase_analysis['coding_standards']
                }
            )
            
            if code_review['changes_requested']:
                # Feedback loop: Developer addresses review comments
                context.set_custom_status({
                    "phase": "addressing_review_comments",
                    "iteration": implementation_iteration
                })
                continue  # Retry implementation
            
            implementation_approved = True
        
        if not implementation_approved:
            # Escalate: Too many iterations
            yield context.call_activity(
                'escalate_to_human',
                {
                    'reason': 'implementation_stuck',
                    'iterations': implementation_iteration,
                    'last_issues': code_review['issues']
                }
            )
            return {'status': 'escalated', 'reason': 'max_iterations_exceeded'}
        
        # ========================================
        # PHASE 5: Testing
        # ========================================
        context.set_custom_status({
            "phase": "testing",
            "progress": 70,
            "current_agent": "test_engineer"
        })
        
        # 5.1: Test Engineer writes tests
        tests = yield context.call_activity(
            'test_engineer_write_tests',
            {
                'implementation': implementation,
                'requirements': story_analysis['requirements'],
                'repo_path': repo_setup['repo_path']
            }
        )
        
        # 5.2: Run tests
        test_results = yield context.call_activity(
            'run_tests',
            {
                'repo_path': repo_setup['repo_path'],
                'test_files': tests['test_files']
            }
        )
        
        # Quality Gate 3: All tests must pass
        if not test_results['all_passed']:
            # Developer fixes failing tests
            fixes = yield context.call_activity(
                'developer_fix_tests',
                {
                    'repo_path': repo_setup['repo_path'],
                    'test_failures': test_results['failures']
                }
            )
            # Re-run tests
            test_results = yield context.call_activity(
                'run_tests',
                {'repo_path': repo_setup['repo_path']}
            )
            
            if not test_results['all_passed']:
                # Escalate
                yield context.call_activity(
                    'escalate_to_human',
                    {'reason': 'tests_failing', 'details': test_results}
                )
                return {'status': 'escalated', 'reason': 'test_failures'}
        
        # ========================================
        # PHASE 6: Validation Against AC
        # ========================================
        context.set_custom_status({
            "phase": "validation",
            "progress": 85,
            "current_agent": "qa_validator"
        })
        
        # 6.1: QA validates against acceptance criteria
        ac_validation = yield context.call_activity(
            'qa_validate_acceptance_criteria',
            {
                'implementation': implementation,
                'tests': tests,
                'test_results': test_results,
                'acceptance_criteria': story_analysis['acceptance_criteria'],
                'repo_path': repo_setup['repo_path']
            }
        )
        
        # Quality Gate 4: All AC must be met
        if not ac_validation['all_criteria_met']:
            # Product Owner reviews
            po_decision = yield context.call_activity(
                'product_owner_final_review',
                {
                    'validation': ac_validation,
                    'implementation': implementation
                }
            )
            
            if po_decision['decision'] == 'reject':
                # Escalate with details
                yield context.call_activity(
                    'escalate_to_human',
                    {
                        'reason': 'acceptance_criteria_not_met',
                        'unmet_criteria': ac_validation['unmet_criteria']
                    }
                )
                return {'status': 'escalated', 'reason': 'ac_not_met'}
        
        # ========================================
        # PHASE 7: Pull Request Creation
        # ========================================
        context.set_custom_status({
            "phase": "pr_creation",
            "progress": 95,
            "current_agent": "devops"
        })
        
        # 7.1: Commit changes
        commit_result = yield context.call_activity(
            'commit_changes',
            {
                'repo_path': repo_setup['repo_path'],
                'message': f"feat: {story_details['title']} ({jira_story_id})",
                'files': implementation['modified_files']
            }
        )
        
        # 7.2: Push to remote
        push_result = yield context.call_activity(
            'push_to_remote',
            {
                'repo_path': repo_setup['repo_path'],
                'branch': branch_created['branch_name']
            }
        )
        
        # 7.3: Create Pull Request
        pr_result = yield context.call_activity(
            'create_pull_request',
            {
                'repo_url': story_details['repository_url'],
                'source_branch': branch_created['branch_name'],
                'target_branch': story_details.get('base_branch', 'main'),
                'title': f"[{jira_story_id}] {story_details['title']}",
                'description': {
                    'story_link': story_details['jira_url'],
                    'summary': story_analysis['summary'],
                    'changes': implementation['summary'],
                    'testing': test_results['summary'],
                    'ac_validation': ac_validation['summary']
                }
            }
        )
        
        # 7.4: Update Jira story
        yield context.call_activity(
            'update_jira_story',
            {
                'story_id': jira_story_id,
                'status': 'In Review',
                'pr_link': pr_result['pr_url'],
                'comment': f"Pull request created: {pr_result['pr_url']}"
            }
        )
        
        # ========================================
        # WORKFLOW COMPLETE
        # ========================================
        context.set_custom_status({
            "phase": "completed",
            "progress": 100
        })
        
        return {
            'status': 'completed',
            'workflow_id': workflow_id,
            'jira_story_id': jira_story_id,
            'pr_url': pr_result['pr_url'],
            'implementation_summary': implementation['summary'],
            'test_coverage': test_results['coverage'],
            'ac_validation': ac_validation
        }
        
    except Exception as e:
        logging.error(f"Workflow failed: {str(e)}")
        yield context.call_activity(
            'escalate_to_human',
            {
                'reason': 'workflow_error',
                'error': str(e),
                'workflow_id': workflow_id
            }
        )
        return {'status': 'failed', 'error': str(e)}
```

---

## Configuration

### Main Configuration File

#### `config/agents_config.yaml`

```yaml
# ============================================
# Jira Story Implementation - Agent Configuration
# ============================================

workflow:
  name: "jira_story_implementation"
  version: "1.0.0"
  max_duration_hours: 4
  auto_escalation_enabled: true

repository:
  clone_base_path: "/repos"
  cleanup_after_completion: false
  git_config:
    user_name: "CrewAI Bot"
    user_email: "crewai-bot@yourcompany.com"

jira:
  base_url: "https://yourcompany.atlassian.net"
  api_version: "3"
  auth_type: "oauth"  # or "api_token"
  fields_to_fetch:
    - summary
    - description
    - acceptance_criteria
    - story_points
    - labels
    - components
    - repository_url

agents:
  # ==========================================
  # Product Owner Agent
  # ==========================================
  product_owner:
    enabled: true
    model:
      provider: "azure_openai"
      deployment: "gpt-4"
      temperature: 0.3
      max_tokens: 4000
    
    tools:
      - name: "jira_reader"
        enabled: true
      - name: "acceptance_criteria_parser"
        enabled: true
      - name: "requirements_validator"
        enabled: true
    
    behavior:
      strict_ac_validation: true
      escalate_on_ambiguity: true
      max_clarification_rounds: 2
    
    prompts:
      system: |
        You are an experienced Product Owner responsible for ensuring 
        implementations meet business requirements. You analyze Jira stories 
        and break down acceptance criteria into clear, testable conditions.
        
        CRITICAL RULES:
        1. Every acceptance criterion must be testable
        2. Escalate if requirements are ambiguous or contradictory
        3. Focus on user value and business outcomes
        4. Validate that technical implementation matches business intent
      
      story_analysis: |
        Analyze the following Jira story:
        
        Story ID: {story_id}
        Title: {title}
        Description: {description}
        Acceptance Criteria: {acceptance_criteria}
        
        Provide:
        1. Clear summary of what needs to be built
        2. List of functional requirements
        3. Each AC broken down into testable conditions
        4. Edge cases to consider
        5. Any ambiguities requiring clarification
        6. Definition of Done checklist
      
      validation: |
        Review the implementation against original requirements:
        
        Original Requirements: {requirements}
        Implementation Summary: {implementation}
        Test Results: {test_results}
        
        Verify:
        1. Each acceptance criterion is fully met
        2. No scope creep or extra features
        3. Edge cases are handled
        4. Implementation matches user intent
        
        Decision: APPROVE or REJECT with specific reasons

  # ==========================================
  # Architect Reviewer Agent
  # ==========================================
  architect_reviewer:
    enabled: true
    model:
      provider: "azure_openai"
      deployment: "gpt-4"
      temperature: 0.2
      max_tokens: 6000
    
    tools:
      - name: "codebase_analyzer"
        enabled: true
        config:
          max_files_to_analyze: 50
          include_patterns:
            - "**/*.py"
            - "**/*.js"
            - "**/*.ts"
            - "**/*.java"
          exclude_patterns:
            - "**/node_modules/**"
            - "**/venv/**"
            - "**/.git/**"
      
      - name: "dependency_checker"
        enabled: true
      
      - name: "pattern_detector"
        enabled: true
        config:
          patterns_to_detect:
            - design_patterns
            - architectural_patterns
            - naming_conventions
            - error_handling_patterns
    
    analysis_depth:
      architecture_review: "deep"
      code_review: "moderate"
      dependency_analysis: "full"
    
    prompts:
      system: |
        You are a Senior Software Architect responsible for maintaining code 
        quality and architectural integrity. You review codebases before 
        implementation to ensure new features align with existing patterns.
        
        CRITICAL RULES:
        1. Identify all relevant existing patterns
        2. Recommend implementation approach that fits codebase style
        3. Flag potential technical debt or anti-patterns
        4. Consider scalability and maintainability
        5. Be specific about which files to modify
      
      codebase_review: |
        Analyze this codebase for implementing the following feature:
        
        Feature Requirements: {requirements}
        Repository Path: {repo_path}
        Key Files: {key_files}
        
        Analyze:
        1. Current architecture and structure
        2. Existing patterns and conventions
        3. Similar implementations in codebase
        4. Dependencies and libraries used
        5. Testing patterns
        
        Provide:
        1. Architecture overview
        2. Implementation strategy
        3. Files to create/modify (be specific)
        4. Code patterns to follow
        5. Potential risks or challenges
        6. Dependencies to add (if any)

  # ==========================================
  # Developer Agent
  # ==========================================
  developer:
    enabled: true
    model:
      provider: "azure_openai"
      deployment: "gpt-4"
      temperature: 0.4
      max_tokens: 8000
    
    tools:
      - name: "file_reader"
        enabled: true
        config:
          max_file_size_kb: 500
      
      - name: "file_writer"
        enabled: true
        config:
          backup_before_write: true
      
      - name: "code_executor"
        enabled: true
        config:
          sandboxed: true
          timeout_seconds: 30
      
      - name: "git_operations"
        enabled: true
    
    constraints:
      max_file_size_lines: 500
      max_function_complexity: 10
      max_files_per_iteration: 10
    
    feedback_loop:
      enabled: true
      max_iterations: 3
      auto_fix_simple_issues: true
    
    prompts:
      system: |
        You are a Senior Software Developer who writes production-quality code.
        You follow existing codebase patterns and implement features correctly.
        
        CRITICAL RULES:
        1. Follow the architecture plan exactly
        2. Use existing code patterns and conventions
        3. Write clean, readable, maintainable code
        4. Handle all edge cases
        5. Add appropriate error handling
        6. Write self-documenting code with comments where needed
        7. NEVER hallucinate APIs or functions that don't exist
        8. Use only imports that are available in the codebase
      
      implementation: |
        Implement the following feature:
        
        Requirements: {requirements}
        Architecture Plan: {architecture_plan}
        Files to Modify: {files_to_modify}
        Code Patterns: {code_patterns}
        
        Repository Context:
        {codebase_context}
        
        For each file:
        1. Show the complete, working implementation
        2. Follow existing naming conventions
        3. Use appropriate error handling
        4. Add necessary imports (verify they exist!)
        5. Include inline comments for complex logic
        
        VALIDATION CHECKLIST:
        - [ ] All imports exist in codebase or dependencies
        - [ ] Function signatures match existing patterns
        - [ ] Error handling is comprehensive
        - [ ] Edge cases are handled
        - [ ] Code is DRY (no duplication)
        - [ ] Names are clear and consistent

  # ==========================================
  # Test Engineer Agent
  # ==========================================
  test_engineer:
    enabled: true
    model:
      provider: "azure_openai"
      deployment: "gpt-4"
      temperature: 0.3
      max_tokens: 6000
    
    tools:
      - name: "test_framework_runner"
        enabled: true
        config:
          frameworks:
            - pytest
            - jest
            - junit
      
      - name: "coverage_analyzer"
        enabled: true
        config:
          min_coverage_required: 80
      
      - name: "mock_generator"
        enabled: true
    
    test_strategy:
      types:
        - unit_tests
        - integration_tests
        - edge_case_tests
      coverage_requirement: 80
      mock_external_dependencies: true
    
    prompts:
      system: |
        You are a QA Engineer who writes comprehensive, maintainable tests.
        You think about edge cases, error conditions, and ensure thorough coverage.
        
        CRITICAL RULES:
        1. Test all happy paths
        2. Test all edge cases
        3. Test error conditions
        4. Use appropriate mocking
        5. Tests should be clear and maintainable
        6. Follow existing test patterns
        7. Aim for >80% coverage
      
      test_writing: |
        Write tests for the following implementation:
        
        Implementation: {implementation}
        Requirements: {requirements}
        Acceptance Criteria: {acceptance_criteria}
        
        Existing Test Patterns: {test_patterns}
        
        Create:
        1. Unit tests for each function/method
        2. Integration tests for component interactions
        3. Edge case tests
        4. Error condition tests
        5. Tests that validate each acceptance criterion
        
        Test Structure:
        - Arrange (setup)
        - Act (execute)
        - Assert (verify)
        
        Each test should:
        - Have a descriptive name
        - Test one specific thing
        - Be independent of other tests
        - Use appropriate fixtures/mocks

  # ==========================================
  # Code Reviewer Agent
  # ==========================================
  code_reviewer:
    enabled: true
    model:
      provider: "azure_openai"
      deployment: "gpt-4"
      temperature: 0.2
      max_tokens: 6000
    
    tools:
      - name: "static_analysis_runner"
        enabled: true
        config:
          tools:
            - pylint
            - eslint
            - sonarqube
      
      - name: "security_scanner"
        enabled: true
        config:
          scanners:
            - bandit
            - safety
            - snyk
      
      - name: "complexity_analyzer"
        enabled: true
    
    review_criteria:
      code_quality:
        - correctness
        - readability
        - maintainability
        - performance
      
      security:
        - no_hardcoded_secrets
        - input_validation
        - sql_injection_prevention
        - xss_prevention
      
      standards:
        - style_guide_compliance: 95
        - max_complexity: 10
        - min_test_coverage: 80
    
    quality_gates:
      blocking:
        - critical_security_issues
        - hardcoded_secrets
        - high_complexity_violations
      
      non_blocking:
        - style_violations
        - minor_suggestions
    
    prompts:
      system: |
        You are a meticulous Code Reviewer who ensures high quality and security.
        You provide constructive, actionable feedback with specific examples.
        
        CRITICAL RULES:
        1. Be thorough but constructive
        2. Categorize issues by severity
        3. Provide specific line numbers
        4. Suggest fixes, don't just point out problems
        5. Check for security vulnerabilities
        6. Verify best practices are followed
      
      review: |
        Review the following code:
        
        Files Changed: {files}
        Implementation: {implementation}
        Coding Standards: {standards}
        
        Review for:
        
        1. CORRECTNESS
           - Logic errors
           - Edge case handling
           - Error handling
        
        2. SECURITY
           - Hardcoded secrets
           - SQL injection risks
           - XSS vulnerabilities
           - Authentication/authorization issues
        
        3. PERFORMANCE
           - Inefficient algorithms
           - Memory leaks
           - Database query optimization
        
        4. MAINTAINABILITY
           - Code clarity
           - DRY violations
           - Complexity issues
           - Documentation
        
        5. STYLE
           - Naming conventions
           - Formatting
           - Comments
        
        For each issue:
        - Severity: CRITICAL | MAJOR | MINOR | SUGGESTION
        - File: <filename>
        - Line: <line_number>
        - Issue: <description>
        - Fix: <suggested_fix>
        
        Final Decision: APPROVE | REQUEST_CHANGES

  # ==========================================
  # QA Validator Agent
  # ==========================================
  qa_validator:
    enabled: true
    model:
      provider: "azure_openai"
      deployment: "gpt-4"
      temperature: 0.1
      max_tokens: 4000
    
    tools:
      - name: "test_runner"
        enabled: true
      
      - name: "ac_validator"
        enabled: true
      
      - name: "regression_tester"
        enabled: true
    
    validation_process:
      - run_all_tests
      - validate_each_ac
      - check_regressions
      - verify_edge_cases
      - final_decision
    
    approval_criteria:
      all_tests_passing: true
      all_ac_met: true
      no_regressions: true
      code_review_approved: true
    
    prompts:
      system: |
        You are a QA Validator who objectively verifies implementations meet 
        all requirements. You are thorough, detail-oriented, and unbiased.
        
        CRITICAL RULES:
        1. Every AC must be explicitly validated
        2. Be objective - approve only if fully complete
        3. Check for regressions
        4. Verify edge cases are handled
        5. Escalate if anything is incomplete
      
      validation: |
        Validate the implementation against requirements:
        
        Acceptance Criteria:
        {acceptance_criteria}
        
        Implementation:
        {implementation}
        
        Test Results:
        {test_results}
        
        For each AC:
        1. State the criterion
        2. Evidence it's met (test results, code review)
        3. Status: MET | PARTIALLY_MET | NOT_MET
        
        Regression Check:
        - Run existing tests
        - Verify no functionality broken
        
        Final Decision:
        - APPROVED: All criteria fully met
        - REJECTED: List unmet criteria with specifics

  # ==========================================
  # DevOps Agent
  # ==========================================
  devops:
    enabled: true
    model:
      provider: "azure_openai"
      deployment: "gpt-4"
      temperature: 0.1
      max_tokens: 2000
    
    tools:
      - name: "git_operations"
        enabled: true
      
      - name: "github_api"
        enabled: true
      
      - name: "azure_devops_api"
        enabled: true
      
      - name: "ci_cd_runner"
        enabled: true
    
    git_workflow:
      branch_naming: "feature/{jira_id}-{short_description}"
      commit_convention: "conventional_commits"
      require_sign_off: true
    
    pr_config:
      use_template: true
      require_description: true
      link_to_jira: true
      assign_reviewers: true
      labels:
        - "automated"
        - "crew-ai"
    
    prompts:
      system: |
        You are a DevOps Engineer who manages code deployment processes.
        You follow git workflows, create clean commits, and ensure CI/CD success.
        
        CRITICAL RULES:
        1. Follow conventional commit format
        2. Create descriptive PR descriptions
        3. Link to Jira stories
        4. Ensure CI/CD passes before finalizing
        5. Use appropriate branch naming

# ============================================
# Hallucination Detection Configuration
# ============================================
hallucination_detection:
  enabled: true
  
  checks:
    - name: "import_validation"
      description: "Verify all imports exist"
      severity: "critical"
      action: "reject"
    
    - name: "api_validation"
      description: "Verify APIs and methods exist"
      severity: "critical"
      action: "reject"
    
    - name: "dependency_validation"
      description: "Verify dependencies are available"
      severity: "critical"
      action: "reject"
    
    - name: "fact_checking"
      description: "Verify factual claims about codebase"
      severity: "major"
      action: "flag"
    
    - name: "pattern_consistency"
      description: "Ensure patterns match codebase"
      severity: "major"
      action: "flag"
  
  validation_strategy:
    - static_analysis
    - codebase_comparison
    - execution_testing
    - peer_review

# ============================================
# Escalation Configuration
# ============================================
escalation:
  enabled: true
  
  triggers:
    - name: "ambiguous_requirements"
      threshold: "immediate"
      notify:
        - product_owner
        - tech_lead
    
    - name: "implementation_stuck"
      threshold: 3  # iterations
      notify:
        - tech_lead
        - developer
    
    - name: "tests_failing"
      threshold: 2  # attempts
      notify:
        - qa_lead
        - tech_lead
    
    - name: "acceptance_criteria_not_met"
      threshold: "immediate"
      notify:
        - product_owner
        - tech_lead
    
    - name: "security_vulnerability"
      threshold: "immediate"
      priority: "critical"
      notify:
        - security_team
        - tech_lead
        - engineering_manager
    
    - name: "hallucination_detected"
      threshold: "immediate"
      notify:
        - ai_team
        - tech_lead
  
  notification_channels:
    - slack
    - email
    - jira_comment

# ============================================
# Quality Control
# ============================================
quality_control:
  gates:
    gate_1:
      name: "Story Analysis"
      checks:
        - requirements_clear
        - ac_testable
        - no_ambiguities
      on_failure: "escalate"
    
    gate_2:
      name: "Architecture Review"
      checks:
        - plan_is_valid
        - follows_patterns
        - no_technical_debt
      on_failure: "revise"
    
    gate_3:
      name: "Code Quality"
      checks:
        - no_security_issues
        - complexity_acceptable
        - tests_passing
        - coverage_acceptable
      on_failure: "revise"
    
    gate_4:
      name: "AC Validation"
      checks:
        - all_ac_met
        - no_regressions
        - edge_cases_handled
      on_failure: "escalate"
  
  metrics:
    track:
      - implementation_time
      - iteration_count
      - test_coverage
      - code_quality_score
      - security_score
    
    alerts:
      - metric: "iteration_count"
        threshold: 3
        action: "escalate"
      
      - metric: "test_coverage"
        threshold: 80
        comparison: "less_than"
        action: "reject"

# ============================================
# Feedback Loop Configuration
# ============================================
feedback_loops:
  developer_code_reviewer:
    enabled: true
    max_iterations: 3
    iteration_strategy: "incremental_improvement"
  
  architect_developer:
    enabled: true
    max_iterations: 2
    iteration_strategy: "plan_refinement"
  
  qa_developer:
    enabled: true
    max_iterations: 2
    iteration_strategy: "bug_fixing"
  
  product_owner_all:
    enabled: true
    trigger: "ac_validation_failure"
    escalation_if_unresolved: true