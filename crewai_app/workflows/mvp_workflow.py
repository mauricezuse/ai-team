import logging
import json
import os
from datetime import datetime
from crewai_app.agents.pm import pm_tool
from crewai_app.agents.architect import architect_tool
from crewai_app.agents.developer import developer_tool
from crewai_app.agents.reviewer import reviewer_tool
from crewai_app.agents.tester import tester_tool
from crewai_app.services.github_service import GitHubService
from crewai_app.services.jira_service import JiraService
from crewai_app.config import settings
from crewai_app.utils.codebase_indexer import build_directory_tree, agent_select_relevant_files, index_selected_files_async

# Setup logging
logging.basicConfig(
    filename='mvp_workflow.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

RESULTS_DIR = "workflow_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

github_service = GitHubService(settings.use_real_github)
jira_service = JiraService(settings.use_real_jira)

def run_mvp_workflow(feature: str):
    logging.info(f"Starting workflow for feature: {feature}")
    result = {"feature": feature, "revision_cycles": 0, "jira_ticket_url": None}
    try:
        pm_prompt = (
            f"Given the following product feature, break it down into clear, testable user stories with acceptance criteria.\n"
            f"Feature: {feature}\n"
            f"Format the output as a numbered list, and for each user story, include a short description and acceptance criteria."
        )
        pm_output = pm_tool._run(pm_prompt)
        result["pm"] = pm_output
        logging.info(f"[PM Output] {pm_output}")
        # Create Jira ticket using service
        jira_ticket = jira_service.create_ticket(f"Feature: {feature}", pm_output)
        result["jira_ticket_url"] = jira_ticket["url"] if jira_ticket else None
    except Exception as e:
        result["pm_error"] = str(e)
        logging.error(f"PM error: {e}")
        return result
    try:
        architect_prompt = (
            f"Given these user stories:\n{pm_output}\n"
            f"Design a high-level software architecture for a web platform that implements these stories.\n"
            f"Include:\n- Main components/services\n- Key data models (with fields)\n- API endpoints (with methods and paths)\n- Any important workflows or interactions\n"
            f"Format your answer with clear sections and code blocks for models and APIs."
        )
        architect_output = architect_tool._run(architect_prompt)
        result["architect"] = architect_output
        logging.info(f"[Architect Output] {architect_output}")
    except Exception as e:
        result["architect_error"] = str(e)
        logging.error(f"Architect error: {e}")
        return result
    # Feedback loop variables
    feedback_round = 0
    max_feedback_rounds = 2
    reviewer_feedback = ""
    tester_feedback = ""
    while True:
        feedback_round += 1
        result["revision_cycles"] = feedback_round - 1
        try:
            developer_prompt = (
                f"Given this architecture design:\n{architect_output}\n"
                f"Write a sample implementation for the main backend API (in Python/FastAPI or Node/Express, your choice).\n"
                f"Include:\n- Data model definitions\n- At least one API endpoint implementation\n- Any necessary configuration or setup code\n"
                f"Format your answer as code blocks with comments."
            )
            # If this is a revision, add Reviewer/Tester feedback to the prompt
            if reviewer_feedback or tester_feedback:
                developer_prompt += ("\n\n[Revision Context] Please address the following feedback before revising your code:\n"
                                    f"Reviewer feedback: {reviewer_feedback}\n"
                                    f"Tester feedback: {tester_feedback}\n")
            developer_output = developer_tool._run(developer_prompt)
            result["developer"] = developer_output
            logging.info(f"[Developer Output] {developer_output}")
        except Exception as e:
            result["developer_error"] = str(e)
            logging.error(f"Developer error: {e}")
            return result
        try:
            reviewer_prompt = (
                f"Review the following code for correctness, style, and best practices.\n"
                f"- Identify any bugs, security issues, or code smells\n- Suggest improvements or refactoring\n- Comment on code structure and documentation\n"
                f"Code:\n{developer_output}"
            )
            reviewer_output = reviewer_tool._run(reviewer_prompt)
            result["reviewer"] = reviewer_output
            logging.info(f"[Reviewer Output] {reviewer_output}")
        except Exception as e:
            result["reviewer_error"] = str(e)
            logging.error(f"Reviewer error: {e}")
            return result
        try:
            dev_code_lines = developer_output.splitlines()
            short_code = "\n".join(dev_code_lines[:40])
            tester_prompt = (
                f"Write comprehensive unit and integration tests for the following code.\n"
                f"If the code is too long, just write a test for the main function or class.\n"
                f"- Use a modern testing framework (e.g., pytest for Python, Jest for Node)\n- Cover both typical and edge cases\n- Include comments explaining each test\n"
                f"Code:\n{short_code}"
            )
            tester_output = tester_tool._openai_service.generate(tester_prompt, max_tokens=512, step="mvp_workflow.tester")
            if not tester_output.strip():
                tester_output = "[Tester Warning] No output generated. The code may be too long or the model context window was exceeded. Try sending a smaller code snippet."
            result["tester"] = tester_output
            logging.info(f"[Tester Output] {tester_output}")
        except Exception as e:
            result["tester_error"] = str(e)
            logging.error(f"Tester error: {e}")
        # Feedback loop: check for issues in reviewer or tester output
        feedback_needed = False
        reviewer_feedback = reviewer_output if ("bug" in reviewer_output.lower() or "issue" in reviewer_output.lower() or "improvement" in reviewer_output.lower()) else ""
        tester_feedback = tester_output if ("fail" in tester_output.lower() or "error" in tester_output.lower()) else ""
        feedback_reason = ""
        if reviewer_feedback:
            feedback_needed = True
            feedback_reason = "Reviewer found issues."
        if tester_feedback:
            feedback_needed = True
            feedback_reason = feedback_reason + " Tester found errors." if feedback_reason else "Tester found errors."
        if feedback_needed and feedback_round < max_feedback_rounds:
            logging.info(f"[Feedback Loop] {feedback_reason} Developer will revise and workflow will re-run from Developer step (round {feedback_round+1}).")
            print(f"[Feedback Loop] {feedback_reason} Developer will revise and workflow will re-run from Developer step (round {feedback_round+1}).")
            continue  # Re-run Developer and downstream steps
        break  # No feedback or max rounds reached
    return result

def run_sprint(features):
    sprint_results = []
    sprint_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = {
        "sprint_id": sprint_id,
        "total_features": len(features),
        "features_passed_first_try": 0,
        "features_with_revisions": 0,
        "feature_results": []
    }
    for i, feature in enumerate(features, 1):
        logging.info(f"\n=== Sprint Feature {i}: {feature} ===")
        result = run_mvp_workflow(feature)
        sprint_results.append(result)
        # Save each feature's result to a JSON file
        fname = os.path.join(RESULTS_DIR, f"feature_{i}_{sprint_id}.json")
        with open(fname, "w") as f:
            json.dump(result, f, indent=2)
        logging.info(f"Saved results to {fname}")
        # Update summary
        if result.get("revision_cycles", 0) == 0:
            summary["features_passed_first_try"] += 1
        else:
            summary["features_with_revisions"] += 1
        summary["feature_results"].append({
            "feature": feature,
            "jira_ticket_url": result.get("jira_ticket_url"),
            "revision_cycles": result.get("revision_cycles", 0)
        })
    # Save sprint summary
    summary_file = os.path.join(RESULTS_DIR, f"sprint_summary_{sprint_id}.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    logging.info(f"Sprint summary saved to {summary_file}")
    return sprint_results

if __name__ == "__main__":
    features = [
        "User can post a job and receive bids from freelancers",
        "User can message freelancers and negotiate terms",
        "User can leave feedback for completed jobs"
    ]
    run_sprint(features)

"""
MVP Workflow
------------

To add robust, scalable codebase context to this workflow, use the codebase_indexer module:

    from crewai_app.utils.codebase_indexer import build_directory_tree, agent_select_relevant_files, index_selected_files_async
    tree = build_directory_tree('.')
    selected_files = agent_select_relevant_files(tree, feature, agent=None, plugin='semantic')
    code_index = index_selected_files_async('.', selected_files)

You can then pass code_index to LLM prompts for the developer, reviewer, or tester agents.

TODO: Integrate codebase_indexer if/when code context is needed for LLM-driven implementation, review, or testing.
""" 