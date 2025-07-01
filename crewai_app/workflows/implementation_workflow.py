"""
Implementation Workflow
----------------------

To add robust, scalable codebase context to this workflow, use the codebase_indexer module:

    from crewai_app.utils.codebase_indexer import build_directory_tree, agent_select_relevant_files, index_selected_files_async
    tree = build_directory_tree('.')
    selected_files = agent_select_relevant_files(tree, story, agent=None, plugin='semantic')
    code_index = index_selected_files_async('.', selected_files)

You can then pass code_index to LLM prompts for the developer or tester agents.

TODO: Integrate codebase_indexer if/when code context is needed for LLM-driven implementation or testing.
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from crewai_app.agents.developer import developer_tool
from crewai_app.agents.tester import tester_tool
from crewai_app.utils.codebase_indexer import build_directory_tree, agent_select_relevant_files, index_selected_files_async

RESULTS_DIR = "workflow_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def implement_stories_with_tests(stories: List[str]):
    results = []
    for idx, story in enumerate(stories, 1):
        # Developer agent prompt
        dev_prompt = (
            "Given the following user story, generate the Angular code (component, service, and any necessary module) to implement it. "
            "Include TypeScript, HTML, and CSS as needed.\n\n"
            f"User Story:\n{story}\n"
        )
        angular_code = developer_tool._run(dev_prompt)
        # Tester agent prompt
        test_prompt = (
            "Given the following Angular code, generate Jasmine/Karma unit and integration tests (spec.ts) for it. "
            "Cover all acceptance criteria and edge cases.\n\n"
            f"Angular Code:\n{angular_code}\n"
        )
        test_code = tester_tool._run(test_prompt)
        # Save result
        result = {
            "story": story,
            "angular_code": angular_code,
            "test_code": test_code
        }
        results.append(result)
        # Save each story's result to a JSON file
        impl_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = os.path.join(RESULTS_DIR, f"implementation_{idx}_{impl_id}.json")
        with open(fname, "w") as f:
            json.dump(result, f, indent=2)
    return results

if __name__ == "__main__":
    # Example usage: load stories from a file
    with open("workflow_results/stories.json") as f:
        stories_data = json.load(f)
    # If stories are a single string, split by numbered list
    if isinstance(stories_data["stories"], str):
        import re
        stories = re.split(r"\n\d+\. ", "\n" + stories_data["stories"])
        stories = [s.strip() for s in stories if s.strip()]
    else:
        stories = stories_data["stories"]
    implement_stories_with_tests(stories) 