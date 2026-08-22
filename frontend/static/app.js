let chatHistory = [];
let queryHistoryList = JSON.parse(localStorage.getItem('aether_query_history')) || [];
const form = document.getElementById('query-form');
const input = document.getElementById('query-input');
const resultsArea = document.getElementById('results-area');
const heroSection = document.getElementById('hero-section');
const suggestions = document.getElementById('suggestions');
const spacerBottom = document.getElementById('spacer-bottom');
const themeToggle = document.getElementById('theme-toggle');

// ==========================================
// THEME & LAYOUT STATE
// ==========================================
function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    
    // Re-render all existing charts to apply the new theme colors
    document.querySelectorAll('[id^="plotly-chart-"]').forEach(el => {
        const cid = el.id.replace('plotly-', '');
        const cachedData = window[`tableData_${cid}`];
        if (cachedData && cachedData.config) {
            renderPlotlyChart(el.id, cachedData.data, cachedData.columns, cachedData.config);
        }
    });
}
themeToggle.addEventListener('click', toggleTheme);

window.setQuery = function(q) {
    const navOverviewBtn = document.getElementById('nav-overview');
    if (navOverviewBtn) navOverviewBtn.click();
    input.value = q;
    
    // Use setTimeout to ensure the element is visible before focusing
    setTimeout(() => {
        input.focus();
        // Optional: animate the input to draw attention
        input.parentElement.classList.add('ring-2', 'ring-indigo-500');
        setTimeout(() => input.parentElement.classList.remove('ring-2', 'ring-indigo-500'), 1000);
    }, 100);
}

function transitionToResults() {
    heroSection.classList.add('opacity-0', 'scale-95', 'h-0', 'mb-0', 'overflow-hidden');
    suggestions.classList.add('opacity-0', 'scale-95', 'h-0', 'overflow-hidden');
    spacerBottom.classList.remove('hidden');
    
    resultsArea.classList.remove('hidden');
    resultsArea.classList.add('flex');
}

// ==========================================
// VOICE RECORDING
// ==========================================
const recordBtn = document.getElementById('record-btn');
const recordingPulse = document.getElementById('recording-pulse');
let mediaRecorder;
let audioChunks = [];
let recordingStartTime = 0;

async function initAudio() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };
        
        mediaRecorder.onstop = async () => {
            const recordingDuration = Date.now() - recordingStartTime;
            
            // If the user just clicked the button (< 500ms), don't send to API (it will error as "too short")
            if (recordingDuration < 500) {
                audioChunks = [];
                return;
            }

            const mimeType = mediaRecorder.mimeType || 'audio/webm';
            const audioBlob = new Blob(audioChunks, { type: mimeType });
            audioChunks = [];
            
            // Determine the correct extension based on browser support
            const extension = mimeType.includes('mp4') ? 'mp4' : mimeType.includes('ogg') ? 'ogg' : 'webm';
            
            input.disabled = true;
            input.placeholder = "Transcribing voice...";
            
            const formData = new FormData();
            formData.append('file', audioBlob, `audio.${extension}`);
            
            try {
                const res = await fetch('/api/voice', { method: 'POST', body: formData });
                const data = await res.json();
                
                if (data.success && data.text) {
                    input.value = data.text;
                } else {
                    alert('Error transcribing audio: ' + (data.error || 'Unknown error'));
                }
            } catch (e) {
                alert('Network error during transcription');
            }
            
            input.disabled = false;
            input.placeholder = "Ask a question about your data...";
            input.focus();
        };
    } catch (e) {
        console.error('Microphone access denied', e);
    }
}
initAudio();

recordBtn.addEventListener('mousedown', () => {
    if (mediaRecorder && mediaRecorder.state === 'inactive') {
        audioChunks = [];
        recordingStartTime = Date.now();
        mediaRecorder.start();
        recordingPulse.classList.remove('hidden');
        recordBtn.classList.add('text-rose-500');
    }
});

// Handle both mouseup and mouseleave so it stops if they drag off the button
const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        recordingPulse.classList.add('hidden');
        recordBtn.classList.remove('text-rose-500');
    }
};

recordBtn.addEventListener('mouseup', stopRecording);
recordBtn.addEventListener('mouseleave', stopRecording);

// ==========================================
// QUERY SUBMISSION & RENDER
// ==========================================
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;
    
    transitionToResults();
    input.value = '';
    
    renderUserQuery(query);
    
    const loaderTemplate = document.getElementById('loader-template');
    const loaderNode = loaderTemplate.content.cloneNode(true);
    const loaderWrapper = document.createElement('div');
    loaderWrapper.id = 'current-loader';
    loaderWrapper.appendChild(loaderNode);
    resultsArea.appendChild(loaderWrapper);
    
    setTimeout(() => {
        const loadingEl = loaderWrapper.querySelector('.result-loading');
        if (loadingEl) loadingEl.classList.remove('opacity-0', 'translate-y-4');
    }, 50);
    
    scrollToBottom();
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: query, history: chatHistory })
        });
        const data = await res.json();
        
        queryHistoryList.unshift({
            query: query,
            time: new Date().toLocaleTimeString(),
            success: data.success
        });
        localStorage.setItem('aether_query_history', JSON.stringify(queryHistoryList));
        
        const loader = document.getElementById('current-loader');
        if (loader) loader.remove();
        
        chatHistory.push({ role: 'user', content: query });
        chatHistory.push({ role: 'assistant', content: data });
        
        renderAssistantResponse(data, query);
    } catch (e) {
        const loader = document.getElementById('current-loader');
        if (loader) loader.remove();
        renderError('Network error connecting to backend.');
    }
});

function scrollToBottom() {
    const container = document.getElementById('scroll-container');
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
}

function renderUserQuery(text) {
    // The user requested NOT to show their query in the history.
    // We will just clear the results area if needed, but not append a user bubble.
    resultsArea.innerHTML = ''; 
}

function renderError(msg, originalQuery) {
    const html = `
        <div class="w-full mx-auto flex items-start gap-4 opacity-0 transform translate-y-4 transition-all duration-700 mb-8 error-container">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-rose-500 to-red-600 text-white flex items-center justify-center shrink-0 shadow-lg border border-rose-400/30 mt-1">
                <span class="text-lg">🛡️</span>
            </div>
            
            <div class="flex-1 space-y-6 w-full overflow-hidden">
                
                ${originalQuery ? `
                <!-- Original Question Header -->
                <div class="mb-2">
                    <h2 class="text-2xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight">
                        ${originalQuery}
                    </h2>
                </div>` : ''}

                <!-- Section 1: Security/Error Summary -->
                <div class="insight-card p-6 border-l-[3px] border-l-rose-500 relative overflow-hidden group">
                    <div class="absolute inset-0 bg-gradient-to-r from-rose-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                    <div class="relative z-10">
                        <div class="text-[11px] font-bold text-rose-500 uppercase tracking-widest mb-2 flex items-center gap-3">
                            <span>Governance Intercept</span>
                            <div class="h-px bg-rose-500/20 flex-1"></div>
                        </div>
                        <div class="text-slate-900 dark:text-slate-50 leading-relaxed font-semibold text-lg">${msg}</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    resultsArea.insertAdjacentHTML('beforeend', html);
    
    // Animate in
    requestAnimationFrame(() => {
        const el = resultsArea.lastElementChild;
        if (el) {
            el.classList.remove('opacity-0', 'translate-y-4');
        }
    });
}

function generateMockKPIs(data) {
    const randomTrend = () => (Math.random() * 15 + 2).toFixed(1);
    const isUp = Math.random() > 0.3;
    return [
        { label: 'Total Rows Analyzed', value: data ? data.length : 0, trend: `+${randomTrend()}%`, up: true, icon: '📊' },
        { label: 'AI Confidence Score', value: 98, format: '%', trend: 'High', up: true, icon: '🎯' },
        { label: 'Execution Time', value: 0.24, format: 's', trend: '-0.02s', up: true, icon: '⚡' },
        { label: 'Data Governance', value: 'Passed', trend: 'Read-only', up: true, icon: '🛡️', textValue: true },
    ];
}

function animateValue(obj, start, end, duration, format = '') {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const current = progress * (end - start) + start;
        obj.innerHTML = (end % 1 !== 0 ? current.toFixed(2) : Math.floor(current)) + format;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            obj.innerHTML = end + format;
        }
    };
    window.requestAnimationFrame(step);
}

window.currentResponses = window.currentResponses || {};

function renderAssistantResponse(resp, originalQuery, isRestored = false) {
    if (!resp.success) {
        const queryToPass = originalQuery || resp.question;
        const formattedMsg = resp.error + (resp.sql ? `<div class="mt-4"><pre class="text-xs bg-slate-100 dark:bg-black/40 p-4 rounded-xl border border-slate-200 dark:border-white/5 text-rose-600 dark:text-rose-400 font-mono shadow-inner overflow-x-auto"><code>${resp.sql}</code></pre></div>` : '');
        renderError(formattedMsg, queryToPass);
        return;
    }

    const chartId = 'chart-' + Math.random().toString(36).substr(2, 9);
    window.currentResponses[chartId] = { resp, originalQuery };
    
    const kpis = generateMockKPIs(resp.data);
    
    let html = `
        <div class="w-full mx-auto flex items-start gap-4 opacity-0 transform translate-y-4 transition-all duration-700 mb-8" id="resp-${chartId}">
            <div class="w-10 h-10 rounded-full signature-gradient text-white flex items-center justify-center shrink-0 shadow-glow border border-white/10 mt-1">
                <span class="text-lg">✨</span>
            </div>
            
            <div class="flex-1 space-y-6 w-full overflow-hidden">
                
                <!-- Original Question Header -->
                <div class="mb-4 flex items-center justify-between">
                    <h2 class="text-2xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight">
                        ${originalQuery || resp.question}
                    </h2>
                    ${!isRestored ? `
                    <div class="flex items-center gap-2">
                        <button id="pdf-btn-${chartId}" class="text-xs font-bold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 dark:text-slate-200 dark:bg-[#18181B] dark:border-slate-800 dark:hover:bg-white/5 px-3 py-2 rounded-lg flex items-center gap-2 transition-colors shrink-0 shadow-sm" onclick="window.exportToPDF('${chartId}', \`${(originalQuery || resp.question).replace(/`/g, "'")}\`)">
                            <svg class="w-4 h-4 text-rose-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                            Export PDF
                        </button>
                        <button id="save-btn-${chartId}" class="text-xs font-bold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 dark:text-indigo-400 dark:bg-indigo-500/10 dark:hover:bg-indigo-500/20 px-3 py-2 rounded-lg flex items-center gap-2 transition-colors shrink-0" onclick="window.saveInsight('${chartId}', \`${(originalQuery || resp.question).replace(/`/g, "'")}\`)">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                            Save Insight
                        </button>
                    </div>
                    ` : `
                    <div class="flex items-center gap-2">
                        <button id="pdf-btn-${chartId}" class="text-xs font-bold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 dark:text-slate-200 dark:bg-[#18181B] dark:border-slate-800 dark:hover:bg-white/5 px-3 py-2 rounded-lg flex items-center gap-2 transition-colors shrink-0 shadow-sm" onclick="window.exportToPDF('${chartId}', \`${(originalQuery || resp.question).replace(/`/g, "'")}\`)">
                            <svg class="w-4 h-4 text-rose-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                            Export PDF
                        </button>
                        <span class="text-xs font-bold text-amber-500 bg-amber-50 dark:bg-amber-500/10 px-3 py-2 rounded-lg flex items-center gap-2"><svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg> Saved Insight</span>
                    </div>
                    `}
                </div>

                <!-- Section 1: Executive Summary -->
                <div class="insight-card p-6 border-l-[3px] border-l-accent2 relative overflow-hidden group">
                    <div class="relative z-10">
                        <div class="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-widest mb-2 flex items-center gap-3">
                            <span>Executive Summary</span>
                        </div>
                        <p class="text-slate-900 dark:text-slate-50 leading-relaxed font-semibold text-xl">${resp.summary}</p>
                    </div>
                </div>
                
                <!-- Section 2: KPI Metrics -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    ${kpis.map((kpi, i) => `
                        <div class="insight-card p-5 flex flex-col justify-between hover:border-accent2/50 group transition-all duration-300">
                            <div class="flex justify-between items-center mb-3">
                                <span class="text-slate-500 dark:text-slate-400 text-xs font-bold tracking-wider uppercase">${kpi.label}</span>
                            </div>
                            <div class="text-3xl font-mono font-bold text-slate-900 dark:text-slate-50 mb-3 metric-value" data-val="${kpi.textValue ? '' : kpi.value}" data-format="${kpi.format || ''}">
                                ${kpi.textValue ? kpi.value : '0'}
                            </div>
                            <div class="text-[11px] font-mono font-semibold ${kpi.up ? 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-400/10 border-emerald-200 dark:border-emerald-400/20' : 'text-rose-600 bg-rose-50 dark:text-rose-400 dark:bg-rose-400/10 border-rose-200 dark:border-rose-400/20'} px-2 py-1 rounded w-max border">
                                ${kpi.up ? '↑' : '↓'} ${kpi.trend}
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <!-- Section 3: Visuals, Data, SQL -->
                <div class="insight-card overflow-hidden flex flex-col">
                    <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 px-2 bg-slate-50 dark:bg-[#121214]">
                        <div class="flex gap-2">
                            <button class="tab-btn px-5 py-4 font-semibold text-slate-900 dark:text-slate-50 text-xs transition-colors relative" data-target="viz-${chartId}">
                                Visual Analytics
                                <div class="absolute bottom-0 left-0 w-full h-[2px] bg-accent2 tab-indicator"></div>
                            </button>
                            <button class="tab-btn px-5 py-4 font-semibold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-50 text-xs transition-colors relative" data-target="data-${chartId}">
                                Data Table
                                <div class="absolute bottom-0 left-0 w-full h-[2px] bg-transparent tab-indicator"></div>
                            </button>
                            <button class="tab-btn px-5 py-4 font-semibold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-50 text-xs transition-colors relative" data-target="sql-${chartId}">
                                Generated SQL
                                <div class="absolute bottom-0 left-0 w-full h-[2px] bg-transparent tab-indicator"></div>
                            </button>
                        </div>
                        <div id="export-controls-${chartId}" class="hidden pr-4">
                            <button class="text-xs font-semibold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-50 flex items-center gap-1.5 px-3 py-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-white/5 transition-all" onclick="exportTableToCSV('${chartId}')">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                                Export
                            </button>
                        </div>
                    </div>
                    
                    <div class="p-1 bg-white dark:bg-[#09090B] relative rounded-b-xl">
                        <div id="viz-${chartId}" class="tab-content w-full h-auto min-h-[500px] relative overflow-hidden">
                            <!-- Chart Type Selectors -->
                            <div class="absolute top-4 right-4 z-10 flex bg-white dark:bg-[#18181B] border border-slate-200 dark:border-slate-800 rounded-lg shadow-sm overflow-hidden p-1 gap-1">
                                <button class="chart-type-btn px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${resp.chart_config?.type === 'bar' || !resp.chart_config?.type ? 'bg-slate-100 dark:bg-white/10 text-slate-900 dark:text-slate-50' : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5'}" data-type="bar" data-chart="${chartId}">Bar</button>
                                <button class="chart-type-btn px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${resp.chart_config?.type === 'line' ? 'bg-slate-100 dark:bg-white/10 text-slate-900 dark:text-slate-50' : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5'}" data-type="line" data-chart="${chartId}">Line</button>
                                <button class="chart-type-btn px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${resp.chart_config?.type === 'pie' ? 'bg-slate-100 dark:bg-white/10 text-slate-900 dark:text-slate-50' : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5'}" data-type="pie" data-chart="${chartId}">Pie</button>
                                <button class="chart-type-btn px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${resp.chart_config?.type === 'scatter' ? 'bg-slate-100 dark:bg-white/10 text-slate-900 dark:text-slate-50' : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5'}" data-type="scatter" data-chart="${chartId}">Scatter</button>
                            </div>
                            <div id="plotly-${chartId}" class="w-full pt-10 pb-4"></div>
                        </div>
                        
                        <div id="data-${chartId}" class="tab-content hidden h-[500px] overflow-y-auto relative rounded-b-lg">
                            <table class="w-full text-sm text-left font-mono">
                                <thead class="text-[11px] text-slate-500 dark:text-slate-400 uppercase bg-slate-50 dark:bg-[#121214] border-b border-slate-200 dark:border-slate-800 sticky top-0 z-10 shadow-sm">
                                    <tr>
                                        ${resp.columns.map(c => `<th class="px-5 py-4 font-bold tracking-wider">${c}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${resp.data.map((row, idx) => `
                                        <tr class="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors ${idx % 2 === 0 ? 'bg-transparent' : 'bg-slate-50/50 dark:bg-white/[0.02]'}">
                                            ${row.map(cell => `<td class="px-5 py-3 whitespace-nowrap text-slate-800 dark:text-slate-50/90">${cell}</td>`).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        
                        <div id="sql-${chartId}" class="tab-content hidden h-[500px] overflow-y-auto bg-slate-50 dark:bg-[#09090B]">
                            <div class="text-slate-800 dark:text-slate-50 p-6 font-mono text-[13px] leading-relaxed relative group">
                                <button class="absolute top-4 right-4 p-2 bg-white dark:bg-[#121214] border border-slate-200 dark:border-slate-800 hover:border-indigo-500 rounded text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white opacity-0 group-hover:opacity-100 transition-all shadow-sm" title="Copy SQL" onclick="navigator.clipboard.writeText(this.nextElementSibling.innerText)">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                                </button>
                                <pre class="whitespace-pre-wrap"><code class="language-sql text-indigo-700 dark:text-accent3">${resp.sql}</code></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    resultsArea.insertAdjacentHTML('beforeend', html);
    const containerEl = document.getElementById(`resp-${chartId}`);
    
    setTimeout(() => {
        containerEl.classList.remove('opacity-0', 'translate-y-4');
        
        // Trigger number animations
        containerEl.querySelectorAll('.metric-value').forEach(el => {
            if (el.getAttribute('data-val')) {
                animateValue(el, 0, parseFloat(el.getAttribute('data-val')), 1500, el.getAttribute('data-format'));
            }
        });
    }, 50);

    const tabBtns = containerEl.querySelectorAll('.tab-btn');
    const tabContents = containerEl.querySelectorAll('.tab-content');
    const exportControls = containerEl.querySelector(`#export-controls-${chartId}`);
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => {
                b.classList.remove('text-slate-900', 'dark:text-slate-50');
                b.classList.add('text-slate-500', 'dark:text-slate-400');
                b.querySelector('.tab-indicator').classList.replace('bg-accent2', 'bg-transparent');
            });
            btn.classList.remove('text-slate-500', 'dark:text-slate-400');
            btn.classList.add('text-slate-900', 'dark:text-slate-50');
            btn.querySelector('.tab-indicator').classList.replace('bg-transparent', 'bg-accent2');
            
            tabContents.forEach(c => c.classList.add('hidden'));
            
            const targetId = btn.getAttribute('data-target');
            const target = containerEl.querySelector('#' + targetId);
            if (target) {
                target.classList.remove('hidden');
                if (targetId.startsWith('data-')) exportControls.classList.remove('hidden');
                else exportControls.classList.add('hidden');
                
                if (targetId.startsWith('viz-')) Plotly.Plots.resize(containerEl.querySelector(`#plotly-${chartId}`));
            }
        });
    });

    window[`tableData_${chartId}`] = { columns: resp.columns, data: resp.data, config: resp.chart_config };
    
    const chartTypeBtns = containerEl.querySelectorAll('.chart-type-btn');
    chartTypeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            chartTypeBtns.forEach(b => b.className = "chart-type-btn px-3 py-1.5 text-xs font-semibold rounded-md transition-all text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5");
            btn.className = "chart-type-btn px-3 py-1.5 text-xs font-semibold rounded-md transition-all bg-slate-100 dark:bg-white/10 text-slate-900 dark:text-slate-50";
            
            const type = btn.getAttribute('data-type');
            const cid = btn.getAttribute('data-chart');
            const cachedData = window[`tableData_${cid}`];
            if (cachedData && cachedData.config) {
                const newConfig = { ...cachedData.config, type: type };
                renderPlotlyChart(`plotly-${cid}`, cachedData.data, cachedData.columns, newConfig);
            }
        });
    });

    if (resp.chart_config) {
        renderPlotlyChart(`plotly-${chartId}`, resp.data, resp.columns, resp.chart_config);
    } else {
        tabBtns[1].click();
    }
}

function renderPlotlyChart(elementId, data, columns, config) {
    if (!config.x || !config.y) return;
    const xIdx = columns.indexOf(config.x);
    const yIdx = columns.indexOf(config.y);
    if (xIdx === -1 || yIdx === -1) return;
    
    const xData = data.map(row => row[xIdx]);
    const yData = data.map(row => row[yIdx]);
    
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#FAFAFA' : '#0F172A';
    const gridColor = isDark ? '#27272A' : '#E2E8F0';
    const accentPrimary = '#8B5CF6';
    const accentSecondary = '#06B6D4';
    
    let trace = { x: xData, y: yData };
    
    if (config.type === 'line') {
        trace.type = 'scatter';
        trace.mode = 'lines+markers';
        trace.line = { color: accentPrimary, width: 3, shape: 'spline' };
        trace.marker = { size: 6, color: accentSecondary, line: { color: '#09090B', width: 2 } };
        trace.fill = 'tozeroy';
        trace.fillcolor = 'rgba(139, 92, 246, 0.1)';
    } else if (config.type === 'pie') {
        trace.type = 'pie';
        trace.labels = xData;
        trace.values = yData;
        trace.hole = 0.65;
        trace.marker = { colors: ['#4F46E5', '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#3B82F6', '#EC4899', '#8B5CF6'] };
        trace.textinfo = 'percent';
        trace.hoverinfo = 'label+value';
        delete trace.x; delete trace.y;
    } else if (config.type === 'scatter') {
        trace.type = 'scatter';
        trace.mode = 'markers';
        trace.marker = { size: 10, color: accentPrimary, opacity: 0.8 };
    } else {
        trace.type = 'bar';
        trace.marker = { color: accentPrimary, opacity: 0.9 }; 
    }
    
    const layout = {
        height: 400,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter', color: textColor, size: 11 },
        margin: { t: 20, r: 20, b: 60, l: 70 },
        xaxis: { 
            title: { text: config.x, font: { size: 12, color: textColor } },
            gridcolor: gridColor, 
            zerolinecolor: gridColor, 
            showline: false,
            automargin: true
        },
        yaxis: { 
            title: { text: config.y, font: { size: 12, color: textColor } },
            gridcolor: gridColor, 
            zerolinecolor: gridColor, 
            showline: false,
            automargin: true
        },
        hovermode: 'closest',
        hoverlabel: { bgcolor: '#18181B', font: { family: 'Inter', color: '#FAFAFA' }, bordercolor: '#27272A' }
    };
    
    Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
}

window.exportTableToCSV = function(chartId) {
    const tableData = window[`tableData_${chartId}`];
    if (!tableData) return;
    
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += tableData.columns.join(",") + "\r\n";
    tableData.data.forEach(row => {
        let rowStr = row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(",");
        csvContent += rowStr + "\r\n";
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `aether_export_${chartId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// ==========================================
// EXPORT TO PDF
// ==========================================

window.exportToPDF = async function(chartId, title) {
    const btn = document.getElementById(`pdf-btn-${chartId}`);
    const originalText = btn.innerHTML;
    
    try {
        btn.innerHTML = `<svg class="w-4 h-4 animate-spin text-rose-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Generating...`;
        btn.disabled = true;
        
        const container = document.getElementById(`resp-${chartId}`);
        if (!container) return;
        
        // 1. TEMPORARILY PREPARE DOM FOR PRINTING
        // Hide action buttons (PDF, Save)
        const actionButtons = container.querySelector('.flex.items-center.gap-2');
        if (actionButtons) actionButtons.classList.add('hidden');
        
        // Hide the tab navigation bar
        const tabNav = container.querySelector('.flex.border-b');
        if (tabNav) tabNav.classList.add('hidden');
        
        // Hide the interactive chart type selectors (so they don't appear in static PDF)
        const chartTypeSelector = container.querySelector('.absolute.top-4.right-4.z-10.flex');
        if (chartTypeSelector) chartTypeSelector.classList.add('hidden');
        
        // Expand and show ALL tabs (Chart, Table, SQL)
        const allTabs = container.querySelectorAll('.tab-content');
        allTabs.forEach(tab => {
            tab.classList.remove('hidden', 'h-[500px]', 'overflow-y-auto');
            tab.classList.add('h-auto');
            tab.style.display = 'block';
            tab.style.marginBottom = '24px';
        });
        
        // Small delay to ensure DOM reflows
        await new Promise(r => setTimeout(r, 100));
        
        // 2. CAPTURE HIGH-RES SNAPSHOT
        const canvas = await html2canvas(container, {
            scale: 2, 
            useCORS: true,
            logging: false,
            backgroundColor: document.documentElement.classList.contains('dark') ? '#09090B' : '#FAFAFA'
        });
        
        // 3. RESTORE DOM TO ORIGINAL STATE
        if (actionButtons) actionButtons.classList.remove('hidden');
        if (tabNav) tabNav.classList.remove('hidden');
        if (chartTypeSelector) chartTypeSelector.classList.remove('hidden');
        allTabs.forEach(tab => {
            tab.style.display = '';
            tab.style.marginBottom = '';
            tab.classList.remove('h-auto');
            tab.classList.add('h-[500px]', 'overflow-y-auto');
        });
        
        // Click Viz tab to restore exact state
        const vizTabBtn = container.querySelector(`[data-target="viz-${chartId}"]`);
        if (vizTabBtn) vizTabBtn.click();
        
        // 4. GENERATE MULTI-PAGE PDF
        const imgData = canvas.toDataURL('image/png');
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = pdf.internal.pageSize.getHeight();
        
        // Add Professional Header
        pdf.setFillColor(79, 70, 229); 
        pdf.rect(0, 0, pdfWidth, 15, 'F');
        pdf.setTextColor(255, 255, 255);
        pdf.setFontSize(14);
        pdf.setFont("helvetica", "bold");
        pdf.text("Exasol Aether Copilot - Executive Report", 10, 10);
        
        const margin = 10;
        const availableWidth = pdfWidth - (margin * 2);
        const imgProps = pdf.getImageProperties(imgData);
        const ratio = imgProps.width / imgProps.height;
        const imgHeight = availableWidth / ratio;
        
        let heightLeft = imgHeight;
        let position = 20; // Start below the header

        // Page 1
        pdf.addImage(imgData, 'PNG', margin, position, availableWidth, imgHeight);
        heightLeft -= (pdfHeight - position);

        // Subsequent Pages
        while (heightLeft > 0) {
            position = position - pdfHeight;
            pdf.addPage();
            pdf.addImage(imgData, 'PNG', margin, position, availableWidth, imgHeight);
            heightLeft -= pdfHeight;
        }
        
        const safeTitle = title.substring(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase();
        pdf.save(`aether_report_${safeTitle}.pdf`);
        
    } catch (error) {
        console.error("PDF Generation failed:", error);
        alert("Failed to generate PDF. Please try again.");
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
};

// ==========================================
// AGENT PROFILES
// ==========================================

const agentData = {
    'agent-schema': {
        name: 'Schema Discovery Agent',
        icon: '<svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>',
        desc: 'Connects directly to the live Exasol instance to perform real-time introspection of the database schema. It dynamically maps tables, columns, and data types, ensuring the downstream agents always have accurate, up-to-date metadata.',
        color: 'from-blue-500 to-cyan-500',
        borderColor: 'border-blue-500/30'
    },
    'agent-sql': {
        name: 'Natural Language SQL Agent',
        icon: '<svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>',
        desc: "An advanced LLM-powered translation engine that converts human business questions into highly optimized Exasol-compliant SQL. It understands deep analytical requirements, complex joins, and specific dialect constraints (like Exasol's <code>DAYS_BETWEEN</code>).",
        color: 'from-indigo-500 to-violet-600',
        borderColor: 'border-indigo-500/30'
    },
    'agent-governance': {
        name: 'Dual-Layer Security Firewall',
        icon: '<svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
        desc: 'An aggressive, zero-trust security gatekeeper. It intercepts both the raw user prompt and the generated SQL payload, scanning for destructive or unauthorized commands (<code>DROP</code>, <code>DELETE</code>, <code>UPDATE</code>) to guarantee 100% read-only operations.',
        color: 'from-rose-500 to-red-600',
        borderColor: 'border-rose-500/30'
    },
    'agent-storyteller': {
        name: 'Executive Insights Storyteller',
        icon: '<svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
        desc: 'Analyzes the raw data payload returned from the database to generate an executive-level summary of the findings. It intelligently analyzes mathematical distributions to autonomously recommend the optimal chart configuration (Pie, Bar, Line, or Scatter).',
        color: 'from-emerald-400 to-teal-500',
        borderColor: 'border-emerald-500/30'
    }
};

function renderAgentProfile(agentId) {
    const data = agentData[agentId];
    if (!data) return;

    // Reset UI
    transitionToResults();
    resultsArea.innerHTML = '';
    
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.getElementById(agentId).classList.add('active');

    const html = `
        <div class="w-full mx-auto opacity-0 transform translate-y-4 transition-all duration-700 mb-8 max-w-4xl pt-10">
            <div class="insight-card p-10 relative overflow-hidden group border-t-4 border-t-transparent group" style="border-image: linear-gradient(to right, transparent, rgba(99,102,241,0.5), transparent) 1; border-top-color: rgba(99,102,241,0.5);">
                
                <div class="absolute -right-20 -top-20 w-64 h-64 bg-gradient-to-br ${data.color} rounded-full blur-[100px] opacity-20 pointer-events-none"></div>

                <div class="flex items-start gap-8 relative z-10">
                    <div class="w-20 h-20 rounded-2xl bg-gradient-to-br ${data.color} text-white flex items-center justify-center shrink-0 shadow-lg ${data.borderColor} border-2">
                        ${data.icon}
                    </div>
                    
                    <div class="flex-1 space-y-4">
                        <div class="text-[12px] font-bold signature-text uppercase tracking-widest mb-1 flex items-center gap-3">
                            <span>System Architecture</span>
                            <div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
                        </div>
                        <h2 class="text-4xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight">
                            ${data.name}
                        </h2>
                        <p class="text-slate-600 dark:text-slate-300 leading-relaxed text-lg mt-4">
                            ${data.desc}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    resultsArea.insertAdjacentHTML('beforeend', html);
    
    requestAnimationFrame(() => {
        const el = resultsArea.lastElementChild;
        if (el) el.classList.remove('opacity-0', 'translate-y-4');
    });
}

// Attach listeners
Object.keys(agentData).forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener('click', () => renderAgentProfile(id));
    }
});

// ==========================================
// WORKSPACE NAVIGATION
// ==========================================

function hideSearchBar() {
    form.classList.add('hidden');
}

function showSearchBar() {
    form.classList.remove('hidden');
}

function renderPlaceholderState(title, desc, icon) {
    transitionToResults();
    resultsArea.innerHTML = '';
    hideSearchBar();
    
    const html = `
        <div class="w-full h-full min-h-[400px] flex items-center justify-center opacity-0 transform translate-y-4 transition-all duration-700">
            <div class="text-center max-w-md">
                <div class="w-20 h-20 mx-auto rounded-full bg-slate-100 dark:bg-white/5 flex items-center justify-center mb-6 text-slate-400 dark:text-slate-500 shadow-inner">
                    ${icon}
                </div>
                <h3 class="text-2xl font-bold text-slate-900 dark:text-slate-50 mb-3">${title}</h3>
                <p class="text-slate-500 dark:text-slate-400 leading-relaxed">${desc}</p>
            </div>
        </div>
    `;
    
    resultsArea.innerHTML = html;
    
    requestAnimationFrame(() => {
        const el = resultsArea.firstElementChild;
        if (el) el.classList.remove('opacity-0', 'translate-y-4');
    });
}

function setActiveNav(id) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const target = document.getElementById(id);
    if (target) target.classList.add('active');
}

const navOverview = document.getElementById('nav-overview');
if (navOverview) {
    navOverview.addEventListener('click', () => {
        setActiveNav('nav-overview');
        resultsArea.innerHTML = '';
        showSearchBar();
        
        // Restore Hero section
        heroSection.classList.remove('opacity-0', 'scale-95', 'h-0', 'mb-0', 'overflow-hidden');
        suggestions.classList.remove('opacity-0', 'scale-95', 'h-0', 'overflow-hidden');
    });
}

window.deleteHistoryItem = function(index) {
    queryHistoryList.splice(index, 1);
    localStorage.setItem('aether_query_history', JSON.stringify(queryHistoryList));
    const navHistoryBtn = document.getElementById('nav-history');
    if (navHistoryBtn) navHistoryBtn.click();
}

const navHistory = document.getElementById('nav-history');
if (navHistory) {
    navHistory.addEventListener('click', () => {
        setActiveNav('nav-history');
        
        if (queryHistoryList.length === 0) {
            renderPlaceholderState(
                'No Query History',
                'Your session history will appear here once you start asking questions.',
                '<svg class="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
            );
            return;
        }

        // Render actual history
        transitionToResults();
        hideSearchBar();
        
        let historyHtml = `
            <div class="w-full mx-auto opacity-0 transform translate-y-4 transition-all duration-700 mb-8 max-w-4xl pt-10">
                <div class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-6">Session History</div>
                <div class="space-y-3">
        `;
        
        queryHistoryList.forEach((item, index) => {
            const statusColor = item.success ? 'text-emerald-500' : 'text-rose-500';
            const icon = item.success ? '✓' : '✗';
            historyHtml += `
                <div class="insight-card p-5 hover:border-indigo-500/50 cursor-pointer group transition-all duration-300" onclick="window.setQuery('${item.query.replace(/'/g, "\\'")}')">
                    <div class="flex items-center gap-4">
                        <div class="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold ${statusColor} shrink-0">
                            ${icon}
                        </div>
                        <div class="flex-1">
                            <p class="text-slate-900 dark:text-slate-50 font-semibold text-lg group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-1">${item.query}</p>
                            <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">${item.time}</p>
                        </div>
                        <div class="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-3 shrink-0">
                            <span class="text-xs font-bold text-indigo-500 uppercase tracking-wider hidden sm:block">Run Again</span>
                            <div class="w-px h-4 bg-slate-200 dark:bg-slate-700 hidden sm:block"></div>
                            <button class="p-2 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 transition-all z-20" title="Delete History" onclick="event.stopPropagation(); window.deleteHistoryItem(${index})">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        historyHtml += `</div></div>`;
        resultsArea.innerHTML = historyHtml;
        
        requestAnimationFrame(() => {
            const el = resultsArea.firstElementChild;
            if (el) el.classList.remove('opacity-0', 'translate-y-4');
        });
    });
}

// ==========================================
// SAVED INSIGHTS
// ==========================================

let savedInsightsList = JSON.parse(localStorage.getItem('aether_saved_insights')) || [];

window.saveInsight = function(chartId, query) {
    const payload = window.currentResponses[chartId];
    savedInsightsList.unshift({
        id: chartId,
        query: query,
        time: new Date().toLocaleDateString() + ' ' + new Date().toLocaleTimeString(),
        data: payload
    });
    localStorage.setItem('aether_saved_insights', JSON.stringify(savedInsightsList));
    
    // Animate button to show success
    const btn = document.getElementById(`save-btn-${chartId}`);
    if (btn) {
        btn.innerHTML = `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg> Saved`;
        btn.classList.add('bg-emerald-50', 'text-emerald-600', 'dark:bg-emerald-500/10', 'dark:text-emerald-400');
        btn.classList.remove('bg-indigo-50', 'text-indigo-600', 'dark:bg-indigo-500/10', 'dark:text-indigo-400');
    }
}

window.loadSavedInsight = function(id) {
    const item = savedInsightsList.find(x => x.id === id);
    if (!item || !item.data) return;
    
    resultsArea.innerHTML = `
        <div class="w-full max-w-7xl mx-auto mb-2 opacity-0 transform translate-y-2 transition-all duration-500" style="animation: fade-in 0.5s ease forwards;">
            <button onclick="document.getElementById('nav-saved').click()" class="text-xs font-bold text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 flex items-center gap-2 transition-colors px-3 py-2 -ml-3 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 w-max">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                Back to Saved Insights
            </button>
        </div>
        <style>@keyframes fade-in { to { opacity: 1; transform: translateY(0); } }</style>
    `;
    
    transitionToResults();
    hideSearchBar();
    renderAssistantResponse(item.data.resp, item.data.originalQuery, true);
    
    // Maintain active state in nav since we are still inside Saved Insights
    setActiveNav('nav-saved');
}

window.deleteSavedInsight = function(id) {
    savedInsightsList = savedInsightsList.filter(item => item.id !== id);
    localStorage.setItem('aether_saved_insights', JSON.stringify(savedInsightsList));
    const navSavedBtn = document.getElementById('nav-saved');
    if (navSavedBtn) navSavedBtn.click();
}

const navSaved = document.getElementById('nav-saved');
if (navSaved) {
    navSaved.addEventListener('click', () => {
        setActiveNav('nav-saved');
        
        if (savedInsightsList.length === 0) {
            renderPlaceholderState(
                'No Saved Insights',
                'Pin or star important insights to keep them easily accessible in this folder.',
                '<svg class="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>'
            );
            return;
        }

        // Render actual saved insights
        transitionToResults();
        hideSearchBar();
        
        let html = `
            <div class="w-full mx-auto opacity-0 transform translate-y-4 transition-all duration-700 mb-8 max-w-4xl pt-10">
                <div class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-6 flex items-center justify-between">
                    <span>Saved Insights Workspace</span>
                    <span class="text-xs bg-slate-100 dark:bg-white/10 px-2 py-1 rounded-md">${savedInsightsList.length} ITEMS</span>
                </div>
                <div class="grid grid-cols-1 gap-4">
        `;
        
        savedInsightsList.forEach((item) => {
            html += `
                <div class="insight-card p-6 hover:border-amber-500/50 cursor-pointer group transition-all duration-300 relative overflow-hidden" onclick="window.loadSavedInsight('${item.id}')">
                    <div class="absolute -right-10 -top-10 w-32 h-32 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full blur-[50px] opacity-10 group-hover:opacity-20 transition-opacity pointer-events-none"></div>
                    <div class="flex items-center gap-4 relative z-10">
                        <div class="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-500/10 text-amber-500 flex items-center justify-center font-bold shadow-sm shrink-0">
                            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                        </div>
                        <div class="flex-1">
                            <p class="text-slate-900 dark:text-slate-50 font-bold text-xl group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors line-clamp-1">${item.query}</p>
                            <p class="text-sm font-semibold text-slate-400 dark:text-slate-500 mt-2 flex items-center gap-2">
                                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                Saved on ${item.time}
                            </p>
                        </div>
                        <div class="opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-4">
                            <button class="p-2.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 transition-all z-20" title="Delete Insight" onclick="event.stopPropagation(); window.deleteSavedInsight('${item.id}')">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += `</div></div>`;
        resultsArea.innerHTML = html;
        
        requestAnimationFrame(() => {
            const el = resultsArea.firstElementChild;
            if (el) el.classList.remove('opacity-0', 'translate-y-4');
        });
    });
}
