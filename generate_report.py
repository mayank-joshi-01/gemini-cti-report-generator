# -*- coding: utf-8 -*-
"""
Generates a Cyber Threat Intelligence (CTI) report in two parts with an interval,
including a Mermaid diagram and a chat interface for further interaction with Gemini,
based on analysis scripts provided in a specified input directory.
Configuration is loaded from config.yaml.
"""

import google.generativeai as genai
import os
import glob
import sys
import time
import yaml
from datetime import datetime

# --- Load Configuration ---
CONFIG_FILE = "config.yaml"

def load_config(config_file):
    """Loads configuration from a YAML file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"Configuration loaded from {config_file}")
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_file}.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file {config_file}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred loading config: {e}")
        sys.exit(1)

config = load_config(CONFIG_FILE)

# --- API Key Configuration ---
try:
    api_key = os.environ.get(config['api_key_env_var'])
    if not api_key:
        raise ValueError(f"Environment variable '{config['api_key_env_var']}' is not set or is empty.")
    genai.configure(api_key=api_key)
    print("Google API Key configured.")
except KeyError:
     print(f"Error: Configuration missing 'api_key_env_var'. Please check {CONFIG_FILE}.")
     sys.exit(1)
except ValueError as e:
    print(f"API Key Configuration Error: {e}")
    print(f"Please set the environment variable '{config.get('api_key_env_var', 'GOOGLE_API_KEY')}' with your API key.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during API key setup: {e}")
    sys.exit(1)


# --- Function to Load Script Files ---
def load_scripts(directory, pattern):
    """Loads content from script files matching a pattern in a directory."""
    script_contents = []
    # Use abspath to be sure where we are looking
    absolute_directory = os.path.abspath(directory)
    search_path = os.path.join(absolute_directory, pattern)
    file_paths = glob.glob(search_path)

    print(f"\nSearching for scripts in: {search_path}")

    if not file_paths:
        print(f"Warning: No files found matching pattern '{pattern}' in directory '{absolute_directory}'.")
        print("Please ensure your analysis scripts are in the correct directory.")
        return None

    print(f"Found {len(file_paths)} script files to process:")
    for i, file_path in enumerate(sorted(file_paths)):
        filename = os.path.basename(file_path)
        print(f"  - Reading: {filename}")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Add markers to identify source files in the combined content
                content = f"--- Start of Content from {filename} ---\n\n"
                content += f.read()
                content += f"\n\n--- End of Content from {filename} ---"
                script_contents.append(content)
        except FileNotFoundError:
            print(f"Warning: File not found {file_path} during iteration, skipping.") # Should not happen with glob, but for safety
        except Exception as e:
            print(f"Error reading file {file_path}: {e}, skipping.")

    if not script_contents:
        print("Error: No script content could be loaded successfully.")
        return None

    return "\n\n".join(script_contents)

# --- Function to Estimate Token Count ---
# Note: This is a rough estimate. The actual token count might differ.
def estimate_tokens(text):
    """Estimates the number of tokens in a text string."""
    return len(text) / 4 # A common heuristic, not precise

# --- Function to Load Prompt Template ---
def load_prompt_template(filepath):
    """Loads a prompt template from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Prompt template file not found at {filepath}.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading prompt template {filepath}: {e}")
        sys.exit(1)

# --- Function to Generate Content using Gemini ---
def generate_content(prompt, model_name, generation_config, safety_settings, task_description="content"):
    """Helper function to generate content using Gemini."""
    print(f"\n[Generating {task_description}...] This may take some time...")
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    try:
        response = model.generate_content(prompt)
        # Check for empty response or safety blocks
        if response is None or not response.text:
             feedback = response.prompt_feedback if response else "No response object"
             return None, feedback, f"Empty response or safety block: {feedback}"
        return response.text, response.prompt_feedback, None
    except Exception as e:
        return None, None, f"Error generating {task_description}: {e}"


# --- Main Execution ---
if __name__ == "__main__":
    print("--- Automated CTI Report Generator using Gemini ---")

    # --- Configuration Values ---
    input_directory = config['input']['directory']
    script_file_pattern = config['input']['file_pattern']
    output_directory = config['output']['directory']
    output_base_filename = config['output']['base_filename']
    report_interval_seconds = config['report_settings']['interval_seconds']

    report_model = config['models']['report_model']
    other_model = config['models']['other_model']

    safety_settings_config = config['safety_settings']
    report_generation_config = config['generation_configs']['report_generation']
    other_generation_config = config['generation_configs']['other_generation']

    part1_prompt_file = config['prompts']['part1_file']
    part2_prompt_file = config['prompts']['part2_file']
    mermaid_prompt_file = config['prompts']['mermaid_file']


    # --- Ensure Output Directory Exists ---
    try:
        os.makedirs(output_directory, exist_ok=True)
        print(f"\nEnsured output directory exists: {os.path.abspath(output_directory)}")
    except Exception as e:
        print(f"Error creating output directory {output_directory}: {e}")
        sys.exit(1)

    # --- Load Data and Prompts ---
    print("\n[Step 1/5] Loading input script data...")
    all_scripts_content = load_scripts(input_directory, script_file_pattern)

    if not all_scripts_content:
        print("\nCritical Error: Failed to load input scripts. Exiting.")
        sys.exit(1)

    print("\n[Step 2/5] Loading prompt templates...")
    part1_prompt_template = load_prompt_template(part1_prompt_file)
    part2_prompt_template = load_prompt_template(part2_prompt_file)
    mermaid_prompt_template = load_prompt_template(mermaid_prompt_file)

    # --- Estimate Input Size ---
    print(f"\nEstimating combined input size...")
    estimated_input_tokens = estimate_tokens(all_scripts_content)
    print(f"  - Estimated input tokens: ~{estimated_input_tokens:.0f}")

    # --- Prepare Prompts with Data ---
    final_prompt_part_1 = part1_prompt_template.format(script_content=all_scripts_content)
    final_prompt_part_2 = part2_prompt_template.format(script_content=all_scripts_content)
    final_prompt_mermaid = mermaid_prompt_template.format(script_content=all_scripts_content)


    # --- Generate Report Part 1 ---
    print("\n[Step 3/5] Starting Report Part 1 generation...")
    report_part_1, feedback_part_1, error_part_1 = generate_content(
        final_prompt_part_1,
        report_model,
        report_generation_config,
        safety_settings_config,
        "CTI Report Part 1"
    )

    if report_part_1:
        print("\n--- Generated CTI Report (Part 1) ---")
        # print(report_part_1) # Optionally print to console
        # Save Part 1
        output_filename_part_1 = os.path.join(output_directory, f"{output_base_filename}_part1.md")
        try:
            with open(output_filename_part_1, "w", encoding="utf-8") as f:
                f.write(f"# XCSSET Malware 2025: Updated Techniques and Payloads (Part 1)\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("---\n\n")
                f.write(report_part_1)
            print(f"\nReport Part 1 successfully saved to: {output_filename_part_1}")
        except Exception as e:
            print(f"\nError saving Report Part 1: {e}")
    else:
        print("\n--- Report Part 1 Generation Failed ---")
        if error_part_1:
            print(f"Error: {error_part_1}")
        if feedback_part_1:
            print(f"Prompt Feedback (Part 1): {feedback_part_1}")
            # Potentially print safety ratings for debugging
            # print(f"Safety Ratings (Part 1): {feedback_part_1.safety_ratings}")


    print(f"\nWaiting for {report_interval_seconds} seconds before generating Part 2...")
    time.sleep(report_interval_seconds)

    # --- Generate Report Part 2 ---
    print(f"\n[Step 4/5] Starting Report Part 2 generation...")
    report_part_2, feedback_part_2, error_part_2 = generate_content(
        final_prompt_part_2,
        report_model,
        report_generation_config,
        safety_settings_config,
        "CTI Report Part 2"
    )

    if report_part_2:
        print("\n--- Generated CTI Report (Part 2) ---")
         # print(report_part_2) # Optionally print to console
        # Save Part 2
        output_filename_part_2 = os.path.join(output_directory, f"{output_base_filename}_part2.md")
        try:
            with open(output_filename_part_2, "w", encoding="utf-8") as f:
                f.write(f"# XCSSET Malware 2025: Updated Techniques and Payloads (Part 2)\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("---\n\n")
                f.write(report_part_2)
            print(f"\nReport Part 2 successfully saved to: {output_filename_part_2}")
        except Exception as e:
            print(f"\nError saving Report Part 2: {e}")
    else:
        print("\n--- Report Part 2 Generation Failed ---")
        if error_part_2:
            print(f"Error: {error_part_2}")
        if feedback_part_2:
            print(f"Prompt Feedback (Part 2): {feedback_part_2}")
             # Potentially print safety ratings for debugging
            # print(f"Safety Ratings (Part 2): {feedback_part_2.safety_ratings}")

    # --- Generate Mermaid Diagram ---
    print(f"\n[Step 5/5] Starting Mermaid Diagram generation...")
    mermaid_syntax, feedback_mermaid, error_mermaid = generate_content(
        final_prompt_mermaid,
        other_model,
        other_generation_config,
        safety_settings_config,
        "Mermaid Diagram"
    )

    if mermaid_syntax:
        print("\n--- Generated Mermaid Diagram ---")
        # print(mermaid_syntax) # Optionally print to console
        # Save Mermaid syntax to a file
        mermaid_filename = os.path.join(output_directory, f"{output_base_filename}_diagram.md")
        try:
            with open(mermaid_filename, "w", encoding="utf-8") as f:
                f.write(f"# XCSSET Malware 2025: Relationship Diagram\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("---\n\n")
                f.write("```mermaid\n")
                # Clean up potential markdown block from the model's response
                mermaid_syntax = mermaid_syntax.strip()
                if mermaid_syntax.startswith("```mermaid"):
                     mermaid_syntax = mermaid_syntax[len("```mermaid"):].strip()
                if mermaid_syntax.endswith("```"):
                     mermaid_syntax = mermaid_syntax[:-len("```")].strip()

                f.write(mermaid_syntax)
                f.write("\n```")
            print(f"\nMermaid diagram syntax saved to: {mermaid_filename}")
        except Exception as e:
            print(f"\nError saving Mermaid diagram: {e}")
    else:
        print("\n--- Mermaid Diagram Generation Failed ---")
        if error_mermaid:
            print(f"Error: {error_mermaid}")
        if feedback_mermaid:
            print(f"Prompt Feedback (Mermaid): {feedback_mermaid}")
            # Potentially print safety ratings for debugging
            # print(f"Safety Ratings (Mermaid): {feedback_mermaid.safety_ratings}")


    # --- Chat System ---
    print("\n--- Starting Chat System ---")
    print("You can now ask questions about the malware scripts and generated report content.")
    print("Type 'exit' or 'quit' to end the chat.")

    # Start a new chat session
    # You might want to initialize the chat with some context, e.g., the combined script content
    # chat = chat_model.start_chat(history=[{'role': 'user', 'parts': [all_scripts_content]}])
    # For simplicity, let's start a fresh chat, relying on the model's general knowledge
    # or the ability to reference recent context depending on the model version.
    # Using the 'other_model' for chat as it might be configured differently from the report model
    try:
        chat_model = genai.GenerativeModel(
             model_name=other_model,
             generation_config=other_generation_config,
             safety_settings=safety_settings_config
        )
        chat = chat_model.start_chat() # Start a blank chat history
        print("Chat session started.")
    except Exception as e:
         print(f"\nError initializing chat model: {e}")
         chat = None # Disable chat if initialization fails


    if chat:
        while True:
            try:
                user_input = input("\nAsk Gemini > ")
                if user_input.lower() in ['exit', 'quit']:
                    break

                # Prepend context to the user input for the chat? Or rely on chat history?
                # For simplicity, let's just send the user input directly to the model.
                # If the model struggles with context, you might need to engineer the chat prompt.
                response = chat.send_message(user_input)
                print(f"Gemini > {response.text}")

            except Exception as e:
                print(f"Error during chat interaction: {e}")
                # Optionally, break the loop on persistent errors
                # break

    print("\n--- Chat System Ended ---")
    print("\n--- Script Finished ---")
