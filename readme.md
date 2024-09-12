# Elara benchmark

The Elara Benchmark is a tool to test LLM models for repetitive words or phrases in unrelated prompts.

It works by generating responses based on writing prompts from https://github.com/EQ-bench/EQ-Bench/blob/main_v2_4/data/creative_writing_prompts_v2.2.json using a specified language model. 

It reads the configuration from a YAML file, processes the prompts, and saves the generated responses along with a report of word occurrences.

## Purpose

This project serves as a tool to test word repetitions in language models (LLMs). Such as how LLMs often keep using the name "elara".

## Requirements

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```
## Configuration

The configuration is specified in a config.yml file. Here is an example of what the config.yml file might look like:

```yaml
words_to_check:
  - elara
  - whispering woods
  - eldoria
models: 
  - Meta-Llama-3.1-8B-Instruct
api_key: your_api_key
llm_urls:
  - http://localhost:8000/v1/completions
max_workers_per_url:
  - 24

- words_to_check: List of words to check in the generated responses.
- models: List of models being tested.
- api_key: Your endpoint API key if needed
- llm_urls: List of URLs for the LLM API endpoints to use.
- max_workers_per_url: List of maximum workers for each URL.

```
## Files

Input Files - prompts.json: A JSON file containing the writing prompts.
Configuration File - config.yml: A YAML file containing the configuration.
Output Files - responses_<model>.json: A JSON file containing the generated responses and their corresponding writing prompts.
Report File - report.txt: A text file containing the word occurrences and the number of responses containing each word.

## Usage 

To run the script, execute the following command:

```bash
python benchmark.py
```

## License

This project is licensed under the MIT License.

[MIT](https://choosealicense.com/licenses/mit/)
