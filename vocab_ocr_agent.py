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
import base64

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

    # Read and encode the image for the VLM
    print(f"📖 Reading image file: {image_path}")
    try:
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        print(f"✅ Image loaded: {len(image_data)} bytes, base64 length: {len(image_b64)}")
        print(f"📊 Base64 preview: {image_b64[:100]}...{image_b64[-50:]}")
    except Exception as e:
        print(f"❌ Failed to read image: {e}")
        raise

    # Clean prompt without base64 workarounds
    query = (
        f"You are analyzing a vocabulary image that contains words, definitions, and examples.\n\n"
        f"🔍 YOUR TASK:\n"
        f"Look at the image and extract the vocabulary words, definitions, and examples you can see.\n"
        f"Format this content as YAML and call yaml_to_anki.\n\n"
        f"YAML FORMAT:\n"
        f"- word: [actual word from image]\n"
        f"  back: '[definition] (\"[example 1]\", \"[example 2]\")'\n"
        f"  tags: [part of speech]\n\n"
        f"EXAMPLE:\n"
        f"<code>\n"
        f"yaml_content = '''- word: abandon\n"
        f"  back: 'to give up completely (\"She abandoned the car\", \"Don't abandon hope\")'\n"
        f"  tags: verb'''\n"
        f"yaml_to_anki(yaml_content)\n"
        f"</code>\n\n"
        f"Extract all vocabulary words you can see in the image."
    )

    print("\n🚀 Starting agent execution...")
    print("📊 Sending structured vision input to VLM...")
    
    try:
        # Use proper structured input format for vision models
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
            ]
        }]
        
        # Call the model directly with structured messages for vision
        print("🔍 Using structured vision input format...")
        model_response = agent.model.call(messages=messages)
        
        # Extract the response content and have the agent process it
        if hasattr(model_response, 'content'):
            vision_result = model_response.content
        elif isinstance(model_response, dict) and 'content' in model_response:
            vision_result = model_response['content']
        else:
            vision_result = str(model_response)
            
        print(f"📋 Vision model response: {vision_result[:200]}...")
        
        # Now have the agent process this vision result and call tools
        processing_query = (
            f"Based on this vision analysis of a vocabulary image:\n\n"
            f"{vision_result}\n\n"
            f"Extract the vocabulary words, definitions, and examples mentioned.\n"
            f"Format as YAML and call yaml_to_anki tool.\n"
            f"Use the format:\n"
            f"<code>\n"
            f"yaml_content = '''- word: [word]\n"
            f"  back: '[definition] (\"[example]\", \"[example]\")'\n"
            f"  tags: [type]'''\n"
            f"yaml_to_anki(yaml_content)\n"
            f"</code>"
        )
        
        result = agent.run(processing_query)
        
    except Exception as e:
        print(f"❌ Structured vision approach failed: {e}")
        print("🔄 Falling back to direct agent.run()...")
        traceback.print_exc()
        
        # Fallback to the previous approach but with cleaner prompt
        try:
            result = agent.run(query)
        except Exception as fallback_error:
            print(f"❌ Agent run raised an exception: {fallback_error}")
            traceback.print_exc()
            
            # Try to provide helpful debugging information
            print("\n🔍 Debugging information:")
            print(f"   📁 Working directory: {os.getcwd()}")
            print(f"   📄 Image exists: {os.path.exists(image_path)}")
            print(f"   📏 Image size: {os.path.getsize(image_path)} bytes")
            print(f"   🔗 Model supports vision: {getattr(agent.model, 'supports_vision', 'unknown')}")
            
            raise
    
    print("\n✅ Agent execution completed!")
    print("Agent run returned:", result)
    
    # Enhanced analysis of the results
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
        
        # Check for specific problematic patterns from the agent output
        result_str = str(result).lower()
        problematic_indicators = [
            'base64.b64decode', 'variable `data` is not defined', 'import base64',
            'decode the base64', 'unicodedecodeerror', 'utf-8 codec'
        ]
        detected_problems = [indicator for indicator in problematic_indicators if indicator in result_str]
        
        if detected_problems:
            print(f"\n🚨 CRITICAL VLM PROCESSING ERROR:")
            print(f"   Detected technical issues: {detected_problems}")
            print("   ❌ The agent is trying to decode base64 instead of using vision")
            print("   📋 Root cause analysis:")
            print("      - The VLM is not recognizing the image as visual input")
            print("      - LiteLLM may not be properly configured for vision models")
            print("      - The Ollama qwen2.5vl model may not be vision-enabled")
            print("      - Image format or size may be incompatible")
            print("\n   🛠️  Recommended fixes:")
            print("      1. Verify: ollama list | grep qwen2.5vl")
            print("      2. Test direct Ollama API with curl")
            print("      3. Check LiteLLM vision model configuration")
            print("      4. Try a smaller/different format image")
        else:
            print("\n✅ No technical processing errors detected!")
            
        # Check content quality
        content_lower = content.lower()
        if len(lines) <= 2:  # Only header + 1 row or less
            print(f"\n⚠️  WARNING: Very little content generated ({len(lines)-1} vocabulary words)")
            print("   This suggests the VLM may not be reading the image properly")
        elif 'test' in content_lower and len(lines) == 3:
            print(f"\n⚠️  WARNING: Only test data found, no real vocabulary extracted")
            print("   The agent may not be processing the actual image content")
    else:
        print("⚠️  No anki_cards.csv file was created - agent failed completely")
    
    return result


if __name__ == "__main__":
    # Run comprehensive self-test
    run_comprehensive_self_test()
    
    # Process vocabulary image
    vocab_image = sys.argv[1] if len(sys.argv) > 1 else "input/vocabulary_page.png"
    print(f"\n🖼️  Processing image: {vocab_image}")
    process_vocab_image(vocab_image)
