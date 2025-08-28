# Stock Market Prediction Game

A fun and interactive web-based game where you predict stock price movements using real market data from Alpha Vantage API.

## 🎯 How to Play

1. **Enter a Stock Ticker**: Input any valid stock symbol (e.g., MSFT, AAPL, GOOGL)
2. **View Historical Data**: The game shows you 7 days of price history leading up to a randomly selected start date
3. **Make Predictions**: Predict whether the stock will go UP or DOWN the next day
4. **Track Your Score**: Earn points for correct predictions and see how well you can read the market!

## ✨ Features

- **Real Stock Data**: Uses Alpha Vantage API for actual market data
- **Interactive Charts**: Beautiful line charts powered by Chart.js
- **Smart Date Selection**: Randomly picks weekday start dates between 1-100 days ago
- **Progressive Revelation**: Stock data is revealed day by day as you make predictions
- **Responsive Design**: Works great on desktop and mobile devices
- **Error Handling**: Validates stock tickers and provides helpful error messages

## 🚀 Live Demo

The game is deployed on GitHub Pages: [Play Now!](https://yourusername.github.io/stock-prediction-game/)

## 🛠 Setup for Development

1. Clone this repository
2. Open `index.html` in your browser
3. No build process required - it's a vanilla JavaScript application!

## 📊 API Information

This game uses the [Alpha Vantage API](https://www.alphavantage.co/) to fetch real stock market data. The API key is included for demonstration purposes, but you may want to get your own free API key if you plan to use this extensively.

## 🎮 Game Rules

- The game randomly selects a start date (weekday, non-holiday) between 1 week and 100 days ago
- You see 7 days of historical price data before the start date
- Predict if the price will go up or down the next trading day
- Correct predictions earn 1 point, incorrect predictions earn 0 points
- Continue predicting until you choose to start a new game or run out of data

## 🔧 Technical Details

- **Frontend**: Pure HTML, CSS, and JavaScript
- **Charts**: Chart.js for interactive line graphs
- **API**: Alpha Vantage for real-time stock data
- **Deployment**: GitHub Pages ready

## 📱 Mobile Friendly

The game is fully responsive and works great on mobile devices, tablets, and desktop computers.

Enjoy predicting the market! 📈📉