#!/usr/bin/env python3
"""
vocab_ocr_agent.py

OCR a vocabulary image with a local Ollama Qwen2.5-VL model (via LiteLLMModel)
and convert the extracted YAML into an Anki-ready CSV (anki_cards.csv).

Notes:
 - Requires smolagents with LiteLLM support (pip install "smolagents[litellm]" pyyaml).
 - Ollama server should be running (default http://127.0.0.1:11434).
"""

import os
import sys
import traceback

from config.prompts import OCR_PROMPT
from core.agent_factory import create_vocab_agent
from utils.testing import run_comprehensive_self_test, safe_tool_name
from tools import yaml_to_anki, file_reader, file_writer

def process_vocab_image(image_path: str):
    """
    Process vocabulary image using the configured agent.
    
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

    # Enhanced query that strongly prohibits fake content and imports
    query = (
        f"EXAMINE THIS SPECIFIC IMAGE: {image_path}\n\n"
        f"🔍 LOOK AT THE IMAGE AND TELL ME:\n"
        f"- What vocabulary words do you actually see?\n"
        f"- What definitions are visible?\n"
        f"- What example sentences are shown?\n\n"
        f"🚫 DO NOT USE PLACEHOLDER TEXT like:\n"
        f"- 'real_word_you_see'\n"
        f"- 'actual_word_from_image'\n"
        f"- 'example_word'\n\n"
        f"✅ EXTRACT ONLY REAL WORDS YOU CAN READ\n\n"
        f"{OCR_PROMPT}\n\n"
        f"Now examine the image and describe what vocabulary you actually see, then extract it."
    )

    print("\n🚀 Starting agent execution...")
    try:
        result = agent.run(query)
    except Exception as e:
        print(f"❌ Agent run raised an exception: {e}")
        traceback.print_exc()
        
        # Try to provide helpful debugging information
        print("\n🔍 Debugging information:")
        print(f"   📁 Working directory: {os.getcwd()}")
        print(f"   📄 Image exists: {os.path.exists(image_path)}")
        if os.path.exists(image_path):
            print(f"   📏 Image size: {os.path.getsize(image_path)} bytes")
        
        raise
    
    print("\n✅ Agent execution completed!")
    print("Agent run returned:", result)
    
    # Check if CSV was actually created and analyze the content
    csv_path = "anki_cards.csv"
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.strip().split('\n')
        print(f"📊 Generated CSV with {len(lines)} lines (including header)")
        print(f"📄 Output file: {os.path.abspath(csv_path)}")
        
        # Show a preview of the generated content
        if len(lines) > 1:
            print("\n📋 Generated vocabulary preview:")
            for i, line in enumerate(lines[:4]):  # Show first few lines
                if i == 0:
                    print(f"   Header: {line}")
                else:
                    # Parse CSV line to show word
                    try:
                        word = line.split(',')[0]
                        print(f"   Word {i}: {word}")
                    except:
                        print(f"   Line {i}: {line[:50]}...")
        
        # Enhanced fake content detection
        content_lower = content.lower()
        fake_indicators = [
            'example_word', 'sample', 'apple', 'banana', 'cat', 'dog', 'elephant', 
            'placeholder', 'assuming', 'noun, fruit', 'noun, animal',
            'real_word_you_see', 'actual_word_from_image', 'actual_definition',
            'real_example', 'another_real_example'
        ]
        detected_fake = [indicator for indicator in fake_indicators if indicator in content_lower]
        
        if detected_fake:
            print(f"\n❌ CRITICAL ERROR: Generated content contains placeholder data!")
            print(f"   Detected placeholder indicators: {detected_fake}")
            print("   🔍 The agent is NOT reading the actual image content.")
            print("   💡 The VLM may not be properly processing the image file.")
            print("   🛠️  Troubleshooting suggestions:")
            print("      - Verify the image file is accessible")
            print("      - Check if the VLM model supports image processing")
            print("      - Ensure the image format is supported (JPEG detected)")
        else:
            print("\n✅ Content appears to be real vocabulary (no obvious placeholder text detected)")
    else:
        print("⚠️  No anki_cards.csv file was created")
    
    return result

if __name__ == "__main__":
    # Run comprehensive self-test
    run_comprehensive_self_test()
    
    # Process vocabulary image
    vocab_image = sys.argv[1] if len(sys.argv) > 1 else "input/vocabulary_page.png"
    print(f"\n🖼️  Processing image: {vocab_image}")
    process_vocab_image(vocab_image)
