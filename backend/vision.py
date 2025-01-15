import base64
import os
import json
import re
from openai import ChatCompletion, OpenAIError
from dotenv import load_dotenv
import openai
from PIL import Image
import tiktoken  # Make sure to install this library

# Load environment variables from the 'key' folder
load_dotenv(os.path.join('key', '.env'))
print(f"Loaded API Key: {os.getenv('OPENAI_API_KEY')}")  # Debugging line

def encode_image(image_path):
    print(f"Encoding image: {image_path}")
    # Resize the image to a smaller size (e.g., 800x800)
    with Image.open(image_path) as img:
        img = img.resize((800, 800), Image.LANCZOS)  # Use LANCZOS for high-quality downsampling
        img.save("temp_resized_image.webp", format="WEBP")  # Save resized image temporarily
        with open("temp_resized_image.webp", "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
    print(f"Encoded image for {image_path}")
    return encoded

def extract_json(raw_response):
    try:
        # Use regex to extract JSON block from the response
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            raise ValueError("No valid JSON found in the response.")
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        raise

def count_tokens(messages):
    encoding = tiktoken.encoding_for_model("gpt-4")
    return sum(len(encoding.encode(message["content"])) for message in messages)

def process_images(image_paths, output_folder="processed_data"):
    os.makedirs(output_folder, exist_ok=True)  # Ensure output folder exists
    print(f"Processing images: {image_paths}")

    openai.api_key = os.getenv("OPENAI_API_KEY")

    output_files = []

    for image_path in image_paths:
        try:
            print(f"Processing image at {image_path}")
            base64_img = f"data:image/{image_path.rsplit('.', 1)[1].lower()};base64,{encode_image(image_path)}"
            
            response = openai.ChatCompletion.create(
                model='gpt-4o-mini',
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": (
                                "Analyze the following image carefully. Identify all visible ingredients and "
                                "provide a detailed JSON document listing each ingredient with its name and type (e.g., "
                                "vegetable, fruit, protein, spice, etc.). If possible, include additional metadata like "
                                "approximate quantity or form (e.g., chopped, whole, liquid). Ensure no ingredient is missed."
                            )},
                            {"type": "image_url", "image_url": {"url": base64_img}}
                        ]
                    }
                ],
                max_tokens=750,
            )

            raw_response = response.choices[0].message.content.strip()
            print(f"Raw JSON response for {image_path}: {raw_response}")
            
            # Extract valid JSON data
            json_data = extract_json(raw_response)
            filename = os.path.splitext(os.path.basename(image_path))[0]
            output_file = os.path.join(output_folder, f"{filename}_data.json")
            
            with open(output_file, 'w') as file:
                json.dump(json_data, file, indent=4)
            print(f"Processed data saved to {output_file}")

            output_files.append(output_file)

        except (OpenAIError, ValueError) as e:
            print(f"Error processing {image_path}: {e}")
            continue

    print(f"All processed files: {output_files}")
    return output_files
if __name__ == "__main__":
    # Example usage
    image_folder = r"C:\Users\Code\Code\nosu\image"  # Specify your image folder here
    if not os.path.exists(image_folder):
        print(f"Error: The specified image folder does not exist: {image_folder}")
    else:
        image_paths = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(('.jpg', '.jpeg', '.png', 'webp'))]
        process_images(image_paths)