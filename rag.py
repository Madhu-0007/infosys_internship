# ---------------- IMPORTS ----------------
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader

from langchain_community.vectorstores import FAISS

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from pathlib import Path
import os
from dotenv import load_dotenv

# ---------------- LOAD ENV ----------------
load_dotenv(dotenv_path="env/.env")   # adjust path if needed
print("Loaded GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))  # Debug
print("Loaded GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))      # Debug

# ---------------- CONFIG ----------------
DOCS_PATH = Path("./my_docs")         # folder or single file (.txt, .md, .pdf, .csv)
INDEX_PATH = Path("./faiss_index")    # where FAISS index is stored
REBUILD_INDEX = True                  # True = rebuild from docs; False = load
EMBED_MODEL = "models/embedding-001"  # Gemini embedding model
TOP_K = 4                             # how many chunks to retrieve
SEARCH_TYPE = "mmr"                   # "mmr" | "similarity"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

QUESTION = "Give me a 2-line summary of the docs and cite sources."
# -----------------------------------------

# STEP 1) ENSURE API KEYS
if not os.environ.get("GOOGLE_API_KEY"):
    raise SystemExit(" GOOGLE_API_KEY is not set. Check your .env file and path.")

if not os.environ.get("GROQ_API_KEY"):
    raise SystemExit(" GROQ_API_KEY is not set. Check your .env file and path.")

# STEP 2) FIND & LOAD DOCUMENTS
def find_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    exts = [".txt", ".md", ".pdf", ".csv"]
    return [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in exts]

def load_documents(paths: list[Path]) -> list[Document]:
    docs: list[Document] = []
    for p in paths:
        try:
            if p.suffix.lower() in (".txt", ".md"):
                docs.extend(TextLoader(str(p), encoding="utf-8").load())
            elif p.suffix.lower() == ".pdf":
                docs.extend(PyPDFLoader(str(p)).load())
            elif p.suffix.lower() == ".csv":
                docs.extend(CSVLoader(file_path=str(p)).load())
        except Exception as e:
            print(f"[WARN] Failed to load {p}: {e}")
    return docs

# STEP 3) SPLIT DOCS INTO CHUNKS
def split_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(docs)

# STEP 4) MAKE / LOAD FAISS VECTOR STORE
def build_or_load_faiss(chunks: list[Document], rebuild: bool) -> FAISS:
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
    if rebuild:
        print(" Building FAISS index from documents...")
        vs = FAISS.from_documents(chunks, embeddings)
        INDEX_PATH.mkdir(parents=True, exist_ok=True)
        vs.save_local(str(INDEX_PATH))
        print(f" Saved index to: {INDEX_PATH.resolve()}")
    print(f" Loading FAISS index from: {INDEX_PATH.resolve()}")
    vs = FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
    print(" Loaded FAISS index.")
    return vs

# STEP 5) ASK QUESTION WITH GROQ
def ask_question(vectorstore: FAISS, question: str) -> str:
    retriever = vectorstore.as_retriever(search_type=SEARCH_TYPE, search_kwargs={"k": TOP_K})

    prompt = ChatPromptTemplate.from_template(
        "Answer the following question based only on the provided context:\n\n"
        "Context:\n{context}\n\n"
        "Question: {input}"
    )

    llm = ChatGroq(model="llama-3.3-70b-versatile")

    chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, chain)

    result = rag_chain.invoke({"input": question})
    return result["answer"]

# ---------------- MAIN ----------------
if __name__ == "__main__":
    files = find_files(DOCS_PATH)
    if not files:
        raise SystemExit(f"No documents found in {DOCS_PATH}. Add some .txt, .md, .pdf, or .csv files.")

    docs = load_documents(files)
    if not docs:
        raise SystemExit(f"No documents loaded from {DOCS_PATH}. Check file formats and permissions.")

    chunks = split_documents(docs)
    if not chunks:
        raise SystemExit("No chunks created from documents. Check chunk size and input files.")

    vs = build_or_load_faiss(chunks, REBUILD_INDEX)
    answer = ask_question(vs, QUESTION)
    print("\n Answer:", answer)
