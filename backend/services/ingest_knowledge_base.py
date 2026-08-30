"""
One-time (or re-runnable) script that loads all numerology knowledge base
files, chunks them, embeds them, and stores them in a local ChromaDB
collection for retrieval.

Uses FastEmbed (ONNX-based, no PyTorch dependency) instead of
sentence-transformers — significantly lighter memory footprint, which
matters on memory-constrained free hosting tiers (e.g. Render's 512MB cap).

Run this whenever you add or edit knowledge base files:
    python services/ingest_knowledge_base.py
"""

import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base")
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")


def load_all_documents():
    """Load every .md file from all subfolders of knowledge_base/."""
    loader = DirectoryLoader(
        KNOWLEDGE_BASE_DIR,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents from {KNOWLEDGE_BASE_DIR}")
    return documents


def chunk_documents(documents):
    """Split documents into smaller overlapping chunks for better retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    return chunks


def build_vectorstore(chunks):
    """Embed chunks and persist them into a local ChromaDB collection."""
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name="numerology_knowledge",
    )
    print(f"Vectorstore persisted at: {CHROMA_PERSIST_DIR}")
    return vectorstore


if __name__ == "__main__":
    print("🔮 Numerology AI Insights")
    print("📚 Starting knowledge base ingestion...\n")
    docs = load_all_documents()
    chunks = chunk_documents(docs)
    build_vectorstore(chunks)
    print("✅ Knowledge base ingested successfully!")