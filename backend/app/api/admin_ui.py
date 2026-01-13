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
                <button class="tab" onclick="showTab('knowledge')">База знаний</button>
            </div>
            <div class="content">
                <div id="contacts-tab">
                    <div class="loading">Загрузка контактов...</div>
                </div>
                <div id="knowledge-tab" style="display: none;">
                    <div class="loading">Загрузка базы знаний...</div>
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
                                        <td>-</td>
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
            
            async function loadKnowledge() {
                try {
                    const response = await fetch(`${API_URL}/api/admin/knowledge`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    const documents = await response.json();
                    
                    const html = `
                        <div style="margin-bottom: 20px;">
                            <h2>База знаний</h2>
                            <input type="file" id="fileInput" accept=".txt,.pdf,.doc,.docx" multiple style="margin-bottom: 10px;">
                            <button onclick="uploadDocuments()" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer;">Загрузить документы</button>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Название</th>
                                    <th>Тип</th>
                                    <th>Размер</th>
                                    <th>Дата загрузки</th>
                                    <th>Действия</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${documents.map(d => `
                                    <tr>
                                        <td>${d.id}</td>
                                        <td>${d.name || '-'}</td>
                                        <td>${d.type || '-'}</td>
                                        <td>${d.size || '-'}</td>
                                        <td>${new Date(d.created_at).toLocaleString('ru-RU')}</td>
                                        <td><button onclick="deleteDocument(${d.id})" style="background: #ff4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Удалить</button></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    document.getElementById('knowledge-tab').innerHTML = html;
                } catch (error) {
                    document.getElementById('knowledge-tab').innerHTML = '<p style="color: red;">Ошибка загрузки: ' + error + '</p>';
                }
            }
            
            async function uploadDocuments() {
                const fileInput = document.getElementById('fileInput');
                const files = fileInput.files;
                if (files.length === 0) {
                    alert('Выберите файлы для загрузки');
                    return;
                }
                
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {
                    formData.append('files', files[i]);
                }
                
                try {
                    const response = await fetch(`${API_URL}/api/admin/knowledge/upload`, {
                        method: 'POST',
                        body: formData
                    });
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    alert('Документы успешно загружены');
                    loadKnowledge();
                } catch (error) {
                    alert('Ошибка загрузки: ' + error);
                }
            }
            
            async function deleteDocument(id) {
                if (!confirm('Удалить документ?')) return;
                try {
                    const response = await fetch(`${API_URL}/api/admin/knowledge/${id}`, {
                        method: 'DELETE'
                    });
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    alert('Документ удален');
                    loadKnowledge();
                } catch (error) {
                    alert('Ошибка удаления: ' + error);
                }
            }
            
            function showTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.getElementById('contacts-tab').style.display = 'none';
                document.getElementById('knowledge-tab').style.display = 'none';
                
                if (tab === 'contacts') {
                    document.querySelector('.tab').classList.add('active');
                    document.getElementById('contacts-tab').style.display = 'block';
                    loadContacts();
                } else {
                    document.querySelectorAll('.tab')[1].classList.add('active');
                    document.getElementById('knowledge-tab').style.display = 'block';
                    loadKnowledge();
                }
            }
            
            // Загружаем контакты при загрузке страницы
            loadContacts();
        </script>
    </body>
    </html>
    """
    return html_content
