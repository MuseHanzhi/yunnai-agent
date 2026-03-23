from os import path

def read_prompt(prompt_name: str):
    root_path = path.join(path.abspath("."), "prompts")
    prompt_path = path.join(root_path, f"{prompt_name}.md")
    if not path.exists(prompt_path):
        raise FileNotFoundError(prompt_path)
    
    with open(prompt_path, encoding="utf-8") as fs:
        return fs.read()

__all__ = [
    "read_prompt"
]
