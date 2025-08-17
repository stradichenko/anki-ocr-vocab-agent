#!/usr/bin/env python3
"""
vocab_ocr_agent.py

OCR a vocabulary image with a local Ollama Qwen2.5-VL model using smolagents
and convert the extracted YAML into an Anki-ready CSV (anki_cards.csv).

Notes:
 - Requires smolagents with LiteLLM support (pip install "smolagents[litellm]" pyyaml).
 - Ollama server should be running (default http://127.0.0.1:11434).
"""

import os
import sys
import traceback
from PIL import Image

from core.agent_factory import create_vocab_agent
from utils.testing import (
    run_comprehensive_self_test,
    safe_tool_name,
    print_agent_debug_info,
    analyze_csv_output,
)
from tools import yaml_to_anki, file_reader, file_writer


def process_vocab_image(image_path: str):
    """
    Process vocabulary image using smolagents vision capabilities.
    
    Args:
        image_path: Path to the vocabulary image file
        
    Returns:
        Agent execution result
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Create agent with improved configuration
    print("🤖 Creating vocabulary processing agent...")
    agent = create_vocab_agent()
    
    # Print tool information
    tools = [yaml_to_anki, file_reader, file_writer]
    print("Local tool instances:", [safe_tool_name(t) for t in tools])
    
    print("Agent created. Tools reported by agent (best-effort):")
    try:
        print([safe_tool_name(t) for t in getattr(agent, "tools", [])])
    except Exception:
        try:
            print("Raw agent.tools:", agent.tools)
        except Exception as e:
            print("Could not display agent.tools:", e)
            traceback.print_exc()

    # Load image using PIL for smolagents
    print(f"📖 Loading image file: {image_path}")
    try:
        image = Image.open(image_path)
        print(f"✅ Image loaded: {image.size} pixels, mode: {image.mode}")
    except Exception as e:
        print(f"❌ Failed to load image: {e}")
        raise

    # Construct message for vision processing
    user_message = (
        f"Analyze this vocabulary image and extract real vocabulary words, definitions, and examples.\n\n"
        f"CRITICAL: Extract ONLY what you actually see in the image and do it only once. If the word is repeated, skip it."
        f"DO NOT generate placeholder content like 'word1', 'word2', 'definition1'.\n\n"
        f"Format as YAML:\n"
        f"- word: [actual word]\n"
        f"  back: '[real definition] (\"[real example 1]\", \"[real example 2]\")'\n"
        f"  tags: [part of speech]\n\n"
        f"Then call yaml_to_anki(yaml_content) with your extracted YAML."
    )

    print("\n🚀 Starting agent execution with vision...")
    print("📊 Using smolagents native image support...")
    
    try:
        # Use smolagents native vision support with images parameter
        result = agent.run(user_message, images=[image])
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Vision processing failed: {error_msg}")
        
        if "flatten_messages_as_text=True" in error_msg:
            print("🔧 Model configuration issue detected:")
            print("   The LiteLLMModel needs flatten_messages_as_text=False for vision")
            print("   Please check core/model_config.py")
        
        print("🔄 Trying fallback approach...")
        traceback.print_exc()
        
        # Fallback: Try without image
        try:
            fallback_message = (
                f"Process vocabulary from image at {image_path}. "
                f"Extract vocabulary words with definitions and examples. "
                f"Format as YAML and call yaml_to_anki. "
                f"DO NOT generate fake content like 'word1', 'word2'."
            )
            result = agent.run(fallback_message)
            
        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {fallback_error}")
            traceback.print_exc()
            
            # Use testing utility for debug info
            print_agent_debug_info(agent, image_path, image)
            raise

    print("\n✅ Agent execution completed!")
    print("Agent run returned:", result)

    # Use testing utility to analyze output
    analyze_csv_output()

    return result


if __name__ == "__main__":
    run_comprehensive_self_test()
    vocab_image = sys.argv[1] if len(sys.argv) > 1 else "input/vocabulary_page.png"
    print(f"\n🖼️  Processing image: {vocab_image}")
    process_vocab_image(vocab_image)
