from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-ui"])

@router.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Админ панель - главная страница с навигацией"""
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
                background: #0a0e27;
                color: #e0e6ed;
                min-height: 100vh;
                padding: 0;
            }
            .navbar {
                background: #151b2e;
                padding: 20px 40px;
                border-bottom: 1px solid #1e2742;
                display: flex;
                align-items: center;
                gap: 30px;
                box-shadow: 0 2px 20px rgba(0,0,0,0.3);
            }
            .logo {
                font-size: 24px;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .nav-links {
                display: flex;
                gap: 10px;
            }
            .nav-link {
                padding: 10px 20px;
                background: transparent;
                border: none;
                color: #8b95a7;
                cursor: pointer;
                border-radius: 8px;
                font-size: 15px;
                transition: all 0.3s ease;
                position: relative;
            }
            .nav-link:hover {
                color: #e0e6ed;
                background: #1e2742;
            }
            .nav-link.active {
                color: #667eea;
                background: #1e2742;
            }
            .nav-link.active::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 20px;
                right: 20px;
                height: 2px;
                background: linear-gradient(90deg, #667eea, #764ba2);
                border-radius: 2px;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 40px;
            }
            .page {
                display: none;
                animation: fadeIn 0.4s ease;
            }
            .page.active {
                display: block;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .card {
                background: #151b2e;
                border-radius: 16px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                border: 1px solid #1e2742;
            }
            .page-title {
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 16px;
                text-align: left;
                border-bottom: 1px solid #1e2742;
            }
            th {
                font-weight: 600;
                color: #8b95a7;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            td {
                color: #e0e6ed;
            }
            tr {
                transition: all 0.2s ease;
            }
            tr:hover {
                background: #1e2742;
            }
            .loading {
                text-align: center;
                padding: 60px;
                color: #8b95a7;
            }
            .spinner {
                border: 3px solid #1e2742;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .upload-area {
                background: #1e2742;
                border: 2px dashed #3a4562;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
                margin-bottom: 30px;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            .upload-area:hover {
                border-color: #667eea;
                background: #252d47;
            }
            .upload-area.dragover {
                border-color: #667eea;
                background: #252d47;
            }
            .file-input {
                display: none;
            }
            .upload-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
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
            .progress-container {
                display: none;
                margin-top: 20px;
            }
            .progress-container.active {
                display: block;
            }
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #1e2742;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 10px;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                width: 0%;
                transition: width 0.3s ease;
                border-radius: 4px;
            }
            .progress-text {
                color: #8b95a7;
                font-size: 14px;
            }
            .delete-btn {
                background: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.2s ease;
            }
            .delete-btn:hover {
                background: #c82333;
                transform: scale(1.05);
            }
            .empty-state {
                text-align: center;
                padding: 60px;
                color: #8b95a7;
            }
            .empty-state-icon {
                font-size: 64px;
                margin-bottom: 20px;
                opacity: 0.5;
            }
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="logo">AI Chat Assistant</div>
            <div class="nav-links">
                <button class="nav-link active" onclick="showPage('contacts')">Контакты</button>
                <button class="nav-link" onclick="showPage('knowledge')">База знаний</button>
            </div>
        </nav>
        
        <div class="container">
            <div id="contacts-page" class="page active">
                <h1 class="page-title">Контакты</h1>
                <div class="card">
                    <div id="contacts-content">
                        <div class="loading">
                            <div class="spinner"></div>
                            Загрузка контактов...
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="knowledge-page" class="page">
                <h1 class="page-title">База знаний</h1>
                <div class="card">
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <div style="font-size: 48px; margin-bottom: 15px;">📄</div>
                        <div style="font-size: 18px; margin-bottom: 10px; color: #e0e6ed;">Перетащите файлы сюда или нажмите для выбора</div>
                        <div style="font-size: 14px; color: #8b95a7;">Поддерживаются: TXT, PDF, DOC, DOCX</div>
                        <input type="file" id="fileInput" class="file-input" accept=".txt,.pdf,.doc,.docx" multiple>
                    </div>
                    
                    <div class="progress-container" id="progressContainer">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill"></div>
                        </div>
                        <div class="progress-text" id="progressText">Загрузка...</div>
                    </div>
                    
                    <div id="knowledge-content">
                        <div class="loading">
                            <div class="spinner"></div>
                            Загрузка базы знаний...
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const API_URL = window.location.origin;
            
            // Навигация
            function showPage(page) {
                document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                
                if (page === 'contacts') {
                    document.getElementById('contacts-page').classList.add('active');
                    document.querySelectorAll('.nav-link')[0].classList.add('active');
                    loadContacts();
                } else {
                    document.getElementById('knowledge-page').classList.add('active');
                    document.querySelectorAll('.nav-link')[1].classList.add('active');
                    loadKnowledge();
                }
            }
            
            // Загрузка контактов
            async function loadContacts() {
                const content = document.getElementById('contacts-content');
                content.innerHTML = '<div class="loading"><div class="spinner"></div>Загрузка контактов...</div>';
                
                try {
                    const response = await fetch(`${API_URL}/api/admin/contacts`);
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    const contacts = await response.json();
                    
                    if (contacts.length === 0) {
                        content.innerHTML = '<div class="empty-state"><div class="empty-state-icon">👤</div><div>Нет контактов</div></div>';
                        return;
                    }
                    
                    const html = `
                        <table>
                            <thead>
                                <tr>
                                    <th>№</th>
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
                    content.innerHTML = html;
                } catch (error) {
                    content.innerHTML = `<div style="color: #dc3545; text-align: center; padding: 40px;">Ошибка загрузки: ${error.message}</div>`;
                }
            }
            
            // Загрузка базы знаний
            async function loadKnowledge() {
                const content = document.getElementById('knowledge-content');
                content.innerHTML = '<div class="loading"><div class="spinner"></div>Загрузка базы знаний...</div>';
                
                try {
                    const response = await fetch(`${API_URL}/api/admin/knowledge`);
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    const documents = await response.json();
                    
                    if (documents.length === 0) {
                        content.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📚</div><div>База знаний пуста</div><div style="margin-top: 10px; font-size: 14px;">Загрузите документы для начала работы</div></div>';
                        return;
                    }
                    
                    const html = `
                        <table>
                            <thead>
                                <tr>
                                    <th>№</th>
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
                    content.innerHTML = html;
                } catch (error) {
                    content.innerHTML = `<div style="color: #dc3545; text-align: center; padding: 40px;">Ошибка загрузки: ${error.message}</div>`;
                }
            }
            
            // Загрузка файлов
            document.getElementById('fileInput').addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    uploadDocuments(e.target.files);
                }
            });
            
            // Drag & Drop
            const uploadArea = document.querySelector('.upload-area');
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                if (e.dataTransfer.files.length > 0) {
                    uploadDocuments(e.dataTransfer.files);
                }
            });
            
            async function uploadDocuments(files) {
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {
                    formData.append('files', files[i]);
                }
                
                const progressContainer = document.getElementById('progressContainer');
                const progressFill = document.getElementById('progressFill');
                const progressText = document.getElementById('progressText');
                
                progressContainer.classList.add('active');
                progressFill.style.width = '0%';
                progressText.textContent = 'Подготовка...';
                
                try {
                    const xhr = new XMLHttpRequest();
                    
                    xhr.upload.addEventListener('progress', (e) => {
                        if (e.lengthComputable) {
                            const percent = (e.loaded / e.total) * 100;
                            progressFill.style.width = percent + '%';
                            progressText.textContent = `Загрузка: ${Math.round(percent)}%`;
                        }
                    });
                    
                    xhr.addEventListener('load', () => {
                        if (xhr.status === 200) {
                            progressFill.style.width = '100%';
                            progressText.textContent = 'Загрузка завершена!';
                            setTimeout(() => {
                                progressContainer.classList.remove('active');
                                loadKnowledge();
                                document.getElementById('fileInput').value = '';
                            }, 1000);
                        } else {
                            throw new Error(`HTTP ${xhr.status}`);
                        }
                    });
                    
                    xhr.addEventListener('error', () => {
                        throw new Error('Ошибка сети');
                    });
                    
                    xhr.open('POST', `${API_URL}/api/admin/knowledge/upload`);
                    xhr.send(formData);
                } catch (error) {
                    progressText.textContent = 'Ошибка: ' + error.message;
                    setTimeout(() => {
                        progressContainer.classList.remove('active');
                    }, 3000);
                }
            }
            
            async function deleteDocument(id) {
                if (!confirm('Удалить документ?')) return;
                
                try {
                    const response = await fetch(`${API_URL}/api/admin/knowledge/${id}`, {
                        method: 'DELETE'
                    });
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    loadKnowledge();
                } catch (error) {
                    alert('Ошибка удаления: ' + error.message);
                }
            }
            
            // Инициализация
            loadContacts();
        </script>
    </body>
    </html>
    """
    return html_content
