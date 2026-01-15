(function() {
    'use strict';
    
    const API_URL = window.API_URL || 'http://localhost:8000';
    const MOCK_MODE = window.MOCK_MODE !== false; // По умолчанию включен
    
    class ChatWidget {
        constructor() {
            this.isOpen = false;
            this.sessionId = localStorage.getItem('chat_session_id') || null;
            this.init();
        }
        
        init() {
            this.createWidget();
            this.attachEvents();
            // На мобильных и планшетах автоматически открываем виджет
            if (window.innerWidth <= 1024) {
                this.isOpen = true;
                const window = document.getElementById('chat-window');
                if (window) {
                    window.classList.add('active');
                }
            }
        }
        
        createWidget() {
            const widget = document.createElement('div');
            widget.id = 'ai-chat-widget';
            widget.className = 'ai-chat-widget';
            widget.innerHTML = `
                <div class="chat-button" id="chat-button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor"/>
                    </svg>
                </div>
                <div class="chat-window" id="chat-window">
                    <div class="chat-header">
                        <h3>AI Ассистент</h3>
                        <button class="close-button" id="close-button">×</button>
                    </div>
                    <div class="chat-messages" id="chat-messages">
                        <div class="message bot-message">
                            <div class="message-content">
                                Привет! Чем могу помочь?
                            </div>
                        </div>
                    </div>
                    <div class="chat-input-container" id="chat-input-container">
                        <input type="text" id="chat-input" placeholder="Введите сообщение...">
                        <button id="send-button">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(widget);
        }
        
        attachEvents() {
            document.getElementById('chat-button').addEventListener('click', () => this.toggleChat());
            document.getElementById('close-button').addEventListener('click', () => this.toggleChat());
            document.getElementById('send-button').addEventListener('click', () => this.sendMessage());
            document.getElementById('chat-input').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }
        
        toggleChat() {
            this.isOpen = !this.isOpen;
            const window = document.getElementById('chat-window');
            if (this.isOpen) {
                window.classList.add('active');
            } else {
                window.classList.remove('active');
            }
        }
        
        async sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            this.addMessage('user', message);
            input.value = '';
            
            this.showTyping();
            
            // Режим заглушки
            if (MOCK_MODE) {
                setTimeout(() => {
                    this.hideTyping();
                    const mockResponses = [
                        'Спасибо за ваше сообщение! Я обработаю ваш запрос.',
                        'Понял, работаю над этим. Можете уточнить детали?',
                        'Отличный вопрос! Давайте разберемся вместе.',
                        'Принято к сведению. Что-то еще интересует?',
                        'Спасибо за обращение! Я передам информацию администратору.'
                    ];
                    const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
                    this.addMessage('bot', randomResponse);
                }, 1000 + Math.random() * 1000);
                return;
            }
            
            try {
                const response = await fetch(`${API_URL}/api/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: this.sessionId
                    })
                });
                
                const data = await response.json();
                this.hideTyping();
                this.addMessage('bot', data.response || 'Извините, произошла ошибка');
                
                // Сохраняем session_id для следующих запросов
                if (data.session_id) {
                    this.sessionId = data.session_id;
                    localStorage.setItem('chat_session_id', data.session_id);
                }
            } catch (error) {
                this.hideTyping();
                this.addMessage('bot', 'Извините, не удалось отправить сообщение. Попробуйте позже.');
                console.error('Error:', error);
            }
        }
        
        addMessage(type, text) {
            const messages = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.innerHTML = `<div class="message-content">${this.escapeHtml(text)}</div>`;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        showTyping() {
            const messages = document.getElementById('chat-messages');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typing-indicator';
            typingDiv.className = 'message bot-message';
            typingDiv.innerHTML = `
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            messages.appendChild(typingDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        hideTyping() {
            const typing = document.getElementById('typing-indicator');
            if (typing) typing.remove();
        }
        
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }
    
    // Инициализация виджета при загрузке страницы
    // Не загружаем виджет на странице админки
    if (window.location.pathname.includes('/admin')) {
        return;
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => new ChatWidget());
    } else {
        new ChatWidget();
    }
})();
