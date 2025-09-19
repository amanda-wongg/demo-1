# 🚨 Slack Alert System for Stock Market Prediction Game

This guide explains how to set up and use the Slack alert system that monitors variance thresholds in your stock market prediction game.

## 📋 Overview

The Slack Alert System monitors various metrics and sends alerts to your Slack channel when:
- Price variance exceeds your threshold
- Daily price changes are unusually large
- Prediction accuracy drops below your target
- Trading volume shows unusual activity
- You have consecutive incorrect predictions

## 🛠️ Setup Instructions

### Step 1: Create a Slack Webhook

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. Name your app (e.g., "Stock Market Alerts") and select your workspace
4. In the left sidebar, click **"Incoming Webhooks"**
5. Toggle **"Activate Incoming Webhooks"** to **On**
6. Click **"Add New Webhook to Workspace"**
7. Choose the channel where you want alerts sent
8. Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)

### Step 2: Configure the Alert System

1. Open your Stock Market Prediction Game
2. Click the **⚙️ configuration button** in the bottom-right corner
3. Paste your Slack webhook URL in the configuration panel
4. Adjust the threshold values according to your preferences:

#### Default Thresholds:
- **Price Variance**: 5.0% - Alert when price variance exceeds this percentage
- **Daily Price Change**: 10.0% - Alert when daily price change exceeds this percentage  
- **Prediction Accuracy**: 60.0% - Alert when accuracy drops below this percentage
- **Volume Variance**: 25.0% - Alert when trading volume variance exceeds this percentage
- **Consecutive Losses**: 3 - Alert after this many wrong predictions in a row

5. Enable alerts by checking **"Enable Slack Alerts"**
6. Click **"Test Connection"** to verify your setup
7. Click **"Save Configuration"**

## 📊 Types of Alerts

### 🚨 High Price Variance Alert
Triggered when the stock's price variance over the last 5 days exceeds your threshold.
```
🚨 High Price Variance Alert
Stock: MSFT
Current Variance: 7.25%
Threshold: 5%
Current Price: $420.50
5-day Average: $415.30
```

### 📈 Large Daily Price Movement
Triggered when the daily price change exceeds your threshold.
```
🚨 Large Daily Price Movement
Stock: AAPL
Direction: 📈 UP
Change: 12.5% ($18.75)
Threshold: 10%
Previous: $150.00 → Current: $168.75
```

### 📊 Low Prediction Accuracy Alert
Triggered when your prediction accuracy drops below your target (after minimum 5 predictions).
```
📊 Low Prediction Accuracy Alert
Stock: GOOGL
Current Accuracy: 45.0%
Threshold: 60%
Correct Predictions: 9/20
Consider reviewing your prediction strategy!
```

### 🔥 Consecutive Losses Alert
Triggered after a streak of incorrect predictions.
```
🔥 Consecutive Losses Alert
Stock: TSLA
Consecutive Wrong Predictions: 4
Threshold: 3
Time to reassess your strategy!
```

### 📊 Unusual Volume Activity
Triggered when trading volume variance exceeds your threshold.
```
📊 Unusual Volume Activity
Stock: NVDA
Volume Change: 35.2% Higher
Threshold: 25%
Current Volume: 45,230,000
5-day Average: 33,500,000
```

### 📈 Game Session Summary
Sent automatically when you finish a game session.
```
📈 Game Session Summary
Stock: MSFT
Total Predictions: 15
Accuracy: 73.3%
Correct: 11 | Incorrect: 4
Games Played: ~3
Session completed at: 12/19/2024, 2:30:45 PM
```

## ⚙️ Configuration Options

### Alert Thresholds
- **Price Variance Threshold**: Monitor price volatility (0-100%)
- **Daily Price Change Threshold**: Track large daily movements (0-100%)
- **Minimum Prediction Accuracy**: Set accuracy targets (0-100%)
- **Volume Variance Threshold**: Monitor unusual trading activity (0-100%)
- **Consecutive Losses Alert**: Set tolerance for losing streaks (1-10)

### Alert Settings
- **Alert Cooldown**: Minimum time between similar alerts (1-60 minutes)
- **Enable/Disable**: Toggle all alerts on/off

## 🔧 Advanced Features

### Alert Cooldown
The system prevents spam by implementing a cooldown period between similar alerts. Default is 5 minutes.

### Automatic Statistics Tracking
The system automatically tracks:
- Total predictions made
- Prediction accuracy percentage
- Consecutive wins/losses
- Game session statistics

### Local Storage
Your configuration is saved locally in your browser and persists between sessions.

## 🧪 Testing Your Setup

1. Click **"Test Connection"** in the configuration panel
2. Check your Slack channel for the test message
3. If successful, you'll see: ✅ "Test message sent successfully!"
4. If failed, verify your webhook URL and try again

## 🚨 Troubleshooting

### Common Issues:

**❌ Test message fails**
- Verify your webhook URL is correct and complete
- Check that your Slack app has proper permissions
- Ensure your webhook is activated in Slack

**❌ No alerts received**
- Confirm "Enable Slack Alerts" is checked
- Verify your thresholds aren't set too high/low
- Check that enough time has passed since the last similar alert (cooldown period)

**❌ Too many alerts**
- Increase your threshold values
- Increase the alert cooldown period
- Consider disabling specific alert types you don't need

### Webhook URL Format
Your webhook URL should look like:
```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
```

## 🔒 Security Notes

- Keep your webhook URL private and secure
- Don't share your webhook URL in public repositories
- Consider regenerating your webhook if compromised
- The webhook URL contains sensitive authentication information

## 🎯 Best Practices

1. **Start with default thresholds** and adjust based on your needs
2. **Test your setup** before relying on alerts
3. **Set appropriate cooldown periods** to avoid spam
4. **Monitor your Slack channel** to ensure alerts are working
5. **Adjust thresholds** based on the volatility of stocks you're analyzing

## 📱 Mobile Compatibility

The configuration panel is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

## 🔄 Updates and Maintenance

The alert system automatically:
- Saves your configuration
- Tracks statistics across sessions
- Handles errors gracefully
- Provides user feedback

---

**Enjoy enhanced monitoring of your stock market predictions! 📈📊**

For additional help or issues, check the browser console for detailed error messages.