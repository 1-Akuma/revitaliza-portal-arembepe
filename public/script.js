document.addEventListener("DOMContentLoaded", function () {
    // --- LÓGICA DO FORMULÁRIO DE CONTATO (EmailJS) ---
    (function(){
        emailjs.init({ publicKey: "Ztf5TxtuJESPKR8LC" });
    })();

    const contactForm = document.getElementById('contactForm');
    const responseMessage = document.getElementById('responseMessage');

    contactForm.addEventListener('submit', function (event) {
        event.preventDefault();
        
        responseMessage.innerText = "Enviando...";
        responseMessage.style.color = "black";

        emailjs.sendForm("service_07frwli", "template_db13fms", this)
            .then(() => {
                responseMessage.innerText = 'Obrigado! Sua mensagem foi enviada com sucesso.';
                responseMessage.style.color = 'green';
                contactForm.reset();
            }, (error) => {
                responseMessage.innerText = 'Houve um erro. Tente novamente mais tarde.';
                responseMessage.style.color = 'red';
                console.error('EmailJS Error:', error);
            });
    });

    // --- LÓGICA DO CHATBOT DE IA ---
    
    // --- Início do Bloco Corrigido ---
const getBackendUrl = () => {
    const hostname = window.location.hostname;
    // Quando o site estiver online, o hostname NÃO será 'localhost' ou '127.0.0.1'
    if (hostname === "localhost" || hostname === "127.0.0.1") {
        // Ambiente de desenvolvimento local
        return 'http://127.0.0.1:5000/chat';
    } else {
        // Ambiente de produção (online)
        // Usa a própria URL do site para encontrar o backend
        return `https://${hostname}/chat`;
    }
};
const backendUrl = getBackendUrl();
// --- Fim do Bloco Corrigido ---
    
    const chatbotButton = document.getElementById('chatbot-button');
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotCloseButton = chatbotContainer.querySelector('.chatbot-close-button');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSendButton = document.getElementById('chatbot-send-button');

    let chatHistory = [];

    // Função auxiliar para criar e adicionar balões de mensagem
    const createMessageBubble = (text, type, isLoading = false) => {
        const bubble = document.createElement('div');
        bubble.classList.add('message-bubble', `message-${type}`);
        if (isLoading) {
            bubble.classList.add('message-loading');
        }
        bubble.innerText = text;
        chatbotMessages.appendChild(bubble);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        return bubble;
    };

    const toggleChatbot = (forceOpen = null) => {
        const isActive = chatbotContainer.classList.contains('active');
        if ((forceOpen === true) || (forceOpen === null && !isActive)) {
             chatbotContainer.classList.add('active');
             chatbotContainer.setAttribute('aria-hidden', 'false');
             chatbotInput.focus();
        } else {
             chatbotContainer.classList.remove('active');
             chatbotContainer.setAttribute('aria-hidden', 'true');
        }
    }

    chatbotButton.addEventListener('click', () => toggleChatbot());
    chatbotCloseButton.addEventListener('click', () => toggleChatbot(false));

    // Saudação inicial da IA
    const initialAiGreeting = "Olá! Sou a IA do Portal de Arembepe. Como posso ajudar com o projeto de revitalização?";
    createMessageBubble(initialAiGreeting, 'ai');
    chatHistory.push({ role: "model", parts: [{ text: initialAiGreeting }] });
    
    const sendMessageToAI = async () => {
        const userMessageText = chatbotInput.value.trim();
        if (!userMessageText) return;

        createMessageBubble(userMessageText, 'user');
        chatHistory.push({ role: "user", parts: [{ text: userMessageText }] });
        
        chatbotInput.value = '';
        const loadingBubble = createMessageBubble('Digitando...', 'ai', true);

        try {
            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_message: userMessageText,
                    chat_history: chatHistory.slice(0, -1)
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const result = await response.json();
            loadingBubble.innerText = result.ai_response || "Desculpe, não consegui processar a resposta.";
            chatHistory.push({ role: "model", parts: [{ text: result.ai_response }] });

        } catch (error) {
            console.error('Error fetching AI response:', error);
            loadingBubble.innerText = "Erro de conexão com o assistente. Por favor, tente novamente.";
        } finally {
            loadingBubble.classList.remove('message-loading');
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        }
    };

    chatbotSendButton.addEventListener('click', sendMessageToAI);
    chatbotInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessageToAI();
        }
    });
});