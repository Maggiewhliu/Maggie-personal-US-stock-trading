name: Multi-Stock Quad Daily Analysis

on:
  schedule:
    # 盤前分析 - 04:00 EST (美東時間)
    - cron: '0 9 * * 1-5'
    # 開盤後分析 - 09:45 EST
    - cron: '45 14 * * 1-5'
    # 午盤分析 - 14:00 EST
    - cron: '0 19 * * 1-5'
    # 盤後分析 - 16:30 EST
    - cron: '30 21 * * 1-5'
  
  # 允許手動觸發
  workflow_dispatch:
  
  # 測試用 - push時也會觸發
  push:
    branches: [ main ]

jobs:
  multi-stock-analysis:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests aiohttp pytz beautifulsoup4 lxml
    
    - name: Run Multi-Stock Analysis
      env:
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        ANALYSIS_SYMBOLS: 'TSLA,AAPL,MSFT'
        POLYGON_API_KEY: ${{ secrets.POLYGON_API_KEY }}
        FINNHUB_API_KEY: ${{ secrets.FINNHUB_API_KEY }}
      run: |
        echo "Starting Multi-Stock Quad Daily Analysis..."
        echo "Execution time (UTC): $(date -u)"
        echo "Execution time (EST): $(TZ='America/New_York' date)"
        echo "Target symbols: $ANALYSIS_SYMBOLS"
        python multi_stock_analyzer.py
    
    - name: Log execution results
      run: |
        echo "Multi-stock analysis execution completed"
        echo "Completion time (UTC): $(date -u)"
        echo "Completion time (EST): $(TZ='America/New_York' date)"
        echo "Next execution: Check cron schedule"
