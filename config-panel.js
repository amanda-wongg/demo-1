/**
 * Configuration Panel for Slack Alert System
 * Provides UI for users to configure Slack webhook and thresholds
 */

class ConfigPanel {
    constructor(slackAlertSystem) {
        this.alertSystem = slackAlertSystem;
        this.isVisible = false;
        this.createConfigPanel();
        this.bindEvents();
    }

    createConfigPanel() {
        // Create the configuration panel HTML
        const configHTML = `
            <div id="configPanel" class="config-panel" style="display: none;">
                <div class="config-content">
                    <div class="config-header">
                        <h3>⚙️ Slack Alert Configuration</h3>
                        <button id="closeConfig" class="close-btn">&times;</button>
                    </div>
                    
                    <div class="config-body">
                        <div class="config-section">
                            <h4>📡 Slack Integration</h4>
                            <div class="form-group">
                                <label for="webhookUrl">Slack Webhook URL:</label>
                                <input type="url" id="webhookUrl" placeholder="https://hooks.slack.com/services/..." />
                                <small class="help-text">
                                    <a href="#" id="webhookHelp">How to get a Slack webhook URL?</a>
                                </small>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="enableAlerts" /> Enable Slack Alerts
                                </label>
                            </div>
                        </div>

                        <div class="config-section">
                            <h4>🎯 Alert Thresholds</h4>
                            
                            <div class="form-group">
                                <label for="priceVariance">Price Variance Threshold (%):</label>
                                <input type="number" id="priceVariance" min="0" max="100" step="0.1" />
                                <small class="help-text">Alert when price variance exceeds this percentage</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="dailyPriceChange">Daily Price Change Threshold (%):</label>
                                <input type="number" id="dailyPriceChange" min="0" max="100" step="0.1" />
                                <small class="help-text">Alert when daily price change exceeds this percentage</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="predictionAccuracy">Minimum Prediction Accuracy (%):</label>
                                <input type="number" id="predictionAccuracy" min="0" max="100" step="1" />
                                <small class="help-text">Alert when prediction accuracy drops below this percentage</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="volumeVariance">Volume Variance Threshold (%):</label>
                                <input type="number" id="volumeVariance" min="0" max="100" step="1" />
                                <small class="help-text">Alert when trading volume variance exceeds this percentage</small>
                            </div>
                            
                            <div class="form-group">
                                <label for="consecutiveLosses">Consecutive Losses Alert:</label>
                                <input type="number" id="consecutiveLosses" min="1" max="10" step="1" />
                                <small class="help-text">Alert after this many consecutive wrong predictions</small>
                            </div>
                        </div>

                        <div class="config-section">
                            <h4>⏱️ Alert Settings</h4>
                            <div class="form-group">
                                <label for="alertCooldown">Alert Cooldown (minutes):</label>
                                <input type="number" id="alertCooldown" min="1" max="60" step="1" />
                                <small class="help-text">Minimum time between similar alerts</small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="config-footer">
                        <button id="testSlack" class="btn btn-test">🧪 Test Connection</button>
                        <button id="resetConfig" class="btn btn-secondary">🔄 Reset to Defaults</button>
                        <button id="saveConfig" class="btn btn-primary">💾 Save Configuration</button>
                    </div>
                </div>
            </div>

            <!-- Webhook Help Modal -->
            <div id="webhookModal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4>📚 How to Get a Slack Webhook URL</h4>
                        <button id="closeModal" class="close-btn">&times;</button>
                    </div>
                    <div class="modal-body">
                        <ol>
                            <li>Go to <a href="https://api.slack.com/apps" target="_blank">Slack API Apps</a></li>
                            <li>Click "Create New App" → "From scratch"</li>
                            <li>Name your app (e.g., "Stock Alerts") and select your workspace</li>
                            <li>Go to "Incoming Webhooks" in the left sidebar</li>
                            <li>Toggle "Activate Incoming Webhooks" to On</li>
                            <li>Click "Add New Webhook to Workspace"</li>
                            <li>Choose the channel where you want alerts sent</li>
                            <li>Copy the webhook URL that starts with "https://hooks.slack.com/services/..."</li>
                            <li>Paste it in the configuration above</li>
                        </ol>
                        <p><strong>Note:</strong> The webhook URL contains sensitive information. Keep it secure!</p>
                    </div>
                </div>
            </div>
        `;

        // Add the HTML to the page
        document.body.insertAdjacentHTML('beforeend', configHTML);

        // Add CSS styles
        this.addStyles();
    }

    addStyles() {
        const styles = `
            <style>
                .config-panel {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }

                .config-content {
                    background: white;
                    border-radius: 12px;
                    width: 90%;
                    max-width: 600px;
                    max-height: 90vh;
                    overflow-y: auto;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                }

                .config-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px 25px;
                    border-bottom: 1px solid #eee;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 12px 12px 0 0;
                }

                .config-header h3 {
                    margin: 0;
                    font-size: 1.5em;
                }

                .close-btn {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 24px;
                    cursor: pointer;
                    padding: 0;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    transition: background-color 0.2s;
                }

                .close-btn:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                }

                .config-body {
                    padding: 25px;
                }

                .config-section {
                    margin-bottom: 30px;
                }

                .config-section h4 {
                    color: #333;
                    margin-bottom: 15px;
                    font-size: 1.2em;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 5px;
                }

                .form-group {
                    margin-bottom: 20px;
                }

                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: 600;
                    color: #555;
                }

                .form-group input[type="url"],
                .form-group input[type="number"] {
                    width: 100%;
                    padding: 10px;
                    border: 2px solid #ddd;
                    border-radius: 6px;
                    font-size: 14px;
                    transition: border-color 0.2s;
                }

                .form-group input[type="url"]:focus,
                .form-group input[type="number"]:focus {
                    outline: none;
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }

                .form-group input[type="checkbox"] {
                    margin-right: 8px;
                    transform: scale(1.2);
                }

                .help-text {
                    display: block;
                    margin-top: 5px;
                    color: #666;
                    font-size: 12px;
                }

                .help-text a {
                    color: #667eea;
                    text-decoration: none;
                }

                .help-text a:hover {
                    text-decoration: underline;
                }

                .config-footer {
                    padding: 20px 25px;
                    border-top: 1px solid #eee;
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                    background: #f8f9fa;
                    border-radius: 0 0 12px 12px;
                }

                .btn-test {
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                }

                .btn-secondary {
                    background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
                }

                .btn-primary {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }

                .modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1001;
                }

                .modal-content {
                    background: white;
                    border-radius: 12px;
                    width: 90%;
                    max-width: 500px;
                    max-height: 80vh;
                    overflow-y: auto;
                }

                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px;
                    border-bottom: 1px solid #eee;
                    background: #f8f9fa;
                    border-radius: 12px 12px 0 0;
                }

                .modal-header h4 {
                    margin: 0;
                    color: #333;
                }

                .modal-header .close-btn {
                    color: #333;
                }

                .modal-body {
                    padding: 20px;
                }

                .modal-body ol {
                    padding-left: 20px;
                }

                .modal-body li {
                    margin-bottom: 8px;
                    line-height: 1.5;
                }

                .modal-body a {
                    color: #667eea;
                    text-decoration: none;
                }

                .modal-body a:hover {
                    text-decoration: underline;
                }

                .config-button {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 15px;
                    border-radius: 50%;
                    font-size: 20px;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    transition: transform 0.2s, box-shadow 0.2s;
                    z-index: 999;
                    width: 60px;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .config-button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
                }

                @media (max-width: 768px) {
                    .config-content {
                        width: 95%;
                        margin: 10px;
                    }
                    
                    .config-footer {
                        flex-direction: column;
                    }
                    
                    .config-footer .btn {
                        width: 100%;
                        margin-bottom: 10px;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);

        // Add floating config button
        const configButton = `
            <button id="openConfig" class="config-button" title="Configure Slack Alerts">
                ⚙️
            </button>
        `;
        document.body.insertAdjacentHTML('beforeend', configButton);
    }

    bindEvents() {
        // Open config panel
        document.getElementById('openConfig').addEventListener('click', () => {
            this.showPanel();
        });

        // Close config panel
        document.getElementById('closeConfig').addEventListener('click', () => {
            this.hidePanel();
        });

        // Show webhook help
        document.getElementById('webhookHelp').addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('webhookModal').style.display = 'flex';
        });

        // Close webhook help modal
        document.getElementById('closeModal').addEventListener('click', () => {
            document.getElementById('webhookModal').style.display = 'none';
        });

        // Test Slack connection
        document.getElementById('testSlack').addEventListener('click', async () => {
            await this.testSlackConnection();
        });

        // Reset configuration
        document.getElementById('resetConfig').addEventListener('click', () => {
            this.resetToDefaults();
        });

        // Save configuration
        document.getElementById('saveConfig').addEventListener('click', () => {
            this.saveConfiguration();
        });

        // Close modal when clicking outside
        document.getElementById('configPanel').addEventListener('click', (e) => {
            if (e.target.id === 'configPanel') {
                this.hidePanel();
            }
        });

        document.getElementById('webhookModal').addEventListener('click', (e) => {
            if (e.target.id === 'webhookModal') {
                document.getElementById('webhookModal').style.display = 'none';
            }
        });
    }

    showPanel() {
        this.loadCurrentConfiguration();
        document.getElementById('configPanel').style.display = 'flex';
        this.isVisible = true;
    }

    hidePanel() {
        document.getElementById('configPanel').style.display = 'none';
        this.isVisible = false;
    }

    loadCurrentConfiguration() {
        const config = this.alertSystem.config;

        // Load Slack settings
        document.getElementById('webhookUrl').value = config.webhookUrl || '';
        document.getElementById('enableAlerts').checked = config.enabled || false;

        // Load thresholds
        document.getElementById('priceVariance').value = config.thresholds.priceVariance || 5.0;
        document.getElementById('dailyPriceChange').value = config.thresholds.dailyPriceChange || 10.0;
        document.getElementById('predictionAccuracy').value = config.thresholds.predictionAccuracy || 60.0;
        document.getElementById('volumeVariance').value = config.thresholds.volumeVariance || 25.0;
        document.getElementById('consecutiveLosses').value = config.thresholds.consecutiveLosses || 3;

        // Load alert settings
        document.getElementById('alertCooldown').value = (config.alertCooldown || 300000) / 60000; // Convert to minutes
    }

    saveConfiguration() {
        try {
            const newConfig = {
                webhookUrl: document.getElementById('webhookUrl').value.trim(),
                enabled: document.getElementById('enableAlerts').checked,
                thresholds: {
                    priceVariance: parseFloat(document.getElementById('priceVariance').value) || 5.0,
                    dailyPriceChange: parseFloat(document.getElementById('dailyPriceChange').value) || 10.0,
                    predictionAccuracy: parseFloat(document.getElementById('predictionAccuracy').value) || 60.0,
                    volumeVariance: parseFloat(document.getElementById('volumeVariance').value) || 25.0,
                    consecutiveLosses: parseInt(document.getElementById('consecutiveLosses').value) || 3
                },
                alertCooldown: (parseInt(document.getElementById('alertCooldown').value) || 5) * 60000 // Convert to milliseconds
            };

            this.alertSystem.updateConfiguration(newConfig);
            
            // Show success message
            this.showMessage('Configuration saved successfully! 🎉', 'success');
            
            // Hide panel after a delay
            setTimeout(() => {
                this.hidePanel();
            }, 1500);

        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showMessage('Error saving configuration. Please try again.', 'error');
        }
    }

    resetToDefaults() {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            // Reset to default values
            document.getElementById('webhookUrl').value = '';
            document.getElementById('enableAlerts').checked = false;
            document.getElementById('priceVariance').value = 5.0;
            document.getElementById('dailyPriceChange').value = 10.0;
            document.getElementById('predictionAccuracy').value = 60.0;
            document.getElementById('volumeVariance').value = 25.0;
            document.getElementById('consecutiveLosses').value = 3;
            document.getElementById('alertCooldown').value = 5;

            this.showMessage('Settings reset to defaults', 'info');
        }
    }

    async testSlackConnection() {
        const webhookUrl = document.getElementById('webhookUrl').value.trim();
        
        if (!webhookUrl) {
            this.showMessage('Please enter a Slack webhook URL first', 'error');
            return;
        }

        // Temporarily update the webhook URL for testing
        const originalUrl = this.alertSystem.config.webhookUrl;
        const originalEnabled = this.alertSystem.config.enabled;
        
        this.alertSystem.config.webhookUrl = webhookUrl;
        this.alertSystem.config.enabled = true;

        try {
            const button = document.getElementById('testSlack');
            button.disabled = true;
            button.textContent = '🔄 Testing...';

            const success = await this.alertSystem.sendTestMessage();
            
            if (success) {
                this.showMessage('Test message sent successfully! Check your Slack channel. ✅', 'success');
            } else {
                this.showMessage('Failed to send test message. Please check your webhook URL.', 'error');
            }

        } catch (error) {
            console.error('Test failed:', error);
            this.showMessage('Test failed. Please check your webhook URL and try again.', 'error');
        } finally {
            // Restore original settings
            this.alertSystem.config.webhookUrl = originalUrl;
            this.alertSystem.config.enabled = originalEnabled;
            
            const button = document.getElementById('testSlack');
            button.disabled = false;
            button.textContent = '🧪 Test Connection';
        }
    }

    showMessage(message, type = 'info') {
        // Create or update message element
        let messageEl = document.getElementById('configMessage');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'configMessage';
            messageEl.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                font-weight: 600;
                z-index: 1002;
                min-width: 250px;
                text-align: center;
                transition: all 0.3s ease;
            `;
            document.body.appendChild(messageEl);
        }

        // Set message and style based on type
        messageEl.textContent = message;
        
        const styles = {
            success: { background: '#d4edda', color: '#155724', border: '1px solid #c3e6cb' },
            error: { background: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb' },
            info: { background: '#d1ecf1', color: '#0c5460', border: '1px solid #bee5eb' }
        };

        const style = styles[type] || styles.info;
        Object.assign(messageEl.style, style);

        // Show and auto-hide
        messageEl.style.display = 'block';
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 4000);
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConfigPanel;
}