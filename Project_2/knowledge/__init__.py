# kb_functions.py

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.schema import Document
from pathlib import Path
import pickle

# -------------------------
# CONFIG
# -------------------------
KB_FOLDER = Path("knowledge/Knowledge Base")
VECTORSTORE_PATH = KB_FOLDER / "kb_vectorstore.faiss"
DOCSTORE_PATH = KB_FOLDER / "kb_docstore.pkl"
HF_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# -------------------------
# 1️⃣ KB Loader
# -------------------------
def load_faq_docs(kb_folder: Path = KB_FOLDER) -> list:
    """
    Load all .txt FAQ documents from the given folder into a list of langchain Document objects.
    
    Args:
        kb_folder (Path): Folder containing FAQ text files.
        
    Returns:
        List[Document]: List of Document objects with metadata.
    
    Raises:
        FileNotFoundError: If folder does not exist.
        ValueError: If no .txt files are found.
    """
    if not kb_folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {kb_folder}")

    faq_docs = []
    for file_path in kb_folder.glob("*.txt"):
        content = file_path.read_text(encoding="utf-8")
        faq_docs.append(
            Document(
                page_content=content,
                metadata={"source": file_path.name, "category": "FAQ"}
            )
        )

    if not faq_docs:
        raise ValueError(f"No .txt files found in {kb_folder}")

    # Save docstore
    with open(DOCSTORE_PATH, "wb") as f:
        pickle.dump(faq_docs, f)

    print(f"Docstore saved to {DOCSTORE_PATH} ({len(faq_docs)} documents).")
    return faq_docs


# -------------------------
# 2️⃣ Vectorstore Builder
# -------------------------
def build_vectorstore(documents: list, hf_model_name: str = HF_MODEL_NAME, vectorstore_path: Path = VECTORSTORE_PATH) -> FAISS:
    """
    Build a FAISS vectorstore from a list of Document objects using HuggingFace embeddings.

    Args:
        documents (list): List of Document objects.
        hf_model_name (str): HuggingFace embedding model name.
        vectorstore_path (Path): Path to save the FAISS vectorstore locally.
    
    Returns:
        FAISS: The built vectorstore.
    """
    hf_embeddings = HuggingFaceEmbeddings(model_name=hf_model_name)
    vectorstore = FAISS.from_documents(documents, hf_embeddings)
    vectorstore.save_local(str(vectorstore_path))
    print(f"Vectorstore saved to {vectorstore_path}")
    return vectorstore


# -------------------------
# 3️⃣ KB Retriever
# -------------------------
def retrieve_from_kb(query_text: str, vectorstore: FAISS, k: int = 3) -> list:
    """
    Retrieve top-k most relevant documents from a FAISS vectorstore based on a query.

    Args:
        query_text (str): User query to search in KB.
        vectorstore (FAISS): FAISS vectorstore object.
        k (int): Number of top documents to return.
    
    Returns:
        list: List of dictionaries with 'source', 'category', and 'snippet'.
    """
    results = vectorstore.similarity_search(query_text, k=k)
    structured_results = []
    for r in results:
        structured_results.append({
            "source": r.metadata.get("source"),
            "category": r.metadata.get("category"),
            "snippet": r.page_content
        })
    return structured_results


# -------------------------
# 4️⃣ Load saved vectorstore
# -------------------------
def load_saved_vectorstore(vectorstore_path: Path = VECTORSTORE_PATH) -> FAISS:
    """
    Load a previously saved FAISS vectorstore from disk.

    Args:
        vectorstore_path (Path): Path to the saved FAISS vectorstore.
    
    Returns:
        FAISS: Loaded vectorstore.
    
    Raises:
        FileNotFoundError: If the vectorstore file does not exist.
    """
    if not vectorstore_path.exists():
        raise FileNotFoundError(f"Vectorstore not found. Run KB loader first: {vectorstore_path}")
    return FAISS.load_local(str(vectorstore_path))


# -------------------------
# 5️⃣ Example test
# -------------------------
if __name__ == "__main__":
    docs = load_faq_docs()
    vs = build_vectorstore(docs)
    results = retrieve_from_kb("App crashes on macOS Ventura", vs)
    for i, doc in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Source: {doc['source']}")
        print(f"Category: {doc['category']}")
        print(f"Snippet: {doc['snippet'][:200]}...")
