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
import json
import glob
from datetime import datetime
from PIL import Image
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

from core.agent_factory import create_vocab_agent
from utils.testing import (
    run_comprehensive_self_test,
    safe_tool_name,
    print_agent_debug_info,
    analyze_csv_output,
)
from tools import yaml_to_anki, file_reader, file_writer


class TeeOutput:
    """Utility class to redirect output to both console and file."""
    
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()


class ImageProcessingTracker:
    """Track which images have been successfully processed."""
    
    def __init__(self, log_file="processed_images.json"):
        self.log_file = log_file
        self.processed_images = self._load_log()
    
    def _load_log(self):
        """Load processing history from JSON file."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_log(self):
        """Save processing history to JSON file."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_images, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"⚠️ Warning: Could not save processing log: {e}")
    
    def is_processed(self, image_path):
        """Check if image has been successfully processed."""
        abs_path = os.path.abspath(image_path)
        return abs_path in self.processed_images
    
    def mark_processed(self, image_path, success=True, error_msg=None):
        """Mark image as processed with status."""
        abs_path = os.path.abspath(image_path)
        self.processed_images[abs_path] = {
            "processed_at": datetime.now().isoformat(),
            "success": success,
            "error": error_msg,
            "file_size": os.path.getsize(image_path) if os.path.exists(image_path) else 0
        }
        self._save_log()
    
    def get_processing_stats(self):
        """Get statistics about processed images."""
        total = len(self.processed_images)
        successful = sum(1 for entry in self.processed_images.values() if entry.get("success", False))
        failed = total - successful
        return {"total": total, "successful": successful, "failed": failed}


def find_images_in_directory(directory="input"):
    """Find all image files in the specified directory."""
    if not os.path.exists(directory):
        print(f"📁 Directory '{directory}' not found")
        return []
    
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.webp', '*.tiff', '*.tif']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(directory, ext)
        image_files.extend(glob.glob(pattern))
        # Also check uppercase extensions
        pattern_upper = os.path.join(directory, ext.upper())
        image_files.extend(glob.glob(pattern_upper))
    
    # Remove duplicates and sort
    image_files = sorted(list(set(image_files)))
    
    print(f"📁 Found {len(image_files)} image files in '{directory}':")
    for img in image_files:
        size = os.path.getsize(img)
        print(f"   🖼️  {os.path.basename(img)} ({size} bytes, {size/1024:.1f} KB)")
    
    return image_files


def process_vocab_image(image_path: str, tracker: ImageProcessingTracker):
    """
    Process vocabulary image using smolagents vision capabilities.
    
    Args:
        image_path: Path to the vocabulary image file
        tracker: ImageProcessingTracker instance
        
    Returns:
        Agent execution result or None if failed
    """
    if not os.path.exists(image_path):
        error_msg = f"Image not found: {image_path}"
        print(f"❌ {error_msg}")
        tracker.mark_processed(image_path, success=False, error_msg=error_msg)
        return None

    print(f"\n{'='*60}")
    print(f"🖼️  Processing: {os.path.basename(image_path)}")
    print(f"{'='*60}")

    try:
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
            error_msg = f"Failed to load image: {e}"
            print(f"❌ {error_msg}")
            tracker.mark_processed(image_path, success=False, error_msg=error_msg)
            return None

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
        
        # Store original CSV state to check if new content was added
        csv_path = "anki_cards.csv"
        original_csv_content = ""
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                original_csv_content = f.read()
        
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
                error_msg = f"Fallback also failed: {fallback_error}"
                print(f"❌ {error_msg}")
                traceback.print_exc()
                
                # Use testing utility for debug info
                print_agent_debug_info(agent, image_path, image)
                tracker.mark_processed(image_path, success=False, error_msg=error_msg)
                return None

        print("\n✅ Agent execution completed!")
        print("Agent run returned:", result)

        # Check if new content was added to CSV
        new_csv_content = ""
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                new_csv_content = f.read()
        
        # Determine if processing was successful
        content_added = new_csv_content != original_csv_content
        
        if content_added:
            print(f"✅ New vocabulary content added to {csv_path}")
            tracker.mark_processed(image_path, success=True)
        else:
            print(f"⚠️ No new content was added to {csv_path}")
            tracker.mark_processed(image_path, success=False, error_msg="No content extracted from image")

        return result

    except Exception as e:
        error_msg = f"Unexpected error processing {image_path}: {e}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        tracker.mark_processed(image_path, success=False, error_msg=error_msg)
        return None


def process_all_images(input_directory="input"):
    """Process all images in the input directory."""
    tracker = ImageProcessingTracker()
    
    # Find all images
    image_files = find_images_in_directory(input_directory)
    
    if not image_files:
        print(f"📁 No image files found in '{input_directory}' directory")
        return
    
    # Check which images need processing
    new_images = []
    skipped_images = []
    
    for image_path in image_files:
        if tracker.is_processed(image_path):
            skipped_images.append(image_path)
        else:
            new_images.append(image_path)
    
    # Show processing summary
    print(f"\n📊 Processing Summary:")
    print(f"   🔍 Total images found: {len(image_files)}")
    print(f"   ✅ Already processed: {len(skipped_images)}")
    print(f"   🆕 New images to process: {len(new_images)}")
    
    if skipped_images:
        print(f"\n⏭️  Skipping already processed images:")
        for img in skipped_images:
            status = tracker.processed_images[os.path.abspath(img)]
            status_icon = "✅" if status.get("success", False) else "❌"
            print(f"   {status_icon} {os.path.basename(img)} (processed: {status.get('processed_at', 'unknown')})")
    
    if not new_images:
        print("\n🎉 All images have already been processed!")
        stats = tracker.get_processing_stats()
        print(f"📊 Final stats: {stats['successful']} successful, {stats['failed']} failed out of {stats['total']} total")
        return
    
    print(f"\n🚀 Processing {len(new_images)} new images...")
    
    # Process each new image
    successful = 0
    failed = 0
    
    for i, image_path in enumerate(new_images, 1):
        print(f"\n📋 Processing image {i}/{len(new_images)}: {os.path.basename(image_path)}")
        
        result = process_vocab_image(image_path, tracker)
        if result is not None:
            successful += 1
        else:
            failed += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🏁 BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successfully processed: {successful}")
    print(f"❌ Failed to process: {failed}")
    
    # Overall stats
    stats = tracker.get_processing_stats()
    print(f"📊 Overall stats: {stats['successful']} successful, {stats['failed']} failed out of {stats['total']} total")
    
    # Use testing utility to analyze final output
    analyze_csv_output()


if __name__ == "__main__":
    # Set up automatic logging to agent_output.txt
    log_file = "agent_output.txt"
    
    # Create TeeOutput to write to both console and file
    tee_stdout = TeeOutput(log_file)
    tee_stderr = TeeOutput(log_file.replace('.txt', '_stderr.txt'))
    
    # Redirect stdout and stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    try:
        sys.stdout = tee_stdout
        sys.stderr = tee_stderr
        
        print(f"📝 Logging output to: {log_file}")
        print("=" * 80)
        
        run_comprehensive_self_test()
        
        # Check for specific image argument or process all images
        if len(sys.argv) > 1:
            specific_image = sys.argv[1]
            print(f"\n🖼️  Processing specific image: {specific_image}")
            tracker = ImageProcessingTracker()
            process_vocab_image(specific_image, tracker)
        else:
            print(f"\n📁 Processing all images in input/ directory...")
            process_all_images()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Restore original stdout/stderr and close log files
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        tee_stdout.close()
        tee_stderr.close()
        
        print(f"✅ Execution complete. Full log saved to: {log_file}")
