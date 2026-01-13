from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-ui"])

@router.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Админ панель для просмотра контактов"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Админ панель - AI Chat</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f7fa;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
                margin-bottom: 30px;
            }
            .tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            .tab {
                padding: 10px 20px;
                background: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                transition: all 0.2s;
            }
            .tab.active {
                background: #667eea;
                color: white;
            }
            .content {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #e0e0e0;
            }
            th {
                background: #f8f9fa;
                font-weight: 600;
                color: #666;
            }
            .message-user {
                background: #e3f2fd;
                padding: 8px;
                border-radius: 8px;
                margin: 5px 0;
            }
            .message-bot {
                background: #f1f8e9;
                padding: 8px;
                border-radius: 8px;
                margin: 5px 0;
            }
            .loading {
                text-align: center;
                padding: 40px;
                color: #999;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Админ панель - AI Chat Assistant</h1>
            <div class="tabs">
                <button class="tab active" onclick="showTab('contacts')">Контакты</button>
                <button class="tab" onclick="showTab('messages')">Сообщения</button>
            </div>
            <div class="content">
                <div id="contacts-tab">
                    <div class="loading">Загрузка контактов...</div>
                </div>
                <div id="messages-tab" style="display: none;">
                    <div class="loading">Загрузка сообщений...</div>
                </div>
            </div>
        </div>
        <script>
            const API_URL = window.location.origin;
            
            async function loadContacts() {
                try {
                    const response = await fetch(`${API_URL}/api/admin/contacts`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    const contacts = await response.json();
                    
                    const html = `
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Имя</th>
                                    <th>Телефон</th>
                                    <th>Дата создания</th>
                                    <th>Действия</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${contacts.map(c => `
                                    <tr>
                                        <td>${c.id}</td>
                                        <td>${c.name || '-'}</td>
                                        <td>${c.phone || '-'}</td>
                                        <td>${new Date(c.created_at).toLocaleString('ru-RU')}</td>
                                        <td><button onclick="loadMessages(${c.id})">История</button></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    document.getElementById('contacts-tab').innerHTML = html;
                } catch (error) {
                    document.getElementById('contacts-tab').innerHTML = '<p style="color: red;">Ошибка загрузки: ' + error + '</p>';
                }
            }
            
            async function loadAllMessages() {
                try {
                    const response = await fetch(`${API_URL}/api/admin/messages?limit=100`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    const messages = await response.json();
                    
                    const html = `
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Контакт</th>
                                    <th>Сообщение</th>
                                    <th>Ответ</th>
                                    <th>Дата</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${messages.map(m => `
                                    <tr>
                                        <td>${m.id}</td>
                                        <td>${m.contact_id || '-'}</td>
                                        <td><div class="message-user">${m.message}</div></td>
                                        <td><div class="message-bot">${m.response || '-'}</div></td>
                                        <td>${new Date(m.created_at).toLocaleString('ru-RU')}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    document.getElementById('messages-tab').innerHTML = html;
                } catch (error) {
                    document.getElementById('messages-tab').innerHTML = '<p style="color: red;">Ошибка загрузки: ' + error + '</p>';
                }
            }
            
            async function loadMessages(contactId) {
                try {
                    const response = await fetch(`${API_URL}/api/admin/contacts/${contactId}/messages`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    const messages = await response.json();
                    
                    const html = `
                        <h2>История сообщений контакта #${contactId}</h2>
                        <button onclick="showTab('contacts')" style="margin-bottom: 20px;">← Назад</button>
                        <div>
                            ${messages.map(m => `
                                <div style="margin: 15px 0;">
                                    <div class="${m.is_from_user ? 'message-user' : 'message-bot'}">
                                        <strong>${m.is_from_user ? 'Пользователь' : 'Бот'}:</strong><br>
                                        ${m.is_from_user ? m.message : m.response}
                                    </div>
                                    <small style="color: #999;">${new Date(m.created_at).toLocaleString('ru-RU')}</small>
                                </div>
                            `).join('')}
                        </div>
                    `;
                    document.getElementById('contacts-tab').innerHTML = html;
                } catch (error) {
                    alert('Ошибка загрузки истории: ' + error);
                }
            }
            
            function showTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.getElementById('contacts-tab').style.display = 'none';
                document.getElementById('messages-tab').style.display = 'none';
                
                if (tab === 'contacts') {
                    document.querySelector('.tab').classList.add('active');
                    document.getElementById('contacts-tab').style.display = 'block';
                    loadContacts();
                } else {
                    document.querySelectorAll('.tab')[1].classList.add('active');
                    document.getElementById('messages-tab').style.display = 'block';
                    loadAllMessages();
                }
            }
            
            // Загружаем контакты при загрузке страницы
            loadContacts();
        </script>
    </body>
    </html>
    """
    return html_content
