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
                <button class="tab" onclick="showTab('widget')">Настройки виджета</button>
            </div>
            <div class="content">
                <div id="contacts-tab">
                    <div class="loading">Загрузка контактов...</div>
                </div>
                <div id="knowledge-tab" style="display: none;">
                    <div class="loading">Загрузка базы знаний...</div>
                </div>
                <div id="widget-tab" style="display: none;">
                    <div class="loading">Загрузка настроек виджета...</div>
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
            
            // Базовые темы для фонов и границ
            const baseThemes = {
                dark: {
                    background_color: '#151b2e',
                    messages_area_color: '#0a0e27',
                    input_background_color: '#0a0e27',
                    border_color: '#1e2742',
                    header_text_color: '#ffffff',
                    bot_message_color: '#1e2742',
                    text_color: '#e0e6ed'
                },
                light: {
                    background_color: '#ffffff',
                    messages_area_color: '#f9fafb',
                    input_background_color: '#ffffff',
                    border_color: '#e5e7eb',
                    header_text_color: '#ffffff',
                    bot_message_color: '#f3f4f6',
                    text_color: '#1f2937'
                }
            };
            
            function toggleTheme() {
                const themeToggle = document.getElementById('themeToggle');
                if (!themeToggle) return;
                
                const isLight = themeToggle.checked;
                const theme = isLight ? baseThemes.light : baseThemes.dark;
                
                // Применяем тему к соответствующим полям
                const bgColor = document.getElementById('backgroundColor');
                const msgAreaColor = document.getElementById('messagesAreaColor');
                const inputBgColor = document.getElementById('inputBackgroundColor');
                const borderColor = document.getElementById('borderColor');
                const headerTextColor = document.getElementById('headerTextColor');
                const botMsgColor = document.getElementById('botMessageColor');
                const textColor = document.getElementById('textColor');
                
                if (bgColor) {
                    bgColor.value = theme.background_color;
                    bgColor.dispatchEvent(new Event('change'));
                }
                if (msgAreaColor) {
                    msgAreaColor.value = theme.messages_area_color;
                    msgAreaColor.dispatchEvent(new Event('change'));
                }
                if (inputBgColor) {
                    inputBgColor.value = theme.input_background_color;
                    inputBgColor.dispatchEvent(new Event('change'));
                }
                if (borderColor) {
                    borderColor.value = theme.border_color;
                    borderColor.dispatchEvent(new Event('change'));
                }
                if (headerTextColor) {
                    headerTextColor.value = theme.header_text_color;
                    headerTextColor.dispatchEvent(new Event('change'));
                }
                if (botMsgColor) {
                    botMsgColor.value = theme.bot_message_color;
                    botMsgColor.dispatchEvent(new Event('change'));
                }
                if (textColor) {
                    textColor.value = theme.text_color;
                    textColor.dispatchEvent(new Event('change'));
                }
                
                // Обновляем визуальный вид тумблера
                const slider = document.getElementById('themeToggleSlider');
                const circle = document.getElementById('themeToggleCircle');
                if (slider && circle) {
                    slider.style.backgroundColor = isLight ? '#667eea' : '#1e2742';
                    slider.style.borderColor = isLight ? '#764ba2' : '#3a4562';
                    circle.style.left = isLight ? '26px' : '4px';
                }
                
                // Обновляем предпросмотр
                if (typeof updatePreview === 'function') {
                    updatePreview();
                }
            }
            
            async function loadWidgetSettings() {
                try {
                    const response = await fetch(`${API_URL}/api/admin/widget/settings`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    const settings = await response.json();
                    
                    // Определяем текущую тему на основе фона
                    const isLightTheme = (settings.background_color || '#151b2e') === '#ffffff' || (settings.background_color || '#151b2e').toLowerCase() === '#ffffff';
                    
                    const html = `
                        <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 24px;" id="widget-settings-grid">
                            <div style="overflow-y: auto; max-height: calc(100vh - 200px);">
                                <h2 style="color: #e0e6ed; margin-bottom: 24px; font-size: 20px;">Настройки виджета</h2>
                                
                                <div style="margin-bottom: 24px; padding: 16px; background: #0a0e27; border-radius: 12px; border: 1px solid #1e2742;">
                                    <h3 style="color: #e0e6ed; margin-bottom: 16px; font-size: 16px;">Базовая тема</h3>
                                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding: 12px; background: #151b2e; border-radius: 8px;">
                                        <span style="color: #8b95a7; font-size: 14px; flex: 1;">Темная тема</span>
                                        <label style="position: relative; display: inline-block; width: 52px; height: 28px;">
                                            <input type="checkbox" id="themeToggle" ${isLightTheme ? 'checked' : ''} style="opacity: 0; width: 0; height: 0;" onchange="toggleTheme()">
                                            <span id="themeToggleSlider" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: ${isLightTheme ? '#667eea' : '#1e2742'}; transition: 0.3s; border-radius: 28px; border: 2px solid ${isLightTheme ? '#764ba2' : '#3a4562'};">
                                                <span id="themeToggleCircle" style="position: absolute; content: ''; height: 20px; width: 20px; left: ${isLightTheme ? '26px' : '4px'}; bottom: 2px; background-color: white; transition: 0.3s; border-radius: 50%;"></span>
                                            </span>
                                        </label>
                                        <span style="color: #8b95a7; font-size: 14px; flex: 1; text-align: right;">Светлая тема</span>
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 24px; padding: 16px; background: #0a0e27; border-radius: 12px; border: 1px solid #1e2742;">
                                    <h3 style="color: #e0e6ed; margin-bottom: 16px; font-size: 16px;">Готовые пресеты</h3>
                                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px;">
                                        <button onclick="applyPreset('dark')" class="preset-btn" style="padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; cursor: pointer; font-size: 14px; transition: all 0.3s; font-weight: 500; display: flex; align-items: center; gap: 10px;" onmouseover="this.style.borderColor='#667eea'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='#1e2742'; this.style.transform='translateY(0)'">
                                            <div style="width: 20px; height: 20px; border-radius: 4px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); flex-shrink: 0;"></div>
                                            <span>Темная</span>
                                        </button>
                                        <button onclick="applyPreset('light')" class="preset-btn" style="padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; cursor: pointer; font-size: 14px; transition: all 0.3s; font-weight: 500; display: flex; align-items: center; gap: 10px;" onmouseover="this.style.borderColor='#667eea'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='#1e2742'; this.style.transform='translateY(0)'">
                                            <div style="width: 20px; height: 20px; border-radius: 4px; background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); flex-shrink: 0;"></div>
                                            <span>Светлая</span>
                                        </button>
                                        <button onclick="applyPreset('blue')" class="preset-btn" style="padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; cursor: pointer; font-size: 14px; transition: all 0.3s; font-weight: 500; display: flex; align-items: center; gap: 10px;" onmouseover="this.style.borderColor='#3b82f6'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='#1e2742'; this.style.transform='translateY(0)'">
                                            <div style="width: 20px; height: 20px; border-radius: 4px; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); flex-shrink: 0;"></div>
                                            <span>Синяя</span>
                                        </button>
                                        <button onclick="applyPreset('green')" class="preset-btn" style="padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; cursor: pointer; font-size: 14px; transition: all 0.3s; font-weight: 500; display: flex; align-items: center; gap: 10px;" onmouseover="this.style.borderColor='#10b981'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='#1e2742'; this.style.transform='translateY(0)'">
                                            <div style="width: 20px; height: 20px; border-radius: 4px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); flex-shrink: 0;"></div>
                                            <span>Зеленая</span>
                                        </button>
                                        <button onclick="applyPreset('red')" class="preset-btn" style="padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; cursor: pointer; font-size: 14px; transition: all 0.3s; font-weight: 500; display: flex; align-items: center; gap: 10px;" onmouseover="this.style.borderColor='#ef4444'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='#1e2742'; this.style.transform='translateY(0)'">
                                            <div style="width: 20px; height: 20px; border-radius: 4px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); flex-shrink: 0;"></div>
                                            <span>Красная</span>
                                        </button>
                                        <button onclick="applyPreset('orange')" class="preset-btn" style="padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; cursor: pointer; font-size: 14px; transition: all 0.3s; font-weight: 500; display: flex; align-items: center; gap: 10px;" onmouseover="this.style.borderColor='#f97316'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='#1e2742'; this.style.transform='translateY(0)'">
                                            <div style="width: 20px; height: 20px; border-radius: 4px; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); flex-shrink: 0;"></div>
                                            <span>Оранжевая</span>
                                        </button>
                                        <button onclick="applyPreset('purple')" class="preset-btn" style="padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; cursor: pointer; font-size: 14px; transition: all 0.3s; font-weight: 500; display: flex; align-items: center; gap: 10px;" onmouseover="this.style.borderColor='#667eea'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='#1e2742'; this.style.transform='translateY(0)'">
                                            <div style="width: 20px; height: 20px; border-radius: 4px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); flex-shrink: 0;"></div>
                                            <span>Фиолетовая</span>
                                        </button>
                                        <button onclick="applyPreset('teal')" class="preset-btn" style="padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; cursor: pointer; font-size: 14px; transition: all 0.3s; font-weight: 500; display: flex; align-items: center; gap: 10px;" onmouseover="this.style.borderColor='#14b8a6'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='#1e2742'; this.style.transform='translateY(0)'">
                                            <div style="width: 20px; height: 20px; border-radius: 4px; background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); flex-shrink: 0;"></div>
                                            <span>Бирюзовая</span>
                                        </button>
                                    </div>
                                    <button onclick="applyPreset('custom')" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 8px; color: white; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">Сбросить к текущим настройкам</button>
                                </div>
                                
                                <div style="margin-bottom: 24px; padding: 16px; background: #0a0e27; border-radius: 12px; border: 1px solid #1e2742;">
                                    <h3 style="color: #e0e6ed; margin-bottom: 16px; font-size: 16px;">Цвета кнопки и сообщения</h3>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Основной цвет (кнопка)</label>
                                        <input type="color" id="buttonColor" value="${settings.button_color || '#667eea'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Вторичный цвет (градиент)</label>
                                        <input type="color" id="secondaryColor" value="${settings.secondary_color || '#764ba2'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет расширенного сообщения</label>
                                        <input type="color" id="messageColor" value="${settings.message_color || '#667eea'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 24px; padding: 16px; background: #0a0e27; border-radius: 12px; border: 1px solid #1e2742;">
                                    <h3 style="color: #e0e6ed; margin-bottom: 16px; font-size: 16px;">Цвета окна чата</h3>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет фона виджета</label>
                                        <input type="color" id="backgroundColor" value="${settings.background_color || '#151b2e'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет области сообщений</label>
                                        <input type="color" id="messagesAreaColor" value="${settings.messages_area_color || '#0a0e27'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет фона поля ввода</label>
                                        <input type="color" id="inputBackgroundColor" value="${settings.input_background_color || '#0a0e27'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет границ</label>
                                        <input type="color" id="borderColor" value="${settings.border_color || '#1e2742'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет заголовка</label>
                                        <input type="color" id="headerColor" value="${settings.header_color || '#667eea'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет текста заголовка</label>
                                        <input type="color" id="headerTextColor" value="${settings.header_text_color || '#ffffff'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет текста</label>
                                        <input type="color" id="textColor" value="${settings.text_color || '#e0e6ed'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 24px; padding: 16px; background: #0a0e27; border-radius: 12px; border: 1px solid #1e2742;">
                                    <h3 style="color: #e0e6ed; margin-bottom: 16px; font-size: 16px;">Цвета сообщений</h3>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет сообщений пользователя</label>
                                        <input type="color" id="userMessageColor" value="${settings.user_message_color || '#667eea'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Цвет сообщений бота</label>
                                        <input type="color" id="botMessageColor" value="${settings.bot_message_color || '#1e2742'}" style="width: 100%; height: 48px; border: 2px solid #1e2742; border-radius: 8px; cursor: pointer; opacity: 0.6;" disabled onchange="updatePreview()">
                                        <p style="color: #8b95a7; font-size: 12px; margin: 4px 0 0 0;">Управляется базовой темой</p>
                                    </div>
                                </div>
                                
                                <div style="margin-bottom: 24px; padding: 16px; background: #0a0e27; border-radius: 12px; border: 1px solid #1e2742;">
                                    <h3 style="color: #e0e6ed; margin-bottom: 16px; font-size: 16px;">Тексты</h3>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Текст расширенного сообщения</label>
                                        <input type="text" id="expandedMessageText" value="${(settings.expanded_message_text || 'Нужна помощь?').replace(/"/g, '&quot;')}" style="width: 100%; padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; font-size: 14px;" oninput="updatePreview()" onchange="updatePreview()">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; color: #8b95a7; margin-bottom: 8px; font-size: 14px;">Приветственное сообщение</label>
                                        <textarea id="welcomeMessage" rows="3" style="width: 100%; padding: 12px; background: #151b2e; border: 2px solid #1e2742; border-radius: 8px; color: #e0e6ed; font-size: 14px; resize: vertical;" oninput="updatePreview()" onchange="updatePreview()">${(settings.welcome_message || 'Привет! Чем могу помочь?').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</textarea>
                                    </div>
                                </div>
                                
                                <button class="upload-btn" onclick="saveWidgetSettings()" style="width: 100%; margin-top: 24px;">Сохранить настройки</button>
                            </div>
                            
                            <div>
                                <h2 style="color: #e0e6ed; margin-bottom: 20px; font-size: 20px;">Предпросмотр</h2>
                                <div id="widget-preview-container" style="position: relative; height: 600px; background: #0a0e27; border-radius: 12px; border: 1px solid #1e2742; padding: 20px; overflow: hidden;">
                                    <div id="widget-preview" style="position: relative; width: 100%; height: 100%;">
                                        <!-- Предпросмотр расширенного виджета -->
                                        <div id="preview-expanded-widget" style="position: absolute; bottom: 20px; right: 20px; display: flex; align-items: center; gap: 0; z-index: 10;">
                                            <div id="preview-message" style="background: linear-gradient(135deg, ${settings.message_color || '#667eea'} 0%, ${settings.secondary_color || '#764ba2'} 100%); color: white; padding: 0 32px; border-radius: 28px 0 0 28px; font-size: 18px; font-weight: 500; white-space: nowrap; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); height: 72px; display: flex; align-items: center; justify-content: center; line-height: 1;">
                                                ${settings.expanded_message_text || 'Нужна помощь?'}
                                            </div>
                                            <div id="preview-button" style="width: 72px; height: 72px; background: linear-gradient(135deg, ${settings.button_color || '#667eea'} 0%, ${settings.secondary_color || '#764ba2'} 100%); border-radius: 0 50% 50% 0; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); cursor: pointer; flex-shrink: 0;">
                                                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="color: white;">
                                                    <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor"/>
                                                </svg>
                                            </div>
                                        </div>
                                        
                                        <!-- Предпросмотр окна чата -->
                                        <div id="preview-chat-window" style="position: absolute; bottom: 100px; right: 20px; width: 380px; height: 480px; background: ${settings.background_color || '#151b2e'}; border-radius: 20px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5); display: flex; flex-direction: column; overflow: hidden; border: 1px solid ${settings.border_color || '#1e2742'};">
                                            <div id="preview-header" style="background: linear-gradient(135deg, ${settings.header_color || '#667eea'} 0%, ${settings.secondary_color || '#764ba2'} 100%); color: ${settings.header_text_color || '#ffffff'}; padding: 20px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;">
                                                <h3 style="font-size: 18px; font-weight: 700; margin: 0;">AI Ассистент</h3>
                                                <button style="background: rgba(255, 255, 255, 0.1); border: none; color: ${settings.header_text_color || '#ffffff'}; font-size: 24px; cursor: pointer; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">×</button>
                                            </div>
                                            <div id="preview-messages" style="flex: 1; overflow-y: auto; padding: 20px; background: ${settings.messages_area_color || '#0a0e27'}; display: flex; flex-direction: column; gap: 12px;">
                                                <div style="display: flex; justify-content: flex-start;">
                                                    <div style="max-width: 75%; padding: 12px 16px; background: ${settings.bot_message_color || '#1e2742'}; color: ${settings.text_color || '#e0e6ed'}; border-radius: 20px; border-bottom-left-radius: 6px; border: 1px solid ${settings.border_color || '#1e2742'}; font-size: 14px; line-height: 1.5;">
                                                        ${settings.welcome_message || 'Привет! Чем могу помочь?'}
                                                    </div>
                                                </div>
                                                <div style="display: flex; justify-content: flex-end;">
                                                    <div style="max-width: 75%; padding: 12px 16px; background: linear-gradient(135deg, ${settings.user_message_color || '#667eea'} 0%, ${settings.secondary_color || '#764ba2'} 100%); color: white; border-radius: 20px; border-bottom-right-radius: 6px; font-size: 14px; line-height: 1.5;">
                                                        Привет! Расскажи о себе
                                                    </div>
                                                </div>
                                                <div style="display: flex; justify-content: flex-start;">
                                                    <div style="max-width: 75%; padding: 12px 16px; background: ${settings.bot_message_color || '#1e2742'}; color: ${settings.text_color || '#e0e6ed'}; border-radius: 20px; border-bottom-left-radius: 6px; border: 1px solid ${settings.border_color || '#1e2742'}; font-size: 14px; line-height: 1.5;">
                                                        Я AI-ассистент, готов помочь вам с любыми вопросами!
                                                    </div>
                                                </div>
                                            </div>
                                            <div style="padding: 16px; background: ${settings.background_color || '#151b2e'}; border-top: 1px solid ${settings.border_color || '#1e2742'}; display: flex; gap: 12px; align-items: center; flex-shrink: 0;">
                                                <input type="text" placeholder="Введите сообщение..." style="flex: 1; padding: 12px 16px; border: 2px solid ${settings.border_color || '#1e2742'}; border-radius: 24px; font-size: 14px; background: ${settings.input_background_color || '#0a0e27'}; color: ${settings.text_color || '#e0e6ed'};" disabled>
                                                <button style="width: 44px; height: 44px; background: linear-gradient(135deg, ${settings.button_color || '#667eea'} 0%, ${settings.secondary_color || '#764ba2'} 100%); border: none; border-radius: 50%; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                                                        <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor"/>
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <style>
                            @media (max-width: 1200px) {
                                #widget-settings-grid {
                                    grid-template-columns: 1fr !important;
                                }
                                #widget-preview-container {
                                    height: 500px !important;
                                }
                            }
                        </style>
                    `;
                    document.getElementById('widget-tab').innerHTML = html;
                } catch (error) {
                    document.getElementById('widget-tab').innerHTML = '<p style="color: #ef4444; padding: 20px; text-align: center;">Ошибка загрузки: ' + error + '</p>';
                }
            }
            
            const presets = {
                dark: {
                    button_color: '#667eea',
                    secondary_color: '#764ba2',
                    message_color: '#667eea',
                    background_color: '#151b2e',
                    messages_area_color: '#0a0e27',
                    input_background_color: '#0a0e27',
                    border_color: '#1e2742',
                    header_color: '#667eea',
                    header_text_color: '#ffffff',
                    user_message_color: '#667eea',
                    bot_message_color: '#1e2742',
                    text_color: '#e0e6ed'
                },
                light: {
                    button_color: '#4f46e5',
                    secondary_color: '#7c3aed',
                    message_color: '#4f46e5',
                    background_color: '#ffffff',
                    messages_area_color: '#f9fafb',
                    input_background_color: '#ffffff',
                    border_color: '#e5e7eb',
                    header_color: '#4f46e5',
                    header_text_color: '#ffffff',
                    user_message_color: '#4f46e5',
                    bot_message_color: '#f3f4f6',
                    text_color: '#1f2937'
                },
                blue: {
                    button_color: '#3b82f6',
                    secondary_color: '#1d4ed8',
                    message_color: '#3b82f6',
                    background_color: '#1e3a8a',
                    messages_area_color: '#1e40af',
                    input_background_color: '#1e40af',
                    border_color: '#3b82f6',
                    header_color: '#3b82f6',
                    header_text_color: '#ffffff',
                    user_message_color: '#3b82f6',
                    bot_message_color: '#1e40af',
                    text_color: '#e0e7ff'
                },
                green: {
                    button_color: '#10b981',
                    secondary_color: '#059669',
                    message_color: '#10b981',
                    background_color: '#064e3b',
                    messages_area_color: '#065f46',
                    input_background_color: '#065f46',
                    border_color: '#10b981',
                    header_color: '#10b981',
                    header_text_color: '#ffffff',
                    user_message_color: '#10b981',
                    bot_message_color: '#065f46',
                    text_color: '#d1fae5'
                },
                red: {
                    button_color: '#ef4444',
                    secondary_color: '#dc2626',
                    message_color: '#ef4444',
                    background_color: '#7f1d1d',
                    messages_area_color: '#991b1b',
                    input_background_color: '#991b1b',
                    border_color: '#ef4444',
                    header_color: '#ef4444',
                    header_text_color: '#ffffff',
                    user_message_color: '#ef4444',
                    bot_message_color: '#991b1b',
                    text_color: '#fee2e2'
                },
                orange: {
                    button_color: '#f97316',
                    secondary_color: '#ea580c',
                    message_color: '#f97316',
                    background_color: '#7c2d12',
                    messages_area_color: '#9a3412',
                    input_background_color: '#9a3412',
                    border_color: '#f97316',
                    header_color: '#f97316',
                    header_text_color: '#ffffff',
                    user_message_color: '#f97316',
                    bot_message_color: '#9a3412',
                    text_color: '#ffedd5'
                },
                purple: {
                    button_color: '#667eea',
                    secondary_color: '#764ba2',
                    message_color: '#667eea',
                    background_color: '#151b2e',
                    messages_area_color: '#0a0e27',
                    input_background_color: '#0a0e27',
                    border_color: '#1e2742',
                    header_color: '#667eea',
                    header_text_color: '#ffffff',
                    user_message_color: '#667eea',
                    bot_message_color: '#1e2742',
                    text_color: '#e0e6ed'
                },
                teal: {
                    button_color: '#14b8a6',
                    secondary_color: '#0d9488',
                    message_color: '#14b8a6',
                    background_color: '#134e4a',
                    messages_area_color: '#155e75',
                    input_background_color: '#155e75',
                    border_color: '#14b8a6',
                    header_color: '#14b8a6',
                    header_text_color: '#ffffff',
                    user_message_color: '#14b8a6',
                    bot_message_color: '#155e75',
                    text_color: '#ccfbf1'
                }
            };
            
            function applyPreset(presetName) {
                if (presetName === 'custom') {
                    // Не применяем пресет, просто обновляем предпросмотр
                    updatePreview();
                    return;
                }
                
                const preset = presets[presetName];
                if (!preset) return;
                
                // Применяем значения пресета только к цветам кнопок и сообщений
                document.getElementById('buttonColor').value = preset.button_color;
                document.getElementById('secondaryColor').value = preset.secondary_color;
                document.getElementById('messageColor').value = preset.message_color;
                document.getElementById('headerColor').value = preset.header_color;
                document.getElementById('userMessageColor').value = preset.user_message_color;
                
                // Базовые цвета (фон, границы и т.д.) не меняем - они управляются тумблером темы
                // Но если это пресет 'custom', не меняем ничего
                
                // Обновляем предпросмотр
                updatePreview();
            }
            
            function updatePreview() {
                const buttonColor = document.getElementById('buttonColor')?.value || '#667eea';
                const secondaryColor = document.getElementById('secondaryColor')?.value || '#764ba2';
                const messageColor = document.getElementById('messageColor')?.value || '#667eea';
                const backgroundColor = document.getElementById('backgroundColor')?.value || '#151b2e';
                const messagesAreaColor = document.getElementById('messagesAreaColor')?.value || '#0a0e27';
                const inputBackgroundColor = document.getElementById('inputBackgroundColor')?.value || '#0a0e27';
                const borderColor = document.getElementById('borderColor')?.value || '#1e2742';
                const headerColor = document.getElementById('headerColor')?.value || '#667eea';
                const headerTextColor = document.getElementById('headerTextColor')?.value || '#ffffff';
                const userMessageColor = document.getElementById('userMessageColor')?.value || '#667eea';
                const botMessageColor = document.getElementById('botMessageColor')?.value || '#1e2742';
                const textColor = document.getElementById('textColor')?.value || '#e0e6ed';
                const expandedMessageText = document.getElementById('expandedMessageText')?.value || 'Нужна помощь?';
                const welcomeMessage = document.getElementById('welcomeMessage')?.value || 'Привет! Чем могу помочь?';
                
                const previewMessage = document.getElementById('preview-message');
                const previewButton = document.getElementById('preview-button');
                const previewHeader = document.getElementById('preview-header');
                const previewChatWindow = document.getElementById('preview-chat-window');
                const previewMessages = document.getElementById('preview-messages');
                const previewInput = document.querySelector('#preview-chat-window input');
                
                if (previewMessage) {
                    previewMessage.style.background = `linear-gradient(135deg, ${messageColor} 0%, ${secondaryColor} 100%)`;
                    previewMessage.textContent = expandedMessageText;
                }
                
                if (previewButton) {
                    previewButton.style.background = `linear-gradient(135deg, ${buttonColor} 0%, ${secondaryColor} 100%)`;
                    previewButton.style.borderRadius = '0 50% 50% 0';
                }
                
                if (previewHeader) {
                    previewHeader.style.background = `linear-gradient(135deg, ${headerColor} 0%, ${secondaryColor} 100%)`;
                    previewHeader.style.color = headerTextColor;
                    const closeBtn = previewHeader.querySelector('button');
                    if (closeBtn) closeBtn.style.color = headerTextColor;
                }
                
                if (previewChatWindow) {
                    previewChatWindow.style.background = backgroundColor;
                    previewChatWindow.style.borderColor = borderColor;
                }
                
                if (previewMessages) {
                    previewMessages.style.background = messagesAreaColor;
                    const botMessages = previewMessages.querySelectorAll('div:first-child > div, div:nth-child(3) > div');
                    botMessages.forEach(msg => {
                        msg.style.background = botMessageColor;
                        msg.style.color = textColor;
                        msg.style.borderColor = borderColor;
                    });
                    
                    const userMessage = previewMessages.querySelector('div:nth-child(2) > div');
                    if (userMessage) {
                        userMessage.style.background = `linear-gradient(135deg, ${userMessageColor} 0%, ${secondaryColor} 100%)`;
                    }
                    
                    const firstMessage = previewMessages.querySelector('div:first-child > div');
                    if (firstMessage) {
                        firstMessage.textContent = welcomeMessage;
                    }
                }
                
                if (previewInput) {
                    previewInput.style.background = inputBackgroundColor;
                    previewInput.style.borderColor = borderColor;
                    previewInput.style.color = textColor;
                }
                
                // Обновляем контейнер поля ввода
                const previewInputContainer = document.querySelector('#preview-chat-window > div:last-child');
                if (previewInputContainer) {
                    previewInputContainer.style.background = backgroundColor;
                    previewInputContainer.style.borderTopColor = borderColor;
                }
                
                // Обновляем кнопку отправки (ищем все кнопки в контейнере ввода)
                const previewSendButton = previewInputContainer ? previewInputContainer.querySelector('button') : null;
                if (previewSendButton) {
                    previewSendButton.style.background = `linear-gradient(135deg, ${buttonColor} 0%, ${secondaryColor} 100%)`;
                }
                
                // Также обновляем заголовок h3 в предпросмотре
                const previewHeaderTitle = previewHeader ? previewHeader.querySelector('h3') : null;
                if (previewHeaderTitle) {
                    previewHeaderTitle.style.color = headerTextColor;
                }
            }
            
            async function saveWidgetSettings() {
                const buttonColor = document.getElementById('buttonColor')?.value || '#667eea';
                const secondaryColor = document.getElementById('secondaryColor')?.value || '#764ba2';
                const messageColor = document.getElementById('messageColor')?.value || '#667eea';
                const backgroundColor = document.getElementById('backgroundColor')?.value || '#151b2e';
                const messagesAreaColor = document.getElementById('messagesAreaColor')?.value || '#0a0e27';
                const inputBackgroundColor = document.getElementById('inputBackgroundColor')?.value || '#0a0e27';
                const borderColor = document.getElementById('borderColor')?.value || '#1e2742';
                const headerColor = document.getElementById('headerColor')?.value || '#667eea';
                const headerTextColor = document.getElementById('headerTextColor')?.value || '#ffffff';
                const userMessageColor = document.getElementById('userMessageColor')?.value || '#667eea';
                const botMessageColor = document.getElementById('botMessageColor')?.value || '#1e2742';
                const textColor = document.getElementById('textColor')?.value || '#e0e6ed';
                const expandedMessageText = document.getElementById('expandedMessageText')?.value || 'Нужна помощь?';
                const welcomeMessage = document.getElementById('welcomeMessage')?.value || 'Привет! Чем могу помочь?';
                
                try {
                    const response = await fetch(`${API_URL}/api/admin/widget/settings`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            primary_color: buttonColor,
                            secondary_color: secondaryColor,
                            button_color: buttonColor,
                            message_color: messageColor,
                            background_color: backgroundColor,
                            messages_area_color: messagesAreaColor,
                            input_background_color: inputBackgroundColor,
                            border_color: borderColor,
                            header_color: headerColor,
                            header_text_color: headerTextColor,
                            user_message_color: userMessageColor,
                            bot_message_color: botMessageColor,
                            text_color: textColor,
                            welcome_message: welcomeMessage,
                            expanded_message_text: expandedMessageText
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    alert('Настройки сохранены успешно!');
                    loadWidgetSettings();
                } catch (error) {
                    alert('Ошибка сохранения: ' + error);
                }
            }
            
            function showTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.getElementById('contacts-tab').style.display = 'none';
                document.getElementById('knowledge-tab').style.display = 'none';
                document.getElementById('widget-tab').style.display = 'none';
                
                if (tab === 'contacts') {
                    document.querySelectorAll('.tab')[0].classList.add('active');
                    document.getElementById('contacts-tab').style.display = 'block';
                    loadContacts();
                } else if (tab === 'knowledge') {
                    document.querySelectorAll('.tab')[1].classList.add('active');
                    document.getElementById('knowledge-tab').style.display = 'block';
                    loadKnowledge();
                } else if (tab === 'widget') {
                    document.querySelectorAll('.tab')[2].classList.add('active');
                    document.getElementById('widget-tab').style.display = 'block';
                    loadWidgetSettings();
                }
            }
            
            // Загружаем контакты при загрузке страницы
            loadContacts();
        </script>
    </body>
    </html>
    """
    return html_content
