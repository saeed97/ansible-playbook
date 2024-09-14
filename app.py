import os
from dotenv import load_dotenv
import chainlit as cl
import openai
import asyncio
import json
from datetime import datetime
from prompts import ASSESSMENT_PROMPT, DNAC_SITE_CREATION_PROMPT
from langsmith.wrappers import wrap_openai
from langsmith import traceable
import yaml

# Load environment variables
load_dotenv()

configurations = {
    "mistral_7B_instruct": {
        "endpoint_url": os.getenv("MISTRAL_7B_INSTRUCT_ENDPOINT"),
        "api_key": os.getenv("RUNPOD_API_KEY"),
        "model": "mistralai/Mistral-7B-Instruct-v0.2"
    },
    "mistral_7B": {
        "endpoint_url": os.getenv("MISTRAL_7B_ENDPOINT"),
        "api_key": os.getenv("RUNPOD_API_KEY"),
        "model": "mistralai/Mistral-7B-v0.1"
    },
    "openai_gpt-4": {
        "endpoint_url": os.getenv("OPENAI_ENDPOINT"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4"
    }
}

# Choose configuration
config_key = "openai_gpt-4"
# config_key = "mistral_7B_instruct"
#config_key = "mistral_7B"

# Get selected configuration
config = configurations[config_key]


client = wrap_openai(openai.AsyncClient(api_key=config["api_key"], base_url=config["endpoint_url"]))

gen_kwargs = {
    "model": config["model"],
    "temperature": 0.3,
    "max_tokens": 500
}

# Configuration setting to enable or disable the system prompt
def read_playbook_status(file_path):
    default_status = {
        "playbook_status": "incomplete",
        "missing_info": ["fabric_name", "site_hierarchy"],
        "collected_info": {},
        "current_playbook": "",
        "alert": ""
    }

    if not os.path.exists(file_path):
        print(f"Playbook status file not found at {file_path}. Using default status.")
        return default_status

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            if isinstance(data, dict):
                print(f"Successfully loaded playbook status: {data}")
                return data
            else:
                print(f"Warning: Unexpected data format in {file_path}. Got {type(data)}. Using default status.")
                return default_status
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}. Using default status.")
        return default_status
    except Exception as e:
        print(f"Unexpected error reading {file_path}: {e}. Using default status.")
        return default_status

def write_playbook_status(file_path, playbook_status):
    with open(file_path, 'w') as file:
        json.dump(playbook_status, file, indent=4)
        
def get_latest_user_message(message_history):
    # Iterate through the message history in reverse to find the last user message
    for message in reversed(message_history):
        if message['role'] == 'user':
            return message['content']
    return None

@traceable
async def assess_message(message_history):
    file_path = "playbook_status.json"
    playbook_status = read_playbook_status(file_path)

    print(f"Playbook status after reading: {playbook_status}")

    latest_message = get_latest_user_message(message_history)

    # Remove the original prompt from the message history for assessment
    filtered_history = [msg for msg in message_history if msg['role'] != 'system']

    # Convert message history and playbook status to strings
    history_str = json.dumps(filtered_history, indent=4)
    
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Generate the current playbook YAML
    current_playbook = generate_playbook_yaml(playbook_status.get("collected_info", {}))

    # Generate the assessment prompt
    filled_prompt = ASSESSMENT_PROMPT.format(
        latest_message=latest_message,
        history=history_str,
        existing_playbook_status=playbook_status["playbook_status"],
        existing_collected_info=json.dumps(playbook_status["collected_info"], indent=4),
        existing_missing_info=json.dumps(playbook_status["missing_info"], indent=4),
        existing_current_playbook=playbook_status["current_playbook"],
        current_date=current_date
    )

    response = await client.chat.completions.create(messages=[{"role": "system", "content": filled_prompt}], **gen_kwargs)

    assessment_output = response.choices[0].message.content.strip()
    print("Assessment Output: \n\n", assessment_output)

    # Parse the assessment output
    updated_playbook_status = parse_assessment_output(assessment_output)

    # Update the playbook status file
    write_playbook_status(file_path, updated_playbook_status)

def parse_assessment_output(output):
    try:
        parsed_output = json.loads(output)
        return {
            "playbook_status": parsed_output.get("playbook_status", "incomplete"),
            "missing_info": parsed_output.get("missing_info", []),
            "collected_info": parsed_output.get("collected_info", {}),
            "current_playbook": parsed_output.get("current_playbook", ""),
            "alert": parsed_output.get("alert", "")
        }
    except json.JSONDecodeError as e:
        print("Failed to parse assessment output:", e)
        return {
            "playbook_status": "incomplete",
            "missing_info": [],
            "collected_info": {},
            "current_playbook": "",
            "alert": "Error parsing assessment output"
        }

def generate_playbook_yaml(collected_info):
    playbook = {
        "hosts": "dnac_servers",
        "vars_files": ["credentials.yml"],
        "gather_facts": False,
        "tasks": [{
            "name": "Create DNAC Site",
            "cisco.dnac.sda_fabric_site": {
                "dnac_host": "{{ dnac_host }}",
                "dnac_username": "{{ dnac_username }}",
                "dnac_password": "{{ dnac_password }}",
                "dnac_verify": collected_info.get("dnac_verify", True),
                "dnac_port": collected_info.get("dnac_port", 443),
                "dnac_version": collected_info.get("dnac_version", "2.2.3.3"),
                "dnac_debug": collected_info.get("dnac_debug", False),
                "state": "present",
                "fabricName": collected_info.get("fabric_name", ""),
                "siteNameHierarchy": collected_info.get("site_hierarchy", "")
            }
        }]
    }
    return yaml.dump([playbook], default_flow_style=False)

@cl.on_message
@traceable
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])

    if  (not message_history or message_history[0].get("role") != "system"):
        system_prompt_content = DNAC_SITE_CREATION_PROMPT
        message_history.insert(0, {"role": "system", "content": system_prompt_content})

    message_history.append({"role": "user", "content": message.content})

    asyncio.create_task(assess_message(message_history))
    
    response_message = cl.Message(content="")
    await response_message.send()

    if config_key == "mistral_7B":
        stream = await client.completions.create(prompt=message.content, stream=True, **gen_kwargs)
        async for part in stream:
            if token := part.choices[0].text or "":
                await response_message.stream_token(token)
    else:
        stream = await client.chat.completions.create(messages=message_history, stream=True, **gen_kwargs)
        async for part in stream:
            if token := part.choices[0].delta.content or "":
                await response_message.stream_token(token)

    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)
    await response_message.update()


if __name__ == "__main__":
    cl.main()
