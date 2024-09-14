# Ansible Playbook Generator for Cisco DNAC Site Creation

## Overview

This project is an interactive Ansible playbook generator for Cisco DNA Center (DNAC) site creation. It uses Chainlit to provide a chat-like interface where users can input information, and the system generates an Ansible playbook based on the provided details.

## Features

- Interactive chat interface for collecting playbook information
- Automatic generation of Ansible playbooks for DNAC site creation
- Real-time updates of playbook status
- Validation of user inputs
- Persistent storage of playbook status

## Project Structure

project_root/
│
├── app.py # Main application file
├── prompts.py # Contains prompt templates
├── requirements.txt # Python dependencies
├── playbook_status.json # Stores the current playbook status
└── README.md # This file


## Prerequisites

- Python 3.7+
- pip (Python package manager)

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <project-directory>
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   Create a `.env` file in the project root and add the following:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

## Running the Application

To start the Chainlit application, run:


This will start the server, and you can access the chat interface by opening a web browser and navigating to `http://localhost:8000` (or the URL provided in the console output).

## Using the Playbook Generator

1. Open the chat interface in your web browser.
2. Start by providing the required information for the DNAC site creation playbook:
   - Fabric name
   - Site hierarchy
3. Optionally, you can provide additional parameters such as:
   - DNAC verification settings
   - DNAC port
   - DNAC version
   - Debug mode
4. The system will update the playbook status in real-time as you provide information.
5. Once all required information is collected, the system will mark the playbook as ready for deployment.
6. You can review the generated playbook at any time during the conversation.

## Customization

- To modify the prompts or add new features, edit the `prompts.py` file.
- To change the playbook structure or add new parameters, update the `generate_playbook_yaml` function in `app.py`.

## Troubleshooting

- If you encounter any issues with missing modules, ensure that all dependencies are installed correctly.
- Check that your OpenAI API key is set correctly in the `.env` file.
- If the playbook status is not updating correctly, verify that the `playbook_status.json` file has write permissions.

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.


