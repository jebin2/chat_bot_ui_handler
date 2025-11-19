// ============================================
// CAPTION GENERATOR - CLIENT-SIDE LOGIC
// ============================================

// DOM ELEMENTS
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const previewContainer = document.getElementById('previewContainer');
const previewImage = document.getElementById('previewImage');
const removeImage = document.getElementById('removeImage');
const form = document.getElementById('captionForm');
const generateBtn = document.getElementById('generateBtn');

// Result States
const placeholder = document.getElementById('placeholder');
const loader = document.getElementById('loader');
const resultContent = document.getElementById('resultContent');
const resultText = document.getElementById('resultText');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');

// Action Buttons
const copyBtn = document.getElementById('copyBtn');
const newCaptionBtn = document.getElementById('newCaptionBtn');
const retryBtn = document.getElementById('retryBtn');

// ============================================
// FILE UPLOAD HANDLING
// ============================================

// Click to upload
uploadZone.addEventListener('click', () => {
    fileInput.click();
});

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop zone when dragging over
['dragenter', 'dragover'].forEach(eventName => {
    uploadZone.addEventListener(eventName, () => {
        uploadZone.classList.add('dragover');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadZone.addEventListener(eventName, () => {
        uploadZone.classList.remove('dragover');
    }, false);
});

// Handle dropped files
uploadZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        fileInput.files = files;
        handleFileSelect();
    }
});

// Handle file input change
fileInput.addEventListener('change', handleFileSelect);

// Handle file selection
function handleFileSelect() {
    const file = fileInput.files[0];
    
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showError('Please select a valid image file (JPG, PNG, GIF)');
        return;
    }
    
    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
        showError('File size must be less than 10MB');
        return;
    }
    
    // Read and preview the image
    const reader = new FileReader();
    
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewContainer.classList.add('active');
        uploadZone.style.display = 'none';
    };
    
    reader.onerror = () => {
        showError('Failed to read the image file');
    };
    
    reader.readAsDataURL(file);
}

// Remove image preview
removeImage.addEventListener('click', (e) => {
    e.stopPropagation();
    resetUpload();
});

function resetUpload() {
    fileInput.value = '';
    previewImage.src = '';
    previewContainer.classList.remove('active');
    uploadZone.style.display = 'block';
}

// ============================================
// FORM SUBMISSION
// ============================================

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate file is selected
    if (!fileInput.files || fileInput.files.length === 0) {
        showError('Please select an image first');
        return;
    }
    
    // Prepare form data
    const formData = new FormData(form);
    
    // Update UI to loading state
    setLoadingState();
    
    try {
        const response = await fetch('/generate-caption', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess(data.caption);
        } else {
            showError(data.detail || 'Failed to generate caption. Please try again.');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Network error. Please check your connection and try again.');
    }
});

// ============================================
// UI STATE MANAGEMENT
// ============================================

function setLoadingState() {
    // Hide all states
    placeholder.classList.add('hidden');
    resultContent.classList.remove('active');
    errorMessage.classList.remove('active');
    
    // Show loader
    loader.classList.add('active');
    
    // Disable button
    generateBtn.disabled = true;
}

function showSuccess(caption) {
    // Hide loader
    loader.classList.remove('active');
    
    // Show result
    resultText.textContent = caption;
    resultContent.classList.add('active');
    
    // Enable button
    generateBtn.disabled = false;
    
    // Smooth scroll to result on mobile
    if (window.innerWidth <= 968) {
        resultContent.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function showError(message) {
    // Hide loader and result
    loader.classList.remove('active');
    resultContent.classList.remove('active');
    placeholder.classList.add('hidden');
    
    // Show error
    errorText.textContent = message;
    errorMessage.classList.add('active');
    
    // Enable button
    generateBtn.disabled = false;
}

function resetResult() {
    // Hide all states
    loader.classList.remove('active');
    resultContent.classList.remove('active');
    errorMessage.classList.remove('active');
    
    // Show placeholder
    placeholder.classList.remove('hidden');
}

// ============================================
// ACTION BUTTONS
// ============================================

// Copy caption to clipboard
copyBtn.addEventListener('click', async () => {
    const text = resultText.textContent;
    
    try {
        await navigator.clipboard.writeText(text);
        
        // Visual feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<span class="btn-icon">✓</span> Copied!';
        copyBtn.style.background = 'var(--success)';
        copyBtn.style.color = 'white';
        copyBtn.style.borderColor = 'var(--success)';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
            copyBtn.style.color = '';
            copyBtn.style.borderColor = '';
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
        
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            copyBtn.innerHTML = '<span class="btn-icon">✓</span> Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = '<span class="btn-icon">📋</span> Copy';
            }, 2000);
        } catch (err) {
            alert('Failed to copy text. Please select and copy manually.');
        }
        
        document.body.removeChild(textArea);
    }
});

// Generate new caption with same image
newCaptionBtn.addEventListener('click', () => {
    if (fileInput.files && fileInput.files.length > 0) {
        form.dispatchEvent(new Event('submit'));
    } else {
        showError('Please upload an image first');
    }
});

// Retry after error
retryBtn.addEventListener('click', () => {
    errorMessage.classList.remove('active');
    placeholder.classList.remove('hidden');
});

// ============================================
// KEYBOARD SHORTCUTS
// ============================================

document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + V to paste image (if clipboard API is supported)
    if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
        if (document.activeElement === document.body || document.activeElement === uploadZone) {
            e.preventDefault();
            handlePaste(e);
        }
    }
    
    // Escape to close preview
    if (e.key === 'Escape' && previewContainer.classList.contains('active')) {
        resetUpload();
    }
});

async function handlePaste(e) {
    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    
    for (let item of items) {
        if (item.type.indexOf('image') !== -1) {
            const blob = item.getAsFile();
            
            // Create a new File object
            const file = new File([blob], 'pasted-image.png', { type: blob.type });
            
            // Create a DataTransfer object and add the file
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            
            // Set it to the file input
            fileInput.files = dataTransfer.files;
            
            // Handle the file
            handleFileSelect();
            
            break;
        }
    }
}

// ============================================
// MOBILE OPTIMIZATIONS
// ============================================

// Add touch feedback for mobile
if ('ontouchstart' in window) {
    const buttons = document.querySelectorAll('.btn, .btn-secondary');
    
    buttons.forEach(button => {
        button.addEventListener('touchstart', () => {
            button.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('touchend', () => {
            setTimeout(() => {
                button.style.transform = '';
            }, 100);
        });
    });
}

// Prevent zoom on double tap for iOS
let lastTouchEnd = 0;
document.addEventListener('touchend', (e) => {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) {
        e.preventDefault();
    }
    lastTouchEnd = now;
}, { passive: false });

// ============================================
// INITIALIZATION
// ============================================

console.log('🎨 Caption Generator initialized');
console.log('📱 Optimized for mobile and desktop');

// Check if running in development mode
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('🔧 Running in development mode');
}