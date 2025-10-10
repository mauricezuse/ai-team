import os
import ast
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Set
import hashlib
import aiofiles

try:
    import openai
except ImportError:
    openai = None

"""
codebase_indexer.py
-------------------

A robust, scalable, and extensible codebase indexing utility for AI-driven workflows.

Features:
- Directory tree summarization and exclusion of irrelevant/sensitive files.
- Semantic file selection using LLM/embedding models (SemanticSearchAgent, plugin='semantic').
- Async file indexing for speed (index_selected_files_async).
- Caching for directory trees, file indices, and embeddings.
- Plugin system for custom file selection/indexing strategies.
- Performance logging and error handling.

Typical usage in a workflow:

    from crewai_app.utils.codebase_indexer import build_directory_tree, agent_select_relevant_files, index_selected_files_async
    
    tree = build_directory_tree('.')
    selected_files = agent_select_relevant_files(tree, story, agent=None, plugin='semantic')
    code_index = index_selected_files_async('.', selected_files)

You can use your own agent or plugin for file selection, or use the built-in semantic search (requires OpenAI API key for real embeddings).

To add to a new workflow:
  1. Build the directory tree with build_directory_tree(root_dir)
  2. Select relevant files with agent_select_relevant_files(tree, story, agent=None, plugin='semantic')
  3. Index the selected files with index_selected_files_async(root_dir, selected_files)

See the StoryImplementationWorkflow for a full integration example.
"""

# --- Logging setup ---
logging.basicConfig(
    filename='codebase_indexer.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# --- Configurable patterns and limits ---
DEFAULT_EXCLUDE_DIRS = {'.git', 'venv', '__pycache__', 'node_modules', 'migrations', 'tests'}
DEFAULT_EXCLUDE_FILES = {'__init__.py', '.env', 'secrets.py', 'settings.py', 'config.py'}
DEFAULT_SENSITIVE_PATTERNS = {'.env', 'secrets', 'credential', 'password', 'token', 'key'}
# File extensions to include in indexing
DEFAULT_INCLUDE_EXTENSIONS = {'.py', '.ts', '.js', '.html', '.scss', '.css', '.json', '.yaml', '.yml'}
MAX_FILES_PER_DIR = 20  # For summarization
TREE_CACHE_FILE = 'codebase_tree_cache.json'
INDEX_CACHE_FILE = 'codebase_index_cache.json'
EMBEDDING_CACHE_FILE = 'embedding_cache.json'

# --- Plugin system for file selection/indexing ---
PLUGIN_REGISTRY: dict[str, Callable] = {}

# --- Codebase root resolution ---
CODEBASE_ROOT_DIR: str = os.getcwd()

def set_codebase_root(root_dir: str) -> None:
    global CODEBASE_ROOT_DIR
    CODEBASE_ROOT_DIR = root_dir or CODEBASE_ROOT_DIR

def register_plugin(name: str):
    def decorator(func):
        PLUGIN_REGISTRY[name] = func
        return func
    return decorator

# --- Directory Tree Utilities ---
def should_exclude(path: str, exclude_dirs: Set[str]) -> bool:
    return any(ex in path for ex in exclude_dirs)

def is_sensitive_file(filename: str, sensitive_patterns: Set[str]) -> bool:
    return any(pat in filename for pat in sensitive_patterns)

def build_directory_tree(
    root_dir: str,
    summarize: bool = True,
    exclude_dirs: Set[str] = DEFAULT_EXCLUDE_DIRS,
    exclude_files: Set[str] = DEFAULT_EXCLUDE_FILES,
    sensitive_patterns: Set[str] = DEFAULT_SENSITIVE_PATTERNS,
    include_extensions: Set[str] = DEFAULT_INCLUDE_EXTENSIONS,
    max_files_per_dir: int = MAX_FILES_PER_DIR,
    allowed_dirs: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Build a directory tree of the codebase, optionally summarized for large repos.
    Excludes sensitive files and dirs.
    Only includes directories in allowed_dirs if provided.
    Returns a dict: {relative_dir: [filenames]}
    """
    tree = {}
    for dirpath, _, filenames in os.walk(root_dir):
        rel_dir = os.path.relpath(dirpath, root_dir)
        # Only index allowed dirs if specified
        if allowed_dirs is not None:
            if not any(rel_dir == d or rel_dir.startswith(d + os.sep) for d in allowed_dirs):
                continue
        if should_exclude(dirpath, exclude_dirs):
            continue
        filtered = [f for f in filenames if any(f.endswith(ext) for ext in include_extensions) and f not in exclude_files and not is_sensitive_file(f, sensitive_patterns)]
        if summarize and len(filtered) > max_files_per_dir:
            filtered = filtered[:max_files_per_dir] + [f'...({len(filtered) - max_files_per_dir} more)']
        tree[rel_dir] = filtered
    return tree

def cache_tree(tree: Dict[str, List[str]], cache_file: str = TREE_CACHE_FILE):
    with open(cache_file, 'w') as f:
        json.dump({'tree': tree, 'timestamp': time.time()}, f, indent=2)

def load_cached_tree(cache_file: str = TREE_CACHE_FILE) -> Optional[Dict[str, List[str]]]:
    if not os.path.exists(cache_file):
        return None
    with open(cache_file, 'r') as f:
        data = json.load(f)
    return data['tree']

# --- Incremental Indexing using Git ---
def get_recently_changed_files(root_dir: str, n_commits: int = 1) -> List[str]:
    """
    Return a list of files changed in the last n_commits using git diff.
    """
    import subprocess
    try:
        result = subprocess.run(
            ["git", "-C", root_dir, "diff", "--name-only", f"HEAD~{n_commits}..HEAD"],
            capture_output=True, text=True
        )
        files = [line.strip() for line in result.stdout.splitlines() if line.strip() and any(line.strip().endswith(ext) for ext in DEFAULT_INCLUDE_EXTENSIONS)]
        return files
    except Exception as e:
        logging.warning(f"Git diff failed: {e}")
        return []

# --- Semantic Search Stub ---
def semantic_search(files: List[str], story: str) -> List[str]:
    """
    Placeholder for semantic search using embeddings.
    TODO: Integrate with OpenAI/Cohere/other embedding models.
    For now, returns all files containing any word from the story.
    """
    keywords = set(story.lower().split())
    relevant = [f for f in files if any(kw in f.lower() for kw in keywords)]
    return relevant if relevant else files[:10]  # fallback: top 10

# --- Summarization Stub ---
def summarize_file_content(content: str, max_length: int = 500) -> str:
    """
    Placeholder for LLM-based or heuristic summarization of large files.
    TODO: Integrate with LLM for real summarization.
    """
    lines = content.splitlines()
    if len(lines) > max_length:
        return '\n'.join(lines[:max_length]) + '\n... (truncated)'
    return content

# --- Async File Indexing ---
async def async_parse_file(file_path: str, rel_path: str) -> Optional[dict]:
    try:
        if not os.path.exists(file_path):
            abs_path = os.path.abspath(file_path)
            logging.error(f"async_parse_file: file does not exist: {abs_path}")
            raise FileNotFoundError(abs_path)
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Handle different file types
        if rel_path.endswith('.py'):
            # Python files - use AST parsing
            tree = ast.parse(content, filename=rel_path)
            file_info = {'classes': [], 'functions': []}
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    file_info['classes'].append({
                        'name': node.name,
                        'docstring': ast.get_docstring(node)
                    })
                elif isinstance(node, ast.FunctionDef):
                    file_info['functions'].append({
                        'name': node.name,
                        'docstring': ast.get_docstring(node)
                    })
        else:
            # Non-Python files - just store content summary
            file_info = {
                'content_preview': content[:500] + ('...' if len(content) > 500 else ''),
                'file_type': rel_path.split('.')[-1] if '.' in rel_path else 'unknown'
            }
        
        return rel_path, file_info
    except Exception as e:
        logging.warning(f"Failed to parse {rel_path}: {e}")
        return None

async def async_index_selected_files(root_dir: str, selected_files: List[str]) -> Dict[str, dict]:
    tasks = []
    for rel_path in selected_files:
        file_path = os.path.join(root_dir, rel_path)
        tasks.append(async_parse_file(file_path, rel_path))
    results = await asyncio.gather(*tasks)
    return {rel_path: info for rel_path, info in results if info}

# --- File Indexing Utilities (sync fallback) ---
def index_selected_files(root_dir: str, selected_files: List[str], use_cache: bool = True) -> Dict[str, dict]:
    """
    Parse and index only the selected files (relative to root_dir).
    Returns a dict: {rel_path: {'classes': [...], 'functions': [...]}}
    Uses a cache if available and up-to-date.
    """
    code_index = {}
    cache = load_cached_index()
    for rel_path in selected_files:
        file_path = os.path.join(root_dir, rel_path)
        try:
            if not os.path.exists(file_path):
                abs_path = os.path.abspath(file_path)
                logging.error(f"index_selected_files: file does not exist: {abs_path}")
                raise FileNotFoundError(abs_path)
            mtime = os.path.getmtime(file_path)
            if use_cache and cache and rel_path in cache and cache[rel_path]['mtime'] == mtime:
                code_index[rel_path] = cache[rel_path]['index']
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Summarize if large
            content = summarize_file_content(content)
            
            # Handle different file types
            if rel_path.endswith('.py'):
                # Python files - use AST parsing
                tree = ast.parse(content, filename=rel_path)
                file_info = {'classes': [], 'functions': []}
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, ast.ClassDef):
                        file_info['classes'].append({
                            'name': node.name,
                            'docstring': ast.get_docstring(node)
                        })
                    elif isinstance(node, ast.FunctionDef):
                        file_info['functions'].append({
                            'name': node.name,
                            'docstring': ast.get_docstring(node)
                        })
            else:
                # Non-Python files - just store content summary
                file_info = {
                    'content_preview': content[:500] + ('...' if len(content) > 500 else ''),
                    'file_type': rel_path.split('.')[-1] if '.' in rel_path else 'unknown'
                }
            code_index[rel_path] = file_info
            # Update cache
            if use_cache:
                update_index_cache(rel_path, file_info, mtime)
        except Exception as e:
            logging.debug(f"Failed to index {rel_path}: {e}")
            continue
    return code_index

def update_index_cache(rel_path: str, file_info: dict, mtime: float, cache_file: str = INDEX_CACHE_FILE):
    cache = load_cached_index(cache_file) or {}
    cache[rel_path] = {'index': file_info, 'mtime': mtime}
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)

def load_cached_index(cache_file: str = INDEX_CACHE_FILE) -> Optional[dict]:
    if not os.path.exists(cache_file):
        return None
    with open(cache_file, 'r') as f:
        return json.load(f)

# --- Embedding Utilities ---
def get_embedding(text: str, model: str = 'text-embedding-ada-002') -> list:
    """
    Get embedding for text using OpenAI API, with caching. Compatible with openai>=1.0.0.
    """
    if not text or not text.strip():
        logging.error("get_embedding called with empty or whitespace-only input. Aborting embedding call.")
        raise RuntimeError("get_embedding called with empty or whitespace-only input.")
    cache = load_embedding_cache()
    key = hashlib.sha256((model + text).encode('utf-8')).hexdigest()
    if cache and key in cache:
        return cache[key]
    if not openai:
        return []  # fallback if openai not installed
    try:
        # For openai>=1.0.0
        if hasattr(openai, 'embeddings') and hasattr(openai.embeddings, 'create'):
            resp = openai.embeddings.create(input=[text], model=model)
            vec = resp.data[0].embedding
        # For openai>=1.0.0 (resource style)
        elif hasattr(openai, 'resources') and hasattr(openai.resources, 'embeddings'):
            resp = openai.resources.embeddings.create(input=[text], model=model)
            vec = resp.data[0].embedding
        # For openai<1.0.0
        else:
            resp = openai.Embedding.create(input=[text], model=model)
            vec = resp['data'][0]['embedding']
        update_embedding_cache(key, vec)
        return vec
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        raise RuntimeError(f"Embedding failed: {e}")

def load_embedding_cache(cache_file: str = EMBEDDING_CACHE_FILE) -> Optional[dict]:
    if not os.path.exists(cache_file):
        return None
    with open(cache_file, 'r') as f:
        return json.load(f)

def update_embedding_cache(key: str, vec: list, cache_file: str = EMBEDDING_CACHE_FILE):
    cache = load_embedding_cache(cache_file) or {}
    cache[key] = vec
    with open(cache_file, 'w') as f:
        json.dump(cache, f)

# --- Cosine Similarity ---
def cosine_similarity(a: list, b: list) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(y*y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

# --- Semantic Search Agent (real embedding) ---
class SemanticSearchAgent:
    """
    Semantic search agent for file selection using OpenAI embeddings.
    Caches embeddings for speed. Falls back to keyword search if openai not available.
    """
    def __init__(self, embedder: Callable[[str], list] = get_embedding, model: str = 'text-embedding-ada-002'):
        self.embedder = embedder
        self.model = model

    def summarize_file(self, file_path: str, max_lines: int = 50) -> str:
        try:
            if not os.path.exists(file_path):
                abs_path = os.path.abspath(file_path)
                logging.error(f"summarize_file: file does not exist: {abs_path}")
                raise FileNotFoundError(abs_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return ''.join(lines[:max_lines])
        except Exception as e:
            logging.debug(f"Failed to summarize {file_path}: {e}")
            return ''

    def select_relevant_files(self, tree: Dict[str, List[str]], story: str, prompt: str = None, top_k: int = 10) -> list:
        if not openai:
            # fallback to stub
            all_files = [os.path.join(d, f) for d, files in tree.items() for f in files if not f.startswith('...')]
            ranked = semantic_search(all_files, story)
            return ranked[:top_k]
        # Embed the story
        if not story or not story.strip():
            logging.warning("[SemanticSearchAgent] Story input to embedding is empty or whitespace. Skipping embedding.")
            return []
        story_emb = self.embedder(story, self.model)
        if not story_emb:
            return []
        # Embed each file summary
        scored = []
        for d, files in tree.items():
            for f in files:
                if f.startswith('...'):
                    continue
                rel_path = os.path.join(d, f)
                if not os.path.exists(rel_path):
                    abs_path = os.path.abspath(rel_path)
                    logging.error(f"select_relevant_files: file does not exist: {abs_path}")
                    raise FileNotFoundError(abs_path)
                summary = self.summarize_file(rel_path)
                if not summary or not summary.strip():
                    logging.debug(f"[SemanticSearchAgent] File summary for {rel_path} is empty or whitespace. Skipping embedding.")
                    continue
                file_emb = self.embedder(summary, self.model)
                sim = cosine_similarity(story_emb, file_emb)
                scored.append((sim, rel_path))
        scored.sort(reverse=True)
        return [rel_path for sim, rel_path in scored[:top_k]]

# --- Register semantic plugin ---
@register_plugin('semantic')
def semantic_plugin(tree: Dict[str, List[str]], story: str) -> list:
    agent = SemanticSearchAgent()
    return agent.select_relevant_files(tree, story)

# --- Async Indexing Wrapper ---
def index_selected_files_async(root_dir: str, selected_files: List[str]) -> Dict[str, dict]:
    """
    Index selected files using async parsing for speed. Falls back to sync if asyncio fails.
    """
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_index_selected_files(root_dir, selected_files))
    except Exception as e:
        logging.info(f"Async indexing failed, falling back to sync: {e}")
        return index_selected_files(root_dir, selected_files)

# --- Agent-Driven File Selection ---
def agent_select_relevant_files(tree: Dict[str, List[str]], story: str, agent: Any, plugin: Optional[str] = None) -> list:
    """
    Use an LLM agent or plugin to select relevant files from a directory tree for a given story/task.
    If semantic search fails or returns an empty list, select all .py files as a fallback.
    Args:
        tree: Directory tree as returned by build_directory_tree.
        story: The story or task description.
        agent: An agent object with a .select_relevant_files(tree, story) method, or a callable.
        plugin: Optional plugin name for custom selection logic.
    Returns:
        List of relative file paths selected by the agent or plugin.
    """
    try:
        if plugin and plugin in PLUGIN_REGISTRY:
            selected = PLUGIN_REGISTRY[plugin](tree, story)
        else:
            prompt = (
                "Given the following directory tree and the story/task description, "
                "select the most relevant files (as a list of relative file paths) needed to implement or update for this story.\n"
                f"Story/Task: {story}\n"
                f"Directory tree: {tree}\n"
                "Return a Python list of file paths."
            )
            if hasattr(agent, 'select_relevant_files'):
                selected = agent.select_relevant_files(tree, story, prompt=prompt)
            elif callable(agent):
                selected = agent(tree, story, prompt=prompt)
            else:
                raise ValueError("Agent must be callable or have a select_relevant_files method.")
        # Fallback: if selection fails or is empty, select all relevant files
        if not selected:
            logging.warning("File selection returned empty. Falling back to all relevant files in the repo.")
            selected = [os.path.join(d, f) for d, files in tree.items() for f in files if any(f.endswith(ext) for ext in DEFAULT_INCLUDE_EXTENSIONS) and not f.startswith('...')]
        return selected
    except Exception as e:
        logging.warning(f"File selection failed: {e}. Falling back to all relevant files in the repo.")
        return [os.path.join(d, f) for d, files in tree.items() for f in files if any(f.endswith(ext) for ext in DEFAULT_INCLUDE_EXTENSIONS) and not f.startswith('...')]

# --- Example LLM Agent Interface ---
class LLMAgent:
    """
    Example LLM agent interface for file selection. Replace with your own LLM integration.
    """
    def __init__(self, llm_callable: Callable[[str], str]):
        self.llm_callable = llm_callable

    def select_relevant_files(self, tree: Dict[str, List[str]], story: str, prompt: str = None) -> list:
        if prompt is None:
            prompt = f"Story: {story}\nDirectory tree: {tree}\nReturn a list of relevant file paths."
        response = self.llm_callable(prompt)
        # Expecting a Python list in the response
        try:
            selected = eval(response, {"__builtins__": {}})
            if isinstance(selected, list):
                return selected
        except Exception:
            pass
        return []

# --- Main for CLI/manual testing ---
def main():
    import sys
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    story = sys.argv[2] if len(sys.argv) > 2 else 'Implement user authentication.'
    print("Building/summarizing directory tree...")
    tree = build_directory_tree(root_dir)
    cache_tree(tree)
    print(json.dumps(tree, indent=2))
    # Example: use a dummy agent that selects all files in 'auth' or 'user' dirs
    class DummyAgent:
        def select_relevant_files(self, tree, story, prompt=None):
            return [os.path.join(d, f) for d, files in tree.items() for f in files if 'auth' in d or 'user' in d]
    agent = DummyAgent()
    selected_files = agent_select_relevant_files(tree, story, agent)
    print("Selected files:", selected_files)
    code_index = index_selected_files(root_dir, selected_files)
    print(json.dumps(code_index, indent=2))

if __name__ == '__main__':
    main() 