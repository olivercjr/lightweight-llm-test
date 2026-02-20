from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import Any
from numpy.typing import NDArray

# import numpy.typing as npt
# from typing import TypeAlias

# Matrix: TypeAlias = npt.NDArray[np.float64]

st_model = SentenceTransformer('all-MiniLM-L6-v2')  # lightweight 384-dim embeddings

## FUNCTIONS & METHODS ######################################################################

def embedder(docs: list[str]):
	emb = st_model.encode(docs, convert_to_numpy=True, normalize_embeddings=True).astype('float32')
	return emb

def query_embedder(query: str):
	query_emb = st_model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype('float32')
	return query_emb



def indexer(embeddings: NDArray[np.str_]):
	dimension = embeddings.shape[1]
	index = faiss.IndexFlatIP(dimension)  # Inner product for cosine sim
	index.add(embeddings)  # Supports incremental adds
	faiss.write_index(index, 'file bin/doc_index.faiss')  # Save to disk
	return index

def retriever(emb_query: NDArray[Any], index: faiss.IndexFlatIP, docs_list: list[str] ,k: int = 3):
	scores, indices = index.search(emb_query, k)

	print("\n\nTop matches:")
	for score, idx in zip(scores[0], indices[0]):
		print(f"- Doc IDX {idx}: {docs_list[idx]} (similarity: {score:.3f})\n")


def chunker(doc: str):
	pass