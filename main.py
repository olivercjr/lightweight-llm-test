from llama_cpp import Llama, LlamaGrammar
from dotenv import load_dotenv
from pathlib import Path
from ddgs import DDGS
from bs4 import BeautifulSoup
import requests
import json

import os

load_dotenv()
gemma_3_4b = Llama(model_path=os.getenv("GEMMA_3_4B_PATH"), n_ctx=4096)

## FUNCTIONS & METHODS ######################################################################

def chatbot(model_temp: float = 0.7):
	# Load the model (update the path!)
	
	print("\n---CHAT STARTS HERE---")
	greeting = os.getenv("GREETING")
	print(f"{os.getenv("BOT_NAME")}: {greeting}")
	chat_history = f"\n<start_of_turn>model\n{greeting}\n<end_of_turn>\n"
	pretty_chat = f"Assistant: {greeting}"


	# Ask questions
	while True:
		user_msg = input(f"\n{os.getenv("USER_NAME")}: ")
		if user_msg == "/stop": break
		else:
			chat_history += (f"\n<start_of_turn>user\n{user_msg}\n<end_of_turn>\n\n<start_of_turn>model\n")
			pretty_chat += f"\nUser: {user_msg}"
		print("--------------")
		
		# Gemma 3 Chat formatting
		system_prompt = Path("prompts/system prompt.txt").read_text(encoding="utf-8")
		full_prompt = f"<start_of_turn>system\n{system_prompt}\n<end_of_turn>\n{chat_history}"
		response = gemma_3_4b(prompt=full_prompt, max_tokens=200, stop=["<end_of_turn>"], temperature=0.6)
		response_str = response['choices'][0]['text']
		chat_history += f"{response_str}\n<end_of_turn>\n" #
		pretty_chat += f"\nAssistant: {response_str}"

		# Print the model's response
		print(f"\n{os.getenv("BOT_NAME")}: {response_str}")

	# end program
	print("\n---CHAT ENDS HERE---")
	# print(f"####SYSTEM PROMPT####\n{system_prompt}\n###########\n{pretty_chat}")
	print(full_prompt)


def ddg_search(query: str, max_results: int):
	with DDGS() as ddgs:
		result_objects = ddgs.text(query, max_results=max_results)

		return_list = []

		for r in result_objects:
			href = r.get("href")
			title = r.get("title")
			body = r.get("body")

			if href and title and body:
				return_list.append({
					"href": href,
					"title": title,
					"body": body
				})
		
		return return_list
	
def check_web_results(raw_results: list, query: str, model_temp: float=0.6):
	# llm = Llama(model_path=os.getenv("MODEL_PATH"), n_ctx=4096)
	gbnf_text = Path("file bin/grammar web results checker.txt").read_text(encoding="utf-8")
	prompt = "<start_of_turn>system\n" + Path("prompts/system web results checker instructions.txt").read_text(encoding="utf-8") + "\n" + query + "\n\n---\n\n### UNRANKED WEB RESULTS\n"
	# grammar = LlamaGrammar.from_string(gbnf_text)

	for idx, dict in enumerate(raw_results, start=1):
		prompt += f"INDEX: {idx}\n"
		prompt += f"TITLE: {dict.get("title")}\n"
		prompt += f"BODY: {dict.get("body")}\n\n"

	prompt += "<end_of_turn>\njson<start_of_turn>\n"

	# response = gemma_3_4b(prompt=prompt, max_tokens=200, stop=["<end_of_turn>"], temperature=model_temp, grammar=grammar)
	response = gemma_3_4b(prompt=prompt, max_tokens=200, stop=["<end_of_turn>"], temperature=model_temp)
	response_str = response['choices'][0]['text']

	#print(f"{prompt}\n\n######MODEL RESOPNSE##############\n{response}")
	print("###### RESPONSE ########\n\n")
	print(f"\n\n\n{response_str}\n\n\n")
	print("###### PROMPT ########\n\n")
	print(prompt)

	return response_str

def parse_page_content():
	pass
		
		

def input_test():
	user_msg = input(f"\n{os.getenv("USER_NAME")}: ")
	print(user_msg)

## MAIN ##################################################################

if __name__ == "__main__":
	# chatbot(model_temp=0.6)

	print("### START QUERY TEST ###")
	user_query = input(f"\n### QUERY: \n")
	# print("### ANSWER")

	list = ddg_search(query=user_query, max_results=15)
	ranked_json = check_web_results(raw_results=list, query=user_query, model_temp=0.6)
	ranked_object = json.loads(ranked_json)
	# create page content parser

