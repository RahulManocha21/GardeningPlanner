import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
import time
import pickle
import hashlib

os.environ["GROQ_API_KEY"]= st.secrets["GROQ_API_KEY"]
os.environ["HF_API_KEY"]= st.secrets["HF_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"]= st.secrets["LANGCHAIN_TRACING_V2"]
os.environ["LANGCHAIN_ENDPOINT"]= st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_API_KEY"]= st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_PROJECT"]= st.secrets["LANGCHAIN_PROJECT"]


# Set the path to your vector store directory
def load_vectors():
    VECTOR_STORE_DIR = "./vector_store"
    CATALOG_DIR = "./Content"
    # Create the vector store directory if it doesn't exist
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    # Calculate the hash of the catalog directory
    catalog_hash = hashlib.sha256(str([os.path.join(CATALOG_DIR, f) for f in os.listdir(CATALOG_DIR)]).encode()).hexdigest()
    # Check if the vector store already exists
    vector_store_path = os.path.join(VECTOR_STORE_DIR, "vector_store.pkl")


    def load_multiple_files(directory_path):
        documents = []
        for filename in os.listdir(directory_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(directory_path, filename)
                csvloader = CSVLoader(file_path)
                documents.extend(csvloader.load())
            elif filename.endswith(".pdf"):
                file_path = os.path.join(directory_path, filename)
                pdfloader = PyPDFLoader(file_path)
                documents.extend(pdfloader.load())
        return documents

    if os.path.exists(vector_store_path):
        # Load the existing vector store and catalog hash
        with open(vector_store_path, "rb") as f:
            vectors, stored_catalog_hash = pickle.load(f)
        # Check if the catalog has changed
        if catalog_hash != stored_catalog_hash:
            # Regenerate the vector store
            with st.spinner('Updating vector store...'):
                embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-en-v1.5", encode_kwargs={'normalize_embeddings': True})
                docs = load_multiple_files(CATALOG_DIR)
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                final_documents = text_splitter.split_documents(docs)
                vectors = FAISS.from_documents(final_documents, embeddings)

            # Save the new vector store and catalog hash
            with open(vector_store_path, "wb") as f:
                pickle.dump((vectors, catalog_hash), f)
    else:
        # Create a new vector store
        with st.spinner('Updating vector store...'):
            embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-en-v1.5", encode_kwargs={'normalize_embeddings': True})
            docs = load_multiple_files(CATALOG_DIR)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            final_documents = text_splitter.split_documents(docs)
            vectors = FAISS.from_documents(final_documents, embeddings)

        # Save the new vector store and catalog hash
        with open(vector_store_path, "wb") as f:
            pickle.dump((vectors, catalog_hash), f)

    return vectors

st.title("ChatGroq with RAG Pipeline")

llm = ChatGroq(groq_api_key=os.environ['GROQ_API_KEY'], model_name="llama3-8b-8192")
prompt = ChatPromptTemplate.from_template(
    """
    Answer the questions based on the provided context only if there is something out of context, response as 'Hi there, Ask me about the catalog information only'. 
    I have providing you the documents of brecks brand, Please provide the well structured and most accurate response, blogs or category URL relevant based on the question.
    <context>
    {context}
    <context>
    Questions:{input}
    """
)

vectors = load_vectors()
document_chain = create_stuff_documents_chain(llm, prompt)
retriever = vectors.as_retriever()
retrieval_chain = create_retrieval_chain(retriever, document_chain)

input_text = st.text_input("Input your prompt here")
if input_text:
    response = retrieval_chain.invoke({"input": input_text})
    st.write(response['answer'])
    
