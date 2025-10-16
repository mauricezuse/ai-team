from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings

class PMTool(BaseTool):
    name: str = "pm_tool"
    description: str = "Breaks down features into user stories using OpenAI."
    _openai_service: OpenAIService = PrivateAttr()

    def __init__(self, openai_service):
        super().__init__()
        self._openai_service = openai_service

    def _run(self, prompt: str) -> str:
        return self._openai_service.generate(prompt)

    def greet(self):
        return self._run("Say hello from the Product Manager agent!")

    def suggest(self, prompt: str) -> str:
        """Suggest improvements or actions based on the given prompt."""
        return self._openai_service.generate(prompt, step="pm.suggest")

class PMAgent:
    def __init__(self):
        self.conversation_service = None  # Will be set by workflow
    
    def review_story(self, story, workflow_id=None, conversation_id=None):
        # Use the LLM to analyze the Jira story and generate acceptance criteria, clarifications, and improvements
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        prompt = (
            f"Given the following Jira story, extract and clarify acceptance criteria, "
            f"identify ambiguities, and suggest improvements.\n"
            f"Story Description: {description}\n"
            f"Summary: {summary}\n"
            f"Output a Python dict with keys: 'acceptance_criteria', 'clarifications', 'improvements'."
        )
        
        # Persist user message if conversation service available
        if self.conversation_service:
            self.conversation_service.append_message(
                role="user",
                content=prompt,
                metadata={"step": "pm.review_story", "agent": "pm", "workflow_id": workflow_id}
            )
        
        # Use OpenAIService directly with LLM tracking context
        suggestions_str = pm_openai.generate(
            prompt,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            step='pm.review_story'
        )
        
        # Persist assistant response if conversation service available
        if self.conversation_service:
            self.conversation_service.append_message(
                role="assistant",
                content=suggestions_str,
                metadata={"step": "pm.review_story", "agent": "pm", "workflow_id": workflow_id}
            )
        
        try:
            suggestions = eval(suggestions_str, {"__builtins__": {}})
            if isinstance(suggestions, dict):
                return suggestions
        except Exception:
            pass
        # Fallback stub
        suggestions = {
            "acceptance_criteria": ["Acceptance criteria not extracted."],
            "clarifications": ["Clarify acceptance criteria."],
            "improvements": ["Add more detail to the description."]
        }
        return suggestions

pm_openai = OpenAIService(deployment=settings.deployment_pm)
pm_tool = PMTool(pm_openai)
pm = Agent(
    role="Product Manager",
    goal="Break down high-level features into clear, testable user stories.",
    backstory="A detail-oriented PM who ensures clarity and testability in every story.",
    tools=[pm_tool],
)

if __name__ == "__main__":
    print("PM says:", pm_tool.greet()) 