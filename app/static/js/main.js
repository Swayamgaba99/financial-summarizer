$(document).ready(function() {
    // Initialize UI components
    initializeUI();
    
    // Setup event handlers
    setupFileUploadHandlers();
    setupFormSubmissionHandler();
    setupEvaluationHandler();
});

/**
 * Initialize UI components and state
 */
function initializeUI() {
    // Add body class for animations with a slight delay for smoother page load
    setTimeout(() => {
        $('body').addClass('loaded');
    }, 100);
    
    // Initialize tooltips if Bootstrap's tooltip is available
    if (typeof $().tooltip === 'function') {
        $('[data-bs-toggle="tooltip"]').tooltip();
    }
    
    // Check for any messages in the URL (for redirects with messages)
    const urlParams = new URLSearchParams(window.location.search);
    const message = urlParams.get('message');
    const messageType = urlParams.get('type') || 'info';
    
    if (message) {
        displayMessage(message, messageType);
    }
    
    // Initialize progress bar but keep it hidden
    $('#progressContainer').hide();
}

/**
 * Set up handlers for file upload interactions with enhanced feedback
 */
function setupFileUploadHandlers() {
    const dropZone = $('#dropZone');
    const fileInput = $('#fileInput');
    const selectedFiles = $('#selectedFiles');
    
    // Drag and drop functionality with enhanced visual feedback
    dropZone.on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('dragover');
    });
    
    dropZone.on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
    });
    
    dropZone.on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover').addClass('drop-success');
        
        const files = e.originalEvent.dataTransfer.files;
        fileInput.prop('files', files);
        updateFileList(files);
        
        // Visual feedback for successful drop
        pulseElement($(this));
        
        // Remove success class after animation
        setTimeout(() => {
            $(this).removeClass('drop-success');
        }, 1500);
    });
    
    // Handle file input change with visual feedback
    fileInput.on('change', function() {
        dropZone.addClass('drop-success');
        updateFileList(this.files);
        pulseElement(dropZone);
        
        // Remove success class after animation
        setTimeout(() => {
            dropZone.removeClass('drop-success');
        }, 1500);
    });
    
    // Handle click on drop zone
    dropZone.on('click', function(e) {
        if (e.target === this || !$(e.target).closest('.file-badge').length) {
            fileInput.trigger('click');
        }
    });
    
    // Enable file removal
    $(document).on('click', '.file-badge .remove-file', function(e) {
        e.stopPropagation();
        
        // Get the file index
        const index = $(this).data('index');
        
        // Create a new FileList without the removed file
        const dt = new DataTransfer();
        const files = fileInput[0].files;
        
        for (let i = 0; i < files.length; i++) {
            if (i !== index) {
                dt.items.add(files[i]);
            }
        }
        
        // Update the file input
        fileInput[0].files = dt.files;
        
        // Update the file list display
        updateFileList(fileInput[0].files);
        
        // Show feedback
        if (fileInput[0].files.length === 0) {
            dropZone.removeClass('drop-success');
        }
    });
}

/**
 * Update the file list display with selected files and enhanced animations
 * @param {FileList} files - The list of selected files
 */
function updateFileList(files) {
    const selectedFiles = $('#selectedFiles');
    
    // Fade out existing files before replacing them
    selectedFiles.children().fadeOut(300, function() {
        selectedFiles.empty();
        
        if (files.length > 0) {
            // Add fade-in animation class
            selectedFiles.addClass('fade-in');
            
            // Create and append file badges with staggered animation
            for (let i = 0; i < files.length; i++) {
                const fileExt = files[i].name.split('.').pop().toLowerCase();
                let iconClass = 'bi-file-earmark';
                
                // Set icon based on file type
                if (fileExt === 'pdf') {
                    iconClass = 'bi-file-earmark-pdf';
                } else if (['doc', 'docx'].includes(fileExt)) {
                    iconClass = 'bi-file-earmark-word';
                } else if (['xls', 'xlsx'].includes(fileExt)) {
                    iconClass = 'bi-file-earmark-excel';
                }
                
                // Format file size
                const fileSize = formatFileSize(files[i].size);
                
                // Create file badge with remove button
                const fileBadge = $(`
                    <div class="file-badge" style="opacity: 0;">
                        <i class="bi ${iconClass}"></i> 
                        ${truncateText(files[i].name, 20)}
                        <span class="ms-1 text-black-50">(${fileSize})</span>
                        <button type="button" class="remove-file" data-index="${i}" title="Remove file">
                            <i class="bi bi-x-circle"></i>
                        </button>
                    </div>
                `);
                
                selectedFiles.append(fileBadge);
                
                // Staggered fade-in animation
                setTimeout(() => {
                    fileBadge.animate({ opacity: 1 }, 300);
                }, i * 100);
            }
            
            // Enable the process button with animation if files are selected
            $('.btn-process').prop('disabled', false).addClass('btn-pulse');
            setTimeout(() => {
                $('.btn-process').removeClass('btn-pulse');
            }, 1000);
        } else {
            // Disable the process button if no files are selected
            $('.btn-process').prop('disabled', true);
        }
    });
}

/**
 * Handle form submission for document processing with progress tracking
 */
function setupFormSubmissionHandler() {
    $('#uploadForm').submit(function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(this);
        
        // Show loading state
        $('#uploadSpinner').removeClass('d-none');
        $('button[type="submit"]').prop('disabled', true);
        
        // Show progress container
        $('#progressContainer').fadeIn(300);
        $('#progressBar').css('width', '0%').attr('aria-valuenow', 0).text('0%');
        
        // Show processing message
        displayMessage('Processing documents. This may take a moment...', 'info', false);

        // Simulate progress with realistic stages
        simulateDocumentProcessingProgress();

        // Make AJAX request
        $.ajax({
            url: '/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            xhr: function() {
                const xhr = new window.XMLHttpRequest();
                
                // Upload progress
                xhr.upload.addEventListener('progress', function(evt) {
                    if (evt.lengthComputable) {
                        const percentComplete = Math.round((evt.loaded / evt.total) * 30);
                        updateProgressBar(percentComplete, 'Uploading files...');
                    }
                }, false);
                
                return xhr;
            },
            success: function(response) {
                // Complete the progress bar
                updateProgressBar(100, 'Complete!');
                
                // Clear any messages
                clearMessages();
                
                // Prepare summary content
                const formattedSummary = response.preview.replace(/\n/g, '<br>');
                
                // First hide old content if visible
                if ($('#summarySection').is(':visible')) {
                    $('#summarySection').fadeOut(300, function() {
                        $('#summaryPreview').html(formattedSummary);
                        // Then show with animation
                        $(this).fadeIn(500).addClass('highlight-section');
                        setTimeout(() => {
                            $(this).removeClass('highlight-section');
                        }, 1500);
                    });
                } else {
                    // Direct show if not visible
                    $('#summaryPreview').html(formattedSummary);
                    $('#summarySection').removeClass('d-none').hide().fadeIn(500).addClass('highlight-section');
                    setTimeout(() => {
                        $('#summarySection').removeClass('highlight-section');
                    }, 1500);
                }
                
                // Hide evaluation results
                $('#evalResults').addClass('d-none');
                
                // Success message
                displayMessage('Documents processed successfully!', 'success');
                
                // Smooth scroll to summary section
                smoothScrollTo('#summarySection');
            },
            error: function(xhr) {
                // Reset progress bar to show error
                $('#progressBar')
                    .removeClass('bg-info bg-success')
                    .addClass('bg-danger')
                    .css('width', '100%')
                    .text('Error');
                
                // Get error message
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                
                // Show error message with details
                displayMessage(`Error processing documents: ${errorMsg}`, 'danger');
                
                // Add retry button
                addRetryButton();
            },
            complete: function() {
                // Hide progress bar after delay
                setTimeout(() => {
                    $('#progressContainer').fadeOut(500);
                }, 1500);
                
                // Reset loading state
                $('#uploadSpinner').addClass('d-none');
                $('button[type="submit"]').prop('disabled', false);
            }
        });
    });
}

/**
 * Simulate realistic document processing progress
 */
function simulateDocumentProcessingProgress() {
    const stages = [
        { progress: 30, message: 'Uploading files...', duration: 1000 },
        { progress: 40, message: 'Extracting text...', duration: 1500 },
        { progress: 60, message: 'Analyzing content...', duration: 2000 },
        { progress: 80, message: 'Generating summary...', duration: 1500 },
        { progress: 90, message: 'Finalizing...', duration: 1000 }
    ];
    
    let currentStage = 0;
    
    function processNextStage() {
        if (currentStage < stages.length) {
            const stage = stages[currentStage];
            updateProgressBar(stage.progress, stage.message);
            
            currentStage++;
            setTimeout(processNextStage, stage.duration);
        }
    }
    
    processNextStage();
}

/**
 * Update the progress bar with animation
 * @param {number} progress - The progress percentage (0-100)
 * @param {string} message - The progress message to display
 */
function updateProgressBar(progress, message) {
    const progressBar = $('#progressBar');
    
    // Change color based on progress
    if (progress < 30) {
        progressBar.removeClass('bg-success bg-warning').addClass('bg-info');
    } else if (progress < 70) {
        progressBar.removeClass('bg-info bg-success').addClass('bg-warning');
    } else {
        progressBar.removeClass('bg-info bg-warning').addClass('bg-success');
    }
    
    // Update progress text
    $('#progressStatus').text(message);
    
    // Animate progress bar
    progressBar.animate(
        { width: progress + '%' },
        {
            duration: 300,
            easing: 'swing',
            step: function(now) {
                const value = Math.round(now);
                $(this).attr('aria-valuenow', value).text(value + '%');
            }
        }
    );
}

/**
 * Add a retry button for error recovery
 */
function addRetryButton() {
    const retryBtn = $(`
        <button id="retryBtn" class="btn btn-outline-danger mt-3">
            <i class="bi bi-arrow-repeat me-2"></i>Retry Upload
        </button>
    `);
    
    $('#progressContainer').after(retryBtn);
    
    // Add pulse animation
    retryBtn.addClass('btn-pulse');
    
    // Handle retry click
    retryBtn.on('click', function() {
        $(this).remove();
        $('#progressBar')
            .removeClass('bg-danger')
            .addClass('bg-info')
            .css('width', '0%')
            .text('0%');
        $('#progressContainer').fadeOut(300);
        $('#uploadForm').trigger('submit');
    });
}

/**
 * Handle evaluation button click with enhanced animations
 */
function setupEvaluationHandler() {
    $('#runEvaluation').click(function() {
        // Show loading state
        $('#evalSpinner').removeClass('d-none');
        $(this).prop('disabled', true);
        
        // Show processing message
        displayMessage('Running RAG evaluation...', 'info', false);

        // Make AJAX request
        $.ajax({
            url: '/evaluate',
            type: 'GET',
            success: function(response) {
                // Clear any messages
                clearMessages();
                
                // Reset metric values first
                $('#relevancyScore, #faithfulnessScore, #recallScore').text('0.0%');
                
                // Show evaluation section with animation
                if ($('#evalResults').is(':visible')) {
                    $('#evalResults').fadeOut(300, function() {
                        $(this).fadeIn(500).addClass('highlight-section');
                        setTimeout(() => {
                            $(this).removeClass('highlight-section');
                        }, 1500);
                    });
                } else {
                    $('#evalResults').removeClass('d-none').hide().fadeIn(500).addClass('highlight-section');
                    setTimeout(() => {
                        $('#evalResults').removeClass('highlight-section');
                    }, 1500);
                }
                
                // Format and set scores with enhanced animation
                setTimeout(() => {
                    animateMetricWithGauge('relevancyScore', response.relevancy);
                    
                    setTimeout(() => {
                        animateMetricWithGauge('faithfulnessScore', response.faithfulness);
                        
                        setTimeout(() => {
                            animateMetricWithGauge('recallScore', response.recall);
                        }, 400);
                    }, 400);
                }, 400);
                
                // Success message
                displayMessage('Evaluation completed successfully!', 'success');
                
                // Smooth scroll to evaluation section
                smoothScrollTo('#evalResults');
            },
            error: function(xhr) {
                // Get error message
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                
                // Show error message with more details
                displayMessage(`Evaluation failed: ${errorMsg}. Please try again or contact support if the issue persists.`, 'danger');
                
                // Shake the evaluation button to indicate error
                $('#runEvaluation').addClass('shake-animation');
                setTimeout(() => {
                    $('#runEvaluation').removeClass('shake-animation');
                }, 800);
            },
            complete: function() {
                // Reset loading state
                $('#evalSpinner').addClass('d-none');
                $('#runEvaluation').prop('disabled', false);
            }
        });
    });
}

/**
 * Animate counting up to a metric value with visual gauge feedback
 * @param {string} elementId - The ID of the element to animate
 * @param {number} finalValue - The final value to count to (0-1)
 */
function animateMetricWithGauge(elementId, finalValue) {
    const element = $(`#${elementId}`);
    const percentValue = finalValue * 100;
    const duration = 1500;
    const frameDuration = 20;
    const frames = duration / frameDuration;
    const increment = percentValue / frames;
    
    let currentValue = 0;
    
    // Add gauge container if it doesn't exist
    const gaugeId = `${elementId}Gauge`;
    if ($(`#${gaugeId}`).length === 0) {
        element.after(`
            <div id="${gaugeId}" class="metric-gauge">
                <div class="gauge-fill"></div>
            </div>
        `);
    }
    
    const gaugeElement = $(`#${gaugeId} .gauge-fill`);
    gaugeElement.css('width', '0%');
    
    // Set color based on value
    let gaugeColor;
    if (percentValue < 50) {
        gaugeColor = '#dc3545'; // danger
    } else if (percentValue < 75) {
        gaugeColor = '#ffc107'; // warning
    } else {
        gaugeColor = '#28a745'; // success
    }
    gaugeElement.css('background-color', gaugeColor);
    
    // Start animation
    const interval = setInterval(() => {
        currentValue += increment;
        if (currentValue >= percentValue) {
            currentValue = percentValue;
            clearInterval(interval);
            
            // Add pulse animation to final value
            element.addClass('pulse-value');
            setTimeout(() => {
                element.removeClass('pulse-value');
            }, 1000);
        }
        
        // Update text and gauge
        element.text(`${currentValue.toFixed(1)}%`);
        gaugeElement.css('width', `${currentValue}%`);
    }, frameDuration);
}

/**
 * Display a message to the user with enhanced animations
 * @param {string} message - The message to display
 * @param {string} type - The type of message (success, info, warning, danger)
 * @param {boolean} autoHide - Whether to auto-hide the message
 */
function displayMessage(message, type = 'info', autoHide = true) {
    // Clear any existing messages
    clearMessages();
    
    // Get the appropriate icon for the message type
    let iconClass = 'bi-info-circle-fill';
    if (type === 'success') iconClass = 'bi-check-circle-fill';
    if (type === 'warning') iconClass = 'bi-exclamation-triangle-fill';
    if (type === 'danger') iconClass = 'bi-exclamation-circle-fill';
    
    // Create message element
    const messageElement = $(`
        <div class="alert alert-${type} d-flex align-items-center" role="alert" style="opacity: 0; transform: translateY(-20px);">
            <i class="bi ${iconClass} me-2"></i>
            <div>${message}</div>
            ${type === 'danger' ? '<button type="button" class="btn-close ms-auto" data-bs-dismiss="alert" aria-label="Close"></button>' : ''}
        </div>
    `);
    
    // Add message to the top of the form
    $('#uploadForm').prepend(messageElement);
    
    // Animate message in
    messageElement.animate(
        { opacity: 1, transform: 'translateY(0)' },
        {
            duration: 300,
            easing: 'easeOutCubic'
        }
    );
    
    // Auto-hide message after delay if enabled
    if (autoHide) {
        setTimeout(() => {
            messageElement.animate(
                { opacity: 0, transform: 'translateY(-20px)' },
                {
                    duration: 300,
                    easing: 'easeInCubic',
                    complete: function() {
                        $(this).remove();
                    }
                }
            );
        }, 5000);
    }
}

/**
 * Clear all displayed messages with animation
 */
function clearMessages() {
    $('.alert').each(function() {
        $(this).animate(
            { opacity: 0, transform: 'translateY(-20px)' },
            {
                duration: 300,
                easing: 'easeInCubic',
                complete: function() {
                    $(this).remove();
                }
            }
        );
    });
}

/**
 * Apply a pulse animation to an element
 * @param {jQuery} element - The element to pulse
 */
function pulseElement(element) {
    element.removeClass('pulse').addClass('pulse');
    setTimeout(() => {
        element.removeClass('pulse');
    }, 1500);
}

/**
 * Smooth scroll to an element with enhanced animation
 * @param {string} selector - The selector for the element to scroll to
 */
function smoothScrollTo(selector) {
    $('html, body').animate({
        scrollTop: $(selector).offset().top - 20
    }, {
        duration: 800,
        easing: 'easeInOutCubic'
    });
}

/**
 * Format a file size in bytes to a human-readable format
 * @param {number} bytes - The file size in bytes
 * @returns {string} - The formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Truncate text with ellipsis if it exceeds max length
 * @param {string} text - The text to truncate
 * @param {number} maxLength - The maximum length
 * @returns {string} - The truncated text
 */
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
}

/**
 * Add jQuery easing functions if not available
 */
if (typeof $.easing.easeInOutCubic !== 'function') {
    $.extend($.easing, {
        easeInCubic: function(x, t, b, c, d) {
            return c * (t /= d) * t * t + b;
        },
        easeOutCubic: function(x, t, b, c, d) {
            return c * ((t = t / d - 1) * t * t + 1) + b;
        },
        easeInOutCubic: function(x, t, b, c, d) {
            if ((t /= d / 2) < 1) return c / 2 * t * t * t + b;
            return c / 2 * ((t -= 2) * t * t + 2) + b;
        }
    });
}