# Commodities Dashboard

A comprehensive dashboard for monitoring and analyzing commodity prices, with a special focus on the steel industry.

## Features

- Real-time commodity price tracking
- Steel industry analysis
- Price trend visualization
- Market performance metrics
- Steel company stock analysis
- Production cost and profit analysis
- News integration for market updates

## Setup

1. Clone the repository:
```bash
git clone https://github.com/minhbuicoder39/Commodities-Dashboard-v1.git
cd Commodities-Dashboard-v1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run Home.py
```

## Data Sources

- Commodity price data
- Steel industry metrics
- Stock market data for Vietnamese steel companies

## Structure

- `Home.py`: Main dashboard entry point
- `pages/`: Individual dashboard pages
  - `Steel_Industry.py`: Steel industry analysis
  - `Chart_Analysis.py`: Detailed chart analysis
  - `ChatGPT_Analysis.py`: AI-powered analysis
- `modules/`: Helper modules
  - `data_loader.py`: Data loading utilities
  - `calculations.py`: Analysis calculations
  - `stock_data.py`: Stock market data handling
  - `styling.py`: UI styling utilities
  - `news_crawler.py`: News aggregation

## Deployment

The dashboard is deployed on Streamlit Cloud and can be accessed at [your-app-url].
