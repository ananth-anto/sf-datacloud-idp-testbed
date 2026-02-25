// Create this file at /Users/ananth.anto/CascadeProjects/hello-curl/static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('extractForm');
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.querySelector('.file-name');
    const imagePreview = document.getElementById('imagePreview');
    const previewSection = document.querySelector('.preview-section');
    const loadingIndicator = document.getElementById('loading');
    const resultSection = document.getElementById('result');
    const resultContent = document.getElementById('resultContent');
    const resultViewToggle = document.getElementById('resultViewToggle');
    const developerReference = document.getElementById('developerReference');
    
    // Developer reference: toggle expand/collapse once at load (works after content is filled)
    developerReference.addEventListener('click', function(e) {
        if (!e.target.classList.contains('developer-reference-toggle')) return;
        const content = developerReference.querySelector('.developer-reference-content');
        if (!content) return;
        const isHidden = content.hidden;
        content.hidden = !isHidden;
        e.target.setAttribute('aria-expanded', String(!isHidden));
        e.target.textContent = isHidden ? 'Hide API request (Developer reference)' : 'Show API request (Developer reference)';
    });
    
    // Authentication elements
    const authStatus = document.getElementById('auth-status');
    const authIcon = document.getElementById('auth-icon');
    const authMessage = document.getElementById('auth-message');
    const authButton = document.getElementById('auth-button');
    const analyzeBtn = document.getElementById('analyze-btn');
    const orgModalOverlay = document.getElementById('org-modal-overlay');
    const orgConfigForm = document.getElementById('org-config-form');
    const orgConfigError = document.getElementById('org-config-error');
    const changeOrgLink = document.getElementById('change-org-link');

    // Check authentication status on page load
    checkAuthStatus();

    // Org config form: save org details (per-user session)
    if (orgConfigForm) {
        orgConfigForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            if (orgConfigError) orgConfigError.style.display = 'none';
            const btn = document.getElementById('org-save-btn');
            if (btn) btn.disabled = true;
            try {
                const loginUrl = document.getElementById('org-login-url').value.trim();
                const clientId = document.getElementById('org-client-id').value.trim();
                const clientSecret = document.getElementById('org-client-secret').value.trim();
                const res = await fetch('/api/org-config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ loginUrl, clientId, clientSecret })
                });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) {
                    if (orgConfigError) {
                        orgConfigError.textContent = data.error || 'Failed to save org configuration';
                        orgConfigError.style.display = 'block';
                    }
                    return;
                }
                if (orgModalOverlay) orgModalOverlay.classList.add('hidden');
                await checkAuthStatus();
            } finally {
                if (btn) btn.disabled = false;
            }
        });
    }

    // Change org: clear session and show org setup again
    if (changeOrgLink) {
        changeOrgLink.addEventListener('click', async function(e) {
            e.preventDefault();
            try {
                await fetch('/api/org-logout', { method: 'POST' });
                if (orgModalOverlay) orgModalOverlay.classList.remove('hidden');
                await checkAuthStatus();
            } catch (err) {
                console.error('Failed to clear org', err);
            }
        });
    }

    // Update file name display when file is selected
    fileInput.addEventListener('change', function() {
        const fileName = this.files[0]?.name || 'No file chosen';
        fileNameDisplay.textContent = fileName;
        
        // Show page range section only for PDFs
        const pageRangeSection = document.getElementById('page-range-section');
        const file = this.files[0];
        
        if (file && file.type === 'application/pdf') {
            pageRangeSection.style.display = 'block';
        } else {
            pageRangeSection.style.display = 'none';
            // Clear page range values when switching to non-PDF
            document.getElementById('total-pages').value = '';
            document.getElementById('page-range').value = '';
            // Clear any error messages
            const errorDiv = document.getElementById('page-range-error');
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
        }

        // Show preview for images only
        if (this.files && this.files[0]) {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    previewSection.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                // Hide preview for non-image files
                previewSection.style.display = 'none';
            }
        }
    });

    // Authentication functions
    async function checkAuthStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            if (data.needs_org_config) {
                if (orgModalOverlay) orgModalOverlay.classList.remove('hidden');
                authIcon.textContent = '⏳';
                authMessage.textContent = 'Enter your Salesforce org details to get started.';
                authStatus.className = 'auth-status not-authenticated';
                authButton.style.display = 'none';
                if (changeOrgLink) changeOrgLink.style.display = 'none';
                analyzeBtn.disabled = true;
                return;
            }

            if (data.authenticated) {
                if (orgModalOverlay) orgModalOverlay.classList.add('hidden');
                authIcon.textContent = '✅';
                authMessage.textContent = 'Authenticated with Salesforce';
                authStatus.className = 'auth-status authenticated';
                authButton.style.display = 'none';
                if (changeOrgLink) changeOrgLink.style.display = 'inline';
                analyzeBtn.disabled = false;
            } else {
                if (orgModalOverlay) orgModalOverlay.classList.add('hidden');
                authIcon.textContent = '❌';
                authMessage.textContent = 'Not authenticated. Please authenticate to use the application.';
                authStatus.className = 'auth-status not-authenticated';
                authButton.style.display = 'block';
                if (changeOrgLink) changeOrgLink.style.display = 'inline';
                analyzeBtn.disabled = true;
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
            authIcon.textContent = '❌';
            authMessage.textContent = 'Error checking authentication status';
            authStatus.className = 'auth-status not-authenticated';
            authButton.style.display = 'block';
            if (changeOrgLink) changeOrgLink.style.display = 'none';
            analyzeBtn.disabled = true;
        }
    }

    // PKCE helper functions
    function base64urlencode(str) {
        return btoa(String.fromCharCode.apply(null, new Uint8Array(str)))
            .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    async function sha256(plain) {
        const encoder = new TextEncoder();
        const data = encoder.encode(plain);
        const hash = await window.crypto.subtle.digest('SHA-256', data);
        return base64urlencode(hash);
    }

    async function authenticateWithSalesforce() {
        try {
            const response = await fetch('/api/auth-info');
            const data = await response.json();
            
            if (!data.loginUrl || !data.clientId) {
                alert('Salesforce configuration missing on server');
                return;
            }

            // PKCE: generate code_verifier and code_challenge
            const codeVerifier = Array.from(crypto.getRandomValues(new Uint8Array(32)))
                .map(b => ('0' + b.toString(16)).slice(-2)).join('');
            const codeChallenge = await sha256(codeVerifier);

            // Store code_verifier in sessionStorage
            sessionStorage.setItem('pkce_code_verifier', codeVerifier);

            const redirectUri = encodeURIComponent(`${window.location.origin}/auth/callback`);
            const authUrl = `https://${data.loginUrl}/services/oauth2/authorize?response_type=code&client_id=${data.clientId}&redirect_uri=${redirectUri}&scope=api%20cdp_query_api%20cdp_profile_api&code_challenge=${codeChallenge}&code_challenge_method=S256`;

            window.location.href = authUrl;
        } catch (error) {
            alert('Failed to initiate authentication: ' + error.message);
        }
    }

    // Add event listener for authentication button
    authButton.addEventListener('click', authenticateWithSalesforce);

    // Function to decode HTML entities
    function decodeHtmlEntities(str) {
        const textarea = document.createElement('textarea');
        textarea.innerHTML = str;
        return textarea.value;
    }

    // Function to validate page range
    function validatePageRange() {
        const pageRangeInput = document.getElementById('page-range');
        const totalPagesInput = document.getElementById('total-pages');
        const errorDiv = document.getElementById('page-range-error');
        
        const pageRange = pageRangeInput.value.trim();
        const totalPages = parseInt(totalPagesInput.value);
        
        // Clear previous errors
        errorDiv.style.display = 'none';
        errorDiv.textContent = '';
        
        // If page range is empty, it's valid (means all pages)
        if (!pageRange) {
            return { valid: true };
        }
        
        // Check format: must be "number-number"
        const rangePattern = /^(\d+)-(\d+)$/;
        const match = pageRange.match(rangePattern);
        
        if (!match) {
            errorDiv.textContent = 'Invalid format. Use format: startPage-endPage (e.g., 1-5)';
            errorDiv.style.display = 'block';
            return { valid: false };
        }
        
        const startPage = parseInt(match[1]);
        const endPage = parseInt(match[2]);
        
        // Validation: start must be less than or equal to end
        if (startPage > endPage) {
            errorDiv.textContent = 'Start page must be less than or equal to end page';
            errorDiv.style.display = 'block';
            return { valid: false };
        }
        
        // Validation: pages must be at least 1 (1-indexed)
        if (startPage < 1 || endPage < 1) {
            errorDiv.textContent = 'Page numbers must be at least 1';
            errorDiv.style.display = 'block';
            return { valid: false };
        }
        
        // If total pages is provided, validate against bounds
        if (totalPages && !isNaN(totalPages)) {
            if (startPage > totalPages || endPage > totalPages) {
                errorDiv.textContent = `Page range exceeds total pages (${totalPages})`;
                errorDiv.style.display = 'block';
                return { valid: false };
            }
        }
        
        return { valid: true, startPage, endPage };
    }

    // Function to get confidence level based on score
    function getConfidenceLevel(score) {
        if (score >= 0.8) return 'high';
        if (score >= 0.5) return 'medium';
        return 'low';
    }

    // Function to render data as formatted tree (with optional confidence badges)
    function renderFormattedTree(data, container, options = {}) {
        const showConfidenceBadges = options.showConfidenceBadges !== false;
        container.innerHTML = '';
        container.className = 'result-content-enhanced';
        let idCounter = 0;
        
        function renderObject(obj, level = 0) {
            let html = '';
            
            for (const [key, value] of Object.entries(obj)) {
                if (key === 'type') continue;
                
                const isConfidenceField = value && typeof value === 'object' && value.value !== undefined && value.confidence_score !== undefined;
                if (isConfidenceField && showConfidenceBadges) {
                    const confidenceLevel = getConfidenceLevel(value.confidence_score);
                    const confidencePercent = (value.confidence_score * 100).toFixed(0);
                    html += `
                        <div class="tree-item confidence-${confidenceLevel}" style="margin-left: ${level * 20}px">
                            <div class="tree-item-content">
                                <span class="field-name-inline">${key}:</span>
                                <span class="field-value-inline">${JSON.stringify(value.value)}</span>
                                <span class="confidence-badge ${confidenceLevel}">${confidencePercent}%</span>
                            </div>
                        </div>
                    `;
                } else if (isConfidenceField && !showConfidenceBadges) {
                    html += `
                        <div class="tree-item" style="margin-left: ${level * 20}px">
                            <div class="tree-item-content">
                                <span class="field-name-inline">${key}:</span>
                                <span class="field-value-inline">${JSON.stringify(value.value)}</span>
                            </div>
                        </div>
                    `;
                } else if (Array.isArray(value)) {
                    // Handle arrays with collapsible items
                    const arrayId = `array-${idCounter++}`;
                    const hasObjects = value.length > 0 && typeof value[0] === 'object';
                    
                    html += `
                        <div class="tree-item" style="margin-left: ${level * 20}px">
                            <div class="tree-item-header ${hasObjects ? 'collapsible' : ''}" data-target="${arrayId}">
                                ${hasObjects ? '<span class="collapse-icon">▼</span>' : ''}
                                <span class="field-name-inline">${key}:</span>
                                <span class="array-count">[${value.length} items]</span>
                            </div>
                            <div class="tree-item-children ${hasObjects ? '' : 'hidden'}" id="${arrayId}">
                    `;
                    
                    value.forEach((item, index) => {
                        if (typeof item === 'object' && item !== null) {
                            const itemId = `item-${idCounter++}`;
                            html += `
                                <div class="tree-item array-item" style="margin-left: ${(level + 1) * 20}px">
                                    <div class="tree-item-header collapsible" data-target="${itemId}">
                                        <span class="collapse-icon">▼</span>
                                        <span class="field-name-inline">Item ${index + 1}</span>
                                    </div>
                                    <div class="tree-item-children" id="${itemId}">
                            `;
                            html += renderObject(item, level + 2);
                            html += `
                                    </div>
                                </div>
                            `;
                        } else {
                            html += `
                                <div class="tree-item" style="margin-left: ${(level + 1) * 20}px">
                                    <div class="tree-item-content">
                                        <span class="field-value-inline">${JSON.stringify(item)}</span>
                                    </div>
                                </div>
                            `;
                        }
                    });
                    
                    html += `
                            </div>
                        </div>
                    `;
                } else if (typeof value === 'object' && value !== null) {
                    // Nested object with collapsible structure
                    const objId = `obj-${idCounter++}`;
                    html += `
                        <div class="tree-item" style="margin-left: ${level * 20}px">
                            <div class="tree-item-header collapsible" data-target="${objId}">
                                <span class="collapse-icon">▼</span>
                                <span class="field-name-inline">${key}</span>
                            </div>
                            <div class="tree-item-children" id="${objId}">
                    `;
                    html += renderObject(value, level + 1);
                    html += `
                            </div>
                        </div>
                    `;
                } else {
                    // Simple value without confidence
                    html += `
                        <div class="tree-item" style="margin-left: ${level * 20}px">
                            <div class="tree-item-content">
                                <span class="field-name-inline">${key}:</span>
                                <span class="field-value-inline">${JSON.stringify(value)}</span>
                            </div>
                        </div>
                    `;
                }
            }
            
            return html;
        }
        
        container.innerHTML = renderObject(data);
        
        container.querySelectorAll('.collapsible').forEach(header => {
            header.addEventListener('click', function(e) {
                e.stopPropagation();
                const targetId = this.getAttribute('data-target');
                const target = document.getElementById(targetId);
                const icon = this.querySelector('.collapse-icon');
                if (target.classList.contains('hidden')) {
                    target.classList.remove('hidden');
                    if (icon) icon.textContent = '▼';
                } else {
                    target.classList.add('hidden');
                    if (icon) icon.textContent = '▶';
                }
            });
        });
    }

    // Keep legacy name for same behavior
    function renderWithConfidenceScores(data, container) {
        renderFormattedTree(data, container, { showConfidenceBadges: true });
    }

    // Function to render plain JSON
    function renderPlainJson(jsonString, container) {
        container.innerHTML = '';
        container.className = 'result-content-plain';
        container.textContent = jsonString;
    }

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Check authentication before proceeding
        if (analyzeBtn.disabled) {
            alert('Please authenticate with Salesforce first.');
            return;
        }
        
        // Validate page range if PDF is uploaded
        const file = fileInput.files[0];
        if (file && file.type === 'application/pdf') {
            const validation = validatePageRange();
            if (!validation.valid) {
                return; // Stop submission if validation fails
            }
        }
        
        loadingIndicator.style.display = 'flex';
        resultSection.style.display = 'none';

        try {
            const formData = new FormData(this);
            const response = await fetch('/extract-data', {
                method: 'POST',
                body: formData
            });

            if (response.status === 401) {
                // Authentication error - recheck status
                await checkAuthStatus();
                alert('Authentication required. Please authenticate with Salesforce first.');
                return;
            }

            let result = await response.text();

            if (!response.ok) {
                resultViewToggle.style.display = 'none';
                developerReference.style.display = 'none';
                try {
                    const errJson = JSON.parse(result);
                    let errMsg = errJson.error || `Request failed (${response.status})`;
                    if (errJson.details) errMsg += '\n\n' + errJson.details;
                    if (errJson.hints && errJson.hints.length) {
                        errMsg += '\n\nSuggestions:\n• ' + errJson.hints.join('\n• ');
                    }
                    renderPlainJson(errMsg, resultContent);
                } catch (_) {
                    renderPlainJson(result || `Request failed with status ${response.status}`, resultContent);
                }
                resultSection.style.display = 'block';
                loadingIndicator.style.display = 'none';
                return;
            }
            
            try {
                const jsonData = JSON.parse(result);
                const hasData = jsonData && jsonData.data !== undefined;
                
                if (hasData) {
                    const rawOutput = { data: jsonData.data };
                    if (jsonData.metadata) rawOutput.metadata = jsonData.metadata;
                    const rawString = JSON.stringify(rawOutput, null, 2);
                    const hasConfidence = jsonData.metadata && jsonData.metadata.confidenceScoresIncluded;
                    resultViewToggle.style.display = 'flex';
                    resultViewToggle.querySelectorAll('.view-toggle-btn').forEach(btn => {
                        btn.classList.toggle('active', btn.getAttribute('data-view') === 'formatted');
                    });
                    renderFormattedTree(jsonData.data, resultContent, { showConfidenceBadges: hasConfidence });
                    
                    const showFormatted = () => {
                        renderFormattedTree(jsonData.data, resultContent, { showConfidenceBadges: hasConfidence });
                        resultViewToggle.querySelectorAll('.view-toggle-btn').forEach(btn => {
                            btn.classList.toggle('active', btn.getAttribute('data-view') === 'formatted');
                        });
                    };
                    const showRaw = () => {
                        renderPlainJson(rawString, resultContent);
                        resultViewToggle.querySelectorAll('.view-toggle-btn').forEach(btn => {
                            btn.classList.toggle('active', btn.getAttribute('data-view') === 'raw');
                        });
                    };
                    resultViewToggle.querySelectorAll('.view-toggle-btn').forEach(btn => {
                        btn.replaceWith(btn.cloneNode(true));
                    });
                    resultViewToggle.querySelector('[data-view="formatted"]').addEventListener('click', showFormatted);
                    resultViewToggle.querySelector('[data-view="raw"]').addEventListener('click', showRaw);
                    
                    if (jsonData.apiRequest) {
                        developerReference.style.display = 'block';
                        document.getElementById('snippet-curl').textContent = jsonData.apiRequest.curl || '';
                        document.getElementById('snippet-apex').textContent = jsonData.apiRequest.apex || '';
                        const content = developerReference.querySelector('.developer-reference-content');
                        const toggleBtn = developerReference.querySelector('.developer-reference-toggle');
                        content.hidden = true;
                        toggleBtn.setAttribute('aria-expanded', 'false');
                        toggleBtn.textContent = 'Show API request (Developer reference)';
                        developerReference.querySelectorAll('.copy-snippet-btn').forEach(btn => {
                            const target = btn.getAttribute('data-target');
                            const code = target === 'curl' ? jsonData.apiRequest.curl : jsonData.apiRequest.apex;
                            btn.onclick = function() {
                                navigator.clipboard.writeText(code || '').then(() => {
                                    this.textContent = 'Copied!';
                                    this.classList.add('copied');
                                    setTimeout(() => { this.textContent = 'Copy'; this.classList.remove('copied'); }, 2000);
                                });
                            };
                        });
                    } else {
                        developerReference.style.display = 'none';
                    }
                } else {
                    resultViewToggle.style.display = 'none';
                    developerReference.style.display = 'none';
                    const formattedJson = JSON.stringify(jsonData, null, 2);
                    renderPlainJson(formattedJson, resultContent);
                }
            } catch (e) {
                console.error('JSON parsing failed:', e);
                resultViewToggle.style.display = 'none';
                developerReference.style.display = 'none';
                result = decodeHtmlEntities(result);
                renderPlainJson(result, resultContent);
            }
            
            resultSection.style.display = 'block';
        } catch (error) {
            resultViewToggle.style.display = 'none';
            developerReference.style.display = 'none';
            renderPlainJson('Error: ' + error.message, resultContent);
            resultSection.style.display = 'block';
        } finally {
            loadingIndicator.style.display = 'none';
        }
    });
});