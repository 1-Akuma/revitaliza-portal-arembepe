import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Any

# Importa o contexto do arquivo separado
from prompt_context import SYSTEM_INSTRUCTION_TEMPLATE

# --- CONFIGURAÇÃO ---
# Carrega variáveis de ambiente do arquivo .env para desenvolvimento local
load_dotenv()

# Obtém a chave da API do Gemini das variáveis de ambiente
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


# --- SERVIÇO DE IA ---

def initialize_ai():
    """Configura o cliente do Google AI se a chave da API estiver disponível."""
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            print("INFO: Cliente do Google AI configurado com sucesso.")
        except Exception as e:
            print(f"ERROR: Falha ao configurar o cliente do Google AI: {e}")
    else:
        print("ERROR: Variável de ambiente GEMINI_API_KEY não encontrada.")

def get_gemini_response(user_message: str, chat_history: List[Dict[str, Any]]) -> str:
    """
    Obtém uma resposta do modelo Gemini com base na mensagem e histórico do usuário.
    """
    if not genai.API_KEY:
        raise ValueError("A chave da API do Gemini não está configurada.")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Constrói o histórico completo para o modelo
        history_for_gemini = [
            {'role': 'user', 'parts': [SYSTEM_INSTRUCTION_TEMPLATE]},
            {'role': 'model', 'parts': ["Olá! Sou a IA do Portal. Como posso ajudar?"]}
        ]
        history_for_gemini.extend(chat_history)

        chat_session = model.start_chat(history=history_for_gemini)
        response = chat_session.send_message(user_message)
        return response.text
    except Exception as e:
        print(f"ERROR: Exceção durante a chamada da API Gemini: {e}")
        # Re-lança a exceção para ser capturada pelo manipulador de rota
        raise

# --- FÁBRICA DE APLICAÇÃO FLASK ---

def create_app() -> Flask:
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__, static_folder='public', static_url_path='')
    
    # Configura o CORS para permitir requisições do seu domínio de frontend em produção
    # Para desenvolvimento, uma configuração mais aberta é aceitável.
    CORS(app) 

    @app.route('/')
    def index():
        """Serve o arquivo principal index.html."""
        return app.send_static_file('index.html')

    @app.route('/chat', methods=['POST'])
    def chat():
        """Manipula as requisições de chat do frontend."""
        try:
            data = request.get_json()
            if not data or 'user_message' not in data:
                return jsonify({"error": "Requisição inválida: 'user_message' é obrigatório."}), 400

            user_message = data.get('user_message')
            chat_history = data.get('chat_history', [])
            
            ai_response_text = get_gemini_response(user_message, chat_history)
            
            return jsonify({"ai_response": ai_response_text})

        except ValueError as ve:
            # Erro específico para chave da API ausente
            print(f"ERROR na rota /chat: {ve}")
            return jsonify({"error": "Erro de configuração do servidor: Serviço de IA indisponível."}), 503
        except Exception as e:
            # Erro geral para outras exceções
            print(f"ERROR na rota /chat: {e}")
            return jsonify({"error": "Ocorreu um erro interno no servidor."}), 500

    return app

# --- EXECUÇÃO PRINCIPAL ---

# Inicializa o cliente de IA na inicialização do aplicativo
initialize_ai()
# Cria a instância da aplicação Flask para ser usada pelo Gunicorn no Render
app = create_app()

if __name__ == '__main__':
    # Este bloco só é executado quando você roda `python index.py` localmente
    # O Gunicorn em produção não executa este bloco.
    app.run(debug=True, port=5000)