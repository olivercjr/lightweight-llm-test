from llama_cpp import Llama, LlamaGrammar
from dotenv import load_dotenv
from pathlib import Path
from ddgs import DDGS
from bs4 import BeautifulSoup
import requests
import json
import re
import numpy as np
import os
import rag_tools

load_dotenv()
gemma_3_4b = Llama(model_path=os.getenv("GEMMA_3_4B_PATH"), n_ctx=4096)

## FUNCTIONS & METHODS ######################################################################

def chatbot(model_temp: float = 0.7):
	# Load the model (update the path!)
	
	print("\n---CHAT STARTS HERE---")
	greeting = os.getenv("GREETING")
	print(f"{os.getenv('BOT_NAME')}: {greeting}")
	chat_history = f"\n<start_of_turn>model\n{greeting}\n<end_of_turn>\n"
	pretty_chat = f"Assistant: {greeting}"


	# Ask questions
	while True:
		user_msg = input(f"\n{os.getenv('USER_NAME')}: ")
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
		print(f"\n{os.getenv('BOT_NAME')}: {response_str}")

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
		prompt += f"TITLE: {dict.get('title')}\n"
		prompt += f"BODY: {dict.get('body')}\n\n"

	prompt += "<end_of_turn>\njson<start_of_turn>\n"

	# response = gemma_3_4b(prompt=prompt, max_tokens=200, stop=["<end_of_turn>"], temperature=model_temp, grammar=grammar)
	response = gemma_3_4b(prompt=prompt, max_tokens=200, stop=["<end_of_turn>"], temperature=model_temp)
	response_str = response['choices'][0]['text']

	return response_str

def clean_string(raw_text: str):
	no_brackets = re.sub(pattern=r'\[\s*\d+\s*\]',repl='', string=raw_text) # Remove all numbers in square brackets
	clean_text = re.sub(pattern=r'\s+', repl=' ', string=no_brackets).strip() # replace multiple spaces with a single space
	return clean_text


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
	##########################################################
	# # Find main content
	# main_selectors = [
	# 	"main", "article", "[role=main]",
	# 	"div#content", "div#main",
	# 	"div.content", "div.main-content",
	# ]

	# content = None
	# for sel in main_selectors:
	# 	content = soup.select_one(selector=sel)
	# 	if content:
	# 		break

	# if not content:
	# 	content = soup.body or soup

	# # Remove universal junk
	# for sel in ["nav", "header", "footer", "aside", "script", "style", "noscript"]:
	# 	for tag in content.select(sel):
	# 		tag.decompose()

	

	# for kw in junk_keywords:
	# 	for tag in content.select(f"[class*='{kw}'], [id*='{kw}']"):
	# 		tag.decompose()
	##########################################################

	# Extract text
	elements = soup.select("h1, h2, h3, h4, h5, h6, p, ul, ol, table, br")
	full_text = ""
	clean_text = ""
	
	junk_keywords = [
		"sidebar", "widget", "advert", "ad-", "promo", "sponsor", "related",
		"post-nav", "pagination", "footer", "menu", "nav", "share", "comment",
		"header", "href"
	]

	for elmnt in elements:
		if (elmnt.name in ["h1", "h2", "h3", "h4", "h5", "h6"]):
			continue # skip headings that are links
		
		if (elmnt.name not in ["ul", "ol", "table"]):
			clean_text = clean_string(elmnt.get_text(separator='\n', strip=True))

		if (elmnt.name in ["header", "footer", "nav"]): continue


		# Skip if any parent has a junk keyword in class or id
		if any(
			any(kw in (classname or "") for kw in junk_keywords) for classname in elmnt.get('class', [])
		):
			continue

		

		match elmnt.name:
			case "br":
				full_text += "\n"
			case "h1":
				full_text += f"\n***{clean_text}***\n"
			case "h2":
				full_text += f"\n**{clean_text}**\n"
			case "h3" | "h4" | "h5" | "h6":
				full_text += f"\n*{clean_text}*\n"
			case "p":
				full_text += f"{clean_text}\n"
			case "ul": # unordered lists
				if elmnt.find("li"):
					clean_li_text = ""
					li_items = elmnt.find_all("li", recursive=False)
					for item in li_items:
						raw_li_text = item.get_text(separator='\n', strip=True)
						clean_li_text = clean_string(raw_li_text)
						full_text += f"\n	- {clean_li_text}"
					full_text += f"\n\n"
			case "ol": # unordered lists
				if elmnt.find("li"):
					clean_li_text = ""
					li_items = elmnt.find_all("li", recursive=False)
					for num, item in enumerate(li_items, start=1):
						raw_li_text = item.get_text(separator='\n', strip=True)
						clean_li_text = clean_string(raw_li_text)
						full_text += f"\n	{num}. {clean_li_text}"
					full_text += f"\n\n"

	print(full_text)
	return full_text

	
		
def write_search_articles_to_file(doc_string: str):
	# Count only files (ignore subdirectories)
	direc = "file bin/scraped articles"
	file_count: int = 0
	for f in (os.listdir(direc)): file_count += 1
	file_path = direc+"/"+f"article {file_count+1}.txt"

	with open(file_path, mode="w", encoding="utf-8") as f:
		f.write(doc_string)


def input_test():
	user_msg = input(f"\n{os.getenv('USER_NAME')}: ")
	print(user_msg)

## MAIN ##################################################################

# if __name__ == "__main__":
# 	# chatbot(model_temp=0.6)

# 	user_query = input(f"\n### QUERY: \n")

# 	results_list = ddg_search(query=user_query, max_results=15)
# 	ranked_json = check_web_results(raw_results=results_list, query=user_query, model_temp=0.6)
# 	ranked_json = ranked_json.replace("```", "") # smh
# 	ranked_json = ranked_json.replace("json", "") # I need money to buy a setup I can finetune on to avoid shit like this smh
# 	ranked_json = ranked_json.strip() # You should see the system prompt. It's disgusting.
# 	ranked_object = json.loads(ranked_json)

# 	doc_string = "### USER QUERY #################################################################################\n"
# 	doc_string += user_query

# 	doc_string += "\n\n### RAW DDG SEARCH RESULTS ###################################################################\n"
# 	for i, result in enumerate(results_list):
# 		doc_string += f"\n/// RESULT {i+1} ////////////////////////"
# 		doc_string += f"\nURL: {results_list[i].get("href")}"
# 		doc_string += f"\nTITLE: {results_list[i].get("title")}"
# 		doc_string += f"\nBLURB: {results_list[i].get("body")}\n"
	
	
# 	doc_string += "\n\n### WEB CHECKER RESPONSE ###################################################################\n"
# 	doc_string += ranked_json
# 	doc_string += "\n\n### WEBPAGES ###############################################################################\n"
# 	doc_string += "\n### ARTICLE 1 #########################################"
# 	doc_string += f"\nURL: {results_list[ranked_object.get("model ranked indices").get("rank 1")-1].get("href")}"
# 	doc_string += f"\nTITLE: {results_list[ranked_object.get("model ranked indices").get("rank 1")-1].get("title")}\n\n"
# 	doc_string += read_page_content(results_list[ranked_object.get("model ranked indices").get("rank 1")-1].get("href"))
# 	doc_string += "\n### ARTICLE 2 ########################################"
# 	doc_string += f"\nURL: {results_list[ranked_object.get("model ranked indices").get("rank 2")-1].get("href")}"
# 	doc_string += f"\nTITLE: {results_list[ranked_object.get("model ranked indices").get("rank 2")-1].get("title")}\n\n"
# 	doc_string += read_page_content(results_list[ranked_object.get("model ranked indices").get("rank 2")-1].get("href"))
# 	doc_string += "\n### ARTICLE 3 ########################################"
# 	doc_string += f"\nURL: {results_list[ranked_object.get("model ranked indices").get("rank 3")-1].get("href")}"
# 	doc_string += f"\nTITLE: {results_list[ranked_object.get("model ranked indices").get("rank 3")-1].get("title")}\n\n"
# 	doc_string += read_page_content(results_list[ranked_object.get("model ranked indices").get("rank 3")-1].get("href"))

# 	write_search_articles_to_file(doc_string=doc_string)
# 	print(doc_string)

# test rag #####################################################################################################

if __name__ == "__main__":
	query = "Star Trek"
	testdocs = [
    "Honey never spoils; archaeologists have found edible honey in ancient Egyptian tombs over 3,000 years old.",
    "The original series starred William Shatner as Captain James T. Kirk and Leonard Nimoy as Mr. Spock aboard the starship USS Enterprise.",
    "Bananas are berries, but strawberries are not.",
    "Octopuses have three hearts and blue blood.",
    "There's a species of jellyfish, Turritopsis dohrnii, that can theoretically live forever by reverting to its juvenile stage.",
    "The Eiffel Tower can be 15 cm taller during hot days due to thermal expansion.",
    "Star Trek was created by Gene Roddenberry and first premiered in 1966 on NBC.",
    "Shakespeare invented over 1,700 words in English, including 'bedroom,' 'eyeball,' and 'lonely.'",
    "A day on Venus is longer than a year on Venus; it rotates very slowly.",
    "Sea otters hold hands while sleeping to keep from drifting apart.",
    "Wombat poop is cube-shaped to prevent rolling and mark territory.",
    "The first video ever uploaded to YouTube was 'Me at the zoo' in April 2005.",
    "There's a museum in Sweden dedicated entirely to failures called the Museum of Failure.",
    "Humans and giraffes have the same number of neck vertebrae — seven.",
    "The shortest war in history lasted 38-45 minutes between Britain and Zanzibar in 1896.",
    "Since its debut, Star Trek has grown into a multimedia franchise including multiple television series, films, novels, and video games.",
    "A single bolt of lightning contains enough energy to toast 100,000 slices of bread.",
    "Sloths can hold their breath longer than dolphins — up to 40 minutes.",
    "Some frogs can freeze solid in winter and thaw in spring, surviving without harm.",
    "There's a species of fungus that can zombify ants, controlling their behavior.",
    "The world's oldest known living tree is over 9,500 years old in Sweden.",
    "The franchise expanded with Star Trek: The Next Generation, which introduced Captain Jean-Luc Picard and ran from 1987 to 1994.",
    "The fingerprints of a koala are so similar to humans that they can confuse crime scene investigators.",
    "In 1969, a man named Yuri Gagarin inspired space exploration by being the first human to orbit Earth."
]

	docs_emb = rag_tools.embedder(docs=testdocs)
	query_emb = rag_tools.embedder(docs=[query])
	index = rag_tools.indexer(embeddings=docs_emb)
	# print(f"\n\nEMBEDDINGS SHAPE: {query_emb.shape}")
	rag_tools.retriever(emb_query=query_emb, index=index, docs_list=testdocs, k=8)
