// Demo Frontend Logic (Updated for UI Upgrade)
let selectedFile = null;
let currentResult = null;
let currentVersion = null;
let selectedGroqModelLabel = null;

const DEFAULT_STEP_TITLES = {
    1: 'Creating E2B Sandbox',
    2: 'Converting via TweekIT MCP',
    3: 'Analyzing with Groq AI'
};

const WEB_PREVIEW_EXTENSIONS = new Set(['pdf', 'ppt', 'pptx']);
const TEXT_EXTRACTION_EXTENSIONS = new Set([
    'md', 'markdown', 'txt', 'rtf', 'rst', 'org', 'log', 'ini', 'cfg', 'conf',
    'json', 'yaml', 'yml', 'csv', 'tsv', 'html', 'htm', 'xml'
]);

function getFileExtension(filename) {
    if (!filename) return '';
    const lastDot = filename.lastIndexOf('.');
    if (lastDot === -1) return '';
    return filename.substring(lastDot + 1).toLowerCase();
}

function determineAutoStrategy(filename) {
    const ext = getFileExtension(filename);

    if (WEB_PREVIEW_EXTENSIONS.has(ext)) {
        return {
            outputFormat: 'png',
            conversionMode: 'preview',
            label: 'Web preview (PNG)',
            description: 'Web preview (PNG first page)',
            pageNumber: 1
        };
    }

    if (TEXT_EXTRACTION_EXTENSIONS.has(ext)) {
        return {
            outputFormat: 'md',
            conversionMode: 'extract',
            label: 'Markdown extraction',
            description: 'Markdown extraction for AI ingestion',
            pageNumber: 1
        };
    }

    return {
        outputFormat: 'pdf',
        conversionMode: 'auto',
        label: 'AI normalization (PDF)',
        description: 'AI-optimized normalization',
        pageNumber: 1
    };
}

function setStepTitle(stepNumber, title) {
    const titleElement = document.querySelector(`#step${stepNumber} .step-title`);
    if (titleElement && title) {
        titleElement.textContent = title;
    }
}

function resetStepTitles() {
    Object.entries(DEFAULT_STEP_TITLES).forEach(([step, title]) => {
        setStepTitle(Number(step), title);
    });
}

// Menu Handling
function toggleMenu() {
    const menu = document.getElementById('navMenu');
    menu.classList.toggle('active');
}

function closeMenu() {
    const menu = document.getElementById('navMenu');
    menu.classList.remove('active');
}

// Close menu when clicking outside
document.addEventListener('click', function (event) {
    const menu = document.getElementById('navMenu');
    const hamburger = document.querySelector('.hamburger');

    if (menu && hamburger && !menu.contains(event.target) && !hamburger.contains(event.target)) {
        menu.classList.remove('active');
    }
});

// Close menu on escape key
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        const menu = document.getElementById('navMenu');
        if (menu) menu.classList.remove('active');
    }
});

// Version checking
async function checkForUpdates() {
    try {
        const response = await fetch('/version');
        const versionInfo = await response.json();

        if (!currentVersion) {
            // First load - store version
            currentVersion = versionInfo.version;
            localStorage.setItem('appVersion', versionInfo.version);
        } else if (currentVersion !== versionInfo.version) {
            // Version changed - show update notification
            showUpdateNotification(versionInfo.version);
        }
    } catch (error) {
        console.error('Failed to check version:', error);
    }
}

function showUpdateNotification(newVersion) {
    const existingBanner = document.getElementById('updateBanner');
    if (existingBanner) return; // Already showing

    const banner = document.createElement('div');
    banner.id = 'updateBanner';
    banner.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        text-align: center;
        z-index: 10000;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        animation: slideDown 0.3s ease-out;
    `;

    banner.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <span style="font-weight: 600;">🎉 New version available (v${newVersion})!</span>
            <button onclick="hardRefresh()" style="
                background: white;
                color: #667eea;
                border: none;
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                Refresh Now
            </button>
            <button onclick="document.getElementById('updateBanner').remove()" style="
                background: transparent;
                color: white;
                border: 1px solid white;
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: 600;
                cursor: pointer;
            ">
                Later
            </button>
        </div>
    `;

    document.body.prepend(banner);

    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from { transform: translateY(-100%); }
            to { transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);
}

function hardRefresh() {
    // Clear all caches and force reload
    if (caches) {
        caches.keys().then(names => {
            names.forEach(name => caches.delete(name));
        });
    }
    localStorage.setItem('appVersion', 'reloading');
    window.location.reload(true);
}

// Check for updates on load and every 5 minutes
checkForUpdates();
setInterval(checkForUpdates, 5 * 60 * 1000);
setInterval(checkForUpdates, 5 * 60 * 1000);

// File upload handling
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');

if (fileInput) {
    fileInput.addEventListener('change', handleFileSelect);
}

if (uploadArea) {
    // Click anywhere in upload area to trigger file selection
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop
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

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    selectedFile = file;
    processFile();
}

async function processFile() {
    if (!selectedFile) return;

    // Hide upload section
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';

    // Smooth scroll to progress section
    setTimeout(() => {
        document.getElementById('progressSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    // Reset progress
    resetProgress();

    const modeValue = document.querySelector('input[name="conversionMode"]:checked')?.value || 'auto';
    const optionTitle = document.querySelector('.option-card.selected .option-title')?.textContent?.trim() || 'Auto TweekIT';
    const groqSelect = document.getElementById('groqModel');
    const groqModelValue = groqSelect?.value || 'llama-3.2-90b-vision-preview';
    const groqModelLabel = groqSelect?.selectedOptions?.[0]?.text?.trim() || groqModelValue;

    selectedGroqModelLabel = groqModelLabel;
    const aiModelBadge = document.getElementById('aiModel');
    if (aiModelBadge) {
        aiModelBadge.textContent = `Model: ${selectedGroqModelLabel}`;
    }
    setStepTitle(3, `Groq Analysis – ${selectedGroqModelLabel}`);

    let autoStrategy = null;
    if (modeValue === 'auto') {
        if (selectedFile) {
            autoStrategy = determineAutoStrategy(selectedFile.name);
        }
        const autoLabel = autoStrategy?.label || 'AI optimization';
        setStepTitle(1, 'Selecting Best Workflow');
        setStepTitle(2, `TweekIT Conversion – ${autoLabel}`);
        updateStep(1, 'active', 'Analyzing file to choose best workflow...');
    } else {
        setStepTitle(2, `TweekIT Conversion – ${optionTitle}`);
        updateStep(1, 'active', 'Preparing file...');
    }

    // Timing phases
    const timings = {
        buttonPressed: Date.now(),
        uploadStart: null,
        uploadComplete: null,
        processingStart: null,
        processingComplete: null,
        analysisStart: null,
        analysisComplete: null
    };

    try {
        // Step 1: Show E2B sandbox creation and file preparation
        timings.uploadStart = Date.now();

        // Read file as base64
        const base64File = await fileToBase64(selectedFile);

        timings.uploadComplete = Date.now();
        const uploadTime = ((timings.uploadComplete - timings.uploadStart) / 1000).toFixed(2);
        if (modeValue === 'auto') {
            const autoLabel = autoStrategy?.label || 'AI optimization';
            updateStep(1, 'complete', `Workflow selected (${uploadTime}s): ${autoLabel}`);
        } else {
            updateStep(1, 'complete', `File ready (${uploadTime}s)`);
        }

        // Step 2: Show conversion
        const conversionLabel = modeValue === 'auto'
            ? (autoStrategy?.description || 'AI optimization')
            : optionTitle;
        updateStep(2, 'active', `Sending to TweekIT – ${conversionLabel}...`);

        timings.processingStart = Date.now();

        // Determine output format and conversion mode based on selection
        let outputFormat = 'pdf';
        let conversionMode = 'preview';  // Backend expects 'preview' or 'extract'
        let pageNumber = 1;

        if (modeValue === 'auto') {
            if (autoStrategy) {
                outputFormat = autoStrategy.outputFormat;
                conversionMode = autoStrategy.conversionMode;
                pageNumber = autoStrategy.pageNumber ?? 1;
            } else {
                conversionMode = 'auto';
                outputFormat = 'pdf';  // Fallback
            }
        } else if (modeValue === 'image') {
            // Web ready image mode - save as desired output format
            const imageFormat = document.getElementById('imageFormat')?.value || 'png';
            const pageInput = document.getElementById('pageNumber')?.value || '1';
            outputFormat = imageFormat;
            conversionMode = 'preview';
            pageNumber = parseInt(pageInput) || 1;  // Default to page 1 if invalid
        } else if (modeValue === 'extract') {
            // Text extraction mode
            outputFormat = 'md';
            conversionMode = 'extract';
        } else if (modeValue === 'pdf') {
            // PDF output mode
            outputFormat = 'pdf';
            conversionMode = 'extract';  // Full document
        }

        // Call API
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_base64: base64File.split(',')[1], // Remove data URL prefix
                filename: selectedFile.name,
                output_format: outputFormat,
                groq_model: groqModelValue,
                conversion_mode: conversionMode,
                page_number: pageNumber
            })
        });

        timings.processingComplete = Date.now();

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();

        if (!result.success) {
            // Create error object with details for display
            const error = new Error(result.error || 'Processing failed');
            error.response = result;  // Attach full response for error_details
            throw error;
        }

        // Calculate processing time
        const processingTime = ((timings.processingComplete - timings.processingStart) / 1000).toFixed(2);
        updateStep(2, 'complete', `${conversionLabel} (${processingTime}s)`);

        // Step 3: Show analysis
        const groqLabelForSteps = selectedGroqModelLabel || 'Groq AI';
        updateStep(3, 'active', `Analyzing with ${groqLabelForSteps}...`);

        timings.analysisStart = Date.now();

        // Simulate small delay for visual effect
        await new Promise(resolve => setTimeout(resolve, 500));

        timings.analysisComplete = Date.now();
        const analysisTime = ((timings.analysisComplete - timings.analysisStart) / 1000).toFixed(2);

        updateStep(3, 'complete', `${groqLabelForSteps} (${analysisTime}s)`);

        // Calculate total time from button press
        const totalTime = ((timings.analysisComplete - timings.buttonPressed) / 1000).toFixed(2);

        // Add timing breakdown to result
        result.timingBreakdown = {
            upload: uploadTime,
            processing: processingTime,
            analysis: analysisTime,
            total: totalTime
        };

        // Show results
        setTimeout(() => {
            showResults(result);
        }, 500);
    } catch (error) {
        console.error('Processing error:', error);

        // If response has error_details, show collapsible details
        if (error.response && error.response.error_details) {
            showError(error.response.error, error.response.error_details, error.response);
        } else {
            showError(error.message || 'An unexpected error occurred', null, error.response);
        }
    }
}

// Secure Download Timer Logic
let downloadTimerInterval = null;
const DOWNLOAD_TIMEOUT_SECONDS = 30;
let isMuted = false;

function toggleMute() {
    isMuted = !isMuted;
    const btn = document.getElementById('muteBtn');
    if (btn) {
        btn.textContent = isMuted ? '🔇' : '🔊';
        btn.style.opacity = isMuted ? '0.7' : '1';
    }
}

// Simple "tick" sound (base64 encoded short beep)
const TICK_SOUND = "data:audio/wav;base64,UklGRl9vT1BXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU"; // Placeholder, will use AudioContext for better sound

function playTickSound() {
    if (isMuted) return;
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            const ctx = new AudioContext();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(800, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(400, ctx.currentTime + 0.1);

            gain.gain.setValueAtTime(0.1, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start();
            osc.stop(ctx.currentTime + 0.1);
        }
    } catch (e) {
        console.error("Audio play failed", e);
    }
}

function playPurgeSound() {
    if (isMuted) return;
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            const ctx = new AudioContext();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            // Bell-like tone (higher pitch, long decay)
            osc.type = 'sine';
            osc.frequency.setValueAtTime(1200, ctx.currentTime);

            gain.gain.setValueAtTime(0, ctx.currentTime);
            gain.gain.linearRampToValueAtTime(0.3, ctx.currentTime + 0.01); // Sharp attack
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5); // Long decay

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start();
            osc.stop(ctx.currentTime + 1.5);
        }
    } catch (e) {
        console.error("Audio play failed", e);
    }
}

function startDownloadTimer() {
    const timerEl = document.getElementById('downloadTimer');
    if (!timerEl) return;

    // Reset state
    clearInterval(downloadTimerInterval);
    timerEl.style.display = 'block';
    timerEl.classList.remove('urgent');

    let timeLeft = DOWNLOAD_TIMEOUT_SECONDS;

    function updateDisplay() {
        timerEl.textContent = `⚠️ Secure Download: ${timeLeft}s remaining`;

        if (timeLeft <= 10) {
            timerEl.classList.add('urgent');
        }

        if (timeLeft <= 5 && timeLeft > 0) {
            playTickSound();
        }

        if (timeLeft <= 0) {
            clearInterval(downloadTimerInterval);
            playPurgeSound(); // Play "ping" on purge
            purgeFile();

            // Scroll to top after purge (wait for sound to start)
            setTimeout(() => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }, 1000);
        }

        timeLeft--;
    }

    // Initial call
    updateDisplay();

    // Start interval
    downloadTimerInterval = setInterval(updateDisplay, 1000);
}

function purgeFile() {
    // Clear data
    if (currentResult) {
        currentResult.converted_file = null;
    }

    // Update UI
    const timerEl = document.getElementById('downloadTimer');
    if (timerEl) {
        timerEl.textContent = "🔒 File Purged from Memory";
        timerEl.style.color = "#9ca3af";
        timerEl.style.borderColor = "#4b5563";
        timerEl.style.background = "rgba(75, 85, 99, 0.1)";
        timerEl.classList.remove('urgent');
    }

    // Disable download buttons
    const downloadButtons = document.querySelectorAll('#resultsSection button.btn-primary');
    downloadButtons.forEach(btn => {
        if (btn.textContent.includes('Download')) {
            btn.disabled = true;
            btn.classList.add('purged');
            btn.innerHTML = '🔒 Download Unavailable (Purged)';
        }
    });

    // Show notification
    showPurgeNotification();
}

function showResults(result) {
    // Store result globally for download
    currentResult = result;

    // Save to history
    saveToHistory(result);

    // Hide progress
    document.getElementById('progressSection').style.display = 'none';

    // Show results
    document.getElementById('resultsSection').style.display = 'block';

    // Reset download button state
    const downloadButtons = document.querySelectorAll('#resultsSection button.btn-primary');
    downloadButtons.forEach(btn => {
        btn.disabled = false;
        btn.classList.remove('purged');
        btn.innerHTML = '📥 Download File';
    });

    // Update metrics
    document.getElementById('conversionFormat').textContent =
        `${result.conversion.input_format} → ${result.conversion.output_format}`;
    document.getElementById('fileSize').textContent = result.conversion.size;

    // Update timing with detailed breakdown
    if (result.timingBreakdown) {
        const breakdown = result.timingBreakdown;
        document.getElementById('processingTime').textContent = `${breakdown.total}s`;
        document.getElementById('totalTime').innerHTML = `
            <strong>Completed in ${breakdown.total}s</strong><br>
            <span style="font-size: 13px; opacity: 0.8; line-height: 1.6;">
                ⏱️ File prep: ${breakdown.upload}s<br>
                🔄 TweekIT conversion: ${breakdown.processing}s<br>
                🤖 AI analysis: ${breakdown.analysis}s
            </span>
        `;
    } else {
        // Fallback to old format
        document.getElementById('processingTime').textContent = `${result.total_time}s`;
        document.getElementById('totalTime').textContent = `Completed in ${result.total_time} seconds`;
    }

    // Update AI analysis
    const analysisModel = result.analysis?.model;
    let modelDisplay = analysisModel || selectedGroqModelLabel || 'Groq Model';
    if (analysisModel && selectedGroqModelLabel && analysisModel !== selectedGroqModelLabel) {
        modelDisplay = `${analysisModel} (${selectedGroqModelLabel})`;
    }
    document.getElementById('aiModel').textContent = `Model: ${modelDisplay}`;
    document.getElementById('aiAnalysis').textContent = result.analysis?.summary || 'Analysis unavailable.';

    // Scroll to results section immediately
    setTimeout(() => {
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Start the secure timer
        startDownloadTimer();
    }, 100);
}

function showError(message, details = null, meta = null) {
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('uploadSection').style.display = 'grid';

    // Scroll back to upload area
    setTimeout(() => {
        document.getElementById('uploadSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    // Show error
    const errorDiv = document.getElementById('errorMessage');

    let hintHtml = '';
    if (meta && meta.error_code === 'unsupported_format') {
        hintHtml = `
            <div style="margin-top: 12px; font-size: 13px; color: rgba(226, 232, 240, 0.75);">
                We logged this format so the team can add support. Try Auto TweekIT or pick another output for now.
            </div>
        `;
    }

    if (details) {
        // Create collapsible error with details
        errorDiv.innerHTML = `
            <div class="error-main">❌ ${message}</div>
            <details class="error-details">
                <summary>Technical Details ▸</summary>
                <pre>${details}</pre>
            </details>
            ${hintHtml}
        `;
    } else {
        errorDiv.innerHTML = `❌ ${message}${hintHtml}`;
    }

    errorDiv.style.display = 'block';
}

function reset() {
    playPurgeSound(); // Play ping on reset

    // Security: Strictly purge data
    if (currentResult) {
        currentResult = null;
    }
    if (downloadTimerInterval) {
        clearInterval(downloadTimerInterval);
    }

    selectedFile = null;
    selectedGroqModelLabel = null;
    fileInput.value = '';

    document.getElementById('uploadSection').style.display = 'grid';
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';

    // Scroll to top of page
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// Download converted file
function downloadFile() {
    if (!currentResult || !currentResult.converted_file) {
        alert('No file available to download');
        return;
    }

    try {
        // Get file details
        const ext = currentResult.conversion.output_format.toLowerCase();
        const inputExt = currentResult.conversion.input_format.toLowerCase();
        const originalFilename = selectedFile?.name || 'converted_file';
        const baseFilename = originalFilename.substring(0, originalFilename.lastIndexOf('.')) || 'converted_file';

        // Create download filename
        const downloadFilename = `${baseFilename}.${ext}`;

        // Convert base64 to blob
        const base64Data = currentResult.converted_file;
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        // Determine MIME type
        const mimeTypes = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'md': 'text/markdown',
            'txt': 'text/plain',
            'html': 'text/html'
        };
        const mimeType = mimeTypes[ext] || 'application/octet-stream';

        // Create blob
        const blob = new Blob([bytes], { type: mimeType });

        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = downloadFilename;
        document.body.appendChild(a);
        a.click();

        // Cleanup
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Clear the file data to prevent re-download
        currentResult.converted_file = null;

        // Show purge notification
        showPurgeNotification();

        // Disable download button after purge - find all download buttons in results section
        const downloadButtons = document.querySelectorAll('#resultsSection button.btn-primary');
        downloadButtons.forEach(btn => {
            if (btn.textContent.includes('Download')) {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
                btn.innerHTML = '✓ Downloaded & Purged';
            }
        });

    } catch (error) {
        console.error('Download error:', error);
        alert('Failed to download file. Please try converting again.');
    }
}

// Show purge notification after download
function showPurgeNotification() {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        font-size: 14px;
        font-weight: 500;
        z-index: 10000;
        max-width: 350px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: slideIn 0.3s ease-out;
    `;

    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 20px;">🗑️</span>
            <div>
                <div style="font-weight: 600; margin-bottom: 4px;">File Purged</div>
                <div style="font-size: 13px; opacity: 0.9;">All files and artifacts from this tweekit have been purged from headless TweekIT Tier-1 Node.</div>
            </div>
        </div>
    `;

    document.body.appendChild(notification);

    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Add animations to document head
if (!document.querySelector('#purge-animations')) {
    const style = document.createElement('style');
    style.id = 'purge-animations';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Save conversion to history (localStorage)
function saveToHistory(result) {
    const historyItem = {
        id: Date.now(),
        filename: selectedFile?.name || 'unknown',
        inputFormat: result.conversion.input_format,
        outputFormat: result.conversion.output_format,
        size: result.conversion.size,
        time: result.total_time,
        timestamp: new Date().toISOString(),
        mode: result.conversion.web_optimized ? 'preview' : 'extract'
    };

    // Get existing history
    const history = JSON.parse(localStorage.getItem('conversionHistory') || '[]');

    // Add new item (keep last 50)
    history.unshift(historyItem);
    if (history.length > 50) history.pop();

    // Save back
    localStorage.setItem('conversionHistory', JSON.stringify(history));
}

// View conversion history
function viewHistory() {
    const history = JSON.parse(localStorage.getItem('conversionHistory') || '[]');

    if (history.length === 0) {
        alert('No conversion history yet.\n\nProcess some files to build your conversion history!');
        return;
    }

    // Create a formatted history display
    let historyText = '📋 CONVERSION HISTORY\n';
    historyText += '═'.repeat(50) + '\n\n';

    history.slice(0, 10).forEach((item, i) => {
        const date = new Date(item.timestamp).toLocaleString();
        historyText += `${i + 1}. ${item.filename}\n`;
        historyText += `   ${item.inputFormat} → ${item.outputFormat} (${item.size})\n`;
        historyText += `   ${item.mode} mode | ${item.time}s | ${date}\n\n`;
    });

    if (history.length > 10) {
        historyText += `\n... and ${history.length - 10} more conversions`;
    }

    alert(historyText);
}

// Handle TweekIT button click for manual mode
async function handleTweekITConversion() {
    // Get selected conversion mode
    const selectedMode = document.querySelector('input[name="conversionMode"]:checked')?.value;

    if (!selectedMode) {
        alert('Please select a conversion mode (Auto TweekIT or Manual Mode option)');
        return;
    }

    // Check if URL is provided
    const urlInput = document.getElementById('fileUrl')?.value?.trim();

    if (urlInput) {
        // Validate URL format
        try {
            new URL(urlInput);
        } catch (e) {
            alert('Please enter a valid URL (e.g., https://example.com/document.pdf)');
            document.getElementById('fileUrl')?.focus();
            return;
        }

        // Fetch file from URL and process
        try {
            const response = await fetch(urlInput);
            if (!response.ok) {
                throw new Error(`Failed to fetch file: ${response.status} ${response.statusText}`);
            }

            // Get filename from URL or Content-Disposition header
            let filename = urlInput.split('/').pop().split('?')[0] || 'downloaded-file';
            const contentDisposition = response.headers.get('content-disposition');
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch) filename = filenameMatch[1];
            }

            // Convert to blob and create File object
            const blob = await response.blob();
            selectedFile = new File([blob], filename, { type: blob.type });

            // Process the file
            processFile();
        } catch (error) {
            alert(`Failed to fetch file from URL: ${error.message}`);
            console.error('URL fetch error:', error);
        }
    } else {
        // For file-based modes, ensure a file is selected
        if (!selectedFile) {
            alert('Please select a file to process or provide a URL');
            fileInput.click();
            return;
        }

        // Process file normally
        processFile();
    }
}

// Monitor URL input to change button text and behavior dynamically
document.addEventListener('DOMContentLoaded', function () {
    const fileUrlInput = document.getElementById('fileUrl');
    const selectFileBtn = document.getElementById('selectFileBtn');
    const fileInput = document.getElementById('fileInput');

    if (fileUrlInput && selectFileBtn && fileInput) {
        // Function to update button based on URL input
        function updateButton() {
            if (fileUrlInput.value.trim()) {
                selectFileBtn.textContent = 'Convert from URL';
                selectFileBtn.onclick = function (e) {
                    e.stopPropagation();
                    handleTweekITConversion();
                };
            } else {
                selectFileBtn.textContent = 'Select File';
                selectFileBtn.onclick = function (e) {
                    e.stopPropagation();
                    fileInput.click();
                };
            }
        }

        // Set initial state
        updateButton();

        // Update on input change
        fileUrlInput.addEventListener('input', updateButton);
    }
});

// Initial check - test API health
fetch('/health')
    .then(r => r.json())
    .then(data => {
        console.log('API Health:', data);
        if (!data.has_tweekit_creds || !data.has_e2b_key || !data.has_groq_key) {
            console.warn('Warning: Some API keys are missing');
        }
    })
    .catch(err => console.error('API health check failed:', err));
