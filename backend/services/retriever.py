"""
Retrieval service — searches the ChromaDB knowledge base for content
relevant to a given query or number, and returns it as context for Gemini.
"""

import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

_vectorstore = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=_embeddings,
    collection_name="numerology_knowledge",
)


def retrieve_relevant_context(query: str, k: int = 4) -> str:
    """
    Given a query (a question, or a description like 'Life Path 7 meaning'),
    retrieve the top-k most relevant knowledge base chunks and return them
    as a single combined string, ready to inject into a prompt.
    """
    results = _vectorstore.similarity_search(query, k=k)
    context_chunks = [doc.page_content for doc in results]
    return "\n\n---\n\n".join(context_chunks)


if __name__ == "__main__":
    # quick manual test
    test_query = "Life Path 7 challenges and strengths"
    context = retrieve_relevant_context(test_query)
    print(f"Query: {test_query}\n")
    print("Retrieved context:\n")
    print(context)