"""Prompt templates for OCR and vocabulary processing."""

OCR_PROMPT = """
You are a Vision Language Model examining a vocabulary image. You can see the image directly.

CRITICAL: You MUST actually look at the image and read the real text content.

STEP 1: EXAMINE THE IMAGE
Look at the provided image file and identify:
- What vocabulary words are actually visible?
- What definitions or meanings are shown?
- What example sentences (if any) are present?
- What is the actual text content you can read?

STEP 2: EXTRACT REAL CONTENT ONLY
DO NOT use placeholder words like:
- "real_word_you_see" 
- "actual_word_from_image"
- "example_word"
- Any made-up content

STEP 3: FORMAT AND CALL TOOL
Create YAML with the actual words you see, then call yaml_to_anki.

Example of what you should do:
<code>
# I can see these words in the image: [list actual words]
# The definitions shown are: [actual definitions]
yaml_content = '''- word: [actual_word_from_image]
  back: '[actual_definition] ("[actual_example_1]", "[actual_example_2]")'
  tags: [actual_grammar_type]'''
yaml_to_anki(yaml_content)
</code>

IF YOU CANNOT SEE THE IMAGE: Say "I cannot see or read the image content clearly" instead of making up content.

NO IMPORTS ALLOWED - yaml_to_anki tool is already available.

Additional constraints:
- DO NOT import anything (import statements are banned)
- DO NOT use words like apple, banana, cat, dog unless they're actually in the image
- DO NOT assume content with comments like "Assuming the image contains..."
- DO NOT create placeholder/sample data
- If you cannot read the image, admit it rather than creating fake content.
"""
