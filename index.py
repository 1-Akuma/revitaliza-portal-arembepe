import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Carrega variáveis de ambiente do arquivo .env (para desenvolvimento local)
load_dotenv()

app = Flask(__name__)

# --- Configuração de CORS para Produção e Desenvolvimento ---
frontend_url = os.environ.get("FRONTEND_URL", "http://127.0.0.1:8000") 
# CORREÇÃO: Adicionamos a porta 5500 para permitir testes com o Live Server do VSCode
CORS(app, origins=[frontend_url, "http://localhost:8000", "http://127.0.0.1:5500"]) 

# --- Configuração da API do Google Gemini ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("ALERTA: GEMINI_API_KEY não foi encontrada nas variáveis de ambiente.")

# --- Contexto Fixo para a IA (Base de Conhecimento) ---
community_content_context = """
Este portal e o projeto "Revitaliza Portal de Arembepe" são iniciativas de moradores do condomínio Portal de Arembepe, distrito litorâneo de Camaçari (BA), focadas na melhoria da qualidade de vida e do meio ambiente através de revitalização, limpeza e preservação ambiental.

**Origem do Projeto:**
O projeto foi idealizado por Dêivide Sobral da Silva Bezerra, morador de Arembepe e entusiasta do desenvolvimento comunitário. Ele se inspirou em EcoPEVs e cooperativas de reciclagem para mobilizar a comunidade.

**Projetos e Iniciativas Específicas do Condomínio Portal:**
1.  **Coleta seletiva comunitária:** O Condomínio Portal organiza mutirões de coleta seletiva com apoio do **EcoPEV municipal** (Ponto de Entrega Voluntária, que recebe entulho, volumosos e recicláveis com capacidade de até 30m³ para entulho e 20m³ para volumosos) e da **Limpec** (empresa municipal com ações de coleta seletiva e educação ambiental em Camaçari). O objetivo é aumentar o volume de recicláveis e reduzir o descarte irregular em dunas, lagoas e praias. O **EcoPEV Arembepe** é uma estrutura para recebimento e triagem de materiais.
2.  **Reflorestamento das dunas:** Em parceria com o ativista **Rivelino Martins** (líder de projeto que visa restaurar a vegetação nativa das dunas para preservar solos e biodiversidade), o Condomínio Portal apoia o reflorestamento das dunas de Arembepe, plantando mudas de espécies nativas com envolvimento familiar.
3.  **Educação ambiental e eventos:** O grupo realiza palestras e oficinas no **Centro de Educação Ambiental de Arembepe**, inaugurado em 1992 ao lado da Aldeia Hippie, criado pelo **Projeto Tamar** (que foca em pesquisa, conservação de tartarugas marinhas e inclusão social). Temas abordados incluem reciclagem, compostagem caseira e manejo de resíduos de óleo, com especialistas e catadores da **Coopama** (cooperativa de reciclagem e gestão de resíduos que atua na coleta, triagem e destinação correta de resíduos, gerando renda e impacto positivo).
4.  **Limpeza e conservação das lagoas:** O grupo atua em parceria com vereadores e órgãos ambientais para limpeza das lagoas de Areias e Arembepe. Existe um **pedido legislativo** (por vereador de Camaçari) para a limpeza das lagoas, enfatizando a importância de sua conservação.
5.  **Remoção de resíduos de óleo:** A **Defesa Civil** e a **Naturalle** (empresa especializada) realizam ações conjuntas para retirada de resíduos de óleo nas praias de Arembepe.

**Motivação e Riscos (Benefícios de agir / Malefícios da inação):**
* **Benefícios de agir:** Valorização de imóveis, redução de doenças (controle de lixo/entulho), convivência harmoniosa, maior contato com a natureza e educação ambiental.
* **Malefícios da inação:** Proliferação de insetos/animais peçonhentos (lixo/mato alto), degradação de áreas comuns/vias, desvalorização do bairro, conflitos entre moradores.

**Medidas Propostas pelo Condomínio Portal:**
* Atuar com mutirões.
* Sinalização educativa.
* Lixeiras apropriadas.
* Comunicação direta com a administração.
* Envolvimento das famílias nas ações.

**Engajamento Comunitário:**
Moradores participam de mutirões de limpeza (como o **Dia Mundial da Limpeza em Arembepe**, um evento anual de mobilização para limpeza de praias, rios, lagoas e áreas verdes) e utilizam o **Plano Municipal de Gestão Integrada de Resíduos Sólidos (PMGIRS) de Camaçari** para sugerir melhorias e fiscalizar metas. O PMGIRS é um documento oficial de Camaçari (inclui Arembepe) com políticas, metas e ações para manejo de resíduos, com investimentos acima da média nacional. A comunicação interna ocorre via o Portal virtual.

**Impactos e Perspectivas:**
Já foram coletadas mais de 5 toneladas de recicláveis, plantadas mais de 300 mudas nas dunas, e mobilizadas mais de 100 famílias em ações de educação. Há expectativa de expandir parcerias (universidades, institutos de pesquisa) e conseguir financiamento para campanhas futuras (prevenção de resíduos de óleo, educação ambiental, limpeza contínua).
O projeto **Reflora Camaçari** é uma iniciativa da Secretaria de Desenvolvimento Urbano para revitalização de áreas degradadas com plantio de espécies nativas e restauração de corredores verdes.

**Conclusão do Projeto:**
O Condomínio Portal de Arembepe é um modelo replicável de gestão comunitária e ambiental, demonstrando que iniciativas de base podem gerar transformações concretas e duradouras com união e consciência.
"""

# --- Prompt do Sistema Otimizado ---
SYSTEM_INSTRUCTION = f"""
Você é a "IA do Portal", um assistente virtual especialista no projeto "Revitaliza Portal de Arembepe".
Sua ÚNICA fonte de conhecimento é o texto abaixo. Responda de forma amigável, concisa e baseada ESTRITAMENTE neste contexto.
Se a pergunta for sobre algo fora do contexto, responda educadamente: "Não tenho informações sobre isso. Meu conhecimento é focado no projeto de revitalização do Portal de Arembepe."
Seja prestativo com saudações, agradecimentos e entenda pequenas variações de escrita.

--- CONTEXTO DO PROJETO ---
{community_content_context}
---
"""

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    # CORREÇÃO: Lida com a requisição de verificação OPTIONS do navegador
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # Se a requisição for POST, a lógica principal é executada
    if request.method == 'POST':
        if not GEMINI_API_KEY:
            return jsonify({"error": "Erro no servidor: Chave da API não configurada."}), 500

        try:
            data = request.get_json()
            user_message = data.get('user_message')
            chat_history = data.get('chat_history', [])

            if not user_message:
                return jsonify({"error": "Mensagem do usuário não fornecida."}), 400
            
            history_for_gemini = [
                {'role': 'user', 'parts': [SYSTEM_INSTRUCTION]},
                {'role': 'model', 'parts': ["Olá! Sou a IA do Portal. Como posso ajudar?"]}
            ]
            history_for_gemini.extend(chat_history)

            model = genai.GenerativeModel('gemini-1.5-flash')
            chat_session = model.start_chat(history=history_for_gemini)
            
            response = chat_session.send_message(user_message)
            
            return jsonify({"ai_response": response.text})

        except Exception as e:
            print(f"ERRO no endpoint /chat: {e}")
            return jsonify({"error": "Ocorreu um erro interno no servidor."}), 500