#!/usr/bin/env python3
"""
vocab_ocr_agent.py

OCR a vocabulary image with local Ollama Qwen2.5-VL (via ollama CLI),
then convert the model's YAML output into an Anki CSV using an in-script smolagents Tool class.

Why this structure?
 - The smolagents agent/tool sandbox attempted forbidden imports (image_qa, yaml_to_anki).
 - To avoid sandbox import restrictions, we call the local Ollama model via the CLI (subprocess),
   extract the YAML text returned by the model, and then call the YamlToAnkiTool.forward()
   function directly (no dynamic imports).
"""

import yaml
import csv
import re
import os
import shlex
import subprocess
from typing import Optional

# -------------------------
# Yaml-to-Anki 'Tool'
# -------------------------
class YamlToAnkiTool:
    """
    A minimal version of your smolagents Tool, implemented as a plain class so it can be
    called directly from this script (avoids sandbox import issues).
    """
    OUTPUT_FILE = "anki_cards.csv"

    @staticmethod
    def is_proper_name(word: str) -> bool:
        return bool(re.match(r'^[A-Z]', str(word).strip()))

    def forward(self, yaml_content: str) -> str:
        """
        Parse YAML text, clean duplicates, write CSV, return absolute path to CSV.
        Raises RuntimeError on parse failure.
        """
        if not isinstance(yaml_content, str):
            raise RuntimeError("yaml_content must be a string.")

        # Remove triple-backtick fences if present
        yaml_text = yaml_content.strip()
        # strip surrounding triple backticks or ```yaml ... ```
        if yaml_text.startswith("```") and yaml_text.endswith("```"):
            yaml_text = yaml_text[3:-3].strip()

        # Some models return extra explanation text before/after YAML.
        # Attempt to extract the first YAML block (from a leading "-" list marker).
        # If the entire text looks like YAML, use it; otherwise try to find a YAML block.
        if not yaml_text.lstrip().startswith("- "):
            # try to find a block that starts with "- word:"
            m = re.search(r"(-\s+word:.*?)(?:\n```|$)", yaml_text, flags=re.S)
            if m:
                yaml_text = m.group(1).strip()
            else:
                # As fallback, try to locate triple-backtick fenced YAML block with leading "-"
                m2 = re.search(r"```(?:yaml)?\s*(\-.*?)\s*```", yaml_text, flags=re.S)
                if m2:
                    yaml_text = m2.group(1).strip()
                # otherwise continue with the whole text and hope it's YAML

        # Try parsing YAML
        try:
            parsed = yaml.safe_load(yaml_text)
        except yaml.YAMLError as e:
            # give a helpful message including a short snippet
            snippet = yaml_text[:1000].replace("\n", "\\n")
            raise RuntimeError(f"YAML parse error: {e}\n---snippet---\n{snippet}")

        # Normalize parsed data into a list of dicts
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            raise RuntimeError("Parsed YAML is not a list or dict of entries.")

        seen = set()
        cleaned_rows = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            word = str(item.get("word", "")).strip()
            back = str(item.get("back", "")).strip()
            tags = str(item.get("tags", "")).strip()

            if not word:
                continue

            if not self.is_proper_name(word):
                word = word.lower()

            if word.lower() in seen:
                continue
            seen.add(word.lower())

            cleaned_rows.append([word, back, tags])

        # Write CSV
        with open(self.OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Word", "Back", "Tags"])
            writer.writerows(cleaned_rows)

        return os.path.abspath(self.OUTPUT_FILE)

# -------------------------
# Prompt (your YAML spec)
# -------------------------
OCR_PROMPT = r"""
I will upload an image containing vocabulary words with their meanings and example sentences.

Your tasks are:
1. For each vocabulary entry, extract:
   - word: the vocabulary word (lowercase unless it is a personal/proper name, in which case keep original capitalization). If the word is a verb, replace it with the infinitive form.
   - back: 
       * Start with the meaning.
       * If the word has a noun alternative add an explanation of the noun.
       * Then add 2–3 examples, all enclosed in a single bracket ("example sentence", "..."). 
         Examples should be realistic and varied in structure.
   - tags: grammatical category such as "noun", "verb", "adjective", "adverb", etc (could be many tags)

2. If any field is missing, try to infer or improve it:
   - If examples are missing or too few, create new ones (ensure at least 2–3 examples per word).
   - If the meaning can be improved for clarity, do so.
   - If the grammatical tag is unclear, deduce it from the word and context.
   - If the word is a verb, determine and include its infinitive in the back field as described.

3. Output the result as pure YAML with the following rules:
   - Use `-` (dash) for each list item, never `*` or any other symbol.
   - Indent all fields by two spaces under the dash.
   - Do not include Markdown formatting, backticks, or any text outside the YAML.
   - Ensure proper YAML syntax so it can be parsed without errors.

The required format example:

- word: example_word
  back: meaning (infinitive if verb). (_"example one"_) (_"example two"_) (_"example three"_)
  tags: noun

Return ONLY the YAML (preferably between triple backticks or nothing else). The input image path is provided below.
"""

# -------------------------
# Ollama CLI runner helper
# -------------------------
def run_ollama_cli(prompt: str, model_tag: str = "qwen2.5-vl:latest", timeout: int = 120) -> str:
    """
    Run local Ollama via the CLI and return the textual output.
    Tries multiple safe invocation methods (some Ollama CLI versions accept -p/--prompt,
    otherwise we pipe the prompt onto stdin).
    """
    # Prefer a short prompt by escaping it
    full_cmd_with_flag = ["ollama", "run", model_tag, "--prompt", prompt]
    try:
        # First attempt: pass prompt via --prompt (works on many versions)
        proc = subprocess.run(full_cmd_with_flag, capture_output=True, text=True, timeout=timeout)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout
        # If non-zero or no stdout, fall back to piping via stdin
    except FileNotFoundError:
        raise RuntimeError("The 'ollama' CLI was not found. Please install Ollama and ensure 'ollama' is on PATH.")
    except subprocess.SubprocessError as e:
        # we'll try fallback
        pass

    # Fallback: echo prompt | ollama run model (pipe)
    try:
        proc2 = subprocess.run(["ollama", "run", model_tag], input=prompt, capture_output=True, text=True, timeout=timeout)
        if proc2.returncode == 0:
            return proc2.stdout
        else:
            # surface error text
            raise RuntimeError(f"ollama returned non-zero exit code {proc2.returncode}:\n{proc2.stderr}\n{proc2.stdout}")
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Failed to invoke ollama CLI: {e}")

# -------------------------
# Main pipeline
# -------------------------
def process_vocab_image(image_path: str, model_tag: str = "qwen2.5-vl:latest"):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Create a compact prompt that includes the OCR_PROMPT and the image path
    prompt = OCR_PROMPT.strip() + "\n\n" + f"Image path: {image_path}\n\nPlease produce only the YAML following the spec."

    print("Sending prompt to local Ollama model (this may be slow on CPU).")
    raw_output = run_ollama_cli(prompt, model_tag=model_tag)
    print("Model output received (first 400 chars):\n", raw_output[:400].replace("\n", "\\n"))

    # Extract YAML block (prefer fenced or starting with '- ')
    yaml_block = None
    # 1) fenced YAML triple backticks
    m = re.search(r"```(?:yaml)?\s*(\-.*?)(?:```|$)", raw_output, flags=re.S)
    if m:
        yaml_block = m.group(1).strip()
    else:
        # 2) find block starting with dash
        m2 = re.search(r"(\n?- \w.*?)(?:\n\n|$)", raw_output, flags=re.S)
        if m2:
            yaml_block = m2.group(1).strip()
        else:
            # fallback: use entire output
            yaml_block = raw_output.strip()

    # If the model returned additional explanations before YAML, try to strip leading lines before first '-' list marker
    first_dash = yaml_block.find("\n- ")
    if first_dash != -1 and not yaml_block.lstrip().startswith("- "):
        yaml_block = yaml_block[first_dash + 1 :]  # include the leading "- "

    # Final clean: if still not starting with "- ", try to locate first "- word:" and slice
    if not yaml_block.lstrip().startswith("- "):
        m3 = re.search(r"(-\s+word:.*)", yaml_block, flags=re.S)
        if m3:
            yaml_block = m3.group(1).strip()

    print("Attempting to parse YAML block (first 300 chars):")
    print(yaml_block[:300].replace("\n", "\\n"))
    tool = YamlToAnkiTool()
    csv_path = tool.forward(yaml_block)
    print(f"✅ Wrote Anki CSV to: {csv_path}")
    return csv_path

# -------------------------
# CLI entrypoint
# -------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process vocabulary image -> Ollama -> YAML -> Anki CSV")
    parser.add_argument("image", help="Path to the vocabulary image (PNG/JPG/PDF page).")
    parser.add_argument("--model", default="qwen2.5vl:latest", help="Ollama model tag (default: qwen2.5-vl:latest)")
    args = parser.parse_args()

    try:
        csv_out = process_vocab_image(args.image, model_tag=args.model)
        print("Done. CSV:", csv_out)
    except Exception as e:
        print("Error:", e)
        raise

