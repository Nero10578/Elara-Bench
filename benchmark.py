import json
import requests
import concurrent.futures
import re
import os
import time
import yaml
from tqdm import tqdm
from collections import Counter
import argparse

def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def load_yaml(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return data

def generate_response(task, i, url, api_key, model, timeout=6000):
    llm_headers = {"Content-Type": "application/json", 'Authorization': f"Bearer {api_key}"}
    system = "You are a creative writer tasked with writing new and interesting stories based on the writing prompt given to you."
    prompt = f"You are given the following writing prompt, write a story based on the prompt. The prompt is:\n{task}" 

    reply = {
            "model": model,
            "max_tokens": 4096,
            "temperature": 0,
            "repetition_penalty": 1,
            "prompt": prompt,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
        }
    
    response = requests.request("POST", f"{url}/v1/chat/completions", headers=llm_headers, data=json.dumps(reply), timeout=timeout)
    
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} - {response.text}")
    
    response_json = response.json()
    if 'choices' in response_json and len(response_json['choices']) > 0 and 'message' in response_json['choices'][0] and 'content' in response_json['choices'][0]['message']:
        response_text = response_json['choices'][0]['message']['content']
    else:
        raise Exception("Error: Unexpected response format")
    
    return response_text

def main(config_file, input_file):
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

    executors = [concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) for max_workers in max_workers_per_url]

    try:
        for model in models:  # Loop through each model
            futures = []  # Clear futures list for each model
            responses = []  # Clear responses list for each model
            print("Finding number of elaras by ", model)
            output_file = f"{model}_responses.json"
            report_file = f"{model}_report.txt"
            for i in range(len(initial_prompts)):
                url_index = i % len(llm_urls)
                futures.append(executors[url_index].submit(generate_response, initial_prompts[i], i, llm_urls[url_index], api_key, model))

            with tqdm(total=len(initial_prompts)) as pbar:
                start_time = time.time()
                for future in concurrent.futures.as_completed(futures):
                    response = future.result()
                    responses.append(response)
                    elapsed_time = time.time() - start_time
                    remaining_tasks = len(initial_prompts) - len(responses)
                    estimated_time_remaining = elapsed_time / len(responses) * remaining_tasks
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
                response_text = response.lower()
                for word in words_to_check:
                    word_counts[word.lower()] += response_text.count(word.lower())
                    if word.lower() in response_text:
                        responses_with_words[word.lower()] += 1

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

    except Exception as e:
        print(e)
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process config and prompts files.")
    parser.add_argument("--config", type=str, default="config.yml", help="Path to the config file")
    parser.add_argument("--prompts", type=str, default="prompts.json", help="Path to the prompts file")
    args = parser.parse_args()

    main(args.config, args.prompts)
