# Anki OCR Vocab Agent

This is an easy 'n quick tool to create Anki vocab cards using agents (`smolagent` library) and a visual model (`qwen2.5-vl`).

---

## Features

- **Batch Processing**: Automatically processes ALL images in the `input/` directory
- **Smart Tracking**: Remembers which images have been successfully processed
- **Skip Duplicates**: Won't reprocess images that already contributed to the CSV
- **Automatic Logging**: All output is automatically saved to `agent_output.txt`
- **Vision Processing**: Uses Qwen2.5-VL for OCR and vocabulary extraction
- **Image Preprocessing**: Automatic image enhancement for better OCR accuracy
    - resizing to optimal dimensions
    - Contrast enhancement for better text visibility
    - Noise reduction to clean up image artifacts
    - Sharpening filters to improve text clarity
    - Compression optimization for faster processing
- **YAML to CSV**: Converts extracted vocabulary to Anki-ready format
- **Error Handling**: Comprehensive error handling with fallback options
- **Configurable**: Easy customization of preprocessing settings


## What You'll End Up With

Folder layout:

```
anki-ocr-agent/
├── .venv/                   # Python virtual environment (auto-created)
├── vocab_ocr_agent.py       # main pipeline script
├── input/                   # put your scanned images here (PNG, JPG, etc.)
│   └── *.png, *.jpg, ...
├── output/                  # stores all outputs and logs
│   ├── processed_images/    # processed images (by config)
│   ├── my_debug/            # optional: intermediate/debug images
│   ├── anki_cards.csv       # generated Anki-ready vocabulary cards
│   ├── agent_output.txt     # execution log (auto-created)
│   ├── agent_output_stderr.txt  # error log (auto-created)
│   └── processed_images.json    # processing/tracking log
```


## Step-by-step


## 1) Create a project folder

```bash
git clone https://github.com/stradichenko/anki-ocr-agent.git
cd anki-ocr-agent
```

## 2) (If needed) Install Ollama and pull the model

If you already have Ollama + `qwen2.5-vl` locally, skip to step 3.

```bash
# Install Ollama (official installer)
curl -fsSL https://ollama.com/install.sh | sh

# Start/enable the Ollama service (Fedora/most systemd distros)
sudo systemctl enable --now ollama

# Pull the visual model
ollama pull qwen2.5vl:latest

# Start the model
ollama serve
```

> Tip: Check it’s installed with `ollama list`.

## 3) Create and activate a Python virtual env

```bash
python3 -m venv .venv
source .venv/bin/activate
```

A virtual environment (venv) in Python does not isolate system daemons or background services — it only affects which Python packages and binaries you use.

So in your case:

ollama (the server listening on localhost:11434) is a system-wide process, not something inside your venv.

When you install a Python package (e.g. ollama, smolagents, etc.) inside a venv, it doesn’t re-run ollama itself — it just gives you Python bindings or client code that talks to the Ollama server.

As long as ollama is running on port 11434, your venv’s Python scripts will be able to connect to it.

👉 In other words: the ollama server runs once per system (outside venv), and any Python environment can connect to it. You don’t need a separate Ollama per venv.


## 4) Install Python packages

```bash
pip install --upgrade pip
pip install smolagents[litellm] pyyaml
```


## 6) Put your vocabulary image in `./input/`

Example:

```bash
cp /path/to/your/scan.png input/vocabulary_page.png
```

The script supports: PNG, JPG, JPEG, GIF, BMP, WebP, TIFF formats.

## 8) Run the pipeline

From the project folder:

```bash
# Process all images in input/ directory
python vocab_ocr_agent.py

# Or process a specific image
python vocab_ocr_agent.py path/to/specific/image.png
```

What happens:

1. All output is automatically logged to `agent_output.txt`
2. The script scans `input/` directory for all image files
3. Checks `processed_images.json` to see which images have been processed
4. Skips images that already contributed vocabulary to the CSV
5. Processes new images using **qwen2.5-vl** via Ollama
6. Appends new vocabulary to **`anki_cards.csv`**
7. Updates the processing log with success/failure status

## TL;DR command list

```bash
# 1) Setup
mkdir -p ~/anki-ocr-agent/input
cd ~/anki-ocr-agent
python3 -m venv .venv
source .venv/bin/activate
pip install smolagents pyyaml

# 2) (If needed) Ollama + model
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama
ollama pull qwen2.5-vl:7b

# 3) Add your script and image
#   - put your image at ./input/

# 4) Run
python vocab_ocr_agent.py

# 5) Import anki_cards.csv into Anki
```

# Tracking System

The script maintains a `processed_images.json` file that tracks:
- Which images have been processed
- When they were processed
- Whether processing was successful
- Any error messages from failed processing

# Logging

The script automatically creates detailed logs:
- `agent_output.txt` - Complete execution log with all output
- `agent_output_stderr.txt` - Error messages and stack traces (if any)
- `processed_images.json` - Processing history and status for each image

# Processing Status

After each run, you'll see a summary like:
```
📊 Processing Summary:
   🔍 Total images found: 5
   ✅ Already processed: 3
   🆕 New images to process: 2

📊 Overall stats: 4 successful, 1 failed out of 5 total
```

## Image Preprocessing

The script automatically applies image preprocessing to improve OCR accuracy.
To change the preprocessing configuration, edit `vocab_ocr_agent.py`:

```python
# Find this line (around line 200):
processed_image, processing_summary = preprocess_image_for_ocr(image_path, QUALITY_CONFIG)

# Replace with your preferred config:
processed_image, processing_summary = preprocess_image_for_ocr(image_path, OCR_OPTIMIZED_CONFIG)
```

### Preprocessing Steps
1. **Resize**: Scales down large images to optimal dimensions (default: 2048x2048 max)
2. **Contrast Enhancement**: Improves text visibility (configurable factor)
3. **Noise Reduction**: Removes image artifacts using Gaussian blur
4. **Sharpening**: Enhances text edges for better recognition
5. **Compression**: Optimizes file size for faster processing

### Choosing the Right Configuration

The script includes several preset configurations optimized for different scenarios:

#### Available Presets

| Config | Best For | Speed | Quality | File Size | Description |
|--------|----------|-------|---------|-----------|-------------|
| **MINIMAL_CONFIG** | Testing/Debug | ⚡⚡⚡ | ⭐ | Original | No preprocessing - uses original image |
| **FAST_CONFIG** | Quick processing | ⚡⚡ | ⭐⭐ | Small | Light processing with JPEG compression |
| **OPTIMIZED_CONFIG** | Most images | ⚡ | ⭐⭐⭐ | Medium | Balanced quality/speed, resizes to 1024x768 |
| **OCR_OPTIMIZED_CONFIG** | Text-heavy images | ⚡ | ⭐⭐⭐⭐ | Small | Aggressive text enhancement, resizes to 800x600 |
| **QUALITY_CONFIG** | High-quality scans | ⭐ | ⭐⭐⭐⭐⭐ | Large | Maximum quality processing |



## Expected Results by Config

### FAST_CONFIG Results
- **Size reduction**: 30-50%
- **Processing time**: 1-2 seconds
- **Quality**: Good for clear images

### OCR_OPTIMIZED_CONFIG Results
- **Size reduction**: 60-80%
- **Processing time**: 2-3 seconds
- **Quality**: Excellent for text recognition

### QUALITY_CONFIG Results
- **Size reduction**: 10-30%
- **Processing time**: 3-5 seconds
- **Quality**: Maximum detail preservation

## Monitoring Preprocessing

The script shows detailed preprocessing statistics:

```
📊 Preprocessing stats:
   Original: (1600, 900) (147036 bytes)
   Processed: (800, 450) (65432 bytes)
   Size reduction: 55.5%
   Resolution reduction: 75.0%
📝 Processing steps: Resized 1600x900 → 800x450 | Contrast enhanced (factor: 1.4) | ...
```

**Good results to look for:**
- Size reduction: 20-70% (depending on config)
- Resolution reduction: 0-75% (depending on config)
- Processing completes without errors
- Processed image saved to `output/processed_images/`

**Warning signs:**
- Size increase (negative reduction %)
- No resize when expected
- Processing errors or failures

---

## Customization

### Creating Custom Image Preprocessing

You can create your own preprocessing configuration for specific needs:

```python
# In vocab_ocr_agent.py, add before the main processing:
from core.image_config import ImagePreprocessingConfig

# Create custom config for your specific images
CUSTOM_CONFIG = ImagePreprocessingConfig(
    enable_preprocessing=True,
    enable_resize=True,
    enable_compression=True,
    enable_contrast=True,
    enable_noise_reduction=False,    # Disable if images are clean
    enable_sharpening=True,
    
    # Size settings
    max_width=1200,                  # Custom size for your images
    max_height=800,
    
    # Enhancement settings
    contrast_factor=1.6,             # Higher for low-contrast scans
    sharpening_factor=1.8,           # Higher for blurry text
    
    # Compression
    output_format="JPEG",
    jpeg_quality=85,
    
    # Debug and output
    save_intermediate_steps=True,    # Enable to see each step
    save_processed_image=True,       # Save final processed image
    intermediate_dir="output/my_debug",
    processed_image_dir="output/my_processed"
)

# Then use it in processing:
processed_image, summary = preprocess_image_for_ocr(image_path, CUSTOM_CONFIG)
```

### Fine-tuning Parameters

#### Contrast Factor
- `1.0` = No change
- `1.2-1.4` = Good for most images
- `1.5-2.0` = For very low contrast images
- `>2.0` = May cause artifacts

#### Noise Reduction Radius
- `0` = No noise reduction
- `0.1-0.3` = Light smoothing, preserves text
- `0.4-0.7` = Moderate smoothing
- `>0.8` = Heavy smoothing, may blur text

#### Sharpening Factor
- `1.0` = No sharpening
- `1.2-1.5` = Good for most text
- `1.6-2.0` = Strong sharpening for blurry images
- `>2.0` = May create artifacts

#### JPEG Quality
- `60-70` = Small files, some quality loss
- `75-85` = Good balance
- `85-95` = High quality, larger files
- `95-100` = Maximum quality

### Image Type Recommendations

**For book/document photos:**
```python
DOCUMENT_CONFIG = ImagePreprocessingConfig(
    max_width=1024, max_height=1024,
    contrast_factor=1.4,
    noise_reduction_radius=0.2,
    sharpening_factor=1.6,
    output_format="JPEG", jpeg_quality=85
)
```

**For handwritten notes:**
```python
HANDWRITING_CONFIG = ImagePreprocessingConfig(
    max_width=1200, max_height=1200,
    contrast_factor=1.5,
    noise_reduction_radius=0.1,
    sharpening_factor=1.3,
    output_format="PNG"  # Better for line art
)
```

**For screenshot/digital images:**
```python
DIGITAL_CONFIG = ImagePreprocessingConfig(
    enable_noise_reduction=False,  # Already clean
    enable_sharpening=False,       # Already sharp
    max_width=800, max_height=600,
    output_format="JPEG", jpeg_quality=75
)
```