VISION_FIRST_FRAME = (
    "You are analyzing a cooking/recipe video frame by frame."
    "Describe what you see in this first frame."
    "Focus on any ingredients, tools, or actions that are visible. "
)

VISION_SUBSEQUENT_FRAME = (
    "You are analyzing a cooking/recipe video frame by frame. "
    "Here are the descriptions of all previous frames:\n\n"
    "{history}\n\n"
    "Describe what you see in the current frame."
    "Focus on what is new or different. If nothing significant has changed, say so briefly."
)

COMPILE_DOCUMENT = """You are analyzing a recipe video. Format the output as **Markdown**.

VIDEO METADATA:
Title: {title}
Uploader: {uploader}
Original Description: {description}

VISUAL TIMELINE (key moments):
{visual_timeline}

AUDIO TRANSCRIPT:
{transcript}

Create a comprehensive recipe document in Markdown including:
1. Recipe title as `# Title`
2. Complete ingredients list with quantities. Use the measurement units in from the given context,
but also give measurements in grams in brackets next to the original measurement. Also,
Format the ingredients list as a task list using - [ ] <ingredient>.(use `## Ingredients` header)
3. Step-by-step numbered instructions (use `## Instructions` header)
4. Cooking time and servings
5. Any tips, techniques, or variations mentioned (use `## Notes` header)
6. Equipment needed (use `## Equipment` header)

Output raw Markdown only. Do NOT wrap the output in a code block or use triple backticks.
Make sure that the ingredients are actually used in the recipe steps."""

GENERATE_RECIPE_NAME = """Based on the recipe below, give it a short, descriptive name (3-5 words max).
Return ONLY the name in Title Case with no punctuation, no quotes, no explanation.
Example: Spicy Garlic Shrimp Pasta

Recipe:
{recipe_document}"""
