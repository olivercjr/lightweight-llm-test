# LLM TOOL TEST

## NOTES
* Work on document chunker
* Table parsing is broken consider json instead

## CHANGELOG
### CHANGES (0.1.0)
* Created a new conda environment
* Reinstalled dependencies manually incl. faiss & sentence*transformers
* Created rag_tools.py with basic embedder, indexer and retriever functions, 
* Created pyproject.toml
* Created README.md

### CHANGES (0.1.1)
* Created search_tools.py and moved search functions to it
* Added table parsing to read_page_content() function
* Improved markdown formatting
* Deleted .venv folder