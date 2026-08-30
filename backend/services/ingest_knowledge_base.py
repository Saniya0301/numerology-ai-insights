"""
One-time (or re-runnable) script that loads all numerology knowledge base
files, chunks them, embeds them, and stores them in a local ChromaDB
collection for retrieval.

Run this whenever you add or edit knowledge base files:

    python services/ingest_knowledge_base.py
"""

import os
import shutil

from dotenv import load_dotenv

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import Chroma


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

KNOWLEDGE_BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "knowledge_base",
    )
)

CHROMA_PERSIST_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "chroma_db",
    )
)


# ---------------------------------------------------------
# Load Markdown documents
# ---------------------------------------------------------

def load_all_documents():
    """Load every .md file from all subfolders of knowledge_base/."""

    loader = DirectoryLoader(
        KNOWLEDGE_BASE_DIR,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={
            "encoding": "utf-8",
        },
    )

    documents = loader.load()

    print(
        f"Loaded {len(documents)} documents "
        f"from {KNOWLEDGE_BASE_DIR}"
    )

    return documents


# ---------------------------------------------------------
# Split documents into chunks
# ---------------------------------------------------------

def chunk_documents(documents):
    """Split documents into smaller overlapping chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=[
            "\n## ",
            "\n\n",
            "\n",
            " ",
            "",
        ],
    )

    chunks = splitter.split_documents(documents)

    print(f"Split into {len(chunks)} chunks")

    return chunks


# ---------------------------------------------------------
# Build ChromaDB vector store
# ---------------------------------------------------------

def build_vectorstore(chunks):
    """Embed chunks and persist them into ChromaDB."""

    # Remove previous database so re-running the
    # ingestion script does not create duplicates.

    if os.path.exists(CHROMA_PERSIST_DIR):
        print("Removing existing ChromaDB...")
        shutil.rmtree(CHROMA_PERSIST_DIR)

    print("Creating Gemini embeddings...")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("Creating ChromaDB vector store...")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name="numerology_knowledge",
    )

    print(
        f"Vectorstore persisted at: "
        f"{CHROMA_PERSIST_DIR}"
    )

    return vectorstore


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    print("\n🔮 Numerology AI Insights")
    print("📚 Starting knowledge base ingestion...\n")

    docs = load_all_documents()

    if not docs:
        print(
            "❌ No Markdown files found in "
            f"{KNOWLEDGE_BASE_DIR}"
        )
        raise SystemExit(1)

    chunks = chunk_documents(docs)

    build_vectorstore(chunks)

    print(
        "\n✅ Knowledge base ingested successfully!"
    )