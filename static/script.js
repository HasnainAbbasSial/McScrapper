// Socket.IO connection
const socket = io();

// DOM elements
const scraperForm = document.getElementById('scraperForm');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const currentStatus = document.getElementById('currentStatus');
const progressInfo = document.getElementById('progressInfo');
const dataTableBody = document.getElementById('dataTableBody');
const totalRecords = document.getElementById('totalRecords');
const recordCount = document.getElementById('recordCount');
const exportButtons = ['exportCsv', 'exportXlsx', 'exportTxt'];

// State variables
let scrapingActive = false;
let dataCount = 0;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    updateButtonStates();
    setupEventListeners();
});

function setupEventListeners() {
    // Form submission
    scraperForm.addEventListener('submit', function(e) {
        e.preventDefault();
        startScraping();
    });
    
    // Stop button
    stopBtn.addEventListener('click', stopScraping);
    
    // Socket event listeners
    socket.on('scraping_started', handleScrapingStarted);
    socket.on('scraping_stopped', handleScrappingStopped);
    socket.on('scraping_complete', handleScrapingComplete);
    socket.on('progress_update', handleProgressUpdate);
    socket.on('data_update', handleDataUpdate);
    socket.on('error', handleError);
    socket.on('license_expired', handleLicenseExpired);
    
    // Initialize Bootstrap toasts
    window.successToast = new bootstrap.Toast(document.getElementById('successToast'));
    window.errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
}

function startScraping() {
    const startMC = document.getElementById('startMC').value;
    const endMC = document.getElementById('endMC').value;
    const entityType = document.getElementById('entityType').value;
    
    if (!startMC) {
        showError('Please enter a starting MC number');
        return;
    }
    
    // Clear existing data
    clearDataTable();
    
    // Send start command
    socket.emit('start_scraping', {
        start_mc: startMC,
        end_mc: endMC || null,
        entity_type: entityType
    });
}

function stopScraping() {
    socket.emit('stop_scraping');
}

function handleScrapingStarted(data) {
    scrapingActive = true;
    updateButtonStates();
    currentStatus.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Scraping started...';
    currentStatus.className = 'status-active pulsing';
    showSuccess(data.message);
}

function handleScrappingStopped(data) {
    scrapingActive = false;
    updateButtonStates();
    currentStatus.innerHTML = '<i class="fas fa-stop-circle me-2"></i>Scraping stopped';
    currentStatus.className = 'status-stopped';
    progressInfo.textContent = '';
    showSuccess(data.message);
}

function handleScrapingComplete(data) {
    scrapingActive = false;
    updateButtonStates();
    currentStatus.innerHTML = '<i class="fas fa-check-circle me-2"></i>Scraping completed';
    currentStatus.className = 'status-active';
    progressInfo.textContent = `Found ${data.total_found} valid records`;
    showSuccess(`Scraping completed! Found ${data.total_found} valid records.`);
}

function handleProgressUpdate(data) {
    if (scrapingActive) {
        currentStatus.innerHTML = `<i class="fas fa-search me-2"></i>Checking MC ${data.current_mc}`;
        currentStatus.className = 'status-processing';
        progressInfo.textContent = data.status;
    }
}

function handleDataUpdate(data) {
    addDataToTable(data.data);
    dataCount = data.total_count;
    updateRecordCounts();
    updateExportButtons();
}

function handleError(data) {
    scrapingActive = false;
    updateButtonStates();
    currentStatus.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error occurred';
    currentStatus.className = 'status-stopped';
    showError(data.message);
}

function updateButtonStates() {
    startBtn.disabled = scrapingActive;
    stopBtn.disabled = !scrapingActive;
    
    if (scrapingActive) {
        startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Scraping...';
        startBtn.className = 'btn btn-secondary';
    } else {
        startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Start Scraping';
        startBtn.className = 'btn btn-success';
    }
}

function clearDataTable() {
    dataTableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center text-muted py-5">
                <i class="fas fa-search fa-3x mb-3 d-block"></i>
                Starting scraping process...
            </td>
        </tr>
    `;
    dataCount = 0;
    updateRecordCounts();
    updateExportButtons();
}

function addDataToTable(data) {
    // Remove empty state if it exists
    if (dataTableBody.children.length === 1 && dataTableBody.children[0].children.length === 1) {
        dataTableBody.innerHTML = '';
    }
    
    const row = document.createElement('tr');
    row.innerHTML = `
        <td title="${escapeHtml(data.mc_number)}">${escapeHtml(data.mc_number) || 'N/A'}</td>
        <td title="${escapeHtml(data.usdot_number)}">${escapeHtml(data.usdot_number) || 'N/A'}</td>
        <td title="${escapeHtml(data.legal_name)}">${escapeHtml(data.legal_name) || 'N/A'}</td>
        <td title="${escapeHtml(data.physical_address)}">${escapeHtml(data.physical_address) || 'N/A'}</td>
        <td title="${escapeHtml(data.phone_number)}">${escapeHtml(data.phone_number) || 'N/A'}</td>
        <td title="${escapeHtml(data.email)}">${escapeHtml(data.email) || 'N/A'}</td>
    `;
    
    // Add with animation
    row.style.opacity = '0';
    dataTableBody.appendChild(row);
    
    // Fade in animation
    setTimeout(() => {
        row.style.transition = 'opacity 0.3s ease-in';
        row.style.opacity = '1';
    }, 10);
    
    // Scroll to bottom of table
    const tableContainer = document.querySelector('.table-responsive');
    tableContainer.scrollTop = tableContainer.scrollHeight;
}

function updateRecordCounts() {
    totalRecords.textContent = `${dataCount} records`;
    recordCount.textContent = `${dataCount} records found`;
}

function updateExportButtons() {
    const hasData = dataCount > 0;
    exportButtons.forEach(buttonId => {
        document.getElementById(buttonId).disabled = !hasData;
    });
}

function exportData(format) {
    if (dataCount === 0) {
        showError('No data to export');
        return;
    }
    
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = `/export/${format}`;
    link.download = `fmcsa_data.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showSuccess(`Exporting data as ${format.toUpperCase()}...`);
}

function showSuccess(message) {
    const toast = document.getElementById('successToast');
    toast.querySelector('.toast-body').textContent = message;
    window.successToast.show();
}

function showError(message) {
    const toast = document.getElementById('errorToast');
    toast.querySelector('.toast-body').textContent = message;
    window.errorToast.show();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility functions for better UX
function formatPhoneNumber(phone) {
    if (!phone) return 'N/A';
    // Basic phone number formatting
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
        return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
    }
    return phone;
}

function truncateText(text, maxLength = 50) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+S or Cmd+S to start scraping
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (!scrapingActive) {
            startScraping();
        }
    }
    
    // Escape to stop scraping
    if (e.key === 'Escape' && scrapingActive) {
        stopScraping();
    }
});

// Page visibility change handling
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && scrapingActive) {
        // Refresh status when page becomes visible
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                scrapingActive = data.scraping_active;
                dataCount = data.data_count;
                updateButtonStates();
                updateRecordCounts();
                updateExportButtons();
            })
            .catch(console.error);
    }
});

// License expiry handling
function handleLicenseExpired(data) {
    // Stop any ongoing scraping
    if (scrapingActive) {
        socket.emit('stop_scraping');
    }
    
    // Show expiry modal
    showLicenseExpiredModal(data.message, data.license_key, data.expiry_date);
    
    // Disable all controls
    disableAllControls();
    
    // Redirect to login after 10 seconds
    setTimeout(function() {
        window.location.href = '/login';
    }, 10000);
}

function showLicenseExpiredModal(message, licenseKey, expiryDate) {
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="licenseExpiredModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-danger">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle me-2"></i>License Expired
                        </h5>
                    </div>
                    <div class="modal-body text-center">
                        <div class="mb-3">
                            <i class="fas fa-times-circle text-danger" style="font-size: 4rem;"></i>
                        </div>
                        <h5 class="text-danger mb-3">Access Blocked</h5>
                        <p class="mb-3">${message}</p>
                        <div class="alert alert-warning">
                            <strong>License Key:</strong> ${licenseKey}<br>
                            <strong>Expired:</strong> ${expiryDate}
                        </div>
                        <p class="text-muted small">
                            You will be redirected to the login page in <span id="countdown">10</span> seconds.
                        </p>
                        <div class="mt-3">
                            <strong>Contact Support:</strong><br>
                            <i class="fas fa-envelope me-2"></i>hasnainabbas.contact@gmail.com<br>
                            <i class="fab fa-whatsapp me-2"></i>+923070467687
                        </div>
                    </div>
                    <div class="modal-footer">
                        <a href="/login" class="btn btn-danger">Go to Login Now</a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('licenseExpiredModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('licenseExpiredModal'));
    modal.show();
    
    // Start countdown
    let countdown = 10;
    const countdownElement = document.getElementById('countdown');
    const countdownInterval = setInterval(function() {
        countdown--;
        if (countdownElement) {
            countdownElement.textContent = countdown;
        }
        if (countdown <= 0) {
            clearInterval(countdownInterval);
        }
    }, 1000);
}

function disableAllControls() {
    // Disable form inputs
    const inputs = document.querySelectorAll('input, button, select');
    inputs.forEach(input => {
        input.disabled = true;
    });
    
    // Update status
    currentStatus.innerHTML = '<i class="fas fa-ban me-2"></i>Access blocked - License expired';
    currentStatus.className = 'status-error';
    
    // Show error message
    showError('License expired! Access blocked. Please contact support.');
}
