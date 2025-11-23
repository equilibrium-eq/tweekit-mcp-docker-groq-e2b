// Demo Frontend Logic
let selectedFile = null;
let currentResult = null;

// File upload handling
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');

fileInput.addEventListener('change', handleFileSelect);

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
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';

    // Reset progress
    resetProgress();

    try {
        // Start timing
        const startTime = Date.now();

        // Step 1: Show E2B sandbox creation
        updateStep(1, 'active', 'Creating sandbox...');

        // Read file as base64
        const base64File = await fileToBase64(selectedFile);

        // Step 2: Show conversion
        updateStep(1, 'complete', 'Sandbox created');
        updateStep(2, 'active', 'Converting file...');

        // Get conversion mode from radio buttons
        const modeValue = document.querySelector('input[name="conversionMode"]:checked')?.value || 'auto';

        // Determine output format and conversion mode based on selection
        let outputFormat = 'pdf';
        let conversionMode = 'preview';  // Backend expects 'preview' or 'extract'
        let pageNumber = 1;

        if (modeValue === 'auto') {
            // Auto mode: Let AI decide (for now, default to preview)
            conversionMode = 'auto';
            outputFormat = 'pdf';  // Can be analyzed by AI
        } else if (modeValue === 'image') {
            // Web ready image mode
            const imageFormat = document.getElementById('imageFormat')?.value || 'png';
            const pageSelect = document.getElementById('pageNumber')?.value || '1';
            outputFormat = imageFormat;
            conversionMode = 'preview';
            pageNumber = pageSelect === 'all' ? 'all' : parseInt(pageSelect);
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
                use_vision: false,
                conversion_mode: conversionMode,
                page_number: pageNumber
            })
        });

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

        // Step 3: Show analysis
        updateStep(2, 'complete', `Converted in ${result.conversion.time}`);
        updateStep(3, 'active', 'Analyzing...');

        // Simulate small delay for visual effect
        await new Promise(resolve => setTimeout(resolve, 500));

        updateStep(3, 'complete', `Analyzed in ${result.analysis.time}`);

        // Show results
        setTimeout(() => {
            showResults(result);
        }, 500);

    } catch (error) {
        console.error('Processing error:', error);

        // If response has error_details, show collapsible details
        if (error.response && error.response.error_details) {
            showError(error.response.error, error.response.error_details);
        } else {
            showError(error.message || 'An unexpected error occurred');
        }
    }
}

function updateStep(stepNumber, status, timeText = '') {
    const step = document.getElementById(`step${stepNumber}`);
    const icon = document.getElementById(`icon${stepNumber}`);
    const time = document.getElementById(`time${stepNumber}`);

    // Remove all status classes
    step.classList.remove('pending', 'active', 'complete');
    icon.classList.remove('pending', 'active', 'complete');

    // Add new status
    step.classList.add(status);
    icon.classList.add(status);

    // Update icon
    if (status === 'active') {
        icon.innerHTML = '<span class="spinner"></span>';
    } else if (status === 'complete') {
        icon.textContent = '✓';
    } else {
        icon.textContent = '⏳';
    }

    // Update time text
    if (timeText) {
        time.textContent = timeText;
    }
}

function resetProgress() {
    for (let i = 1; i <= 3; i++) {
        updateStep(i, 'pending', '');
    }
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

    // Update metrics
    document.getElementById('conversionFormat').textContent =
        `${result.conversion.input_format} → ${result.conversion.output_format}`;
    document.getElementById('fileSize').textContent = result.conversion.size;
    document.getElementById('processingTime').textContent = `${result.total_time}s`;
    document.getElementById('totalTime').textContent = `Completed in ${result.total_time} seconds`;

    // Update AI analysis
    document.getElementById('aiModel').textContent = `Model: ${result.analysis.model}`;
    document.getElementById('aiAnalysis').textContent = result.analysis.summary;
}

function showError(message, details = null) {
    // Hide progress
    document.getElementById('progressSection').style.display = 'none';

    // Show error
    const errorDiv = document.getElementById('errorMessage');

    if (details) {
        // Create collapsible error with details
        errorDiv.innerHTML = `
            <div class="error-main">❌ ${message}</div>
            <details class="error-details">
                <summary>Technical Details ▸</summary>
                <pre>${details}</pre>
            </details>
        `;
    } else {
        errorDiv.textContent = `❌ ${message}`;
    }

    errorDiv.style.display = 'block';

    // Show upload section again
    setTimeout(() => {
        document.getElementById('uploadSection').style.display = 'block';
    }, 2000);
}

function reset() {
    selectedFile = null;
    fileInput.value = '';

    document.getElementById('uploadSection').style.display = 'block';
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';
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
    if (!currentResult) {
        alert('No file to download');
        return;
    }

    // For now, show an informative message
    // In a future version, we'll modify the backend to return the converted file
    const ext = currentResult.conversion.output_format.toLowerCase();
    const mode = currentResult.conversion.web_optimized ? 'preview' :
                 (ext === 'md' ? 'extract' : 'unknown');

    alert(`Download functionality coming soon!\n\nYour file was converted to: ${ext.toUpperCase()}\nMode: ${mode}\n\nNext version will include automatic file downloads.`);
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
