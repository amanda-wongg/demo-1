class StockPredictionGame {
    constructor() {
        this.apiKey = '3CQXJRM3U5UUGXN4';
        this.chart = null;
        this.stockData = [];
        this.gameData = [];
        this.currentDateIndex = 0;
        this.score = 0;
        this.ticker = '';
        this.startDate = null;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        document.getElementById('startGame').addEventListener('click', () => this.startGame());
        document.getElementById('tickerInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.startGame();
        });
        document.getElementById('predictUp').addEventListener('click', () => this.makePrediction('up'));
        document.getElementById('predictDown').addEventListener('click', () => this.makePrediction('down'));
        document.getElementById('newGame').addEventListener('click', () => this.resetGame());
    }

    async startGame() {
        const tickerInput = document.getElementById('tickerInput');
        this.ticker = tickerInput.value.trim().toUpperCase();
        
        if (!this.ticker) {
            this.showError('Please enter a stock ticker symbol.');
            return;
        }

        this.showLoading(true);
        this.hideError();

        try {
            // Fetch stock data from Alpha Vantage
            const stockData = await this.fetchStockData(this.ticker);
            
            if (!stockData || stockData.length === 0) {
                throw new Error('Invalid stock ticker or no data available. Please try another ticker.');
            }

            this.stockData = stockData;
            this.setupGame();
            
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async fetchStockData(ticker) {
        try {
            // Using Alpha Vantage TIME_SERIES_DAILY function
            const response = await fetch(
                `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${ticker}&apikey=${this.apiKey}&outputsize=full`
            );
            
            if (!response.ok) {
                throw new Error('Failed to fetch stock data');
            }
            
            const data = await response.json();
            
            // Check for API errors
            if (data['Error Message']) {
                throw new Error('Invalid stock ticker symbol. Please enter a valid ticker.');
            }
            
            if (data['Note']) {
                throw new Error('API rate limit exceeded. Please try again in a moment.');
            }

            const timeSeries = data['Time Series (Daily)'];
            if (!timeSeries) {
                throw new Error('No stock data available for this ticker.');
            }

            // Convert to array format and sort by date
            const stockArray = Object.entries(timeSeries).map(([date, values]) => ({
                date: new Date(date),
                open: parseFloat(values['1. open']),
                high: parseFloat(values['2. high']),
                low: parseFloat(values['3. low']),
                close: parseFloat(values['4. close']),
                volume: parseInt(values['5. volume'])
            })).sort((a, b) => a.date - b.date);

            return stockArray;
            
        } catch (error) {
            console.error('Error fetching stock data:', error);
            throw error;
        }
    }

    generateRandomStartDate() {
        const today = new Date();
        const oneWeekAgo = new Date(today);
        oneWeekAgo.setDate(today.getDate() - 7);
        
        const hundredDaysAgo = new Date(today);
        hundredDaysAgo.setDate(today.getDate() - 100);
        
        // Generate random date between 100 and 7 days ago
        const timeDiff = oneWeekAgo.getTime() - hundredDaysAgo.getTime();
        const randomTime = Math.random() * timeDiff;
        const randomDate = new Date(hundredDaysAgo.getTime() + randomTime);
        
        // Ensure it's a weekday (Monday = 1, Friday = 5)
        while (randomDate.getDay() === 0 || randomDate.getDay() === 6) {
            randomDate.setDate(randomDate.getDate() - 1);
        }
        
        // Check if we have data for this date and surrounding dates
        const dateStr = this.formatDate(randomDate);
        const dataIndex = this.stockData.findIndex(item => this.formatDate(item.date) === dateStr);
        
        if (dataIndex >= 7) { // Need at least 7 days before
            return randomDate;
        } else {
            // Find a suitable date with enough historical data
            for (let i = 7; i < this.stockData.length - 10; i++) {
                const checkDate = this.stockData[i].date;
                if (checkDate.getDay() !== 0 && checkDate.getDay() !== 6) { // Weekday
                    const daysDiff = Math.floor((today - checkDate) / (1000 * 60 * 60 * 24));
                    if (daysDiff >= 7 && daysDiff <= 100) {
                        return checkDate;
                    }
                }
            }
        }
        
        // Fallback: use a date 30 days ago
        const fallbackDate = new Date(today);
        fallbackDate.setDate(today.getDate() - 30);
        while (fallbackDate.getDay() === 0 || fallbackDate.getDay() === 6) {
            fallbackDate.setDate(fallbackDate.getDate() - 1);
        }
        return fallbackDate;
    }

    setupGame() {
        this.startDate = this.generateRandomStartDate();
        
        // Find the index of start date in our data
        const startDateStr = this.formatDate(this.startDate);
        const startIndex = this.stockData.findIndex(item => this.formatDate(item.date) === startDateStr);
        
        if (startIndex === -1 || startIndex < 7) {
            throw new Error('Insufficient historical data for this ticker. Please try another.');
        }
        
        // Prepare game data: 7 days before start date + start date + future days for predictions
        this.gameData = this.stockData.slice(startIndex - 7, startIndex + 20); // Include some future data
        this.currentDateIndex = 7; // Start at the randomly selected date (8th item, 0-indexed)
        this.score = 0;
        
        // Update display
        this.updateStockInfo();
        this.updateGameDisplay();
        this.createChart();
        
        // Show game interface
        document.querySelector('.chart-container').style.display = 'block';
        document.getElementById('gameInfo').style.display = 'block';
        document.getElementById('tickerInput').disabled = true;
        document.getElementById('startGame').disabled = true;
    }

    updateStockInfo() {
        const currentData = this.gameData[this.currentDateIndex];
        document.getElementById('stockName').textContent = `${this.ticker} Stock`;
        document.getElementById('currentPrice').textContent = `Current Price: $${currentData.close.toFixed(2)}`;
        document.getElementById('stockInfo').style.display = 'block';
    }

    updateGameDisplay() {
        const currentData = this.gameData[this.currentDateIndex];
        document.getElementById('score').textContent = this.score;
        document.getElementById('currentDate').textContent = this.formatDisplayDate(currentData.date);
        
        // Enable prediction buttons if there's a next day
        const hasNextDay = this.currentDateIndex + 1 < this.gameData.length;
        document.getElementById('predictUp').disabled = !hasNextDay;
        document.getElementById('predictDown').disabled = !hasNextDay;
        
        if (!hasNextDay) {
            document.getElementById('resultMessage').innerHTML = 
                '<div class="correct">Game completed! No more data available.</div>';
            document.getElementById('resultMessage').style.display = 'block';
            document.getElementById('newGame').style.display = 'inline-block';
        }
    }

    createChart() {
        const ctx = document.getElementById('stockChart').getContext('2d');
        
        // Prepare data for chart (show current data up to current date)
        const chartData = this.gameData.slice(0, this.currentDateIndex + 1);
        
        if (this.chart) {
            this.chart.destroy();
        }
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.map(item => this.formatDisplayDate(item.date)),
                datasets: [{
                    label: `${this.ticker} Price`,
                    data: chartData.map(item => item.close),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.1,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Price ($)'
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    async makePrediction(direction) {
        const currentData = this.gameData[this.currentDateIndex];
        const nextData = this.gameData[this.currentDateIndex + 1];
        
        if (!nextData) {
            this.showError('No more data available for predictions.');
            return;
        }
        
        // Disable prediction buttons
        document.getElementById('predictUp').disabled = true;
        document.getElementById('predictDown').disabled = true;
        
        // Check if prediction is correct
        const priceChange = nextData.close - currentData.close;
        const actualDirection = priceChange > 0 ? 'up' : 'down';
        const isCorrect = direction === actualDirection;
        
        // Update score
        if (isCorrect) {
            this.score++;
        }
        
        // Move to next day
        this.currentDateIndex++;
        
        // Show result
        const resultDiv = document.getElementById('resultMessage');
        const priceChangeText = priceChange > 0 ? `+$${priceChange.toFixed(2)}` : `-$${Math.abs(priceChange).toFixed(2)}`;
        const emoji = isCorrect ? '✅' : '❌';
        
        resultDiv.innerHTML = `
            ${emoji} ${isCorrect ? 'Correct!' : 'Wrong!'} 
            The price ${actualDirection === 'up' ? 'went UP' : 'went DOWN'} by ${priceChangeText} 
            to $${nextData.close.toFixed(2)}
        `;
        resultDiv.className = `result-message ${isCorrect ? 'correct' : 'incorrect'}`;
        resultDiv.style.display = 'block';
        
        // Update displays
        this.updateStockInfo();
        this.updateGameDisplay();
        this.updateChart();
        
        // Hide result message after a delay and re-enable buttons for next prediction
        setTimeout(() => {
            resultDiv.style.display = 'none';
            const hasNextDay = this.currentDateIndex + 1 < this.gameData.length;
            if (hasNextDay) {
                document.getElementById('predictUp').disabled = false;
                document.getElementById('predictDown').disabled = false;
            }
        }, 3000);
    }

    updateChart() {
        if (!this.chart) return;
        
        // Update chart data to include the new day
        const chartData = this.gameData.slice(0, this.currentDateIndex + 1);
        this.chart.data.labels = chartData.map(item => this.formatDisplayDate(item.date));
        this.chart.data.datasets[0].data = chartData.map(item => item.close);
        this.chart.update('active');
    }

    resetGame() {
        // Reset all game state
        this.chart = null;
        this.stockData = [];
        this.gameData = [];
        this.currentDateIndex = 0;
        this.score = 0;
        this.ticker = '';
        this.startDate = null;
        
        // Reset UI
        document.getElementById('tickerInput').value = '';
        document.getElementById('tickerInput').disabled = false;
        document.getElementById('startGame').disabled = false;
        document.querySelector('.chart-container').style.display = 'none';
        document.getElementById('gameInfo').style.display = 'none';
        document.getElementById('stockInfo').style.display = 'none';
        document.getElementById('resultMessage').style.display = 'none';
        document.getElementById('newGame').style.display = 'none';
        
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        this.hideError();
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    formatDisplayDate(date) {
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });
    }

    showLoading(show) {
        document.getElementById('loading').style.display = show ? 'block' : 'none';
    }

    showError(message) {
        const errorDiv = document.getElementById('error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    hideError() {
        document.getElementById('error').style.display = 'none';
    }
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new StockPredictionGame();
});