import os
import json
import logging
from datetime import datetime
from crewai_app.agents.pm import pm_tool
from crewai_app.agents.architect import architect_tool
from typing import Optional

RESULTS_DIR = "workflow_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

logging.basicConfig(
    filename='planning_workflow.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def run_planning_workflow(product_vision: str, feature_name: Optional[str] = None):
    result = {"product_vision": product_vision}
    try:
        pm_prompt = (
            "Given the following product vision, break it down into clear, testable user stories with acceptance criteria.\n"
            f"Product Vision: {product_vision}\n"
            "Format the output as a numbered list, and for each user story, include a short description and acceptance criteria."
        )
        pm_output = pm_tool._run(pm_prompt)
        result["user_stories"] = pm_output
        logging.info(f"[PM Output] {pm_output}")
    except Exception as e:
        result["pm_error"] = str(e)
        logging.error(f"PM error: {e}")
        return result
    try:
        architect_prompt = (
            f"Given these user stories:\n{pm_output}\n"
            "Design a high-level software architecture for a web platform that implements these stories.\n"
            "Include:\n- Main components/services\n- Key data models (with fields)\n- API endpoints (with methods and paths)\n- Any important workflows or interactions\n"
            "Format your answer with clear sections and code blocks for models and APIs."
        )
        architect_output = architect_tool._run(architect_prompt)
        result["architecture"] = architect_output
        logging.info(f"[Architect Output] {architect_output}")
    except Exception as e:
        result["architect_error"] = str(e)
        logging.error(f"Architect error: {e}")
    # Save results
    planning_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = os.path.join(
        RESULTS_DIR,
        f"planning_{feature_name or 'main'}_{planning_id}.json"
    )
    with open(fname, "w") as f:
        json.dump(result, f, indent=2)
    logging.info(f"Planning results saved to {fname}")
    return result

if __name__ == "__main__":
    product_vision = (
        "Build a web platform where clients can post freelance jobs, freelancers can bid, message, deliver work, and both parties can leave feedback. "
        "The platform should support user profiles, job listings, messaging, payments, and reviews."
    )
    run_planning_workflow(product_vision, feature_name="freelancer_app") 