import os
import json
import logging
from datetime import datetime
from crewai_app.agents.pm import pm_tool
from crewai_app.agents.architect import architect_tool
from typing import Optional, Dict

RESULTS_DIR = "workflow_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

logging.basicConfig(
    filename='planning_workflow.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def run_planning_and_design(product_vision: str) -> Dict:
    result = {"product_vision": product_vision}
    try:
        # 1. Architecture document
        architect_prompt = (
            "Given the following product vision, write a high-level architecture document for a web platform.\n"
            f"Product Vision: {product_vision}\n"
            "Include: goals, main components/services, data flow, and technology choices."
        )
        architecture_doc = architect_tool._run(architect_prompt)
        result["architecture_doc"] = architecture_doc
        logging.info(f"[Architecture Doc] {architecture_doc}")
        # 2. Component list
        component_prompt = (
            f"Given this architecture document:\n{architecture_doc}\n"
            "List all required components/services as a bullet list, with a 1-sentence description for each."
        )
        component_list = architect_tool._run(component_prompt)
        result["component_list"] = component_list
        logging.info(f"[Component List] {component_list}")
        # 3. Architecture diagram (Mermaid)
        mermaid_arch_prompt = (
            f"Given this architecture document:\n{architecture_doc}\n"
            "Generate a Mermaid diagram (flowchart or graph) showing the main components and their relationships.\n"
            "Return only the Mermaid code block."
        )
        architecture_mermaid = architect_tool._run(mermaid_arch_prompt)
        result["architecture_mermaid"] = architecture_mermaid
        logging.info(f"[Architecture Mermaid] {architecture_mermaid}")
        # 4. C4 diagram (Mermaid)
        mermaid_c4_prompt = (
            f"Given this architecture document:\n{architecture_doc}\n"
            "Generate a Mermaid C4 diagram (using C4-PlantUML syntax if possible) for the system.\n"
            "Return only the Mermaid code block."
        )
        c4_mermaid = architect_tool._run(mermaid_c4_prompt)
        result["c4_mermaid"] = c4_mermaid
        logging.info(f"[C4 Mermaid] {c4_mermaid}")
    except Exception as e:
        result["error"] = str(e)
        logging.error(f"Planning & design error: {e}")
    # Save results
    planning_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = os.path.join(
        RESULTS_DIR,
        f"planning_{planning_id}.json"
    )
    with open(fname, "w") as f:
        json.dump(result, f, indent=2)
    logging.info(f"Planning results saved to {fname}")
    return result

def generate_stories(design_docs: str, additional_context: Optional[str] = None):
    endpoints = """
    Available API endpoints:
    - POST /plan-and-design: Generate architecture, component list, and diagrams from product vision.
    - POST /generate-stories: Generate user stories with story points from design docs.
    - POST /gap-analysis: Compare Jira and generated stories, return gap analysis.
    - GET /health: Health check.
    """
    prompt = (
        "Given the following design documents and the available API endpoints, generate a list of user stories for implementation.\n"
        f"Design Documents:\n{design_docs}\n"
        f"{endpoints}\n"
    )
    if additional_context:
        prompt += f"\nAdditional context: {additional_context}\n"
    prompt += (
        "For each user story, include:\n"
        "- The relevant API endpoint(s) (from the list above)\n"
        "- A short title\n"
        "- A detailed description\n"
        "- Acceptance criteria\n"
        "- Story points (1 = half day, 2 = 1 day)\n"
        "Format the output as a numbered list, with each story clearly separated and all required fields included."
    )
    stories = pm_tool._run(prompt)
    result = {"stories": stories}
    # Save to file
    story_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = os.path.join(RESULTS_DIR, f"stories_{story_id}.json")
    with open(fname, "w") as f:
        json.dump(result, f, indent=2)
    return result

def gap_analysis(jira_stories: list, generated_stories: list):
    prompt = (
        "You are a Product Manager. Compare the following two lists of user stories.\n"
        "List A: Stories already in Jira:\n" + "\n".join(jira_stories) + "\n"
        "List B: Newly generated stories:\n" + "\n".join(generated_stories) + "\n"
        "Draft a gap analysis report that includes:\n"
        "- Stories in List B missing from List A (potential gaps)\n"
        "- Stories in List A missing from List B (potential redundancies or outdated)\n"
        "- Any unclear or ambiguous stories\n"
        "- Recommendations for next steps\n"
        "Format the output with clear sections."
    )
    report = pm_tool._run(prompt)
    result = {"gap_analysis": report}
    # Save to file
    gap_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = os.path.join(RESULTS_DIR, f"gap_analysis_{gap_id}.json")
    with open(fname, "w") as f:
        json.dump(result, f, indent=2)
    return result

if __name__ == "__main__":
    product_vision = (
        "Build a web platform where clients can post freelance jobs, freelancers can bid, message, deliver work, and both parties can leave feedback. "
        "The platform should support user profiles, job listings, messaging, payments, and reviews."
    )
    run_planning_and_design(product_vision) 