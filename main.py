import os
from typing import List
import PyPDF2
import tiktoken
import json
from langchain_community.chat_message_histories.redis import RedisChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from senhas import APY_KEY
from difflib import SequenceMatcher

# Global Variables
chave_openai = APY_KEY
embeddings = OpenAIEmbeddings(openai_api_key=chave_openai)
FAISS_INDEX_PATH = "manual.faiss"
db = None
store = {}


# --- Model Initialization ---
model = ChatOpenAI(openai_api_key=chave_openai, temperature=0.1)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Você é um assistente de busca de conteúdo em um manual, você deve informar ao usuário as informações sobre sua pergunta com base nas informações do assistant, se o assunto ao qual estiver respondendo estiver no contexto do conteúdo fornecido, adicione 'Assunto do manual' no início do texto de resposta"),
        ("assistant", "{input_documents}"),
        ("human", "{input}"),
    ]
)
runnable = prompt | model

# --- Cache Class ---
class AnswerCache:
    def __init__(self, cache_file="answer_cache.json", similarity_threshold=0.8):
        self.cache_file = cache_file
        self.similarity_threshold = similarity_threshold
        self.cache = self.load_cache()

    def load_cache(self):
        """Loads the answer cache from a JSON file."""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_cache(self):
        """Saves the answer cache to a JSON file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)

    def normalizar_prompt(self, prompt):
        """Normalizes the prompt for better similarity matching."""
        return prompt.lower().strip()  # You can add more normalization steps here

    def encontrar_prompt_similar(self, prompt):
        """Finds a similar prompt in the cache based on SequenceMatcher."""
        prompt_normalizado = self.normalizar_prompt(prompt)
        for chave_cache in self.cache:
            similaridade = SequenceMatcher(None, prompt_normalizado, chave_cache).ratio()
            if similaridade >= self.similarity_threshold:
                return chave_cache
        return None

    def get_answer_from_cache(self, query):
        """Retrieves an answer from the cache using the similar prompt search."""
        similar_prompt = self.encontrar_prompt_similar(query)
        if similar_prompt:
            return self.cache[similar_prompt]
        return None

    def add_answer_to_cache(self, prompt, answer):
        """Adds an answer to the cache."""
        self.cache[prompt] = answer
        self.save_cache()

# --- Text Extraction ---
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return "\n\n".join(page.extract_text() for page in reader.pages)
    except Exception as e:
        raise IOError(f"Erro ao ler o PDF: {e}")

# --- FAISS Functions ---
def create_faiss_index(text: str):
    """Creates a FAISS index from text and saves it."""
    try:
        encoding = tiktoken.encoding_for_model("text-davinci-003")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512, chunk_overlap=24, length_function=lambda t: len(encoding.encode(t))
        )
        chunks = text_splitter.create_documents([text])
        embeddings = OpenAIEmbeddings(openai_api_key=chave_openai, model="text-embedding-ada-002")
        db = FAISS.from_documents(chunks, embeddings)
        db.save_local(FAISS_INDEX_PATH)
        print("Índice FAISS criado e salvo.")
    except Exception as e:
        raise RuntimeError(f"Erro ao criar índice FAISS: {e}")

def load_faiss_index() -> FAISS:
    """Loads an existing FAISS index."""
    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError(f"Arquivo de índice não encontrado: {FAISS_INDEX_PATH}")
    return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# --- Chatbot Function ---
def get_answer_from_chatbot(db: FAISS, chain: RunnableWithMessageHistory, query: str, session_id: str, cache) -> str:
    """Gets an answer from the chatbot for a given query."""
    try:
        # Check cache first
        cached_answer = cache.get_answer_from_cache(query)
        if cached_answer:
            return cached_answer
        
        retriever = db.as_retriever(search_kwargs={"k": 10})
        result = chain.invoke(
            {"input_documents": retriever.invoke(query),
             "input": query},
            config={"configurable": {"session_id": session_id}},                  
        )
        
        if result.content != "Texto não encontrado no manual, posso te ajudar com algo a mais?":
            cache.add_answer_to_cache(query, result.content)
            
        return result.content
    except Exception as e:
        raise RuntimeError(f"Erro ao obter resposta do chatbot: {e}")

# --- Main Function ---
def main():
    """Main function to handle user interaction and chatbot responses."""
    global db

    usuario = input("Informe o usuário: ")
    conversa_id = input("Informe o ID da conversa: ")

    session_id = f"{usuario} - {conversa_id}"
    if input("Deseja adicionar um novo arquivo PDF (s/n)? ").lower() == 's':
        pdf_path = input("Digite o caminho para o arquivo PDF: ")
        text = extract_text_from_pdf(pdf_path)
        create_faiss_index(text)

    db = load_faiss_index()  # Load index after potential creation
    
    # Load cache
    cache = AnswerCache()  # Create AnswerCache instance

    while True:
        query = input("Usuário: ")
        if query.lower() == "sair":
            # Save cache before exiting
            cache.save_cache()
            break
        
        chain = RunnableWithMessageHistory(
            runnable,
            lambda session_id=session_id: get_session_history(session_id),
            input_messages_key="input",
            history_messages_key="history",
            chain_type="stuff",
        )
        answer = get_answer_from_chatbot(db, chain, query, session_id, cache) 
        print("Assistente:", answer)


if __name__ == "__main__":
    main()
