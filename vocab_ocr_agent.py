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
from core.image_config import DEFAULT_CONFIG, QUALITY_CONFIG, FAST_CONFIG, OCR_OPTIMIZED_CONFIG
from utils.testing import (
    run_comprehensive_self_test,
    safe_tool_name,
    print_agent_debug_info,
    analyze_csv_output,
)
from utils.image_preprocessing import preprocess_image_for_ocr, get_preprocessing_stats
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
    
    def __init__(self, log_file="output/processed_images.json"):
        self.log_file = log_file
        self.processed_images = self._load_log()
    
    def _load_log(self):
        """Load processing history from JSON file."""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
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
        if abs_path not in self.processed_images:
            return False
        
        # Only consider it processed if it was successful
        entry = self.processed_images[abs_path]
        return entry.get("success", False) is True
    
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

        # Load and preprocess image
        print(f"📖 Loading and preprocessing image: {image_path}")
        try:
            # Apply image preprocessing
            print("🔧 Applying image preprocessing pipeline...")
            processed_image, processing_summary = preprocess_image_for_ocr(image_path, OCR_OPTIMIZED_CONFIG)
            
            # Get preprocessing statistics
            stats = get_preprocessing_stats(image_path, processed_image, OCR_OPTIMIZED_CONFIG)
            print(f"📊 Preprocessing stats:")
            print(f"   Original: {stats['original_dimensions']} ({stats['original_file_size']} bytes)")
            print(f"   Processed: {stats['processed_dimensions']} ({stats['processed_file_size']} bytes)")
            print(f"   Size reduction: {stats['size_reduction_percent']:.1f}%")
            print(f"   Resolution reduction: {stats['dimension_reduction_percent']:.1f}%")
            print(f"📝 Processing steps: {processing_summary}")
            
            print(f"✅ Image preprocessed: {processed_image.size} pixels, mode: {processed_image.mode}")
        except Exception as e:
            error_msg = f"Failed to preprocess image: {e}"
            print(f"❌ {error_msg}")
            print("🔄 Falling back to original image...")
            traceback.print_exc()
            
            # Fallback to original image
            try:
                processed_image = Image.open(image_path)
                print(f"✅ Fallback image loaded: {processed_image.size} pixels, mode: {processed_image.mode}")
            except Exception as fallback_error:
                error_msg = f"Failed to load original image: {fallback_error}"
                print(f"❌ {error_msg}")
                tracker.mark_processed(image_path, success=False, error_msg=error_msg)
                return None

        # Construct message for vision processing - improved to avoid syntax errors
        user_message = (
            f"You are a vocabulary extraction specialist. Your task is to analyze the provided vocabulary image "
            f"Providing definitions and examples, in the same language as the vocabulary word\n\n"
            f"You will encounter 3 different types of images:\n\n"
            f"1. Vocabulary pages with multiple words and definitions\n"
            f"2. Lists of vocabulary words\n"
            f"3. Printed pages with desired vocabulary words highlighted in blue (ignore other content)\n\n"

            f"CRITICAL REQUIREMENTS:\n"
            f"1. Extract ONLY what you actually see in the image - no placeholder content\n"
            f"2. DO NOT read the same definition more than once\n"
            f"3. If a word appears multiple times, include it only once\n"
            f"5. DO NOT use Python libraries\n"
            f"6. Focus on complete, meaningful vocabulary entries only\n\n"

            f"WORKFLOW:\n"
            f"1. Carefully examine the image for vocabulary words and their definitions\n"
            f"2. Extract each word with its complete definition and examples\n"
            f"3. Format the extracted content as proper YAML\n"
            f"4. Call yaml_to_anki(yaml_string) with your YAML content\n\n"

            f"YAML FORMAT: Use this exact structure:\n"
            f"- word: actual_word\n"
            f"  back: 'definition with examples (\"example1\", \"example2\")'\n"
            f"  tags: part_of_speech\n\n"
            
            f"IMPORTANT INSTRUCTIONS:\n"
            f"- DO NOT create variables like yaml_content = \"\"\"\n"
            f"- DO NOT use triple quotes in your code\n"
            f"- Call yaml_to_anki() directly with a simple YAML string\n"
            f"- Use single quotes for YAML values containing quotes\n"
            f"- Keep your YAML concise and well-formatted\n\n"
            
            f"EXAMPLE OF CORRECT APPROACH:\n"
            f"yaml_string = '''- word: example\n"
            f"  back: 'A sample instance (\"This is an example\", \"For example\")'\n"
            f"  tags: noun'''\n"
            f"yaml_to_anki(yaml_string)\n\n"
            
            f"ERROR HANDLING:\n"
            f"- If you cannot read text clearly, skip that entry\n"
            f"- If no vocabulary content is found, call yaml_to_anki('[]')\n"
            f"- Keep YAML simple and avoid complex formatting\n\n"
            
            f"Remember: Extract real content from the image and call the tool directly. "
            f"Avoid creating large code blocks or variables that might cause parsing errors."
        )

        print("\n🚀 Starting agent execution with vision...")
        print("📊 Using smolagents native image support with preprocessed image...")
        
        # Store original CSV state to check if new content was added
        csv_path = "output/anki_cards.csv"
        original_csv_content = ""
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                original_csv_content = f.read()
        
        try:
            # Use smolagents native vision support with preprocessed image
            result = agent.run(user_message, images=[processed_image])
            
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
                print_agent_debug_info(agent, image_path, processed_image)
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
    failed_images = []
    
    for image_path in image_files:
        abs_path = os.path.abspath(image_path)
        if tracker.is_processed(image_path):
            skipped_images.append(image_path)
        elif abs_path in tracker.processed_images:
            # Image was processed before but failed - allow reprocessing
            failed_images.append(image_path)
            new_images.append(image_path)
        else:
            new_images.append(image_path)
    
    # Show processing summary
    print(f"\n📊 Processing Summary:")
    print(f"   🔍 Total images found: {len(image_files)}")
    print(f"   ✅ Already processed (successful): {len(skipped_images)}")
    print(f"   🔄 Failed previously (will retry): {len(failed_images)}")
    print(f"   🆕 New images to process: {len(new_images) - len(failed_images)}")
    print(f"   📋 Total to process this run: {len(new_images)}")
    
    if skipped_images:
        print(f"\n⏭️  Skipping successfully processed images:")
        for img in skipped_images:
            status = tracker.processed_images[os.path.abspath(img)]
            print(f"   ✅ {os.path.basename(img)} (processed: {status.get('processed_at', 'unknown')})")
    
    if failed_images:
        print(f"\n🔄 Retrying previously failed images:")
        for img in failed_images:
            status = tracker.processed_images[os.path.abspath(img)]
            error_msg = status.get('error', 'Unknown error')
            print(f"   🔄 {os.path.basename(img)} (last error: {error_msg[:50]}...)")
    
    if not new_images:
        print("\n🎉 All images have already been successfully processed!")
        stats = tracker.get_processing_stats()
        print(f"📊 Final stats: {stats['successful']} successful, {stats['failed']} failed out of {stats['total']}")
        return
    
    print(f"\n🚀 Processing {len(new_images)} images...")
    
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
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Set up automatic logging to output/agent_output.txt
    log_file = "output/agent_output.txt"
    
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
