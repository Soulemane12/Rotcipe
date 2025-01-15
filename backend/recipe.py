import os
from julep import Julep
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../key', '.env'))

# Check if the API key is set
if not os.getenv("JULEP_API_KEY"):
    raise ValueError("JULEP_API_KEY environment variable is not set.")

# Initialize Julep client
client = Julep(api_key=os.getenv("JULEP_API_KEY"))

# Initialize Julep agent
try:
    agent = client.agents.create(
        name="Recipe Creator",
        model="gpt-4o",
        about="You create funny and creative recipes using modern slang."
    )
    print("Julep Agent created successfully.")
except Exception as e:
    print(f"Error creating Julep Agent: {str(e)}")
    agent = None


def generate_funny_recipe(ingredients, output_file="funny_generated_recipe.txt"):
    """
    Generate a recipe using the Julep API from a list of ingredients, adding humor with modern slang.

    Args:
        ingredients (list): List of ingredient names.
        output_file (str): File to save the generated recipe.

    Returns:
        str: Generated recipe as a string.
    """
    if not ingredients:
        print("No ingredients provided. Cannot generate a recipe.")
        return ""

    if agent is None:
        print("Julep Agent not initialized. Skipping recipe generation.")
        return ""

    # Prepare the prompt for recipe generation
    ingredient_list = ", ".join(ingredients)
    prompt = f"""
    You are a master chef and Gen Z comedian. Create a hilarious recipe using only the following ingredients:

    Main ingredients: {ingredient_list}

    You may add common condiments, seasonings, or spices (e.g., salt, pepper, olive oil, soy sauce) as needed.
    
    Important style guidelines:
    1. Use these trendy terms and slang throughout the recipe:
       - "Skibidi" (reference to YouTube series)
       - "Rizz" (charm/charisma)
       - "Gyatt" (exclamation of amazement)
       - "Fanum tax" (stealing food)
       - "Sigma" (alpha male behavior)
       - "Delulu" (delusional)
       - "Bussin'" (amazing/great)
       - "No cap" (not lying)
       - "Demure" (elegant)
       - "Ick" (something you don't vibe with)
       - "GYAT" (God damn)
       - "Mewing" (jaw exercise)
       - "NPC" (basic behavior)
       - "Ohio" (weird/strange)
       
    2. Write in a very Gen Z style, mixing these terms naturally into the recipe steps
    3. Include cooking time and serving suggestions
    4. Do not use any asterisks (*) or markdown formatting like hashtags (#)
    
    Example style:
    "No cap, this recipe is about to be bussin fr fr. First step: Start mewing while you prep these skibidi ingredients like a true sigma."
    """

    # Send task to Julep agent
    try:
        task = client.tasks.create(
            agent_id=agent.id,
            name="Generate Funny Recipe",
            description="Generate a funny recipe using Gen Z slang.",
            main=[
                {
                    "prompt": [
                        {"role": "system", "content": "You are a Gen Z chef creating recipes with modern internet slang. Do not use asterisks or markdown formatting."},
                        {"role": "user", "content": prompt}
                    ],
                    "return": {"result": "Generated funny recipe as text."}
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

        if result.status == "succeeded":
            if "choices" in result.output and len(result.output["choices"]) > 0:
                recipe = result.output["choices"][0]["message"]["content"]
                # Remove any remaining asterisks from the response
                recipe = recipe.replace('*', '')
                print("Recipe generation succeeded.")
            else:
                print("No 'choices' found in the output.")
                return ""
        else:
            print(f"Julep task failed: {result.error}")
            return ""

    except Exception as e:
        print(f"Error generating recipe with Julep: {e}")
        return ""

    # Save the recipe to a file
    try:
        with open(output_file, 'w') as f:
            f.write(recipe)
        print(f"Generated funny recipe saved to {output_file}")
    except Exception as e:
        print(f"Error saving recipe to file {output_file}: {e}")

    return recipe


if __name__ == "__main__":
    # Example usage
    ingredient_file = "combined_ingredients.txt"  # Output from the previous script

    try:
        with open(ingredient_file, 'r') as f:
            ingredients = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"Error reading ingredient file {ingredient_file}: {e}")
        ingredients = []

    recipe = generate_funny_recipe(ingredients)
    print("Generated Funny Recipe:")
    print(recipe)
