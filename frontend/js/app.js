/**
 * Main application logic for notepad scanner.
 */

class App {
    constructor() {
        this.currentScreen = 'user-selection-screen';
        this.sessionId = null;
        this.users = [];
        this.previewInterval = null;
        this.capturedCount = 0;
        
        this.initializeEventListeners();
        this.loadUsers();
    }

    initializeEventListeners() {
        // User selection buttons
        document.querySelectorAll('.user-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const userId = e.currentTarget.dataset.userId;
                this.startSession(userId);
            });
        });

        // Capture screen buttons
        document.getElementById('capture-button').addEventListener('click', () => {
            this.capture();
        });

        document.getElementById('done-button').addEventListener('click', () => {
            this.done();
        });

        // Review screen buttons
        document.getElementById('process-button').addEventListener('click', () => {
            this.process();
        });

        document.getElementById('cancel-button').addEventListener('click', () => {
            this.cancel();
        });

        // Error screen button
        document.getElementById('error-ok-button').addEventListener('click', () => {
            this.showScreen('user-selection-screen');
        });
    }

    async loadUsers() {
        try {
            const data = await API.getUsers();
            this.users = data.users;
        } catch (error) {
            this.showError('Failed to load users: ' + error.message);
        }
    }

    async startSession(userId) {
        try {
            const data = await API.startSession(userId);
            this.sessionId = data.session_id;
            this.capturedCount = 0;
            this.updatePageCounter();
            this.showScreen('capture-screen');
            this.startPreview();
        } catch (error) {
            this.showError('Failed to start session: ' + error.message);
        }
    }

    startPreview() {
        if (this.previewInterval) {
            clearInterval(this.previewInterval);
        }

        const updatePreview = async () => {
            try {
                const data = await API.getPreview(this.sessionId);
                const img = document.getElementById('preview-image');
                img.src = data.image;

                // Update marker count and capture button state
                const markerCount = document.getElementById('marker-count');
                const markerIndicator = document.getElementById('marker-indicator');
                const captureButton = document.getElementById('capture-button');

                if (markerCount && data.marker_count !== undefined) {
                    markerCount.textContent = data.marker_count;
                    if (markerIndicator) {
                        const hasAllMarkers = data.marker_count >= 4;
                        markerIndicator.classList.toggle('has-markers', hasAllMarkers);
                    }
                    if (captureButton) {
                        const hasAllMarkers = data.marker_count >= 4;
                        captureButton.disabled = !hasAllMarkers;
                        captureButton.classList.toggle('disabled', !hasAllMarkers);
                    }
                }
            } catch (error) {
                console.error('Preview error:', error);
            }
        };

        updatePreview();
        this.previewInterval = setInterval(updatePreview, 100); // 10 FPS
    }

    stopPreview() {
        if (this.previewInterval) {
            clearInterval(this.previewInterval);
            this.previewInterval = null;
        }
    }

    async capture() {
        try {
            const data = await API.capture(this.sessionId);
            this.capturedCount = data.page_count;
            this.updatePageCounter();
            
            // Visual feedback
            const btn = document.getElementById('capture-button');
            btn.style.background = '#28a745';
            setTimeout(() => {
                btn.style.background = '';
            }, 200);
        } catch (error) {
            this.showError('Failed to capture: ' + error.message);
        }
    }

    updatePageCounter() {
        // Update text version (vertical layout)
        const counterText = document.getElementById('page-counter');
        if (counterText) {
            counterText.textContent = 
                `${this.capturedCount} page${this.capturedCount !== 1 ? 's' : ''} captured`;
        }
        
        // Update number version (horizontal layout)
        const counterNum = document.getElementById('page-counter-num');
        if (counterNum) {
            counterNum.textContent = this.capturedCount;
        }
    }

    async done() {
        if (this.capturedCount === 0) {
            this.showError('Please capture at least one page');
            return;
        }

        this.stopPreview();
        this.showScreen('processing-screen');
        document.getElementById('processing-progress').textContent = 
            'Processing images...';

        try {
            const data = await API.review(this.sessionId);
            this.showReviewScreen(data.images);
        } catch (error) {
            this.showError('Failed to process images: ' + error.message);
        }
    }

    showReviewScreen(images) {
        const grid = document.getElementById('review-grid');
        grid.innerHTML = '';

        images.forEach((imgData, index) => {
            const item = document.createElement('div');
            item.className = 'review-item';
            
            if (imgData) {
                const img = document.createElement('img');
                img.src = imgData;
                img.alt = `Page ${index + 1}`;
                item.appendChild(img);
            } else {
                item.style.background = '#333';
                item.style.display = 'flex';
                item.style.alignItems = 'center';
                item.style.justifyContent = 'center';
                item.style.minHeight = '200px';
                const errorText = document.createElement('div');
                errorText.textContent = `Page ${index + 1}\n(Processing failed)`;
                errorText.style.color = '#ff6b6b';
                errorText.style.textAlign = 'center';
                item.appendChild(errorText);
            }
            
            const label = document.createElement('div');
            label.className = 'page-label';
            label.textContent = `Page ${index + 1}`;
            item.appendChild(label);
            
            grid.appendChild(item);
        });

        this.showScreen('review-screen');
    }

    async process() {
        this.showScreen('processing-screen');
        
        try {
            const data = await API.process(this.sessionId);
            
            // Check if there were any errors
            const failedResults = data.results.filter(r => !r.success);
            if (failedResults.length > 0) {
                const errorMessages = failedResults.map(r => 
                    `Page ${r.page_number}: ${r.error || 'Unknown error'}`
                ).join('\n');
                console.error('Processing errors:', errorMessages);
                this.showError(`Processing completed with errors:\n\n${errorMessages}`);
                return;
            }
            
            // Show success message
            const successDetails = document.getElementById('success-details');
            if (successDetails) {
                successDetails.textContent = 
                    `${data.success_count} of ${data.total_count} pages processed`;
                this.showScreen('success-screen');
                
                setTimeout(() => {
                    this.endSession();
                    this.showScreen('user-selection-screen');
                }, 3000);
            } else {
                // Fallback for old layout
                document.getElementById('processing-progress').textContent = 
                    `Successfully processed ${data.success_count} of ${data.total_count} pages`;
                
                setTimeout(() => {
                    this.endSession();
                    this.showScreen('user-selection-screen');
                }, 2000);
            }
        } catch (error) {
            console.error('Process error:', error);
            this.showError('Failed to process: ' + error.message);
        }
    }

    cancel() {
        this.endSession();
        this.showScreen('user-selection-screen');
    }

    async endSession() {
        this.stopPreview();
        if (this.sessionId) {
            try {
                await API.endSession(this.sessionId);
            } catch (error) {
                console.error('Error ending session:', error);
            }
            this.sessionId = null;
        }
        this.capturedCount = 0;
    }

    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        document.getElementById(screenId).classList.add('active');
        this.currentScreen = screenId;
    }

    showError(message) {
        document.getElementById('error-message').textContent = message;
        this.showScreen('error-screen');
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new App();
});
