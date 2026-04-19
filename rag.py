
import json
import warnings
warnings.filterwarnings("ignore")

from database import SessionLocal
from models import Patient

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_community.llms import Ollama

from sentence_transformers import CrossEncoder


# -----------------------------
# Load Patient Data
# -----------------------------
def load_patient_text(mrd_number):
    db = SessionLocal()
    mrd_number = mrd_number.strip().lower()
    digits = ''.join(filter(str.isdigit, mrd_number))
    if not digits:
        db.close()
        return None, "Invalid MRD"
    patient = db.query(Patient).filter(
    Patient.mrd_number.ilike(f"%{digits}")).first()
    db.close()

    if not patient:
        return None, "Invalid MRD"

    try:
        with open(patient.file_path) as f:
            data = json.load(f)
    except:
        return None, "File read error"

    texts = []

    try:
        if isinstance(data, list):
            for item in data:
                texts.append(item.get("description", ""))
        else:
            texts.append(data.get("description", ""))
    except:
        return None, "Unsupported document"

    if not texts:
        return None, "No content"

    return texts, None


# -----------------------------
# Chunking
# -----------------------------
def create_chunks(texts):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    return splitter.create_documents(texts)


# -----------------------------
# Hybrid Retriever Setup
# -----------------------------
def create_retrievers(docs):

    # 🔥 Ollama Embedding
    embedding_model = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    # Vector DB
    vector_db = FAISS.from_documents(docs, embedding_model)

    vector_retriever = vector_db.as_retriever(
        search_kwargs={"k": 7}
    )

    # BM25
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 7

    return vector_retriever, bm25_retriever


# -----------------------------
# Hybrid Retrieval
# -----------------------------
def hybrid_retrieve(query, vector_retriever, bm25_retriever):

    vec_docs = vector_retriever.invoke(query)
    bm_docs = bm25_retriever.invoke(query)

    docs = vec_docs + bm_docs

    # Remove duplicates
    unique = {d.page_content: d for d in docs}

    return list(unique.values())


# -----------------------------
# Reranker
# -----------------------------
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, docs, top_k=3):

    pairs = [(query, d.page_content) for d in docs]

    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(scores, docs),
        key=lambda x: x[0],
        reverse=True
    )

    return [doc for _, doc in ranked[:top_k]]


# -----------------------------
# LLM
# -----------------------------
def create_llm():
    return Ollama(model="llama3.2:1b")


# -----------------------------
# Final Answer Generator
# -----------------------------
def generate_answer(query, docs):

    llm = create_llm()

    context = "\n\n".join([d.page_content for d in docs])

    prompt = f"""
    Answer the question based on the context below:

    Context:
    {context}

    Question:
    {query}
    """

    return llm.invoke(prompt)


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run_query(mrd, query):

    if not mrd:
        return {"error": "Invalid MRD"}

    if not query.strip():
        return {"error": "Empty query"}

    # 1. Load data
    texts, err = load_patient_text(mrd)
    if err:
        return {"error": err}

    # 2. Chunk
    docs = create_chunks(texts)

    if not docs:
        return {"error": "No content"}

    # 3. Hybrid retrievers
    vector_retriever, bm25_retriever = create_retrievers(docs)

    # 4. Hybrid retrieve
    retrieved_docs = hybrid_retrieve(query, vector_retriever, bm25_retriever)

    # 5. Rerank
    top_docs = rerank(query, retrieved_docs)

    # 6. Generate answer
    try:
        answer = generate_answer(query, top_docs)
    except:
        return {"error": "LLM error"}

    return {
        "mrd_number": mrd,
        "answer": answer,
        "confidence": "High"
    }