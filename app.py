from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import requests
from datetime import datetime
import os

app = FastAPI(title="My Portfolio API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1d")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            previous_close = info.get('previousClose', 0)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            return {
                "ticker": ticker,
                "name": info.get('shortName', ticker),
                "current_price": round(current_price, 2),
                "previous_close": round(previous_close, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "currency": info.get('currency', 'USD'),
                "timestamp": datetime.now().isoformat()
            }
        return None
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def get_exchange_rate(from_currency, to_currency):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if to_currency in data['rates']:
            rate = data['rates'][to_currency]
            return {
                "from": from_currency,
                "to": to_currency,
                "rate": round(rate, 4),
                "last_update": data['date'],
                "timestamp": datetime.now().isoformat()
            }
        return None
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

@app.get("/", response_class=HTMLResponse)
def root():
    """웹 인터페이스 - 모바일 최적화"""
    html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>My Portfolio</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #000;
            color: #fff;
            padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
            overflow-x: hidden;
        }
        
        .header {
            position: sticky;
            top: 0;
            background: #000;
            padding: 20px 15px 10px;
            z-index: 100;
            border-bottom: 1px solid #333;
        }
        
        .header h1 {
            font-size: 28px;
            margin-bottom: 5px;
        }
        
        .update-time {
            font-size: 12px;
            color: #888;
        }
        
        .content {
            padding: 15px;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: bold;
            margin: 20px 0 10px;
            padding-bottom: 8px;
            border-bottom: 2px solid #444;
        }
        
        .stock-card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            touch-action: manipulation;
        }
        
        .stock-info {
            flex: 1;
        }
        
        .stock-name {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 4px;
        }
        
        .stock-ticker {
            font-size: 14px;
            color: #888;
        }
        
        .stock-price {
            text-align: right;
        }
        
        .price {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 4px;
        }
        
        .change {
            font-size: 15px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 6px;
            display: inline-block;
        }
        
        .change.positive {
            color: #ff3b30;
            background: rgba(255, 59, 48, 0.15);
        }
        
        .change.negative {
            color: #007aff;
            background: rgba(0, 122, 255, 0.15);
        }
        
        .exchange-card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .exchange-label {
            font-size: 18px;
            font-weight: bold;
        }
        
        .exchange-rate {
            font-size: 20px;
            font-weight: bold;
            color: #34c759;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 16px;
            color: #888;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 30px;
            background: #007aff;
            border: none;
            color: white;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
            cursor: pointer;
            z-index: 1000;
            touch-action: manipulation;
        }
        
        .refresh-btn:active {
            transform: scale(0.95);
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 24px;
            }
            .stock-name {
                font-size: 16px;
            }
            .price {
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 My Portfolio</h1>
        <div class="update-time" id="updateTime">Loading...</div>
    </div>
    
    <div id="loading" class="loading">Loading data...</div>
    
    <div id="content" class="content" style="display: none;"></div>
    
    <button class="refresh-btn" onclick="loadData()">🔄</button>
    
    <script>
        const API_URL = window.location.origin;
        
        function formatNumber(num) {
            return num.toLocaleString('ko-KR');
        }
        
        function formatChange(change, changePercent) {
            const sign = change >= 0 ? '+' : '';
            return `${sign}${formatNumber(change)} (${sign}${changePercent}%)`;
        }
        
        function createStockCard(stock) {
            const changeClass = stock.change >= 0 ? 'positive' : 'negative';
            const priceStr = stock.currency === 'KRW' 
                ? `${formatNumber(stock.current_price)} KRW`
                : `$${formatNumber(stock.current_price)}`;
            
            return `
                <div class="stock-card">
                    <div class="stock-info">
                        <div class="stock-name">${stock.name}</div>
                        <div class="stock-ticker">${stock.ticker}</div>
                    </div>
                    <div class="stock-price">
                        <div class="price">${priceStr}</div>
                        <div class="change ${changeClass}">
                            ${formatChange(stock.change, stock.change_percent)}
                        </div>
                    </div>
                </div>
            `;
        }
        
        function createExchangeCard(label, rate) {
            let rateText;
            if (label.includes('KRW')) {
                rateText = `${formatNumber(rate)} KRW`;
            } else if (label.includes('CNY')) {
                rateText = `${rate.toFixed(4)} CNY`;
            } else {
                rateText = `$${rate.toFixed(4)}`;
            }
            
            return `
                <div class="exchange-card">
                    <div class="exchange-label">${label}</div>
                    <div class="exchange-rate">${rateText}</div>
                </div>
            `;
        }
        
        async function loadData() {
            try {
                document.getElementById('updateTime').textContent = 'Loading...';
                
                const response = await fetch(`${API_URL}/portfolio`);
                const data = await response.json();
                
                let html = '';
                
                // Korean stocks
                if (data.korean_stocks && data.korean_stocks.length > 0) {
                    html += '<div class="section-title">🇰🇷 Korean Stocks</div>';
                    data.korean_stocks.forEach(stock => {
                        html += createStockCard(stock);
                    });
                }
                
                // US stocks
                if (data.us_stocks && data.us_stocks.length > 0) {
                    html += '<div class="section-title">🇺🇸 US Stocks</div>';
                    data.us_stocks.forEach(stock => {
                        html += createStockCard(stock);
                    });
                }
                
                // Chinese stocks
                if (data.chinese_stocks && data.chinese_stocks.length > 0) {
                    html += '<div class="section-title">🇨🇳 Chinese Stocks</div>';
                    data.chinese_stocks.forEach(stock => {
                        html += createStockCard(stock);
                    });
                }
                
                // Exchange rates
                html += '<div class="section-title">💱 Exchange Rates</div>';
                if (data.exchange_rates.USD_KRW) {
                    html += createExchangeCard('USD/KRW', data.exchange_rates.USD_KRW.rate);
                }
                if (data.exchange_rates.CNY_KRW) {
                    html += createExchangeCard('CNY/KRW', data.exchange_rates.CNY_KRW.rate);
                }
                if (data.exchange_rates.USD_CNY) {
                    html += createExchangeCard('USD/CNY', data.exchange_rates.USD_CNY.rate);
                }
                
                document.getElementById('content').innerHTML = html;
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'block';
                
                const updateTime = new Date(data.timestamp).toLocaleString('ko-KR');
                document.getElementById('updateTime').textContent = `Last Update: ${updateTime}`;
                
            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('loading').innerHTML = 
                    '❌ Failed to load data.<br>Please check your connection.';
            }
        }
        
        // Load data on page load
        loadData();
        
        // Auto refresh every 60 seconds
        setInterval(loadData, 60000);
        
        // Pull to refresh (mobile)
        let touchStartY = 0;
        document.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchmove', (e) => {
            const touchY = e.touches[0].clientY;
            const touchDiff = touchY - touchStartY;
            
            if (touchDiff > 100 && window.scrollY === 0) {
                loadData();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/stocks/{ticker}")
def get_stock(ticker: str):
    stock_data = get_stock_price(ticker)
    if stock_data:
        return stock_data
    raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

@app.get("/exchange/{from_currency}/{to_currency}")
def get_exchange(from_currency: str, to_currency: str):
    exchange_data = get_exchange_rate(from_currency.upper(), to_currency.upper())
    if exchange_data:
        return exchange_data
    raise HTTPException(status_code=404, detail="Exchange rate not found")

@app.get("/portfolio")
def get_portfolio():
    # Default portfolio
    korean_stocks = [
        ("005930.KS", "Samsung"),
        ("000660.KS", "SK Hynix")
    ]
    us_stocks = [
        ("AAPL", "Apple"),
        ("GOOGL", "Google"),
        ("TSLA", "Tesla")
    ]
    chinese_stocks = []
    
    korean_data = []
    for ticker, name in korean_stocks:
        data = get_stock_price(ticker)
        if data:
            data['name'] = name
            korean_data.append(data)
    
    us_data = []
    for ticker, name in us_stocks:
        data = get_stock_price(ticker)
        if data:
            data['name'] = name
            us_data.append(data)
    
    chinese_data = []
    for ticker, name in chinese_stocks:
        data = get_stock_price(ticker)
        if data:
            data['name'] = name
            chinese_data.append(data)
    
    usd_krw = get_exchange_rate("USD", "KRW")
    cny_krw = get_exchange_rate("CNY", "KRW")
    usd_cny = get_exchange_rate("USD", "CNY")
    
    return {
        "korean_stocks": korean_data,
        "us_stocks": us_data,
        "chinese_stocks": chinese_data,
        "exchange_rates": {
            "USD_KRW": usd_krw,
            "CNY_KRW": cny_krw,
            "USD_CNY": usd_cny
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
