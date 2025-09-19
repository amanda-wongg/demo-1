/**
 * Slack Alert System for Stock Market Prediction Game
 * Monitors variances and sends alerts when thresholds are exceeded
 */

class SlackAlertSystem {
    constructor() {
        // Default configuration - can be customized via UI
        this.config = {
            webhookUrl: '', // Will be set via configuration panel
            thresholds: {
                priceVariance: 5.0,        // Alert if price variance > 5%
                predictionAccuracy: 60.0,   // Alert if accuracy drops below 60%
                volumeVariance: 25.0,       // Alert if volume variance > 25%
                consecutiveLosses: 3,       // Alert after 3 consecutive wrong predictions
                dailyPriceChange: 10.0      // Alert if daily price change > 10%
            },
            enabled: false
        };
        
        // Tracking variables
        this.gameStats = {
            totalPredictions: 0,
            correctPredictions: 0,
            consecutiveLosses: 0,
            lastAlertTime: null,
            alertCooldown: 300000 // 5 minutes cooldown between similar alerts
        };
        
        // Load configuration from localStorage if available
        this.loadConfiguration();
    }

    /**
     * Load configuration from localStorage
     */
    loadConfiguration() {
        try {
            const savedConfig = localStorage.getItem('slackAlertConfig');
            if (savedConfig) {
                const parsed = JSON.parse(savedConfig);
                this.config = { ...this.config, ...parsed };
            }
        } catch (error) {
            console.warn('Failed to load Slack alert configuration:', error);
        }
    }

    /**
     * Save configuration to localStorage
     */
    saveConfiguration() {
        try {
            localStorage.setItem('slackAlertConfig', JSON.stringify(this.config));
        } catch (error) {
            console.warn('Failed to save Slack alert configuration:', error);
        }
    }

    /**
     * Update configuration
     */
    updateConfiguration(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.saveConfiguration();
    }

    /**
     * Check if alerts are enabled and webhook URL is configured
     */
    isConfigured() {
        return this.config.enabled && this.config.webhookUrl && this.config.webhookUrl.trim() !== '';
    }

    /**
     * Send a message to Slack
     */
    async sendSlackMessage(message, color = '#36a64f') {
        if (!this.isConfigured()) {
            console.log('Slack alerts not configured. Message:', message);
            return false;
        }

        try {
            const payload = {
                attachments: [{
                    color: color,
                    fields: [{
                        title: "Stock Market Prediction Game Alert",
                        value: message,
                        short: false
                    }],
                    footer: "Stock Prediction Game",
                    ts: Math.floor(Date.now() / 1000)
                }]
            };

            const response = await fetch(this.config.webhookUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            console.log('Slack message sent successfully');
            return true;

        } catch (error) {
            console.error('Failed to send Slack message:', error);
            return false;
        }
    }

    /**
     * Check if enough time has passed since last alert of same type
     */
    canSendAlert(alertType) {
        const now = Date.now();
        const lastAlert = this.gameStats[`lastAlert_${alertType}`];
        
        if (!lastAlert) {
            return true;
        }
        
        return (now - lastAlert) > this.config.alertCooldown;
    }

    /**
     * Record that an alert was sent
     */
    recordAlert(alertType) {
        this.gameStats[`lastAlert_${alertType}`] = Date.now();
    }

    /**
     * Monitor price variance and send alerts
     */
    async checkPriceVariance(stockData, ticker) {
        if (!this.isConfigured() || !stockData || stockData.length < 2) {
            return;
        }

        try {
            // Calculate recent price variance (last 5 days)
            const recentData = stockData.slice(-5);
            if (recentData.length < 2) return;

            const prices = recentData.map(d => d.close);
            const avgPrice = prices.reduce((sum, price) => sum + price, 0) / prices.length;
            
            // Calculate variance percentage
            const variance = prices.reduce((sum, price) => {
                const diff = price - avgPrice;
                return sum + (diff * diff);
            }, 0) / prices.length;
            
            const stdDev = Math.sqrt(variance);
            const variancePercent = (stdDev / avgPrice) * 100;

            if (variancePercent > this.config.thresholds.priceVariance && this.canSendAlert('priceVariance')) {
                const message = `🚨 *High Price Variance Alert*\n` +
                    `Stock: *${ticker}*\n` +
                    `Current Variance: *${variancePercent.toFixed(2)}%*\n` +
                    `Threshold: ${this.config.thresholds.priceVariance}%\n` +
                    `Current Price: $${recentData[recentData.length - 1].close.toFixed(2)}\n` +
                    `5-day Average: $${avgPrice.toFixed(2)}`;

                await this.sendSlackMessage(message, '#ff9900');
                this.recordAlert('priceVariance');
            }

        } catch (error) {
            console.error('Error checking price variance:', error);
        }
    }

    /**
     * Monitor daily price changes
     */
    async checkDailyPriceChange(previousPrice, currentPrice, ticker) {
        if (!this.isConfigured() || !previousPrice || !currentPrice) {
            return;
        }

        try {
            const changePercent = Math.abs(((currentPrice - previousPrice) / previousPrice) * 100);

            if (changePercent > this.config.thresholds.dailyPriceChange && this.canSendAlert('dailyChange')) {
                const direction = currentPrice > previousPrice ? '📈 UP' : '📉 DOWN';
                const changeAmount = Math.abs(currentPrice - previousPrice);
                
                const message = `🚨 *Large Daily Price Movement*\n` +
                    `Stock: *${ticker}*\n` +
                    `Direction: ${direction}\n` +
                    `Change: *${changePercent.toFixed(2)}%* ($${changeAmount.toFixed(2)})\n` +
                    `Threshold: ${this.config.thresholds.dailyPriceChange}%\n` +
                    `Previous: $${previousPrice.toFixed(2)} → Current: $${currentPrice.toFixed(2)}`;

                await this.sendSlackMessage(message, '#ff6b6b');
                this.recordAlert('dailyChange');
            }

        } catch (error) {
            console.error('Error checking daily price change:', error);
        }
    }

    /**
     * Monitor prediction accuracy
     */
    async checkPredictionAccuracy(isCorrect, ticker) {
        if (!this.isConfigured()) {
            return;
        }

        try {
            // Update stats
            this.gameStats.totalPredictions++;
            if (isCorrect) {
                this.gameStats.correctPredictions++;
                this.gameStats.consecutiveLosses = 0;
            } else {
                this.gameStats.consecutiveLosses++;
            }

            const accuracy = (this.gameStats.correctPredictions / this.gameStats.totalPredictions) * 100;

            // Check accuracy threshold (only after minimum predictions)
            if (this.gameStats.totalPredictions >= 5 && 
                accuracy < this.config.thresholds.predictionAccuracy && 
                this.canSendAlert('accuracy')) {
                
                const message = `📊 *Low Prediction Accuracy Alert*\n` +
                    `Stock: *${ticker}*\n` +
                    `Current Accuracy: *${accuracy.toFixed(1)}%*\n` +
                    `Threshold: ${this.config.thresholds.predictionAccuracy}%\n` +
                    `Correct Predictions: ${this.gameStats.correctPredictions}/${this.gameStats.totalPredictions}\n` +
                    `Consider reviewing your prediction strategy!`;

                await this.sendSlackMessage(message, '#ffa500');
                this.recordAlert('accuracy');
            }

            // Check consecutive losses
            if (this.gameStats.consecutiveLosses >= this.config.thresholds.consecutiveLosses && 
                this.canSendAlert('consecutive')) {
                
                const message = `🔥 *Consecutive Losses Alert*\n` +
                    `Stock: *${ticker}*\n` +
                    `Consecutive Wrong Predictions: *${this.gameStats.consecutiveLosses}*\n` +
                    `Threshold: ${this.config.thresholds.consecutiveLosses}\n` +
                    `Time to reassess your strategy!`;

                await this.sendSlackMessage(message, '#dc3545');
                this.recordAlert('consecutive');
            }

        } catch (error) {
            console.error('Error checking prediction accuracy:', error);
        }
    }

    /**
     * Monitor volume variance
     */
    async checkVolumeVariance(stockData, ticker) {
        if (!this.isConfigured() || !stockData || stockData.length < 2) {
            return;
        }

        try {
            // Calculate recent volume variance (last 5 days)
            const recentData = stockData.slice(-5);
            if (recentData.length < 2) return;

            const volumes = recentData.map(d => d.volume);
            const avgVolume = volumes.reduce((sum, vol) => sum + vol, 0) / volumes.length;
            
            const currentVolume = volumes[volumes.length - 1];
            const volumeChangePercent = Math.abs(((currentVolume - avgVolume) / avgVolume) * 100);

            if (volumeChangePercent > this.config.thresholds.volumeVariance && this.canSendAlert('volume')) {
                const direction = currentVolume > avgVolume ? 'Higher' : 'Lower';
                
                const message = `📊 *Unusual Volume Activity*\n` +
                    `Stock: *${ticker}*\n` +
                    `Volume Change: *${volumeChangePercent.toFixed(1)}%* ${direction}\n` +
                    `Threshold: ${this.config.thresholds.volumeVariance}%\n` +
                    `Current Volume: ${currentVolume.toLocaleString()}\n` +
                    `5-day Average: ${Math.round(avgVolume).toLocaleString()}`;

                await this.sendSlackMessage(message, '#17a2b8');
                this.recordAlert('volume');
            }

        } catch (error) {
            console.error('Error checking volume variance:', error);
        }
    }

    /**
     * Send a test message to verify Slack integration
     */
    async sendTestMessage() {
        const message = `✅ *Slack Integration Test*\n` +
            `Your Stock Market Prediction Game is now connected to Slack!\n` +
            `Alerts will be sent when variance thresholds are exceeded.\n` +
            `Test sent at: ${new Date().toLocaleString()}`;

        return await this.sendSlackMessage(message, '#28a745');
    }

    /**
     * Reset game statistics
     */
    resetStats() {
        this.gameStats = {
            totalPredictions: 0,
            correctPredictions: 0,
            consecutiveLosses: 0,
            lastAlertTime: null,
            alertCooldown: 300000
        };
    }

    /**
     * Get current statistics
     */
    getStats() {
        return {
            ...this.gameStats,
            accuracy: this.gameStats.totalPredictions > 0 ? 
                (this.gameStats.correctPredictions / this.gameStats.totalPredictions) * 100 : 0
        };
    }

    /**
     * Generate summary report
     */
    async sendSummaryReport(ticker, gameData) {
        if (!this.isConfigured()) {
            return;
        }

        try {
            const stats = this.getStats();
            const totalGames = Math.floor(stats.totalPredictions / 5) || 1; // Assuming ~5 predictions per game
            
            const message = `📈 *Game Session Summary*\n` +
                `Stock: *${ticker}*\n` +
                `Total Predictions: ${stats.totalPredictions}\n` +
                `Accuracy: *${stats.accuracy.toFixed(1)}%*\n` +
                `Correct: ${stats.correctPredictions} | Incorrect: ${stats.totalPredictions - stats.correctPredictions}\n` +
                `Games Played: ~${totalGames}\n` +
                `Session completed at: ${new Date().toLocaleString()}`;

            await this.sendSlackMessage(message, '#6f42c1');

        } catch (error) {
            console.error('Error sending summary report:', error);
        }
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SlackAlertSystem;
}