# Features Implementation Guide

## Overview
This document explains the 3 major features to complete the demo:
1. Conversion Mode Toggle (Web Preview vs Text Extraction)
2. Download Converted File Button
3. Conversion History (localStorage)

## Current Status
✅ Backend fully implemented (api.py updated)
✅ Frontend conversion_mode parameter added
⏳ Need to add: UI toggle, download button, history

## Implementation Steps

### 1. Add Conversion Mode Toggle to HTML

Add this after the upload area in `demo/static/index.html`:

```html
<!-- Conversion Mode Selection -->
<div class="conversion-mode" style="margin-top: 20px; text-align: center;">
    <label style="font-weight: 600; margin-bottom: 10px; display: block;">Conversion Mode:</label>
    <div style="display: inline-flex; gap: 20px; background: #f5f7fa; padding: 15px; border-radius: 8px;">
        <label style="cursor: pointer; display: flex; align-items: center; gap: 8px;">
            <input type="radio" name="conversionMode" value="preview" checked>
            <span>🖼️ Web Preview (PNG)</span>
        </label>
        <label style="cursor: pointer; display: flex; align-items: center; gap: 8px;">
            <input type="radio" name="conversionMode" value="extract">
            <span>📄 Text Extraction (Markdown)</span>
        </label>
    </div>
    <p style="font-size: 12px; color: #666; margin-top: 10px;">
        Preview mode converts first page to image. Extract mode converts full document to markdown.
    </p>
</div>
```

### 2. Add Download Button to Results

Update the action buttons section in `demo/static/index.html`:

```html
<div class="action-buttons">
    <button class="btn btn-primary" onclick="downloadFile()">📥 Download File</button>
    <button class="btn btn-secondary" onclick="reset()">Process Another File</button>
    <button class="btn btn-secondary" onclick="viewHistory()">📋 View History</button>
</div>
```

### 3. Add Download & History Functions to app.js

Add these functions at the end of `demo/static/app.js`:

```javascript
// Global variable to store current result
let currentResult = null;

// Update showResults to store the result
function showResults(result) {
    // Store result globally for download
    currentResult = result;

    // Save to history
    saveToHistory(result);

    // ... rest of existing showResults code ...
}

// Download converted file
function downloadFile() {
    if (!currentResult) {
        alert('No file to download');
        return;
    }

    // Get output format from result
    const ext = currentResult.conversion.output_format.toLowerCase();
    const filename = `converted_${Date.now()}.${ext}`;

    // Note: We don't have the actual file data in the response
    // Need to modify backend to return the converted file
    alert('Download feature requires backend modification to return converted file');
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
        alert('No conversion history yet');
        return;
    }

    // Simple modal/alert for now
    let historyText = 'Conversion History:\\n\\n';
    history.slice(0, 10).forEach((item, i) => {
        const date = new Date(item.timestamp).toLocaleString();
        historyText += `${i+1}. ${item.filename}\\n`;
        historyText += `   ${item.inputFormat} → ${item.outputFormat} (${item.size})\\n`;
        historyText += `   ${date} - ${item.time}s\\n\\n`;
    });

    alert(historyText);
}
```

### 4. Backend Modification for Download

To enable file downloads, modify `demo/api.py` to return the converted file in the response:

```python
# Add to ProcessResponse model
class ProcessResponse(BaseModel):
    success: bool
    conversion: Optional[dict] = None
    analysis: Optional[dict] = None
    converted_file_base64: Optional[str] = None  # NEW
    error: Optional[str] = None
    error_details: Optional[str] = None
    total_time: Optional[float] = None
```

Then in the conversion logic, extract and return the converted file data.

## Quick Test Plan

1. **Test Conversion Mode Toggle**
   - Upload PDF with "Web Preview" selected → Should get PNG
   - Upload same PDF with "Text Extraction" selected → Should get Markdown

2. **Test Download Button**
   - After conversion, click "Download File"
   - File should download with correct extension

3. **Test History**
   - Process 3-4 files
   - Click "View History" button
   - Should see list of past conversions
   - Reload page, history should persist

## Notes

- History is client-side only (localStorage)
- No server-side storage required
- Download requires backend to return the actual file data
- History limited to 50 items to avoid localStorage issues

## Priority Order

1. Add UI toggle (5 mins) - **CRITICAL**
2. Add history buttons (5 mins) - Easy
3. Implement history functions (10 mins) - Easy
4. Modify backend for download (20 mins) - **Complex**
5. Test everything (10 mins)

**Total: ~50 minutes of work**

## Current State

✅ Backend supports conversion_mode parameter
✅ Frontend sends conversion_mode parameter
⏳ Need UI elements (toggle, buttons)
⏳ Need history functions
⏳ Need download support in backend
