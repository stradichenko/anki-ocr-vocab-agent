# Anki OCR vocab agent

This is a an easy 'n quick tool to create anki vocab cards using agents (smolagent library) and a visual model (`qwen2.5-vl`).

---

# What you'll end up with

Folder layout:

```
anki-ocr-agent/
├── .venv/                 # Python virtual env (auto-created by you)
├── vocab_ocr_agent.py     # the unified pipeline script
├── input/
│   └── *.png, *.jpg       # put your scanned images here
├── anki_cards.csv         # will be created after running the script
├── agent_output.txt       # automatic execution log (auto-created)
└── processed_images.json  # tracking log for processed images
```

# Features

- **Batch Processing**: Automatically processes ALL images in the `input/` directory
- **Smart Tracking**: Remembers which images have been successfully processed
- **Skip Duplicates**: Won't reprocess images that already contributed to the CSV
- **Automatic Logging**: All output is automatically saved to `agent_output.txt`
- **Vision Processing**: Uses Qwen2.5-VL for OCR and vocabulary extraction
- **YAML to CSV**: Converts extracted vocabulary to Anki-ready format
- **Error Handling**: Comprehensive error handling with fallback options

# Step-by-step

## 1) Create a project folder

```bash
mkdir -p ~/anki-ocr-agent/input
cd ~/anki-ocr-agent
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
pip install smolagents pyyaml
pip install smolagents[litellm] pyyaml

```


## 6) Put your vocabulary image in `./input/`

Example:

```bash
cp /path/to/your/scan.png input/vocabulary_page.png
```

## 7) Put your vocabulary images in `./input/`

You can now add multiple images:

```bash
cp /path/to/your/scan1.png input/
cp /path/to/your/scan2.jpg input/
cp /path/to/your/scan3.jpeg input/
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

# Tracking System

The script maintains a `processed_images.json` file that tracks:
- Which images have been processed
- When they were processed
- Whether processing was successful
- Any error messages from failed processing

This ensures:
- ✅ No duplicate processing of the same image
- ✅ You can add new images anytime and only new ones get processed
- ✅ Failed images can be retried by removing them from the tracking log

# Logging

The script automatically creates detailed logs:
- `agent_output.txt` - Complete execution log with all output
- `agent_output_stderr.txt` - Error messages and stack traces (if any)
- `processed_images.json` - Processing history and status for each image

# Example Usage

```bash
# First run: processes image1.png and image2.jpg
python vocab_ocr_agent.py

# Add more images
cp newvocab.png input/

# Second run: only processes newvocab.png (skips previous images)
python vocab_ocr_agent.py

# Force reprocess a specific image (bypasses tracking)
python vocab_ocr_agent.py input/image1.png
```

# Processing Status

After each run, you'll see a summary like:
```
📊 Processing Summary:
   🔍 Total images found: 5
   ✅ Already processed: 3
   🆕 New images to process: 2

📊 Overall stats: 4 successful, 1 failed out of 5 total
```

---

# Common bumps & quick fixes

* \*\*“YAML error: found character ‘`’…”**  
  That means the model wrapped the YAML in triple backticks. Quick fix: strip them before parsing.
  In `YamlToAnkiTool.forward`, add this right before `yaml.safe\_load(yaml\_content)\`:

  ````python
  yaml_content = yaml_content.strip()
  if yaml_content.startswith("```") and yaml_content.endswith("```"):
      yaml_content = yaml_content[3:-3].strip()
  ````

* **CSV not created**
  Rerun. Also ensure the prompt asks the agent to “use the `yaml_to_anki` tool”.
  (The unified script I gave already nudges it to call the tool.)

* **Slow on old CPU**
  That’s normal for VLMs. Start with smaller/clean images, and keep just the vocab area if you can.

* **Different model tag**
  If you pulled a different tag, just change:

  ```python
  model = OllamaModel("qwen2.5-vl:7b")
  ```

  to whatever `ollama list` shows you.

---

# TL;DR command list

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
#   - save vocab_ocr_agent.py here
#   - put your image at ./input/vocabulary_page.png

# 4) Run
python vocab_ocr_agent.py

# 5) Import anki_cards.csv into Anki
```

If you want, I can also give you a **batch mode** version (process all images in `./input/`) or wire it to **AnkiConnect** so it imports automatically after generating the CSV.




---

## Auto watch implementation

Got it 👍 You want your `vocab_ocr_agent.py` to **auto-watch a folder** for new images and process them as soon as they appear — no need to manually re-run. This is basically like “loop mode + auto-watch.”

Here’s a clean version with that added:

```python
import os
import time
import pytesseract
from PIL import Image
import ollama
import argparse

def process_image(image_path, output_file):
    """Extract text from image and process with Ollama."""
    try:
        print(f"[INFO] Processing: {image_path}")
        img = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(img)

        # Skip if no text found
        if not extracted_text.strip():
            print(f"[WARN] No text found in {image_path}")
            return

        prompt = f"""
        I will upload an image containing vocabulary words with their meanings and example sentences.

        Your tasks are:
        1. For each vocabulary entry, extract:
           - word: the vocabulary word (lowercase unless it is a personal/proper name, in which case keep original capitalization)
           - meaning: the definition of the word
           - example: an example sentence using the word

        Text:
        {extracted_text}
        """

        response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
        result = response["message"]["content"]

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n# Processed from {os.path.basename(image_path)}\n")
            f.write(result.strip())

        print(f"[SUCCESS] Results written to {output_file}")
    except Exception as e:
        print(f"[ERROR] Failed to process {image_path}: {e}")

def watch_folder(input_dir, output_file, interval=5):
    """Continuously watch a folder for new images and process them."""
    print(f"[WATCH] Monitoring folder: {input_dir}")
    seen = set()

    while True:
        try:
            # Look for new images
            images = [f for f in os.listdir(input_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            new_images = [f for f in images if f not in seen]

            for img_file in new_images:
                img_path = os.path.join(input_dir, img_file)
                process_image(img_path, output_file)
                seen.add(img_file)

            time.sleep(interval)

        except KeyboardInterrupt:
            print("\n[EXIT] Stopped watching.")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR Vocabulary Agent with Auto-Watch Mode")
    parser.add_argument("--input", type=str, required=True, help="Input directory with images")
    parser.add_argument("--output", type=str, required=True, help="Output markdown file")
    parser.add_argument("--watch", action="store_true", help="Enable auto-watch mode")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds")
    args = parser.parse_args()

    if args.watch:
        watch_folder(args.input, args.output, args.interval)
    else:
        for img_file in os.listdir(args.input):
            if img_file.lower().endswith((".png", ".jpg", ".jpeg")):
                img_path = os.path.join(args.input, img_file)
                process_image(img_path, args.output)
```

---

### 🔧 How to use

1. Put this script as `vocab_ocr_agent.py` in your working folder.

2. Run **normal (batch) mode**:

   ```bash
   python vocab_ocr_agent.py --input ./images --output vocab.md
   ```

   → Processes all images in `./images` once.

3. Run in **auto-watch mode**:

   ```bash
   python vocab_ocr_agent.py --input ./images --output vocab.md --watch
   ```

   → Keeps watching `./images`. Whenever you drop a new `.png/.jpg/.jpeg`, it auto-extracts and appends results to `vocab.md`.

---