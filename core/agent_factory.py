"""Agent factory for creating configured agents."""

from smolagents import CodeAgent
from .model_config import create_ollama_qwen_model
from tools import yaml_to_anki, file_reader, file_writer

def create_vocab_agent(
    model_name: str = "qwen2.5vl:latest",
    api_base: str = "http://127.0.0.1:11434",
    max_steps: int = 5,
    verbosity_level: int = 1
) -> CodeAgent:
    """
    Create a configured vocabulary processing agent with vision support.
    
    Args:
        model_name: Name of the Ollama model to use
        api_base: Ollama API base URL
        max_steps: Maximum steps for agent execution
        verbosity_level: Agent verbosity level
        
    Returns:
        Configured CodeAgent instance with vision capabilities
    """
    model = create_ollama_qwen_model(model_name, api_base)
    
    tools = [yaml_to_anki, file_reader, file_writer]
    
    # Create agent with vision support
    agent = CodeAgent(
        tools=tools,
        model=model,
        max_steps=max_steps,
        verbosity_level=verbosity_level,
        add_base_tools=False,
        additional_authorized_imports=['io', 'yaml', 'PIL']
    )
    
    return agent

# Notes for usage:
# 1. Store YAML content in a variable first, then pass it to yaml_to_anki
# 2. Do NOT wrap YAML content in backticks when calling tools
# 3. Extract REAL content from images, not placeholder examples
# 1. Store YAML content in a variable first, then pass it to yaml_to_anki
# 2. Do NOT wrap YAML content in backticks when calling tools
# 3. Extract REAL content from images, not placeholder examples
