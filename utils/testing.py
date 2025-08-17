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

def print_agent_debug_info(agent, image_path, image=None):
    """Print debugging information for agent and image processing."""
    print("\n🔍 Debugging information:")
    print(f"   📁 Working directory: {os.getcwd()}")
    print(f"   📄 Image exists: {os.path.exists(image_path)}")
    print(f"   📏 Image size: {os.path.getsize(image_path)} bytes")
    print(f"   🔗 Model: {type(agent.model).__name__}")
    if image:
        print(f"   🖼️  PIL Image: {image.size} {image.mode}")
    print(f"   ⚙️  Model config: flatten_messages_as_text={getattr(agent.model, 'flatten_messages_as_text', 'unknown')}")

def analyze_csv_output(csv_path="anki_cards.csv"):
    """Analyze and report on generated CSV output."""
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.strip().split('\n')
        print(f"📊 Generated CSV with {len(lines)} lines (including header)")
        print(f"📄 Output file: {os.path.abspath(csv_path)}")
        
        if len(lines) > 1:
            print("\n📋 Generated vocabulary preview:")
            for i, line in enumerate(lines[:4]):
                if i == 0:
                    print(f"   Header: {line}")
                else:
                    try:
                        word = line.split(',')[0]
                        print(f"   Word {i}: {word}")
                    except:
                        print(f"   Line {i}: {line[:50]}...")
        
        # Detect fake content
        content_lower = content.lower()
        fake_indicators = ['word1','word2','definition1','example1']
        detected_fake = [f for f in fake_indicators if f in content_lower]
        if detected_fake:
            print(f"\n❌ FAKE CONTENT DETECTED: {detected_fake}")
        elif len(lines) <= 2:
            print(f"\n⚠️ Very little content generated ({len(lines)-1} words)")
    else:
        print("⚠️ No anki_cards.csv file was created - agent failed completely")

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
    
    # Test 6: Vision model test
    print("\n👁️  TEST 6: Vision Model Capabilities")
    print("-" * 40)
    
    try:
        from PIL import Image
        import io
        
        # Create a simple test image with text
        print("→ Testing PIL and image loading...")
        test_image_path = "input/vocabulary_page.png"
        
        if os.path.exists(test_image_path):
            image = Image.open(test_image_path)
            print(f"   ✅ PIL successfully loaded image: {image.size} {image.mode}")
            
            # Test image conversion
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            print(f"   ✅ Image conversion successful: {len(img_bytes.getvalue())} bytes")
        else:
            print(f"   ⚠️  Test image not found: {test_image_path}")
            
    except ImportError as e:
        print(f"   ❌ PIL import error: {e}")
        print("   💡 Install with: pip install Pillow")
    except Exception as e:
        print(f"   ❌ Vision test error: {e}")
    
    print("\n" + "="*80)
    print("🏁 SELF-TEST COMPLETE")
    print("="*80)
