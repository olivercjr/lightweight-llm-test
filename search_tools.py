from ddgs import DDGS
from bs4 import BeautifulSoup
import requests
import re
import os



## FUNCTIONS & METHODS ######################################################################

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
	elements = soup.select("h1, h2, h3, h4, h5, h6, p, ul, ol, table, br")
	full_text = ""
	clean_text = ""
	
	junk_keywords = [
		"sidebar", "widget", "advert", "ad-", "promo", "sponsor", "related",
		"post-nav", "pagination", "footer", "menu", "nav", "share", "comment",
		"header", "href", "site-header", "navbar", "main-menu", "site-footer",
		"bottom", "adsbygoogle", "top-bar", "sidenav", "top-nav-bar", "nav-bar",
		"footerwrapper"
	]

	for elmnt in elements:
		if (elmnt.name in ["h1", "h2", "h3", "h4", "h5", "h6"]):
			pass # allow headings
		
		if (elmnt.name not in ["ul", "ol", "table"]):
			clean_text = clean_string(elmnt.get_text(separator='\n', strip=True))

		if (elmnt.name in junk_keywords or elmnt.find_parent(junk_keywords)): # Skip if any parent has a junk keyword in class or id
			continue

		

		match elmnt.name:
			case "br":
				full_text += "\n"
			case "h1":
				full_text += f"\n# {clean_text}\n"
			case "h2":
				full_text += f"\n## {clean_text}\n"
			case "h3":
				full_text += f"\n### {clean_text}\n"
			case "h4":
				full_text += f"\n#### {clean_text}\n"
			case "h5":
				full_text += f"\n##### {clean_text}\n"
			case "h6":
				full_text += f"\n###### {clean_text}\n"
			case "p":
				full_text += f"{clean_text}\n"
			case "ul": # unordered lists
				if elmnt.find("li"):
					clean_li_text = ""
					li_items = elmnt.find_all("li", recursive=False)
					for item in li_items:
						raw_li_text = item.get_text(separator='\n', strip=True)
						clean_li_text = clean_string(raw_li_text)
						full_text += f"\n	* {clean_li_text}"
					full_text += f"\n\n"
			case "ol": # ordered lists
				if elmnt.find("li"):
					clean_li_text = ""
					li_items = elmnt.find_all("li", recursive=False)
					for num, item in enumerate(li_items, start=1):
						raw_li_text = item.get_text(separator='\n', strip=True)
						clean_li_text = clean_string(raw_li_text)
						full_text += f"\n	{num}. {clean_li_text}"
					full_text += f"\n\n"

			case "table":
				has_header = True if elmnt.find("th") else False
				is_horizontal = True
				table_string = ""

				if is_horizontal: # Horizontal Header
					rows = elmnt.find_all("tr")
					list_table = []
					for row in rows:
						row_cells = row.find_all(["td", "th"])

						row_list = [
							clean_string(cell.text) if cell.text else "    "
							for cell in row_cells
						]
						list_table.append(row_list)
					
					for idx, row_list_ in enumerate(list_table):
						row_string = "|"
						for cell_text in row_list_:
							row_string += f" {cell_text} |"

						if idx == 0 and has_header: # add header separator
							row_string += "\n" + ("|--------" * len(row_list_)) + "|"

						
						table_string += row_string + "\n"
			
					full_text += table_string + "\n\n"
						

				else: # Vertical Header
					pass

				



	print(full_text)
	return full_text


def clean_string(raw_text: str):
	no_brackets = re.sub(pattern=r'\[\s*\d+\s*\]',repl='', string=raw_text) # Remove all numbers in square brackets
	clean_text = re.sub(pattern=r'\s+', repl=' ', string=no_brackets).strip() # Replace multiple spaces with a single space
	return clean_text

def write_search_articles_to_file(doc_string: str):
	# Count only files (ignore subdirectories)
	direc = "file bin/scraped articles"
	file_count: int = 0
	for f in (os.listdir(direc)): file_count += 1
	file_path = direc+"/"+f"article {file_count+1}.txt"

	with open(file_path, mode="w", encoding="utf-8") as f:
		f.write(doc_string)