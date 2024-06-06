from flask import Flask, render_template, request, jsonify
from threading import Lock # Adicione esta linha
from main import get_answer_from_chatbot, load_faiss_index, AnswerCache, runnable, get_session_history # Importe as funções do seu código
from langchain_core.runnables.history import RunnableWithMessageHistory

app = Flask(__name__)

# Carregue o índice FAISS e o cache apenas uma vez
db = load_faiss_index()
cache = AnswerCache()

# Dicionário para armazenar históricos de conversa por sessão
session_histories = {}
lock = Lock() # Mutex para proteger o acesso ao dicionário

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_answer', methods=['POST'])
def get_bot_response():
    user_message = request.form['msg']
    session_id = request.form.get('session_id') # Obtenha o ID da sessão

    # Crie/obtenha o histórico da sessão usando um bloqueio para garantir a segurança da thread
    with lock:
        if session_id not in session_histories:
            session_histories[session_id] = []

    chain = RunnableWithMessageHistory(
        runnable,
        lambda session_id=session_id: get_session_history(session_id),
        input_messages_key="input",
        history_messages_key="history",
        chain_type="stuff",
    )

    bot_response = get_answer_from_chatbot(db, chain, user_message, session_id, cache)

    # Armazene a mensagem do usuário e a resposta do bot no histórico da sessão
    with lock:
        session_histories[session_id].append(("Usuário:", user_message))
        session_histories[session_id].append(("Assistente:", bot_response))

    return jsonify({'answer': bot_response})

if __name__ == '__main__':
    app.run(debug=True)