import re

def strip_code_fences(s):
    """
    Remove triple backticks and any language tag (e.g., ```python) from LLM output.
    Handles leading/trailing whitespace and works for both single-line and multi-line code fences.
    """
    return re.sub(r"^```[a-zA-Z]*\s*|```$", "", s.strip(), flags=re.MULTILINE)

# --- Unit Tests ---
def _test_strip_code_fences():
    cases = [
        ("""```python\nprint('hello')\n```""", "print('hello')"),
        ("""```\nprint('hello')\n```""", "print('hello')"),
        ("print('hello')", "print('hello')"),
        ("""   ```json\n[1,2,3]\n```   """, "[1,2,3]"),
        ("""```PYTHON\ndef foo(): pass\n```""", "def foo(): pass"),
        ("""\n```python\nprint('hi')\n```\n""", "print('hi')"),
        ("""\n```\nprint('hi')\n```\n""", "print('hi')"),
        ("""\nprint('hi')\n""", "print('hi')"),
    ]
    for i, (inp, expected) in enumerate(cases):
        out = strip_code_fences(inp)
        assert out == expected, f"Test case {i} failed: got {out!r}, expected {expected!r}"
    print("All strip_code_fences tests passed.")

if __name__ == "__main__":
    _test_strip_code_fences() 