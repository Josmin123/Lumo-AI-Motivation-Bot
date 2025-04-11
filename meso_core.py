import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from pathlib import Path

#load environment variable
load_dotenv()
DATA_PATH=os.getenv("DATA_PATH","./data")
VECTOR_PATH=os.getenv("VECTOR_DB_PATH","./data/vectorstore")
MODEL=os.getenv("MODEL","mistral")

#step1: Load journal,goals,notes as documents

def load_documents():
    print("Loading personal files...")

    subfolders=["journal","goals","notes"]
    docs=[]

    for folder in subfolders:
        path=os.path.join(DATA_PATH,folder)
        if os.path.exists(path):
            loader=DirectoryLoader(path,glob="**/*.md",loader_cls=TextLoader)
            docs.extend(loader.load())

    print(f"Loader {len(docs)} documents")
    return docs

def get_or_create_vector_store(docs):
    # Check if the FAISS DB exists
    if Path(VECTOR_PATH).exists():
        print("Loading existing vector store...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return FAISS.load_local(VECTOR_PATH, embeddings, allow_dangerous_deserialization=True)

    
    # Otherwise: embed and save
    print("Embedding and indexing documents...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)

    vector_store = FAISS.from_documents(chunks, embedding=embeddings)
    vector_store.save_local(VECTOR_PATH)
    print("Vector store saved.")
    return vector_store


# Step 3: Load Ollama RAG pipeline
def create_qa_chain(vector_store):
    print(" Initializing Lumo assistant with Ollama...")
    retriever = vector_store.as_retriever()
    llm = Ollama(model=MODEL)

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return qa

# Step 4: Start chat loop
def start_chat(qa):
    print("\n Lumo is ready! Ask questions about your life data.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("You: ")
        if query.lower() in ["exit", "quit"]:
            break
        result = qa(query)
        print(f"\n Lumo: {result['result']}\n")

if __name__ == "__main__":
    documents = load_documents()
    vector_store = get_or_create_vector_store(documents)
    qa_chain = create_qa_chain(vector_store)
    start_chat(qa_chain)

