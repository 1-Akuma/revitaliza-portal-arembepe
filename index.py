import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Any

# Importa o contexto do arquivo separado
from prompt_context import SYSTEM_INSTRUCTION_TEMPLATE

# Carrega variáveis de ambiente do arquivo .env para desenvolvimento local
load_dotenv()

# --- CLASSE DE CONFIGURAÇÃO ---
class Config:
    """Carrega configurações a partir de variáveis de ambiente."""
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    # Futuras configurações, como SECRET_KEY, podem ser adicionadas aqui.


# --- SERVIÇO DE IA ---

def get_gemini_response(logger: logging.Logger, user_message: str, chat_history: List[Dict[str, Any]]) -> str:
    """Obtém uma resposta do modelo Gemini com base na mensagem e histórico."""
    if not Config.GEMINI_API_KEY:
        raise ValueError("A chave da API do Gemini não está configurada.")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        history_for_gemini = [
            {'role': 'user', 'parts': [SYSTEM_INSTRUCTION_TEMPLATE]},
            {'role': 'model', 'parts': ["Olá! Sou a IA do Portal. Como posso ajudar?"]}
        ]
        history_for_gemini.extend(chat_history)

        chat_session = model.start_chat(history=history_for_gemini)
        response = chat_session.send_message(user_message)
        logger.info("Resposta recebida com sucesso da API Gemini.")
        return response.text
    except Exception as e:
        logger.error(f"Exceção durante a chamada da API Gemini: {e}", exc_info=True)
        # Re-lança a exceção para ser capturada pelo manipulador de erro global
        raise

# --- FÁBRICA DE APLICAÇÃO FLASK ---

def create_app(config_class=Config) -> Flask:
    """Cria e configura a aplicação Flask usando o padrão de fábrica."""
    app = Flask(__name__, static_folder='public', static_url_path='')
    
    # Carrega a configuração a partir da classe Config
    app.config.from_object(config_class)

    # Configura o CORS para ser mais flexível
    CORS(app)

    # Configura o logger para funcionar bem com Gunicorn/Render
    if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
        app.logger.info("Logging configurado para Gunicorn.")

    # --- ROTAS DA APLICAÇÃO ---
    
    @app.route('/')
    def index():
        """Serve o arquivo principal index.html."""
        return app.send_static_file('index.html')

    @app.route('/chat', methods=['POST'])
    def chat():
        """Manipula as requisições de chat do frontend."""
        data = request.get_json()
        if not data or 'user_message' not in data:
            app.logger.warning("Requisição para /chat recebida sem 'user_message'.")
            return jsonify({"error": "Requisição inválida: 'user_message' é obrigatório."}), 400

        user_message = data.get('user_message')
        chat_history = data.get('chat_history', [])
        
        app.logger.info(f"Recebida mensagem do usuário para /chat: '{user_message[:50]}...'")
        
        ai_response_text = get_gemini_response(app.logger, user_message, chat_history)
        
        return jsonify({"ai_response": ai_response_text})

    # --- MANIPULADORES DE ERRO ---

    @app.errorhandler(500)
    def internal_server_error(error):
        """Manipulador de erro global para erros inesperados."""
        app.logger.error(f"Erro interno do servidor: {error}", exc_info=True)
        return jsonify(error="Ocorreu um erro interno inesperado no servidor."), 500

    return app

# --- EXECUÇÃO PRINCIPAL ---

def initialize_ai_client():
    """Configura o cliente do Google AI se a chave da API estiver disponível."""
    if Config.GEMINI_API_KEY:
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            # Usamos o logger padrão aqui porque o app logger ainda não está configurado
            logging.info("Cliente do Google AI configurado com sucesso.")
        except Exception as e:
            logging.error(f"Falha ao configurar o cliente do Google AI: {e}")
    else:
        logging.warning("Variável de ambiente GEMINI_API_KEY não encontrada.")


# Inicializa o cliente de IA na inicialização do módulo
initialize_ai_client()

# Cria a instância da aplicação Flask para ser usada pelo Gunicorn no Render
app = create_app()

if __name__ == '__main__':
    # Este bloco só é executado quando você roda `python index.py` localmente
    app.run(debug=True, port=5000)