(function() {
    'use strict';
    
    const API_URL = window.API_URL || 'http://localhost:8000';
    const MOCK_MODE = window.MOCK_MODE === true; // По умолчанию выключен
    
    class ChatWidget {
        constructor() {
            this.isOpen = false;
            this.isExpanded = false;
            this.sessionId = localStorage.getItem('chat_session_id') || null;
            this.expandTimer = null;
            this.init();
        }
        
        init() {
            this.createWidget();
            this.attachEvents();
            this.startExpandTimer();
        }
        
        createWidget() {
            const widget = document.createElement('div');
            widget.id = 'ai-chat-widget';
            widget.className = 'ai-chat-widget';
            widget.innerHTML = `
                <div class="ai-chat-widget-container">
                    <div class="chat-expanded-message" id="chat-expanded-message">
                        <span>Нужна помощь?</span>
                    </div>
                    <div class="chat-button" id="chat-button">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor"/>
                        </svg>
                    </div>
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
            this.loadWidgetSettings();
        }
        
        async loadWidgetSettings() {
            try {
                // Определяем правильный API URL
                let apiUrl = API_URL;
                if (!apiUrl || apiUrl === 'http://localhost:8000') {
                    // Если API_URL не установлен или это localhost, пытаемся определить автоматически
                    const protocol = window.location.protocol;
                    const hostname = window.location.hostname;
                    // Если frontend и backend на одном домене, используем относительный путь
                    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
                        apiUrl = `${protocol}//${hostname}:8000`;
                    } else {
                        apiUrl = API_URL || 'http://localhost:8000';
                    }
                }
                
                const response = await fetch(`${apiUrl}/api/admin/widget/settings/public`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    mode: 'cors',
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const settings = await response.json();
                    const widget = document.getElementById('ai-chat-widget');
                    if (widget) {
                        widget.style.setProperty('--widget-primary-color', settings.primary_color || '#667eea');
                        widget.style.setProperty('--widget-secondary-color', settings.secondary_color || '#764ba2');
                        widget.style.setProperty('--widget-button-color', settings.button_color || '#667eea');
                        widget.style.setProperty('--widget-message-color', settings.message_color || '#667eea');
                        widget.style.setProperty('--widget-background-color', settings.background_color || '#151b2e');
                        widget.style.setProperty('--widget-header-color', settings.header_color || '#667eea');
                        widget.style.setProperty('--widget-header-text-color', settings.header_text_color || '#ffffff');
                        widget.style.setProperty('--widget-user-message-color', settings.user_message_color || '#667eea');
                        widget.style.setProperty('--widget-bot-message-color', settings.bot_message_color || '#1e2742');
                        widget.style.setProperty('--widget-text-color', settings.text_color || '#e0e6ed');
                        widget.style.setProperty('--widget-messages-area-color', settings.messages_area_color || '#0a0e27');
                        widget.style.setProperty('--widget-input-background-color', settings.input_background_color || '#0a0e27');
                        widget.style.setProperty('--widget-border-color', settings.border_color || '#1e2742');
                    }
                    
                    // Обновляем приветственное сообщение
                    const welcomeMsg = document.querySelector('#chat-messages .bot-message .message-content');
                    if (welcomeMsg && settings.welcome_message) {
                        welcomeMsg.textContent = settings.welcome_message;
                    }
                    
                    // Обновляем текст расширенного сообщения
                    const expandedMsg = document.getElementById('chat-expanded-message');
                    if (expandedMsg && settings.expanded_message_text) {
                        expandedMsg.querySelector('span').textContent = settings.expanded_message_text;
                    }
            } catch (error) {
                console.error('Ошибка загрузки настроек виджета:', error);
                // Используем настройки по умолчанию при ошибке
                console.warn('Используются настройки виджета по умолчанию');
            }
        }
        
        attachEvents() {
            const chatButton = document.getElementById('chat-button');
            const expandedMessage = document.getElementById('chat-expanded-message');
            
            chatButton.addEventListener('click', () => {
                this.cancelExpandTimer();
                this.collapseWidget();
                this.toggleChat();
            });
            
            expandedMessage.addEventListener('click', () => {
                this.cancelExpandTimer();
                this.collapseWidget();
                this.toggleChat();
            });
            
            document.getElementById('close-button').addEventListener('click', () => {
                this.collapseWidget();
                this.toggleChat();
            });
            
            document.getElementById('send-button').addEventListener('click', () => this.sendMessage());
            document.getElementById('chat-input').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }
        
        startExpandTimer() {
            // Отменяем существующий таймер, если он есть
            this.cancelExpandTimer();
            
            this.expandTimer = setTimeout(() => {
                if (!this.isOpen && !this.isExpanded) {
                    this.expandWidget();
                }
                this.expandTimer = null;
            }, 5000); // 5 секунд
        }
        
        cancelExpandTimer() {
            if (this.expandTimer) {
                clearTimeout(this.expandTimer);
                this.expandTimer = null;
            }
        }
        
        expandWidget() {
            if (this.isExpanded || this.isOpen) return;
            
            this.isExpanded = true;
            const widget = document.getElementById('ai-chat-widget');
            widget.classList.add('expanded');
        }
        
        collapseWidget() {
            if (!this.isExpanded) return;
            
            this.isExpanded = false;
            const widget = document.getElementById('ai-chat-widget');
            widget.classList.remove('expanded');
        }
        
        toggleChat() {
            this.isOpen = !this.isOpen;
            const window = document.getElementById('chat-window');
            const widget = document.getElementById('ai-chat-widget');
            if (this.isOpen) {
                window.classList.add('active');
                widget.classList.add('chat-open');
                this.collapseWidget();
            } else {
                window.classList.remove('active');
                widget.classList.remove('chat-open');
                // Перезапускаем таймер, если виджет закрыт
                if (!this.isExpanded) {
                    this.startExpandTimer();
                }
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
            
            // Для бот-сообщений рендерим Markdown, для пользовательских - экранируем HTML
            let content;
            if (type === 'bot') {
                // Проверяем наличие marked и рендерим Markdown для бот-сообщений
                if (typeof marked !== 'undefined' && marked && marked.parse) {
                    try {
                        content = marked.parse(text);
                    } catch (e) {
                        console.error('Markdown parsing error:', e);
                        content = this.escapeHtml(text);
                    }
                } else {
                    console.warn('marked.js не загружен, используем обычный текст');
                    content = this.escapeHtml(text);
                }
            } else {
                // Экранируем HTML для пользовательских сообщений
                content = this.escapeHtml(text);
            }
            
            messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
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
