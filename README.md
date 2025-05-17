# Automated CTI Report Generator using Gemini

This project provides a Python script to automate the generation of Cyber Threat Intelligence (CTI) reports and a malware relationship diagram based on text analysis outputs from various tools or manual notes. It leverages the Google Gemini API to process the input text and generate structured markdown reports and Mermaid diagram syntax.

The script is designed to be customizable through a configuration file (`config.yaml`) and external prompt templates.

## Features

* **Automated Reporting:** Generates a multi-part CTI report based on your analysis notes.
* **Mermaid Diagram:** Creates a visual representation of the threat based on the provided data.
* **Customizable Prompts:** Tailor the prompts used by Gemini to control the report's focus and format.
* **Configurable Settings:** Easily adjust input/output paths, Gemini models, generation parameters, and safety settings.
* **Chat Interface:** Interact with Gemini after report generation to ask follow-up questions about the analysis data.
* **Input Flexibility:** Processes multiple text files from a specified directory.

## Project Structure
cti-report-generator/
├── generate_report.py          # The main script
├── config.yaml                 # Configuration file
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── input_scripts/              # Directory for your input analysis scripts
│   └── sample_analysis.txt     # Example input file
├── prompts/                    # Directory for prompt templates
│   ├── part1_prompt.txt        # Prompt for report part 1
│   ├── part2_prompt.txt        # Prompt for report part 2
│   └── mermaid_prompt.txt      # Prompt for the Mermaid diagram
└── .gitignore                  # Files to ignore


## Prerequisites

* Python 3.7+
* A Google AI API Key. You can obtain one from the [Google AI Studio](https://aistudio.google.com/fundamentals/api_key).
* Internet connection to access the Gemini API.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_GITHUB_USERNAME/cti-report-generator.git](https://github.com/YOUR_GITHUB_USERNAME/cti-report-generator.git)
    cd cti-report-generator
    ```
    *(Replace `YOUR_GITHUB_USERNAME/cti-report-generator` with your actual GitHub path after you create the repository)*

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your Google AI API Key:**
    The script reads your API key from an environment variable specified in `config.yaml` (default is `GOOGLE_API_KEY`).
    * **Linux/macOS:**
        ```bash
        export GOOGLE_API_KEY='YOUR_API_KEY'
        # Add this line to your shell profile (~/.bashrc, ~/.zshrc, etc.) to make it permanent
        ```
    * **Windows (Command Prompt):**
        ```cmd
        set GOOGLE_API_KEY=YOUR_API_KEY
        rem For permanent effect, set it via System Properties -> Environment Variables
        ```
    * **Windows (PowerShell):**
        ```powershell
        $env:GOOGLE_API_KEY="YOUR_API_KEY"
        # For permanent effect, set it via System Properties -> Environment Variables
        ```
    *(Replace `YOUR_API_KEY` with your actual key)*

## Configuration

Edit the `config.yaml` file to customize the script's behavior:

* `api_key_env_var`: The name of the environment variable holding your API key.
* `input.directory`: The path to the directory containing your analysis text files.
* `input.file_pattern`: The glob pattern to select files (e.g., `*.txt`).
* `output.directory`: The path where generated files will be saved.
* `output.base_filename`: The base name for output files.
* `models.report_model`: The Gemini model for report generation.
* `models.other_model`: The Gemini model for diagrams and chat.
* `generation_configs.report_generation` / `other_generation`: Fine-tune model parameters like `temperature`, `max_output_tokens`.
* `safety_settings`: Adjust content safety blocking thresholds.
* `report_settings.interval_seconds`: The pause duration between report parts.
* `prompts.part1_file`, `prompts.part2_file`, `prompts.mermaid_file`: Paths to your custom prompt files.

## Input Scripts

Place your malware analysis text files (outputs from static/dynamic analysis tools, manual notes, etc.) into the directory specified by `input.directory` in `config.yaml` (default: `input_scripts/`). The script will concatenate the content of all files matching the `file_pattern`.

Ensure sensitive information in input files is handled appropriately before processing with an external API.

## Customizing Prompts

The script uses template files in the `prompts/` directory. These files contain the instructions given to the Gemini model.

* `part1_prompt.txt`: Defines the instructions for generating the first part of the report.
* `part2_prompt.txt`: Defines the instructions for generating the second part of the report.
* `mermaid_prompt.txt`: Defines the instructions for generating the Mermaid syntax diagram.

You can edit these files to change the structure, focus, language, or required output format of the generated content. The script will automatically replace the placeholder `{script_content}` within these files with the combined content of your input analysis scripts.

## Running the Script

Navigate to the project root directory in your terminal and run:

```bash
python generate_report.py

The script will load your data, interact with the Gemini API, save the output files, and then start an interactive chat session.


## Output

The generated files will be saved in the directory specified by output.directory (default: output/) with names based on output.base_filename:

* [base_filename]_part1.md
* [base_filename]_part2.md
* [base_filename]_diagram.md (contains the Mermaid syntax within a markdown code block)

You can use tools that support Mermaid syntax (like GitHub markdown, Mermaid Live Editor, VS Code extensions) to render the diagram.

## Chat System

After the reports and diagram are generated, the script will start a simple chat interface. You can type questions about the malware analysis data or the generated report content, and Gemini will respond. Type exit or quit to end the chat.

## Troubleshooting

* API Key Error: Ensure the environment variable (GOOGLE_API_KEY or whatever you set in config.yaml) is correctly set in your terminal session before running the script. Double-check the key itself.
* File Not Found: Verify that the input.directory and prompts file paths in config.yaml are correct and exist relative to where you run generate_report.py or are absolute paths.
* No Input Files Found: Check the input.directory and input.file_pattern in config.yaml and ensure there are files matching the pattern in that directory.
* Generation Errors/Safety Blocks: Review the console output for error messages or safety feedback from the API. Adjust your input data, prompts, or the safety_settings in config.yaml if necessary. The model might also block if the input content is flagged.
* Output Files Not Created: Check the output.directory in config.yaml and ensure the script has permissions to create directories and files there.

## Contributing

Feel free to fork the repository, open issues, and submit pull requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details. (You'll need to add a https://www.google.com/search?q=LICENSE file with the MIT license text).   

## Disclaimer

This script uses an AI model for report generation. The output should be reviewed and validated by a human analyst before being used for critical decisions or disseminated as final intelligence. AI models can hallucinate or misinterpret data.

---

**5. `input_scripts/sample_analysis.txt` (Example Input)**

Create this directory and file with some sample text.

```txt
# Sample Analysis Output - FileA.txt

Observed process: explorer.exe spawns malicious.dll via rundll32.exe.
Persistence mechanism: Adds a run key in the registry: HKCU\Software\Microsoft\Windows\CurrentVersion\Run "MalwareLoader" = "rundll32.exe C:\Users\Public\malicious.dll"
Network activity: Connects to 192.168.1.100 on port 443. Sends data.
Files created: C:\Users\Public\malicious.dll (MD5: abc123def456), C:\Temp\temp_data.bin

---

# Sample Analysis Output - FileB.txt

Process: Identified process `malicious.dll` performing browser hook injections. Targets Chrome, Firefox.
Technique: Uses API hooking to steal cookies and auto-fill data.
Exfiltration: Data is POSTed to hxxps://malware-c2.evilcorp.com/upload
Detected Mutex: Global\MalwareMutex_XCS

---

# Sample Analysis Output - FileC.txt

Additional persistence: Scheduled Task "MalwareUpdateCheck" runs daily, executing C:\Program Files\Common Files\Updater\update.exe (SHA256: xyz789abc123).
Lateral movement: Attempts SMB connections to internal IPs using stolen credentials.
Payload: Appears to download and execute secondary payloads based on C2 response.

