# AI-Team Setup Guide

## Overview
This guide will help you set up and run the AI-Team system for retrieving Jira stories and having multiple agents collaborate on implementation.

## Prerequisites

### 1. Python Environment
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### 2. Required Accounts & API Keys
- **Azure OpenAI**: API key, endpoint, and deployment names
- **Jira**: API token, email, and base URL
- **GitHub**: Personal access token and repository access

## Step-by-Step Setup

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-team

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the environment template and configure your settings:

```bash
cp env_template .env
```

Edit `.env` with your actual values:

```env
# Azure OpenAI Service (Required)
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=default-gpt-deployment

# Multi-model support (Optional - fallback to AZURE_OPENAI_DEPLOYMENT if not set)
AZURE_OPENAI_DEPLOYMENT_PM=pm-gpt-deployment
AZURE_OPENAI_DEPLOYMENT_ARCHITECT=architect-gpt-deployment
AZURE_OPENAI_DEPLOYMENT_DEVELOPER=developer-gpt-deployment
AZURE_OPENAI_DEPLOYMENT_REVIEWER=reviewer-gpt-deployment
AZURE_OPENAI_DEPLOYMENT_TESTER=tester-gpt-deployment
AZURE_OPENAI_DEPLOYMENT_FRONTEND=frontend-gpt-deployment

# Environment
ENVIRONMENT=development

# Jira Integration (Required for story retrieval)
NEGISHI_JIRA_API_TOKEN=your-jira-api-token
NEGISHI_JIRA_BASE_URL=https://your-domain.atlassian.net
NEGISHI_JIRA_EMAIL=your-email@example.com
NEGISHI_PROJECT_KEY=NEGISHI

# GitHub Integration (Required for code management)
GITHUB_TOKEN=your-github-token
GITHUB_REPO=your-org/your-repo
NEGISHI_GITHUB_REPO=your-org/your-repo
NEGISHI_GITHUB_ORG=your-org

# Project Configuration
PROJECT_KEY=NEGISHI

# Integration Flags (Set to true after testing)
USE_REAL_GITHUB=false
USE_REAL_JIRA=false
```

### 3. Test Integrations

Before running the full workflow, test your integrations:

```bash
# Test with stub mode first
python test_integrations.py

# Test with real integrations (after setting up credentials)
python test_real_integrations.py
```

### 4. Verify Azure OpenAI Setup

Test your Azure OpenAI configuration:

```bash
python test_openai_deployments.py
```

## Running the AI-Team Workflow

### 1. Basic Story Implementation

```bash
# Run with a specific Jira story ID
python -m crewai_app.main --workflow story_implementation --story NEGISHI-178 --log-level INFO
```

### 2. Enhanced Workflow (Recommended)

```bash
# Run the enhanced workflow with better collaboration
python -c "
from crewai_app.workflows.enhanced_story_workflow import EnhancedStoryWorkflow
workflow = EnhancedStoryWorkflow('NEGISHI-178', use_real_jira=True, use_real_github=True)
results = workflow.run()
print('Workflow completed:', results)
"
```

### 3. Test Workflow

```bash
# Run test workflow with sample data
python test_real_workflow_negishi_178.py
```

## Configuration Options

### Agent Configuration

Each agent can be configured with different Azure OpenAI deployments:

```env
# Use different models for different agents
AZURE_OPENAI_DEPLOYMENT_PM=gpt-4o-mini
AZURE_OPENAI_DEPLOYMENT_ARCHITECT=gpt-4o
AZURE_OPENAI_DEPLOYMENT_DEVELOPER=gpt-4o
AZURE_OPENAI_DEPLOYMENT_FRONTEND=gpt-4o
```

### Integration Modes

- **Stub Mode** (`USE_REAL_GITHUB=false`, `USE_REAL_JIRA=false`): Uses mock data for testing
- **Real Mode** (`USE_REAL_GITHUB=true`, `USE_REAL_JIRA=true`): Uses actual APIs

### Workflow Modes

- **User Intervention Mode**: Pauses for user approval at key steps
- **Resume Mode**: Continues from last checkpoint if workflow was interrupted

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'crewai_app'**
   ```bash
   # Run from project root with module syntax
   python -m crewai_app.main --workflow story_implementation --story NEGISHI-178
   ```

2. **Azure OpenAI API Errors**
   - Verify API key and endpoint
   - Check deployment names exist
   - Ensure sufficient quota

3. **Jira Integration Failures**
   - Verify API token has correct permissions
   - Check project key exists
   - Ensure email matches token owner

4. **GitHub Integration Failures**
   - Verify token has repo access
   - Check repository exists and is accessible
   - Ensure branch permissions

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
python -m crewai_app.main --workflow story_implementation --story NEGISHI-178 --log-level DEBUG
```

### Checkpoint Recovery

If a workflow fails, you can resume from the last checkpoint:

```python
from crewai_app.workflows.enhanced_story_workflow import EnhancedStoryWorkflow
workflow = EnhancedStoryWorkflow('NEGISHI-178')
results = workflow.run(resume=True)  # Resume from checkpoint
```

## Advanced Configuration

### Custom Coding Rules

Edit `coding_rules.yaml` to customize coding standards:

```yaml
python:
  style: "black"
  max_line_length: 88
  docstring_style: "google"

typescript:
  style: "prettier"
  max_line_length: 100
  strict_mode: true
```

### Custom Agent Prompts

Modify agent prompts in `crewai_app/agents/` files to customize behavior.

### Environment-Specific Settings

Create environment-specific `.env` files:
- `.env.development`
- `.env.staging`
- `.env.production`

## Monitoring and Logs

### Log Files

- `logs/ai_team.log`: Main application logs
- `workflow_results/`: Checkpoint and result files
- `*.log`: Various workflow logs

### Metrics to Monitor

- Token usage per agent
- Workflow completion rates
- Integration success rates
- Error frequencies

## Security Considerations

1. **API Keys**: Never commit `.env` files to version control
2. **Repository Access**: Use minimal required permissions for GitHub tokens
3. **Jira Permissions**: Use project-specific tokens when possible
4. **Network Security**: Ensure secure connections to Azure OpenAI

## Performance Optimization

1. **Caching**: LLM outputs are cached to reduce API calls
2. **Parallel Processing**: Some tasks can run in parallel
3. **Incremental Indexing**: Only re-index changed files
4. **Model Selection**: Use appropriate models for different tasks

## Support and Maintenance

### Regular Tasks

1. **Update Dependencies**: `pip install -r requirements.txt --upgrade`
2. **Clear Caches**: Remove `*.log` and `workflow_results/` for fresh start
3. **Monitor Quotas**: Check Azure OpenAI usage regularly
4. **Backup Checkpoints**: Archive important workflow results

### Getting Help

1. Check logs for detailed error messages
2. Review this setup guide
3. Test integrations individually
4. Use stub mode for debugging

## Next Steps

After successful setup:

1. **Test with Real Stories**: Try with actual Jira stories
2. **Customize Agents**: Modify prompts and behaviors
3. **Add Monitoring**: Set up alerts and dashboards
4. **Scale Up**: Deploy to production environment 