# Chatbot para Busca em Manual (Flask)

Este projeto implementa um chatbot que responde a perguntas sobre um manual em PDF usando Langchain, OpenAI e Flask.

## Instalação

1. Clone o repositório: `git clone https://github.com/<seu-usuario>/<nome-do-repositorio>.git`
2. Crie um ambiente virtual: `python -m venv venv`
3. Ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`
4. Instale as dependências: `pip install -r requirements.txt`
5. Configure suas variáveis de ambiente:
   - `OPENAI_API_KEY`: Sua chave de API do OpenAI, disponível em https://openai.com/index/openai-api/.
   - `FAISS_INDEX_PATH`: Caminho para o arquivo de índice FAISS, sugere-se que seja a mesma pasta do programa.
6. Para o primeiro uso, execute diretamente o main.py e adicione o caminho do seu PDF, para gerar a biblioteca de consulta. 
   O modelo irá gerar embeddings do pdf e montar um índice para consultas futuras (você só pagará uma vez para converter seus dados.

## Uso

1. Execute o servidor Flask: `python app.py`
2. Envie requisições POST para `http://127.0.0.1:5000/chat` com um JSON contendo a chave `query` (e opcionalmente `session_id`).

## Exemplo de requisição:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"query": "Qual a política de reembolso?"}' http://127.0.0.1:5000/chat
