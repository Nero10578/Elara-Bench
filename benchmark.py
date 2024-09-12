import json
import requests
import concurrent.futures
import re
import os
import time
import yaml
from tqdm import tqdm
from collections import Counter

def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def load_yaml(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return data

def generate_response(task, i, url, model):
    system = "You are a creative writer tasked with writing new and interesting stories based on the writing prompt given to you."
    prompt = f"You are given the following writing prompt, write a story based on the prompt. The prompt is:\n{task}" 

    reply = {
            "model": model,
            "max_tokens": 4096,
            "temperature": 0,
            "repetition_penalty": 1,
            "prompt": prompt,
            "stop": "<|eot_id|>"
        }
    
    response = requests.request("POST", url, headers=llm_headers, data=json.dumps(reply))
    response = response.json()['choices'][0]['text']

    return response

config_file = "config.yml"
input_file = "prompts.json"

# Read config file
config = load_yaml(config_file)
words_to_check = config['words_to_check']
models = config['models']  # Changed to read a list of models
llm_urls = config['llm_urls']
max_workers_per_url = config['max_workers_per_url']
api_key = config['api_key']

# Read input file
prompts = load_json(input_file)
initial_prompts = list(prompts.values())

print("Testing prompts obtained")

executors = [concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) for max_workers in max_workers_per_url]

futures = []
responses = []
llm_headers = {"Content-Type": "application/json", 'Authorization': 'Bearer '.format(api_key)}

for model in models:  # Loop through each model
    output_file = f"{model}_responses.json"
    report_file = f"{model}_report.txt"
    for i in range(len(initial_prompts)):
        url_index = i % len(llm_urls)
        futures.append(executors[url_index].submit(generate_response, initial_prompts[i], i, llm_urls[url_index], model))

    with tqdm(total=len(initial_prompts)) as pbar:
        start_time = time.time()
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            response = future.result()
            responses.append({"prompt": initial_prompts[i], "response": response})
            elapsed_time = time.time() - start_time
            remaining_tasks = len(initial_prompts) - (i + 1)
            estimated_time_remaining = elapsed_time / (i + 1) * remaining_tasks
            hours, remainder = divmod(estimated_time_remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            pbar.update(1)
            pbar.set_description(f"Estimated time remaining: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")

    # Save responses to a JSON file
    with open(output_file, 'w') as f:
        json.dump(responses, f, indent=4)

    # Count occurrences of words in words_to_check in all responses
    word_counts = {word: 0 for word in words_to_check}
    responses_with_words = {word: 0 for word in words_to_check}

    for response in responses:
        response_text = response["response"].lower()
        for word in words_to_check:
            word_counts[word] += response_text.count(word)
            if word in response_text:
                responses_with_words[word] += 1

    # Write report to a text file
    with open(report_file, 'w') as f:
        f.write("Word occurrences in responses:\n")
        for word, count in word_counts.items():
            f.write(f"{word}: {count}\n")
        f.write("Number of responses containing each word:\n")
        for word, count in responses_with_words.items():
            f.write(f"{word}: {count}\n")

    print(f"Word occurrences in responses for model {model}:")
    for word, count in word_counts.items():
        print(f"{word}: {count}")
    print(f"Number of responses containing each word for model {model}:")
    for word, count in responses_with_words.items():
        print(f"{word}: {count}")
