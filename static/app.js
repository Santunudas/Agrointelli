document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const btnBrowse = document.getElementById('btn-browse');
    const previewContainer = document.getElementById('preview-container');
    const selectedFilesContainer = document.getElementById('selected-files');
    const btnRemoveImage = document.getElementById('btn-remove-image');
    const btnAnalyze = document.getElementById('btn-analyze');
    const btnSpinner = document.getElementById('btn-spinner');
    const fieldModeToggle = document.getElementById('field-mode-toggle');
    const cropNameInput = document.getElementById('crop-name');
    const fieldNameInput = document.getElementById('field-name');
    const progressContainer = document.getElementById('batch-progress');
    const progressText = document.getElementById('batch-progress-text');
    const progressCount = document.getElementById('batch-progress-count');
    const progressBar = document.getElementById('batch-progress-bar');
    const historyCard = document.getElementById('history-card');
    const historyMessage = document.getElementById('history-message');
    const historyList = document.getElementById('history-list');
    const historyRefresh = document.getElementById('history-refresh');
    const batchResultsCard = document.getElementById('batch-results-card');
    const batchResultsSummary = document.getElementById('batch-results-summary');
    const batchResultsList = document.getElementById('batch-results-list');
    
    const emptyState = document.getElementById('empty-state');
    const skeletonState = document.getElementById('skeleton-state');
    const dashboardResults = document.getElementById('dashboard-results');
    
    const predictedDisease = document.getElementById('predicted-disease');
    const scientificName = document.getElementById('scientific-name');
    const confidenceBadge = document.getElementById('confidence-badge');
    const confidencePercentage = document.getElementById('confidence-percentage');
    const alternatesList = document.getElementById('alternates-list');
    
    const severityRadial = document.getElementById('severity-radial');
    const lesionPercentage = document.getElementById('lesion-percentage');
    const severityLevel = document.getElementById('severity-level');
    
    const qualityStatusBadge = document.getElementById('quality-status-badge');
    const barBrightness = document.getElementById('bar-brightness');
    const valBrightness = document.getElementById('val-brightness');
    const barContrast = document.getElementById('bar-contrast');
    const valContrast = document.getElementById('val-contrast');
    const barSharpness = document.getElementById('bar-sharpness');
    const valSharpness = document.getElementById('val-sharpness');
    const qualityWarningsBox = document.getElementById('quality-warnings-box');
    const adviceText = document.getElementById('advice-text');

    const MAX_BATCH_IMAGES = 20;
    const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
    let uploadedFiles = [];
    let signedIn = false;

    const accountLink = document.getElementById('account-link');
    fetch('/auth/me')
        .then((response) => {
            if (!response.ok) return null;
            return response.json();
        })
        .then((data) => {
            if (data && data.user) {
                signedIn = true;
                accountLink.textContent = `Hi, ${data.user.name}`;
                historyCard.classList.remove('hidden');
                loadBatchHistory();
            }
        })
        .catch(() => {
            // Accounts are optional; keep the main app available if auth is offline.
        });

    function csrfToken() {
        const cookie = document.cookie.split('; ').find((part) => part.startsWith('agro_csrf='));
        return cookie ? decodeURIComponent(cookie.slice('agro_csrf='.length)) : '';
    }

    async function readJsonResponse(response) {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const detail = Array.isArray(data.detail)
                ? data.detail.map((item) => item.msg).join('. ')
                : data.detail;
            throw new Error(detail || 'The request could not be completed.');
        }
        return data;
    }

    function updateAnalyzeButton() {
        const disabled = uploadedFiles.length === 0;
        btnAnalyze.classList.toggle('disabled', disabled);
        btnAnalyze.toggleAttribute('disabled', disabled);
    }

    // Toggle Labels Active State
    fieldModeToggle.addEventListener('change', () => {
        const labels = document.querySelectorAll('.mode-label');
        labels.forEach(l => l.classList.toggle('active'));
    });

    // Browse Button
    btnBrowse.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    // Drag and Drop
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    }

    function unhighlight(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    }

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        handleFiles(e.dataTransfer.files);
    });

    function handleFiles(fileList) {
        const files = Array.from(fileList);
        const invalidFiles = files.filter((file) => !file.type.startsWith('image/'));
        if (invalidFiles.length) {
            alert('Please select only valid image files (PNG, JPG, BMP, WEBP).');
            return;
        }
        if (!files.length) return;
        if (files.length > MAX_BATCH_IMAGES) {
            alert(`Choose no more than ${MAX_BATCH_IMAGES} photos for one visit.`);
            return;
        }
        const oversized = files.find((file) => file.size > MAX_IMAGE_BYTES);
        if (oversized) {
            alert(`${oversized.name} is larger than 10 MB.`);
            return;
        }
        uploadedFiles = files;
        renderSelectedFiles();
        updateAnalyzeButton();
        if (signedIn) loadBatchHistory();
    }

    function renderSelectedFiles() {
        selectedFilesContainer.innerHTML = '';
        uploadedFiles.forEach((file) => {
            const item = document.createElement('div');
            item.className = 'selected-file';
            item.innerHTML = '<i class="fa-regular fa-image"></i>';
            const name = document.createElement('span');
            name.textContent = file.name;
            const size = document.createElement('small');
            size.textContent = `${(file.size / (1024 * 1024)).toFixed(1)} MB`;
            item.append(name, size);
            selectedFilesContainer.appendChild(item);
        });
        selectedFilesContainer.classList.toggle('hidden', uploadedFiles.length === 0);
        previewContainer.classList.toggle('hidden', uploadedFiles.length === 0);
    }

    fileInput.addEventListener('change', () => handleFiles(fileInput.files));

    btnRemoveImage.addEventListener('click', (e) => {
        e.stopPropagation();
        uploadedFiles = [];
        fileInput.value = '';
        renderSelectedFiles();
        updateAnalyzeButton();
    });

    btnAnalyze.addEventListener('click', async () => {
        if (!uploadedFiles.length) return;
        const filesToAnalyze = uploadedFiles.slice();
        if (signedIn && (!cropNameInput.value.trim() || !fieldNameInput.value.trim())) {
            alert('Enter the crop and field name to save this visit to your timeline.');
            return;
        }

        btnAnalyze.classList.add('disabled');
        btnAnalyze.setAttribute('disabled', 'true');
        btnSpinner.classList.remove('hidden');
        progressContainer.classList.remove('hidden');
        progressBar.value = 0;
        emptyState.classList.add('hidden');
        dashboardResults.classList.remove('visible');
        dashboardResults.classList.add('hidden');
        batchResultsCard.classList.remove('hidden');
        batchResultsList.innerHTML = '';
        batchResultsSummary.textContent = signedIn ? 'Saving each result to your field timeline.' : 'Sign in to save these results to a field timeline.';
        const fieldMode = fieldModeToggle.checked;
        let batch = null;
        let completed = 0;
        let failed = 0;
        try {
            if (signedIn) {
                const response = await fetch('/batches', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrfToken()
                    },
                    body: JSON.stringify({
                        crop_name: cropNameInput.value.trim(),
                        field_name: fieldNameInput.value.trim()
                    })
                });
                batch = await readJsonResponse(response);
            }

            for (let index = 0; index < filesToAnalyze.length; index += 1) {
                const file = filesToAnalyze[index];
                progressText.textContent = `Analyzing ${file.name}`;
                progressCount.textContent = `${index + 1} of ${filesToAnalyze.length}`;
                const formData = new FormData();
                formData.append('file', file);
                const url = batch
                    ? `/batches/${encodeURIComponent(batch.id)}/images?field_mode=${fieldMode}`
                    : `/predict?field_mode=${fieldMode}`;
                const headers = batch ? { 'X-CSRF-Token': csrfToken() } : {};
                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers,
                        body: formData
                    });
                    const result = await readJsonResponse(response);
                    if (result.ok === false) {
                        throw new Error(result.error || 'Image analysis failed.');
                    }
                    result.filename = result.filename || file.name;
                    result.analyzed_at = result.analyzed_at || new Date().toISOString();
                    completed += 1;
                    addBatchResult(result, index + 1);
                    renderResults(result);
                } catch (error) {
                    failed += 1;
                    addBatchFailure(file.name, error.message);
                }
                progressBar.value = ((index + 1) / filesToAnalyze.length) * 100;
            }

            progressText.textContent = failed
                ? `Finished with ${failed} photo${failed === 1 ? '' : 's'} not analyzed.`
                : 'Visit analysis complete.';
            batchResultsSummary.textContent = `${completed} photo${completed === 1 ? '' : 's'} analyzed${batch ? ' and saved' : ''}${failed ? ` · ${failed} failed` : ''}.`;
            if (completed === 0) {
                dashboardResults.classList.add('hidden');
                emptyState.classList.remove('hidden');
            }
            if (batch) await loadBatchHistory();

        } catch (error) {
            console.error('Batch analysis error:', error);
            progressText.textContent = `Could not start this visit: ${error.message}`;
            batchResultsSummary.textContent = 'No photos were analyzed.';
            if (batchResultsList.children.length === 0) {
                batchResultsCard.classList.add('hidden');
                emptyState.classList.remove('hidden');
            }
        } finally {
            btnAnalyze.classList.remove('disabled');
            btnAnalyze.removeAttribute('disabled');
            btnSpinner.classList.add('hidden');
        }
    });

    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return Number.isNaN(date.getTime())
            ? 'Date unavailable'
            : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
    }

    function addBatchResult(result, number) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'batch-result-item';
        const title = document.createElement('strong');
        title.textContent = `${number}. ${result.filename}`;
        const diagnosis = document.createElement('span');
        diagnosis.textContent = cleanClassName(result.prediction);
        const details = document.createElement('small');
        details.textContent = `${(result.confidence * 100).toFixed(1)}% match · ${result.severity_proxy.severity} · ${formatTimestamp(result.analyzed_at)}`;
        button.append(title, diagnosis, details);
        button.addEventListener('click', () => renderResults(result));
        batchResultsList.appendChild(button);
    }

    function addBatchFailure(filename, message) {
        const item = document.createElement('div');
        item.className = 'batch-result-item batch-result-failure';
        const title = document.createElement('strong');
        title.textContent = filename;
        const details = document.createElement('small');
        details.textContent = message;
        item.append(title, details);
        batchResultsList.appendChild(item);
    }

    async function loadBatchHistory() {
        if (!signedIn) return;
        historyMessage.textContent = 'Loading saved visits...';
        const query = new URLSearchParams({ limit: '50' });
        if (cropNameInput.value.trim()) query.set('crop_name', cropNameInput.value.trim());
        if (fieldNameInput.value.trim()) query.set('field_name', fieldNameInput.value.trim());
        try {
            const response = await fetch(`/batches?${query.toString()}`, { credentials: 'same-origin' });
            const data = await readJsonResponse(response);
            renderBatchHistory(data.batches);
        } catch (error) {
            historyList.innerHTML = '';
            historyMessage.textContent = `Could not load saved visits: ${error.message}`;
        }
    }

    function renderBatchHistory(batches) {
        historyList.innerHTML = '';
        if (!batches.length) {
            historyMessage.textContent = 'No previous visits found for this crop and field.';
            return;
        }
        const visitNumbers = new Map();
        batches.slice().reverse().forEach((batch) => {
            const key = `${batch.crop_name.toLocaleLowerCase()}|${batch.field_name.toLocaleLowerCase()}`;
            visitNumbers.set(key, (visitNumbers.get(key) || 0) + 1);
            batch.visit_number = visitNumbers.get(key);
        });
        historyMessage.textContent = 'Select a visit to review its saved results.';
        batches.forEach((batch) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'timeline-visit';
            const label = document.createElement('strong');
            label.textContent = `Visit ${batch.visit_number} · ${formatTimestamp(batch.created_at)}`;
            const detail = document.createElement('span');
            const diagnoses = [...new Set(batch.results.map((result) => cleanClassName(result.prediction)))];
            detail.textContent = `${batch.crop_name} · ${batch.field_name} · ${batch.result_count} photo${batch.result_count === 1 ? '' : 's'}${diagnoses.length ? ` · ${diagnoses.join(', ')}` : ''}`;
            button.append(label, detail);
            button.addEventListener('click', () => showSavedBatch(batch));
            historyList.appendChild(button);
        });
    }

    function showSavedBatch(batch) {
        batchResultsCard.classList.remove('hidden');
        batchResultsList.innerHTML = '';
        batchResultsSummary.textContent = `${batch.crop_name} · ${batch.field_name} · ${formatTimestamp(batch.created_at)} · saved visit`;
        batch.results.forEach((result, index) => addBatchResult(result, index + 1));
        if (batch.results.length) {
            emptyState.classList.add('hidden');
            renderResults(batch.results[batch.results.length - 1]);
        } else {
            dashboardResults.classList.add('hidden');
            emptyState.classList.remove('hidden');
        }
    }

    historyRefresh.addEventListener('click', loadBatchHistory);
    cropNameInput.addEventListener('change', () => signedIn && loadBatchHistory());
    fieldNameInput.addEventListener('change', () => signedIn && loadBatchHistory());

    // Formatting Helpers
    function cleanClassName(className) {
        // e.g. Tomato___Tomato_Yellow_Leaf_Curl_Virus -> Tomato: Yellow Leaf Curl Virus
        // e.g. Apple___Apple_scab -> Apple: Apple Scab
        if (!className) return 'Unknown Plant';
        
        const parts = className.split('___');
        let plant = parts[0] || '';
        let disease = parts[1] || 'Healthy';
        
        // Clean plant name
        plant = plant.replace(/_/g, ' ');
        
        // Clean disease name
        disease = disease.replace(/_/g, ' ');
        // If disease starts with plant name, remove redundancy
        if (disease.toLowerCase().startsWith(plant.toLowerCase())) {
            disease = disease.substring(plant.length).trim();
        }
        
        // Title Case Helper
        const toTitleCase = (str) => str.replace(/\b\w/g, c => c.toUpperCase());
        
        plant = toTitleCase(plant);
        disease = toTitleCase(disease);
        
        if (disease === '' || disease.toLowerCase() === 'healthy') {
            return `${plant} (Healthy)`;
        }
        
        return `${plant}: ${disease}`;
    }

    function getScientificName(className) {
        const map = {
            'apple': 'Malus domestica',
            'cherry': 'Prunus avium',
            'grape': 'Vitis vinifera',
            'peach': 'Prunus persica',
            'potato': 'Solanum tuberosum',
            'strawberry': 'Fragaria × ananassa',
            'tomato': 'Solanum lycopersicum',
            'pepper': 'Capsicum annuum',
            'corn': 'Zea mays',
            'squash': 'Cucurbita pepo',
            'orange': 'Citrus sinensis'
        };
        
        const firstWord = (className || '').split('___')[0].toLowerCase();
        return map[firstWord] || 'Plantae';
    }

    // Render Results to UI
    function renderResults(res) {
        skeletonState.classList.add('hidden');
        
        // 1. Predicted Disease
        const rawPrediction = res.prediction;
        predictedDisease.innerText = cleanClassName(rawPrediction);
        scientificName.innerText = getScientificName(rawPrediction);
        
        // 2. Confidence & Mode Badge
        const conf = res.confidence;
        confidencePercentage.innerText = `${(conf * 100).toFixed(1)}%`;
        
        confidenceBadge.innerText = res.mode;
        confidenceBadge.className = 'badge'; // reset
        if (conf >= 0.85) {
            confidenceBadge.classList.add('success');
        } else if (conf >= 0.55) {
            confidenceBadge.classList.add('medium');
        } else {
            confidenceBadge.classList.add('low');
        }
        
        // 3. Top-3 Alternatives
        alternatesList.innerHTML = '';
        res.top3.forEach(([name, p]) => {
            const row = document.createElement('div');
            row.className = 'alt-row';
            row.innerHTML = `
                <div class="alt-info">
                    <span class="alt-name">${cleanClassName(name)}</span>
                    <span class="alt-pct">${(p * 100).toFixed(1)}%</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${(p * 100).toFixed(1)}%"></div>
                </div>
            `;
            alternatesList.appendChild(row);
        });
        
        // 4. Severity Proxy Radial
        const sev = res.severity_proxy;
        const ratio = sev.lesion_ratio;
        lesionPercentage.innerText = `${(ratio * 100).toFixed(1)}%`;
        severityLevel.innerText = sev.severity.toUpperCase();
        
        // SVG Radial stroke dashoffset calculation
        const radius = 42;
        const circumference = 2 * Math.PI * radius; // ~263.89
        const offset = circumference - (ratio * circumference);
        severityRadial.style.strokeDasharray = `${circumference}`;
        severityRadial.style.strokeDashoffset = offset;
        
        // Radial color based on severity
        if (sev.severity.toLowerCase().includes('healthy')) {
            severityRadial.style.stroke = 'var(--success)';
        } else if (sev.severity.toLowerCase().includes('early') || sev.severity.toLowerCase().includes('moderate')) {
            severityRadial.style.stroke = 'var(--warning)';
        } else {
            severityRadial.style.stroke = 'var(--danger)';
        }
        
        // 5. Image Quality Check
        const q = res.quality;
        qualityStatusBadge.className = 'quality-status'; // reset
        if (q.ok) {
            qualityStatusBadge.innerHTML = `<i class="fa-solid fa-circle-check"></i> Good Capture Quality`;
            qualityStatusBadge.classList.add('success');
            qualityWarningsBox.classList.add('hidden');
        } else {
            qualityStatusBadge.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> Quality Warnings`;
            qualityStatusBadge.classList.add('warning');
            
            // Populate warnings
            qualityWarningsBox.innerHTML = `<strong>Warnings:</strong> ${q.warnings.join(', ')}`;
            qualityWarningsBox.classList.remove('hidden');
        }
        
        // Normalize metrics to percentage of 255
        const brightnessPct = (q.brightness / 255 * 100).toFixed(0);
        const contrastPct = (q.contrast / 100 * 100).toFixed(0); // contrast usually maxes lower
        const sharpnessPct = (q.sharpness / 40 * 100).toFixed(0); // sharpness maxes around 30-40 in standard sets
        
        barBrightness.style.width = `${Math.min(brightnessPct, 100)}%`;
        valBrightness.innerText = q.brightness.toFixed(0);
        
        barContrast.style.width = `${Math.min(contrastPct, 100)}%`;
        valContrast.innerText = q.contrast.toFixed(0);
        
        barSharpness.style.width = `${Math.min(sharpnessPct, 100)}%`;
        valSharpness.innerText = q.sharpness.toFixed(1);
        
        // 6. Care Advice
        adviceText.innerText = res.advice;
        
        // Store current diagnosis for AgroBot context
        currentDiagnosisClass = rawPrediction;
        
        // Reveal Dashboard
        dashboardResults.classList.remove('hidden');
        setTimeout(() => {
            dashboardResults.classList.add('visible');
        }, 50);
    }

    // =========================================================================
    // AgroBot — Bilingual Smart Farm Assistant Controller
    // =========================================================================
    let currentDiagnosisClass = null;
    let activeDiagnosisContext = null;
    let chatLanguage = localStorage.getItem('agrobot_lang') || 'auto';
    let quickTopicsCache = null;

    // AgroBot DOM elements
    const agrobotFab = document.getElementById('agrobot-fab');
    const agrobotPanel = document.getElementById('agrobot-panel');
    const btnCloseChat = document.getElementById('btn-close-chat');
    const btnClearChat = document.getElementById('btn-clear-chat');
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const btnChatSend = document.getElementById('btn-chat-send');
    const btnChatMic = document.getElementById('btn-chat-mic');
    const micWave = document.getElementById('mic-wave');
    const chatTypingIndicator = document.getElementById('chat-typing-indicator');
    const typingText = document.getElementById('typing-text');
    const quickTopicsTrack = document.getElementById('quick-topics-track');
    const chatContextBar = document.getElementById('chat-context-bar');
    const chatContextText = document.getElementById('chat-context-text');
    const btnClearContext = document.getElementById('btn-clear-context');
    const btnAskBotDiagnosis = document.getElementById('btn-ask-bot-diagnosis');
    const langBtns = document.querySelectorAll('.lang-btn');

    // 1. Language Toggle
    function setChatLanguage(lang) {
        chatLanguage = lang;
        localStorage.setItem('agrobot_lang', lang);

        langBtns.forEach(btn => {
            if (btn.dataset.lang === lang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update placeholder
        if (lang === 'bn') {
            chatInput.placeholder = "এখানে আপনার কৃষিকাজের সমস্যা বাংলায় লিখুন...";
            typingText.innerText = "এগ্রো মিত্র ভাবছে...";
        } else if (lang === 'en') {
            chatInput.placeholder = "Ask your farming question in English...";
            typingText.innerText = "AgroBot is thinking...";
        } else {
            chatInput.placeholder = "Ask your farming problem in English or বাংলা...";
            typingText.innerText = "Thinking / ভাবছে...";
        }

        renderQuickTopics();
    }

    langBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            setChatLanguage(btn.dataset.lang);
        });
    });

    // 2. Open / Close AgroBot
    function openChat(focusInput = true) {
        agrobotPanel.classList.remove('hidden');
        if (chatMessages.children.length === 0) {
            sendWelcomeMessage();
        }
        if (focusInput) {
            setTimeout(() => chatInput.focus(), 200);
        }
        scrollChatToBottom();
    }

    function closeChat() {
        agrobotPanel.classList.add('hidden');
        if (window.speechSynthesis && window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }
        if (isRecording) {
            stopRecording();
        }
    }

    agrobotFab.addEventListener('click', () => {
        if (agrobotPanel.classList.contains('hidden')) {
            openChat();
        } else {
            closeChat();
        }
    });

    btnCloseChat.addEventListener('click', closeChat);

    // 3. Clear Chat
    btnClearChat.addEventListener('click', () => {
        if (confirm('Clear chat conversation? / কথোপকথন মুছে ফেলতে চান?')) {
            chatMessages.innerHTML = '';
            sendWelcomeMessage();
        }
    });

    // 4. Context Bar Handler
    function setDiagnosisContext(clsName) {
        activeDiagnosisContext = clsName;
        if (clsName) {
            chatContextText.innerText = `Active Diagnosis: ${cleanClassName(clsName)}`;
            chatContextBar.classList.remove('hidden');
        } else {
            chatContextBar.classList.add('hidden');
        }
    }

    btnClearContext.addEventListener('click', () => {
        setDiagnosisContext(null);
    });

    // 5. Ask AgroBot about current leaf diagnosis
    if (btnAskBotDiagnosis) {
        btnAskBotDiagnosis.addEventListener('click', () => {
            if (!currentDiagnosisClass) return;
            setDiagnosisContext(currentDiagnosisClass);
            openChat();

            const isBn = (chatLanguage === 'bn');
            const cleanName = cleanClassName(currentDiagnosisClass);
            const query = isBn 
                ? `আমার গাছে "${cleanName}" রোগ শনাক্ত হয়েছে। এর সঠিক চিকিৎসা, ঔষধের মাত্রা ও প্রতিকার কী?`
                : `My crop was diagnosed with "${cleanName}". What is the best treatment, dosage, and prevention plan?`;

            handleUserSendMessage(query);
        });
    }

    // 6. Fetch Quick Starter Topics
    async function loadQuickTopics() {
        try {
            const resp = await fetch('/chat/quick-topics');
            if (resp.ok) {
                quickTopicsCache = await resp.json();
                renderQuickTopics();
            }
        } catch (e) {
            console.warn('Failed to load quick topics:', e);
        }
    }

    function renderQuickTopics() {
        if (!quickTopicsCache) return;
        quickTopicsTrack.innerHTML = '';

        const langKey = (chatLanguage === 'bn') ? 'bn' : (chatLanguage === 'en' ? 'en' : 'bn');
        const topics = quickTopicsCache[langKey] || quickTopicsCache['bn'] || [];

        topics.forEach(t => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'topic-chip';
            chip.innerText = t.label;
            chip.addEventListener('click', () => {
                handleUserSendMessage(t.query);
            });
            quickTopicsTrack.appendChild(chip);
        });
    }

    // 7. Markdown Formatting Helper
    function renderMarkdown(md) {
        if (!md) return '';
        let html = md
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h3>$1</h3>')
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/gim, '<em>$1</em>')
            .replace(/`([^`]+)`/gim, '<code>$1</code>')
            .replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');

        // Group <li> into <ul>
        html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
        html = html.replace(/<\/ul>\s*<ul>/g, '');

        // Paragraphs
        const blocks = html.split('\n\n');
        html = blocks.map(block => {
            const b = block.trim();
            if (!b) return '';
            if (b.startsWith('<h3>') || b.startsWith('<ul>') || b.startsWith('<div')) return b;
            return `<p>${b.replace(/\n/g, '<br>')}</p>`;
        }).join('');

        return html;
    }

    // 8. Text-to-Speech (Audio Voice Readout)
    function speakText(text, lang, button) {
        if (!('speechSynthesis' in window)) {
            alert('Voice audio is not supported in this browser.');
            return;
        }

        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
            if (button.classList.contains('speaking')) {
                button.classList.remove('speaking');
                button.innerHTML = `<i class="fa-solid fa-volume-high"></i> <span>${lang === 'bn' ? 'শুনুন' : 'Listen'}</span>`;
                return;
            }
        }

        // Clean text for speech
        const cleanSpeech = text
            .replace(/###|\*\*|\*|`|_|#|-/g, ' ')
            .replace(/https?:\/\/\S+/g, '')
            .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
            .trim();

        const utterance = new SpeechSynthesisUtterance(cleanSpeech);
        utterance.lang = (lang === 'bn') ? 'bn-BD' : 'en-US';

        // Select voice if available
        const voices = window.speechSynthesis.getVoices();
        if (lang === 'bn') {
            const bnVoice = voices.find(v => v.lang && v.lang.toLowerCase().startsWith('bn'));
            if (bnVoice) utterance.voice = bnVoice;
        }

        button.classList.add('speaking');
        button.innerHTML = `<i class="fa-solid fa-volume-xmark"></i> <span>${lang === 'bn' ? 'থামুন' : 'Stop'}</span>`;

        utterance.onend = () => {
            button.classList.remove('speaking');
            button.innerHTML = `<i class="fa-solid fa-volume-high"></i> <span>${lang === 'bn' ? 'শুনুন' : 'Listen'}</span>`;
        };
        utterance.onerror = () => {
            button.classList.remove('speaking');
            button.innerHTML = `<i class="fa-solid fa-volume-high"></i> <span>${lang === 'bn' ? 'শুনুন' : 'Listen'}</span>`;
        };

        window.speechSynthesis.speak(utterance);
    }

    // 9. Speech-to-Text (Voice Recognition)
    let recognition = null;
    let isRecording = false;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRec();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = (chatInput.value + ' ' + transcript).trim();
            adjustTextareaHeight();
            stopRecording();
        };

        recognition.onerror = () => {
            stopRecording();
        };

        recognition.onend = () => {
            stopRecording();
        };
    }

    function startRecording() {
        if (!recognition) {
            alert('Voice input is supported in Google Chrome, Microsoft Edge, and Android Chrome.');
            return;
        }
        const recLang = (chatLanguage === 'bn') ? 'bn-BD' : ((chatLanguage === 'en') ? 'en-US' : 'bn-BD');
        recognition.lang = recLang;
        try {
            recognition.start();
            isRecording = true;
            btnChatMic.classList.add('listening');
            if (micWave) micWave.classList.remove('hidden');
        } catch (e) {
            console.warn('Speech start error:', e);
        }
    }

    function stopRecording() {
        isRecording = false;
        btnChatMic.classList.remove('listening');
        if (micWave) micWave.classList.add('hidden');
        try {
            if (recognition) recognition.stop();
        } catch (e) {}
    }

    btnChatMic.addEventListener('click', () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });

    // 10. Message DOM Builders
    function appendUserMessage(text) {
        const wrapper = document.createElement('div');
        wrapper.className = 'msg-wrapper user';

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';
        bubble.innerText = text;

        const meta = document.createElement('div');
        meta.className = 'msg-meta';
        meta.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        wrapper.appendChild(bubble);
        wrapper.appendChild(meta);
        chatMessages.appendChild(wrapper);
        scrollChatToBottom();
    }

    function appendBotMessage(data) {
        const wrapper = document.createElement('div');
        wrapper.className = 'msg-wrapper bot';

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';

        // Category Tag
        if (data.category) {
            const catBadge = document.createElement('div');
            catBadge.className = 'bot-cat-badge';
            catBadge.innerHTML = `<i class="fa-solid fa-seedling"></i> ${data.category}`;
            bubble.appendChild(catBadge);
        }

        // Formatted Markdown Content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'msg-content-html';
        contentDiv.innerHTML = renderMarkdown(data.reply);
        bubble.appendChild(contentDiv);

        // Follow-up Suggestions
        if (data.suggestions && data.suggestions.length > 0) {
            const suggBox = document.createElement('div');
            suggBox.className = 'bot-suggestions';
            data.suggestions.forEach(suggText => {
                const suggBtn = document.createElement('button');
                suggBtn.type = 'button';
                suggBtn.className = 'suggestion-chip';
                suggBtn.innerText = suggText;
                suggBtn.addEventListener('click', () => {
                    handleUserSendMessage(suggText);
                });
                suggBox.appendChild(suggBtn);
            });
            bubble.appendChild(suggBox);
        }

        // Meta Bar (Timestamp, Audio Readout, Copy)
        const meta = document.createElement('div');
        meta.className = 'msg-meta';

        const timeSpan = document.createElement('span');
        timeSpan.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        meta.appendChild(timeSpan);

        // Voice Readout Button
        const speakBtn = document.createElement('button');
        speakBtn.type = 'button';
        speakBtn.className = 'msg-action-btn';
        const isBn = (data.language === 'bn');
        speakBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> <span>${isBn ? 'শুনুন' : 'Listen'}</span>`;
        speakBtn.addEventListener('click', () => {
            speakText(data.reply, data.language || 'bn', speakBtn);
        });
        meta.appendChild(speakBtn);

        // Copy Button
        const copyBtn = document.createElement('button');
        copyBtn.type = 'button';
        copyBtn.className = 'msg-action-btn';
        copyBtn.innerHTML = `<i class="fa-regular fa-copy"></i> <span>Copy</span>`;
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(data.reply);
                copyBtn.innerHTML = `<i class="fa-solid fa-check"></i> <span>Copied!</span>`;
                setTimeout(() => {
                    copyBtn.innerHTML = `<i class="fa-regular fa-copy"></i> <span>Copy</span>`;
                }, 2000);
            } catch (e) {
                console.warn('Copy failed:', e);
            }
        });
        meta.appendChild(copyBtn);

        wrapper.appendChild(bubble);
        wrapper.appendChild(meta);
        chatMessages.appendChild(wrapper);
        scrollChatToBottom();
    }

    function sendWelcomeMessage() {
        const isBn = (chatLanguage === 'bn');
        const welcomeText = isBn
            ? "🌾 **নমস্কার! আমি এগ্রো মিত্র (AgroBot)**।\n\nফসলের যেকোনো সমস্যা যেমন পোকা দমন, রোগ প্রতিকার, সারের সঠিক মাত্রা, বা সেচ পদ্ধতি সম্পর্কে বাংলায় প্রশ্ন করুন।"
            : "🌾 **Hello! I am AgroBot — Your Bilingual Farm Assistant.**\n\nAsk me anything in English or বাংলা about crop diseases, pest remedies, balanced fertilizer doses, or smart irrigation!";

        appendBotMessage({
            reply: welcomeText,
            language: isBn ? 'bn' : 'en',
            category: 'Welcome',
            suggestions: isBn
                ? ["ধানের মাজরা পোকা দমন", "আলুর নাবি ধসা রোগ", "ইউরিয়া ও ডিএপি সারের নিয়ম", "কিষাণ হেল্পলাইন নম্বর"]
                : ["Rice stem borer remedies", "Potato late blight control", "Fertilizer dosage guide", "Farmer helpline numbers"]
        });
    }

    function scrollChatToBottom() {
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 50);
    }

    function adjustTextareaHeight() {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + 'px';
    }

    chatInput.addEventListener('input', adjustTextareaHeight);

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Thinking text phase cycler
    let thinkingInterval = null;
    function startThinkingAnimation() {
        const isBn = (chatLanguage === 'bn');
        const phases = isBn
            ? ["এগ্রো মিত্র ভাবছে...", "তথ্যভাণ্ডারে খোঁজা হচ্ছে...", "সমাধান প্রস্তুত করছে..."]
            : ["AgroBot is thinking...", "Searching knowledge base...", "Preparing expert advice..."];
        let idx = 0;
        typingText.innerText = phases[0];
        thinkingInterval = setInterval(() => {
            idx = (idx + 1) % phases.length;
            typingText.innerText = phases[idx];
        }, 700);
    }

    function stopThinkingAnimation() {
        if (thinkingInterval) {
            clearInterval(thinkingInterval);
            thinkingInterval = null;
        }
    }

    // 11. Form Submit Handler
    async function handleUserSendMessage(userText) {
        const text = (userText || chatInput.value).trim();
        if (!text) return;

        chatInput.value = '';
        adjustTextareaHeight();
        appendUserMessage(text);

        // Show thinking indicator with animated text phases
        chatTypingIndicator.classList.remove('hidden');
        startThinkingAnimation();
        scrollChatToBottom();

        const thinkingStartTime = Date.now();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    language: chatLanguage,
                    diagnosis_context: activeDiagnosisContext
                })
            });

            if (!response.ok) {
                throw new Error('Server returned error response');
            }

            const data = await response.json();

            // Enforce minimum thinking delay (2 seconds) for attention span
            const thinkingDelay = data.thinking_delay || 2000;
            const elapsed = Date.now() - thinkingStartTime;
            const remaining = Math.max(0, thinkingDelay - elapsed);

            if (remaining > 0) {
                await new Promise(resolve => setTimeout(resolve, remaining));
            }

            stopThinkingAnimation();
            chatTypingIndicator.classList.add('hidden');
            appendBotMessage(data);

        } catch (error) {
            console.error('Chat error:', error);

            // Still enforce a small delay on error for consistency
            const elapsed = Date.now() - thinkingStartTime;
            const remaining = Math.max(0, 1500 - elapsed);
            if (remaining > 0) {
                await new Promise(resolve => setTimeout(resolve, remaining));
            }

            stopThinkingAnimation();
            chatTypingIndicator.classList.add('hidden');
            appendBotMessage({
                reply: (chatLanguage === 'bn')
                    ? "দুঃখিত, সংযোগে ত্রুটি হয়েছে। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
                    : "Sorry, a connection error occurred. Please try again in a moment.",
                language: chatLanguage === 'bn' ? 'bn' : 'en',
                category: 'Error'
            });
        }
    }

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleUserSendMessage();
    });

    // Initial setup
    setChatLanguage(chatLanguage);
    loadQuickTopics();
});
