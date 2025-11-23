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
		response = gemma_3_4b(prompt=full_prompt, max_tokens=200, stop=["<end_of_turn>"], temperature=model_temp)
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
			# origin = r.get("origin")

			if href and title and body:
				return_list.append({
					"href": href,
					"title": title,
					"body": body,
					# "origin": origin
				})
		
		return return_list
	
def check_web_results(raw_results: list, query: str, model_temp: float=0.6):
	prompt = "<start_of_turn>system\n" + Path("prompts/system web results checker instructions.txt").read_text(encoding="utf-8") + "\n" + query + "\n\n---\n\n### UNRANKED WEB RESULTS\n"

	for idx, dict in enumerate(raw_results, start=1):
		prompt += f"INDEX: {idx}\n"
		prompt += f"TITLE: {dict.get("title")}\n"
		prompt += f"BODY: {dict.get("body")}\n\n"

	prompt += "<end_of_turn>\njson<start_of_turn>\n"

	# response = gemma_3_4b(prompt=prompt, max_tokens=200, stop=["<end_of_turn>"], temperature=model_temp, grammar=grammar)
	response = gemma_3_4b(prompt=prompt, max_tokens=200, stop=["<end_of_turn>"], temperature=model_temp)
	response_str = response['choices'][0]['text']

	#print(f"{prompt}\n\n######MODEL RESOPNSE##############\n{response}")
	print("\n\n###### WEB CHECKER RESPONSE ########\n\n")
	print(f"\n\n\n{response_str}\n\n\n")
	# print("###### PROMPT ########\n\n")
	# print(prompt)

	return response_str

def read_page_content(url: str):

	headers = {
		"User-Agent": os.getenv("USER_AGENT"),
		"Accept": os.getenv("ACCEPT"),
		"Accept-Language": os.getenv("ACCEPT_LANGUAGE"),
		"Referer": os.getenv("REFERER"),
		"Connection": os.getenv("CONNECTION"),
		"Upgrade-Insecure-Requests": os.getenv("UPGRADE_INSECURE_REQUESTS")
	}

	# Fetch the page
	try:
		http_resp = requests.get(url, timeout=10, headers=headers)
		http_resp.raise_for_status()   # Raises an error if the request failed
	except requests.exceptions.HTTPError as e:
		print("HTTP error:", e, "status:", e.response.status_code)
	except requests.exceptions.RequestException as e:
		print("Network error or timeout:", e)
	else:
		# runs only if the request succeeded
		print("status", http_resp.status_code)
	finally:
		print("done (cleanup if needed)")

	# Parse HTML with BeautifulSoup
	soup = BeautifulSoup(markup=http_resp.text, features="html.parser")

	# Extract text
	elements = soup.select("h1, h2, h3, h4, h5, h6, p")
	full_text = ""

	for elmnt in elements:
		raw_text = elmnt.get_text(separator='\n', strip=True)
		clean_text = ' '.join(raw_text.split())

		match elmnt.name:
			case "h1":
				full_text += f"\n***{clean_text}***\n"
			case "h2":
				full_text += f"\n**{clean_text}**\n"
			case "h3" | "h4" | "h5" | "h6":
				full_text += f"\n*{clean_text}*\n"
			case "p":
				full_text += f"{clean_text}\n"


	print(full_text)
		
		

def input_test():
	user_msg = input(f"\n{os.getenv("USER_NAME")}: ")
	print(user_msg)

## MAIN ##################################################################

if __name__ == "__main__":
	# chatbot(model_temp=0.6)

	print("\n\n### START QUERY TEST ###")
	user_query = input(f"\n### QUERY: \n")
	# print("### ANSWER")

	results_list = ddg_search(query=user_query, max_results=15)
	ranked_json = check_web_results(raw_results=results_list, query=user_query, model_temp=0.6)
	ranked_json = ranked_json.replace("```", "") # smh
	ranked_json = ranked_json.replace("json", "") # I need money to buy a setup I can finetune on to avoid shit like this smh
	ranked_json = ranked_json.strip() # You should see the system prompt. It's disgusting.
	ranked_object = json.loads(ranked_json)

	print("\n\n### BEAUTIFUL SOUP #####################################\n")
	print("\n### ARTICLE 1 #######################")
	print(f"\nURL: {results_list[ranked_object.get("model ranked indices").get("rank 1")-1].get("href")}")
	# print(f"\nORIGIN: {results_list[ranked_object.get("model ranked indices").get("rank 1")-1].get("origin")}\n")
	read_page_content(results_list[ranked_object.get("model ranked indices").get("rank 1")-1].get("href"))
	print("\n### ARTICLE 2 #######################")
	print(f"\nURL: {results_list[ranked_object.get("model ranked indices").get("rank 2")-1].get("href")}")
	# print(f"\nORIGIN: {results_list[ranked_object.get("model ranked indices").get("rank 2")-1].get("origin")}\n")
	read_page_content(results_list[ranked_object.get("model ranked indices").get("rank 2")-1].get("href"))
	print("\n### ARTICLE 3 #######################")
	print(f"\nURL: {results_list[ranked_object.get("model ranked indices").get("rank 3")-1].get("href")}")
	# print(f"\nORIGIN: {results_list[ranked_object.get("model ranked indices").get("rank 3")-1].get("origin")}\n")
	read_page_content(results_list[ranked_object.get("model ranked indices").get("rank 3")-1].get("href"))
	
