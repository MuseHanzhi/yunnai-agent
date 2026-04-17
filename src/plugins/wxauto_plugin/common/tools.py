import yaml
from os import path
from ..types import *

root_path = path.join(path.dirname(__file__), "..")

def parse_yaml(file_path) -> Config:
    with open(path.join(root_path, file_path), 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data

def read_prompt(prompt_name: str):
    """
    Read prompt from prompts.yaml
    """
    prompt_file_path = path.join(root_path, "prompts", f"{prompt_name}.md")
    try:
        with open(prompt_file_path, encoding="utf-8") as fs:
            return fs.read()
    except FileNotFoundError:
        raise FileNotFoundError(prompt_file_path)
