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
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
        <title>Админ панель - AI Chat</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0a0e27;
                color: #e0e6ed;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: #e0e6ed;
                margin-bottom: 30px;
                font-size: 28px;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            .tab {
                padding: 12px 24px;
                background: #151b2e;
                border: 1px solid #1e2742;
                border-radius: 12px;
                cursor: pointer;
                font-size: 16px;
                transition: all 0.3s ease;
                color: #8b95a7;
                font-weight: 500;
            }
            .tab:hover {
                background: #1e2742;
                border-color: #667eea;
            }
            .tab.active {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-color: transparent;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .content {
                background: #151b2e;
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                border: 1px solid #1e2742;
                overflow-x: auto;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                min-width: 600px;
            }
            th, td {
                padding: 14px 12px;
                text-align: left;
                border-bottom: 1px solid #1e2742;
            }
            th {
                background: #0a0e27;
                font-weight: 600;
                color: #667eea;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            td {
                color: #e0e6ed;
                font-size: 14px;
            }
            tr:hover {
                background: #1e2742;
            }
            .upload-section {
                margin-bottom: 24px;
                padding: 20px;
                background: #0a0e27;
                border-radius: 12px;
                border: 1px solid #1e2742;
            }
            .upload-section h2 {
                color: #e0e6ed;
                margin-bottom: 16px;
                font-size: 20px;
            }
            .file-input-wrapper {
                margin-bottom: 12px;
            }
            .file-input-wrapper input[type="file"] {
                width: 100%;
                padding: 12px;
                background: #151b2e;
                border: 2px dashed #1e2742;
                border-radius: 8px;
                color: #e0e6ed;
                font-size: 14px;
                cursor: pointer;
            }
            .file-input-wrapper input[type="file"]:hover {
                border-color: #667eea;
            }
            .upload-btn {
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .upload-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            .upload-btn:active {
                transform: translateY(0);
            }
            .delete-btn {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            .delete-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
            }
            .loading {
                text-align: center;
                padding: 60px 20px;
                color: #8b95a7;
                font-size: 16px;
            }
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #1e2742;
                border-radius: 4px;
                overflow: hidden;
                margin-top: 12px;
                display: none;
            }
            .progress-bar.active {
                display: block;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                width: 0%;
                transition: width 0.3s ease;
                animation: shimmer 2s infinite;
            }
            @keyframes shimmer {
                0% { background-position: -1000px 0; }
                100% { background-position: 1000px 0; }
            }
            
            /* Мобильная адаптация */
            @media (max-width: 768px) {
                body {
                    padding: 12px;
                }
                h1 {
                    font-size: 24px;
                    margin-bottom: 20px;
                }
                .tabs {
                    gap: 8px;
                    margin-bottom: 16px;
                }
                .tab {
                    padding: 10px 16px;
                    font-size: 14px;
                    flex: 1;
                    min-width: calc(50% - 4px);
                }
                .content {
                    padding: 16px;
                    border-radius: 12px;
                }
                table {
                    min-width: 500px;
                    font-size: 12px;
                }
                th, td {
                    padding: 10px 8px;
                }
                th {
                    font-size: 11px;
                }
                td {
                    font-size: 12px;
                }
                .upload-section {
                    padding: 16px;
                }
                .upload-section h2 {
                    font-size: 18px;
                    margin-bottom: 12px;
                }
                .file-input-wrapper input[type="file"] {
                    font-size: 12px;
                    padding: 10px;
                }
                .upload-btn {
                    width: 100%;
                    padding: 14px;
                    font-size: 15px;
                }
                .delete-btn {
                    padding: 6px 12px;
                    font-size: 12px;
                }
            }
            
            @media (max-width: 480px) {
                body {
                    padding: 8px;
                }
                h1 {
                    font-size: 20px;
                    margin-bottom: 16px;
                }
                .tabs {
                    flex-direction: column;
                    gap: 8px;
                }
                .tab {
                    width: 100%;
                    min-width: 100%;
                }
                .content {
                    padding: 12px;
                    border-radius: 10px;
                }
                table {
                    min-width: 400px;
                }
                th, td {
                    padding: 8px 6px;
                }
                th {
                    font-size: 10px;
                }
                td {
                    font-size: 11px;
                }
                .upload-section {
                    padding: 12px;
                }
                .upload-section h2 {
                    font-size: 16px;
                }
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
                                </tr>
                            </thead>
                            <tbody>
                                ${contacts.map((c, idx) => `
                                    <tr>
                                        <td>${idx + 1}</td>
                                        <td>${c.name || '-'}</td>
                                        <td>${c.phone || '-'}</td>
                                        <td>${new Date(c.created_at).toLocaleString('ru-RU')}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    document.getElementById('contacts-tab').innerHTML = html;
                } catch (error) {
                    document.getElementById('contacts-tab').innerHTML = '<p style="color: #ef4444; padding: 20px; text-align: center;">Ошибка загрузки: ' + error + '</p>';
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
                        <div class="upload-section">
                            <h2>База знаний</h2>
                            <div class="file-input-wrapper">
                                <input type="file" id="fileInput" accept=".txt,.pdf,.doc,.docx" multiple>
                            </div>
                            <button class="upload-btn" onclick="uploadDocuments()">Загрузить документы</button>
                            <div class="progress-bar" id="progressBar">
                                <div class="progress-fill" id="progressFill"></div>
                            </div>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Название</th>
                                    <th>Дата загрузки</th>
                                    <th>Действия</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${documents.map((d, idx) => `
                                    <tr>
                                        <td>${idx + 1}</td>
                                        <td>${d.name || '-'}</td>
                                        <td>${new Date(d.created_at).toLocaleString('ru-RU')}</td>
                                        <td><button class="delete-btn" onclick="deleteDocument(${d.id})">Удалить</button></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    document.getElementById('knowledge-tab').innerHTML = html;
                } catch (error) {
                    document.getElementById('knowledge-tab').innerHTML = '<p style="color: #ef4444; padding: 20px; text-align: center;">Ошибка загрузки: ' + error + '</p>';
                }
            }
            
            async function uploadDocuments() {
                const fileInput = document.getElementById('fileInput');
                const files = fileInput.files;
                if (files.length === 0) {
                    alert('Выберите файлы для загрузки');
                    return;
                }
                
                const progressBar = document.getElementById('progressBar');
                const progressFill = document.getElementById('progressFill');
                progressBar.classList.add('active');
                progressFill.style.width = '0%';
                
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {
                    formData.append('files', files[i]);
                }
                
                try {
                    const xhr = new XMLHttpRequest();
                    xhr.upload.addEventListener('progress', (e) => {
                        if (e.lengthComputable) {
                            const percentComplete = (e.loaded / e.total) * 100;
                            progressFill.style.width = percentComplete + '%';
                        }
                    });
                    
                    xhr.addEventListener('load', () => {
                        if (xhr.status === 200) {
                            progressFill.style.width = '100%';
                            setTimeout(() => {
                                progressBar.classList.remove('active');
                                progressFill.style.width = '0%';
                                alert('Документы успешно загружены');
                                loadKnowledge();
                            }, 500);
                        } else {
                            progressBar.classList.remove('active');
                            progressFill.style.width = '0%';
                            alert('Ошибка загрузки: HTTP ' + xhr.status);
                        }
                    });
                    
                    xhr.addEventListener('error', () => {
                        progressBar.classList.remove('active');
                        progressFill.style.width = '0%';
                        alert('Ошибка загрузки');
                    });
                    
                    xhr.open('POST', `${API_URL}/api/admin/knowledge/upload`);
                    xhr.send(formData);
                } catch (error) {
                    progressBar.classList.remove('active');
                    progressFill.style.width = '0%';
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
                    document.querySelectorAll('.tab')[0].classList.add('active');
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
