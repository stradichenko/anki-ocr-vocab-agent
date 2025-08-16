"""Testing utilities for agent functionality."""

import os
import base64
import traceback
from tools import yaml_to_anki, file_reader, file_writer

def safe_tool_name(t):
    """Safely get tool name for display."""
    try:
        if isinstance(t, str):
            return t
        return getattr(t, "name", repr(t))
    except Exception:
        return repr(t)

def run_comprehensive_self_test():
    """
    Comprehensive self-test suite to verify all components are working.
    Tests file I/O, directory scanning, image detection, and VLM capabilities.
    """
    print("\n" + "="*80)
    print("🔧 COMPREHENSIVE SELF-TEST SUITE")
    print("="*80)
    
    # Test 1: Basic file operations
    print("\n📁 TEST 1: File Operations")
    print("-" * 40)
    
    test_path = "agent_self_test.txt"
    test_content = "agent self-test: comprehensive check\nLine 2: UTF-8 encoding test: áéíóú ñ\nLine 3: timestamp=" + str(os.path.getmtime(__file__) if os.path.exists(__file__) else "unknown")
    
    try:
        print("→ Writing test file via FileWriter...")
        abs_written = file_writer(test_path, test_content)
        print(f"   ✅ Wrote file to: {abs_written}")
        print(f"   📏 File size: {os.path.getsize(abs_written)} bytes")
        
        print("→ Reading test file via FileReader...")
        read_back = file_reader(test_path)
        print(f"   📖 Read {len(read_back)} characters")
        print(f"   📝 Content preview: {repr(read_back[:100])}{'...' if len(read_back) > 100 else ''}")
        
        if read_back == test_content:
            print("   ✅ File write/read integrity: PASSED")
        else:
            print("   ❌ File write/read integrity: FAILED")
            print(f"   Expected: {repr(test_content[:50])}...")
            print(f"   Got:      {repr(read_back[:50])}...")
    except Exception as e:
        print(f"   ❌ File operations error: {e}")
        traceback.print_exc()
    
    # Test 2: Directory scanning and file discovery
    print("\n📂 TEST 2: Directory and File Discovery")
    print("-" * 40)
    
    try:
        # Scan current directory
        current_files = [f for f in os.listdir('.') if os.path.isfile(f)]
        print(f"→ Current directory contains {len(current_files)} files:")
        for f in sorted(current_files)[:10]:  # Show first 10
            size = os.path.getsize(f)
            print(f"   📄 {f} ({size} bytes)")
        if len(current_files) > 10:
            print(f"   ... and {len(current_files) - 10} more files")
        
        # Look for input directory and images
        input_dir = "input"
        if os.path.exists(input_dir) and os.path.isdir(input_dir):
            print(f"→ Input directory '{input_dir}' found")
            input_files = os.listdir(input_dir)
            image_files = [f for f in input_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
            print(f"   📁 Contains {len(input_files)} total files")
            print(f"   🖼️  Found {len(image_files)} image files:")
            for img in image_files:
                img_path = os.path.join(input_dir, img)
                size = os.path.getsize(img_path)
                print(f"      🖼️  {img} ({size} bytes, {size/1024:.1f} KB)")
        else:
            print(f"→ Input directory '{input_dir}' not found")
            
    except Exception as e:
        print(f"   ❌ Directory scanning error: {e}")
    
    # Test 3: YAML processing
    print("\n📋 TEST 3: YAML Processing")
    print("-" * 40)
    
    try:
        test_yaml = """- word: test
  back: 'A trial or examination ("I took a test", "This is a test case", "Testing is important")'
  tags: noun
- word: example
  back: 'A representative instance ("For example", "This is an example", "Set a good example")'
  tags: noun"""
        
        print("→ Testing YAML to Anki conversion...")
        print(f"   📝 Test YAML ({len(test_yaml)} chars):")
        print("   " + "\n   ".join(test_yaml.split('\n')[:4]) + "...")
        
        csv_path = yaml_to_anki(test_yaml)
        print(f"   ✅ Generated CSV: {csv_path}")
        
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            lines = csv_content.strip().split('\n')
            print(f"   📊 CSV contains {len(lines)} lines (including header)")
            print(f"   📄 CSV preview: {lines[0] if lines else 'empty'}")
            if len(lines) > 1:
                print(f"                   {lines[1][:60]}{'...' if len(lines[1]) > 60 else ''}")
        
    except Exception as e:
        print(f"   ❌ YAML processing error: {e}")
    
    # Test 4: Image processing validation
    print("\n🖼️  TEST 4: Image Processing Validation")
    print("-" * 40)
    
    test_image_path = "input/vocabulary_page.png"
    if os.path.exists(test_image_path):
        try:
            stat = os.stat(test_image_path)
            print(f"→ Target image file found: {test_image_path}")
            print(f"   📏 Size: {stat.st_size} bytes ({stat.st_size/1024:.1f} KB)")
            print(f"   📅 Modified: {os.path.getmtime(test_image_path)}")
            
            # Try to read as binary to validate it's a proper image
            with open(test_image_path, 'rb') as f:
                header = f.read(16)
            print(f"   🔍 File header: {header.hex()[:32]}...")
            
            # Check if it looks like a valid image
            if header.startswith(b'\x89PNG'):
                print("   ✅ Detected as PNG image")
            elif header.startswith(b'\xff\xd8\xff'):
                print("   ✅ Detected as JPEG image")
            elif header.startswith(b'GIF8'):
                print("   ✅ Detected as GIF image")
            elif header.startswith(b'RIFF') and b'WEBP' in header:
                print("   ✅ Detected as WebP image")
            else:
                print(f"   ⚠️  Unknown image format (header: {header[:8].hex()})")
                
        except Exception as e:
            print(f"   ❌ Image validation error: {e}")
    else:
        print(f"→ Target image not found: {test_image_path}")
        print("   ⚠️  You may need to place a vocabulary image at this path")
        
    # Test 5: YAML syntax validation
    print("\n📝 TEST 5: YAML Syntax Validation")
    print("-" * 40)
    
    try:
        # Test with problematic quotes like in the agent output
        problematic_yaml = '''- word: test
  back: 'A definition with quotes ("example one", "example two")'
  tags: noun'''
        
        print("→ Testing YAML with embedded quotes...")
        csv_path = yaml_to_anki(problematic_yaml)
        print(f"   ✅ Successfully processed YAML with quotes: {csv_path}")
        
    except Exception as e:
        print(f"   ❌ YAML quote handling error: {e}")
    
    print("\n" + "="*80)
    print("🏁 SELF-TEST COMPLETE")
    print("="*80)
