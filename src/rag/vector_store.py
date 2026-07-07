import streamlit as st
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from crewai.tools import tool

from src.config import POLICIES_FILE, CHROMA_PATH, OLLAMA_BASE_URL, EMBEDDING_MODEL

embedding_model = OllamaEmbeddings(
    model=EMBEDDING_MODEL,
    base_url=OLLAMA_BASE_URL
)

try:
    loader = TextLoader(POLICIES_FILE, encoding="utf-8")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embedding_model,
        persist_directory=CHROMA_PATH
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    RAG_AVAILABLE = True
except Exception as e:
    st.error(f"Error al cargar la base de datos RAG: {e}")
    RAG_AVAILABLE = False
    retriever = None

@tool("Consultar politicas de la empresa (RAG)")
def consultar_politicas_rag(pregunta: str) -> str:
    """Busca en el documento de politicas de la empresa usando busqueda semantica."""
    if not RAG_AVAILABLE or retriever is None:
        return "El sistema de politicas no esta disponible. Verifica que el archivo politicas_empresa.txt exista y que Ollama este corriendo."
    docs = retriever.invoke(pregunta)
    if not docs:
        return "No se encontró informacion relevante en las politicas."
    contexto = "\n".join([doc.page_content for doc in docs])
    return f"Informacion recuperada de las politicas:\n{contexto}"