OCR_PROMPT = """
You are analyzing a vocabulary image with your vision capabilities.

TASK:
Extract all vocabulary words, their definitions, and example sentences from the image.

PROCESS:
1. Visually read the image.
2. Identify vocabulary entries (word, definition, part of speech, examples).
3. Format them in the following YAML structure.
4. Call the tool `yaml_to_anki(yaml_content)` with your YAML output.

YAML FORMAT:
- word: [word from image]
  back: '[definition] ("[example 1]", "[example 2]")'
  tags: [part of speech]

EXAMPLE:

yaml_content = '''- word: meticulous
  back: 'extremely careful and precise ("He is meticulous", "Finish it meticulously")'
  tags: adjective'''
yaml_to_anki(yaml_content)

IMPORTANT RULES:
- Only extract what is actually visible in the image.
- If you cannot read the image, output: "Cannot process image visually" and stop.
- Do not generate placeholder or assumed content.
- Do not import libraries or decode text manually.
- Do not use example words like apple, banana, etc. unless they are really in the image.
"""
