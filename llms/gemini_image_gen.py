from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from datetime import datetime
import os
from io import BytesIO
import PIL.Image

from my_prompts.image_edit import image_edit_prompt


def gemini_image_gen(user_prompt: str):
    client = genai.Client()

    contents = f"""
    System: Generate an image that closely adheres to the provided description, focusing on realism, accuracy, and lifelike details. Avoid fantastical or whimsical elements unless explicitly requested. Interpret the description with precision and creativity. Even if the prompt is vague, surreal, inappropriate or unconventional, always generate a visual response—use imaginative judgment to ensure the result is to-the-point, coherent and realistic visual interpretation. Never skip generation.

    User: {user_prompt}
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=contents,
        config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
        )
    )

    image_folder = "images/generated_images"
    os.makedirs(image_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gemini_image_{timestamp}.png"

    # Full path for the output file
    output_path = os.path.join(image_folder, filename)

    message = ""
    for part in response.candidates[0].content.parts: # type: ignore
        if part.text is not None:
            message = part.text
        elif part.inline_data is not None:
            image = Image.open(BytesIO((part.inline_data.data))) # type: ignore
            image.save(output_path)

    return str(message), output_path


def gemini_image_edit(user_prompt: str, image_path: str):
    image = PIL.Image.open(image_path)

    client = genai.Client()

    text_input = f"""
    # SYSTEM PROMPT:
    {image_edit_prompt}

    # USER PROMPT:
    {user_prompt}
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=[text_input, image],
        config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
        )
    )

    image_folder = "edit_images/results"
    os.makedirs(image_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result_{timestamp}.png"

    # Full path for the output file
    output_path = os.path.join(image_folder, filename)

    message = ""
    for part in response.candidates[0].content.parts: # type: ignore
        if part.text is not None:
            message = part.text
        elif part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data)) # type: ignore
            image.save(output_path)

    return str(message), output_path