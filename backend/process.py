import os
import json
from julep import Julep
from dotenv import load_dotenv
import time
import ast

# Load environment variables
load_dotenv(os.path.join('key', '.env'))

# Initialize Julep client
client = Julep(api_key=os.getenv("JULEP_API_KEY"))

# Initialize Julep agent
try:
    agent = client.agents.create(
        name="Ingredient Refiner",
        model="gpt-4o",
        about="You refine and organize ingredient lists from extracted JSON data."
    )
    print("Julep Agent created successfully.")
except Exception as e:
    print(f"Error creating Julep Agent: {str(e)}")
    agent = None

def process_ingredient_json(input_files, output_file="combined_ingredients.txt"):
    """
    Process extracted JSON files to refine ingredient lists using Julep API.
    
    Args:
        input_files (list): List of JSON file paths containing extracted ingredient data.
        output_file (str): Output file to save refined ingredient list.
        
    Returns:
        list: Refined ingredient names.
    """
    combined_data = []
    
    print(f"Combining data from files: {input_files}")

    # Combine data from all JSON files
    for file in input_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                if "ingredients" in data:
                    combined_data.extend(data["ingredients"])
        except Exception as e:
            print(f"Error reading file {file}: {e}")
            continue

    # Extract ingredient descriptions
    print("Extracting ingredients...")
    ingredients = [item["name"] for item in combined_data if isinstance(item, dict) and "name" in item]

    if not ingredients:
        print("No ingredients found. Exiting.")
        return []

    # Prepare text for Julep processing
    raw_text = "\n".join(ingredients)
    prompt = f"Please refine the following ingredient list into distinct names, separated by commas:\n\n{raw_text}"

    if agent is None:
        print("Julep Agent not initialized. Skipping refinement.")
        return ingredients

    # Send prompt to Julep agent using Julep's API
    try:
        task = client.tasks.create(
            agent_id=agent.id,
            name="Refine Ingredient List",
            description="Process and deduplicate a list of ingredients.",
            main=[
                {
                    "prompt": [
                        {"role": "system", "content": "You refine and deduplicate ingredient lists."},
                        {"role": "user", "content": prompt}
                    ],
                    "return": {"result": "Extracted and refined ingredient list as comma-separated values."}
                }
            ]
        )
        print("Task created. Waiting for execution result...")

        # Execute the task
        execution = client.executions.create(task_id=task.id, input={})
        while True:
            result = client.executions.get(execution.id)
            if result.status in ["succeeded", "failed"]:
                break
            print("Processing...")
            time.sleep(1)

        # Log the full output for debugging
        print(f"Execution result output: {result.output}")

        if result.status == "succeeded":
            if "choices" in result.output and len(result.output["choices"]) > 0:
                refined_text = result.output["choices"][0]["message"]["content"]
                refined_ingredients = [item.strip() for item in refined_text.split(",") if item.strip()]
            else:
                print("No 'choices' found in the output.")
                return ingredients
        else:
            print(f"Julep task failed: {result.error}")
            return ingredients

    except Exception as e:
        print(f"Error processing with Julep: {e}")
        return ingredients

    # Save refined ingredients to output file
    try:
        with open(output_file, 'w') as f:
            f.write("\n".join(refined_ingredients))
        print(f"Refined ingredients saved to {output_file}")
    except Exception as e:
        print(f"Error saving to file {output_file}: {e}")

    return refined_ingredients

if __name__ == "__main__":
    # Example usage
    output_folder = r"processed_data"  # Folder containing the JSON output of the first script
    input_files = [os.path.join(output_folder, file) for file in os.listdir(output_folder) if file.endswith(".json")]
    
    refined_ingredients = process_ingredient_json(input_files)
    print(f"Refined Ingredients: {refined_ingredients}")
