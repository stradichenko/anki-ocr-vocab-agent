"""Model configuration and initialization utilities."""

from smolagents import LiteLLMModel

def create_ollama_qwen_model(
    model_name: str = "qwen2.5vl:latest",
    api_base: str = "http://127.0.0.1:11434",
    num_ctx: int = 8192
) -> LiteLLMModel:
    """Create and configure Ollama Qwen2.5-VL model with optimized VLM settings."""
    return LiteLLMModel(
        model_id=f"ollama_chat/{model_name}",
        api_base=api_base,
        num_ctx=num_ctx,
        # Add temperature for more consistent output and better image reading
        temperature=0.1,
        # Ensure proper vision capabilities
        supports_vision=True
    )
