"""Model configuration and initialization utilities."""

from smolagents import LiteLLMModel

def create_ollama_qwen_model(
    model_name: str = "qwen2.5-vl",
    api_base: str = "http://127.0.0.1:11434",
    num_ctx: int = 8192
) -> LiteLLMModel:
    """Create and configure Ollama Qwen2.5-VL model with proper vision support."""
    return LiteLLMModel(
        model_id=f"ollama/{model_name}",  # Use ollama/ prefix instead of ollama_chat/
        api_base=api_base,
        num_ctx=num_ctx,
        temperature=0.1,
        max_tokens=2048,
        supports_vision=True
    )