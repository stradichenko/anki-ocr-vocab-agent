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

    # Construct message for vision processing - improved based on smolagents best practices
    user_message = (
        f"You are a vocabulary extraction specialist. Your task is to analyze the provided vocabulary image "
        f"and extract REAL vocabulary words with their definitions and examples.\n\n"
        f"There are three image scenarios: \n"
        f"1) handwritten notes on vocabulary and some related information to the vocabulary terms; \n"
        f"2) printed text with highlighted words in color blue [vocabulary].\n"
        f"3) just a list of vocabulary words word1, word2, word3.\n\n"

        f"CRITICAL REQUIREMENTS:\n"
        f"1. Extract ONLY what you actually see in the image - no placeholder content\n"
        f"2. DO NOT read the same definition more than once\n"
        f"3. If a word appears multiple times, include it only once\n"
        f"4. DO NOT generate fake content like 'word1', 'word2', 'definition1', 'example1'\n"
        f"5. DO NOT attempt to import Python libraries\n"
        f"6. Focus on complete, meaningful vocabulary entries only\n\n"

        f"EXPECTED INPUT: A vocabulary page containing real words with definitions and example sentences in the same language of the vocabulary word\n\n"

        f"OUTPUT FORMAT: You must format your extracted content as valid YAML with this exact structure:\n"
        f"```yaml\n"
        f"- word: [actual_word_from_image]\n"
        f"  back: '[complete_definition_from_image] (\"[example_sentence_1]\", \"[example_sentence_2]\")'\n"
        f"  tags: [part_of_speech]\n"
        f"```\n\n"
        
        f"IMPORTANT NOTES:\n"
        f"- Use single quotes around the 'back' field value to handle embedded quotes properly\n"
        f"- Include 2-3 example sentences in double quotes within the definition if available\n"
        f"- Valid tags include: noun, verb, adjective, adverb, preposition, conjunction, etc.\n"
        f"- Ensure proper YAML indentation (2 spaces)\n\n"
        
        f"WORKFLOW:\n"
        f"1. Carefully examine the image for vocabulary words and their definitions\n"
        f"2. Extract each word with its complete definition and examples\n"
        f"3. Format the extracted content as YAML following the structure above\n"
        f"4. Once text has been extracted call yaml_to_anki(yaml_content) with your properly formatted YAML string, so it formats the content for Anki\n\n"

        f"ERROR HANDLING:\n"
        f"- If you cannot read text clearly, skip that entry rather than guessing\n"
        f"- If no vocabulary content is found, return an empty YAML list: []\n"
        f"- If YAML formatting fails, double-check quote escaping and indentation\n\n"
        
        f"Remember: Quality over quantity. Extract only what you can clearly read and understand from the image."
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
