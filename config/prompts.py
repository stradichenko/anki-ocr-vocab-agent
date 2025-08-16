"""Prompt templates for OCR and vocabulary processing."""

OCR_PROMPT = """
You are a Vision Language Model analyzing a vocabulary image.

CRITICAL RULES:
1. Look at the provided image and extract ONLY real content you can see
2. DO NOT generate fake data like "word1", "word2", "definition1", "example1"
3. If you cannot see the image clearly, say "Cannot process image visually"

TASK:
Examine the image and extract vocabulary words, definitions, and examples.
Format as YAML and call yaml_to_anki.

YAML FORMAT:
- word: [real word from image]
  back: '[real definition] ("[real example 1]", "[real example 2]")'
  tags: [part of speech]

EXAMPLE TOOL CALL:
<code>
yaml_content = '''- word: magnificent
  back: 'extremely beautiful or impressive ("The view was magnificent", "She gave a magnificent performance")'
  tags: adjective'''
yaml_to_anki(yaml_content)
</code>

Extract ONLY what you actually see in the image!
"""
