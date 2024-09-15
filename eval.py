from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langsmith.schemas import Run, Example
from bs4 import BeautifulSoup
import requests
from openai import OpenAI
import json
import time
import random


from dotenv import load_dotenv
load_dotenv()

from langsmith.wrappers import wrap_openai
from langsmith import traceable

client = wrap_openai(OpenAI())

url = "https://www.simplilearn.com/what-is-ansible-playbook-article"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")
text = [p.text for p in soup.find_all("p")]
full_text = "\n".join(text)

@traceable
def ansible_compliance_evaluator(run: Run, example: Example) -> dict:
    time.sleep(random.uniform(1, 3))

    inputs = example.inputs['messages']
    outputs = example.outputs['generations']

    # Extract system prompt
    system_prompt = next((msg['data']['content'] for msg in inputs if msg['type'] == 'system'), "")

    # Extract message history
    message_history = []
    for msg in inputs:
        if msg['type'] in ['human', 'ai']:
            message_history.append({
                "role": "user" if msg['type'] == 'human' else "assistant",
                "content": msg['data']['content']
            })

    # Extract latest user message and model output
    latest_message = message_history[-1]['content'] if message_history else ""
    model_output = outputs[0]['text']



    evaluation_prompt = f"""
    System Prompt: {system_prompt}

    Message History:
    {json.dumps(message_history, indent=2)}

    Latest User Message: {latest_message}

    Model Output: {model_output}

    Based on the above information, evaluate the model's output for compliance with Ansible best practices, accuracy of Ansible concepts, and relevance to the user's question. 
    Provide a score from 0 to 10, where 0 is completely incorrect or irrelevant and 10 is perfectly accurate and helpful.
    Also provide a brief explanation for your score. Make sure the syntax is correct and follw yaml syntax.

    Article on Ansible Playbook: {full_text}

    Respond in the following JSON format:
    {{
        "score": <int>,
        "explanation": "<string>"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant tasked with evaluating the accuracy and helpfulness of Ansible-related responses."},
            {"role": "user", "content": evaluation_prompt}
        ],
        temperature=0.2
    )

    try:
        result = json.loads(response.choices[0].message.content)
        time.sleep(14)
        return {
            "key": "ansible_compliance",
            "score": result["score"] / 10,  # Normalize to 0-1 range
            "reason": result["explanation"]
        }
       
    except json.JSONDecodeError:
        return {
            "key": "ansible_compliance",
            "score": 0,
            "reason": "Failed to parse evaluator response"
        }

# The name or UUID of the LangSmith dataset to evaluate on.
data = "ansible-playbook-dataset"

# A string to prefix the experiment name with.
experiment_prefix = "Ansible playbook compliance"

# List of evaluators to score the outputs of target task
evaluators = [
    ansible_compliance_evaluator
]

# Evaluate the target task
results = evaluate(
    lambda inputs: inputs,
    data=data,
    evaluators=evaluators,
    experiment_prefix=experiment_prefix,
)

print(results)
