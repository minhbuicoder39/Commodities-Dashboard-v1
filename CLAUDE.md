# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based commodity market dashboard that displays real-time commodity price data with interactive charts and analysis. The application features a clean, modern interface with advanced filtering capabilities and performance visualization.

## Architecture

**Main Application Structure:**
- `Home.py` - Main Streamlit app entry point with sidebar filters and main content sections
- `modules/` - Core functionality modules:
  - `data_loader.py` - CSV data loading and preprocessing with caching
  - `calculations.py` - Price change calculations (daily, weekly, monthly, quarterly, YTD)
  - `styling.py` - Clean CSS styling and KPI metrics display
  - `stock_data.py` - Stock price fetching from TCBS API with caching
- `pages/` - Additional Streamlit pages (multi-page app structure)
- `data/` - CSV data files:
  - `Data.csv` - Historical commodity price data
  - `Commo_list.csv` - Commodity metadata (sectors, nations, impact stock codes)

**Key Data Flow:**
1. Data loaded via `load_data()` from CSV files with preprocessing and cleaning
2. Price changes calculated using `calculate_price_changes()` based on latest date
3. Advanced filters applied (sector, nation, change type, commodity)
4. Performance charts generated with tab-based interface
5. Line charts use date range and interval selections from sidebar
6. Stock data fetched from TCBS API based on Impact column stock codes

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install streamlit-aggrid  # Required for advanced table features

# Run the application
streamlit run Home.py

# Run with specific port
streamlit run Home.py --server.port 8501
```

## UI Structure

**Sidebar Organization:**
- **Advanced Filters Section:**
  - Sector multiselect
  - Nation multiselect
  - Change Type multiselect (Positive/Negative/Neutral)
  - Commodity multiselect (filtered by sector selection)
- **Chart Options Section:**
  - Start Date and End Date inputs (side by side)
  - Interval selection (Daily/Weekly/Monthly/Quarterly)

**Main Content Sections:**
1. **Key Market Metrics & Sector Metrics** - 8 KPI cards in 2x4 grid layout:
   - Market: Most Bullish, Most Bearish, Highest Volatility (TBD), Monthly Leader
   - Sector: Strongest Sector, Extreme Moves (>±2%), Future KPI 3, Future KPI 4
2. **Detailed Price Table** - Advanced AG-Grid table with scroll view, conditional formatting, and professional styling
3. **Performance Chart & Impact** - Tab-based charts with split view (decreasing/increasing performance)
4. **Commodity Price Trends** - Interactive line chart with stock impact integration

## Key Technical Details

**Data Processing:**
- Uses `@st.cache_data(ttl=3600)` for performance optimization
- All main sections use latest date from data
- Chart Options (date range/interval) applied to commodity price trends line chart
- Robust data filtering with multiple criteria
- Stock data integration with TCBS API fetching and timezone handling

**Styling System:**
- Clean design with `--primary-teal: #00816D`, `--secondary-red: #e11d48`, `--accent-green: #10b981`
- Light background (`--bg-light: #f8fafc`) with white content containers
- No background images - modern card-based layout
- Responsive design with proper margins and shadows

**Performance Charts:**
- **Tab-based Interface:** 5 tabs (Daily, Weekly, Monthly, Quarterly, YTD)
- **Split View Design:** Left side for decreasing performance, right side for increasing
- **Balanced Layout:** Empty bars added to balance both sides equally
- **Custom Labels:** 
  - Decreasing: `(Impact) Commodity   -2.5%`
  - Increasing: `2.5%   Commodity (Impact)`
- **No Axis Display:** X and Y axes completely hidden for clean presentation
- **Text Positioning:** `textposition='outside'` for all labels

**Chart Technical Specs:**
- Uses `make_subplots` with `horizontal_spacing=0` for seamless split
- Dynamic height calculation: `max(300, max_items * 40)`
- Margin settings: `l=50, r=50, t=60, b=20` to prevent text cutoff
- Empty bars use `rgba(0,0,0,0)` for transparency
- Hover templates show full commodity information

**Data Dependencies:**
- CSV files in `data/` directory with specific columns:
  - `Data.csv`: Date, Commodities, Price
  - `Commo_list.csv`: Commodities, Sector, Nation, Impact (stock codes)
- All date calculations based on latest available data
- Change type calculation uses weekly performance for classification

**Stock Impact Integration:**
- **Automatic Detection:** Extracts stock codes from Impact column when commodities selected
- **Side-by-Side Charts:** Displays commodity prices (left) and stock prices (right) when impact stocks available
- **Synchronized Options:** Both charts use same date range and interval from sidebar
- **TCBS API Integration:** Fetches Vietnamese stock data with rate limiting and caching
- **Chart Styling:** Clean line charts without markers, using lighter color palette
- **Timezone Handling:** Proper datetime conversion to avoid comparison errors

**KPI Metrics Updates:**
- **Market Metrics:** Most Bullish, Most Bearish, Highest Volatility (placeholder), Monthly Leader
- **Sector Metrics:** Strongest Sector (highest avg %Week), Extreme Moves count (>±2% weekly change)
- **Calculation Logic:** Strongest sector based on average weekly performance, extreme moves count absolute weekly changes > 2%

## Advanced Table Features (AG-Grid)

**Detailed Price Table Implementation:**
- **AG-Grid Integration:** Uses `streamlit-aggrid` for professional table rendering
- **Light Theme:** Clean white background with subtle row striping
- **Scroll View:** No pagination - continuous scroll through all data
- **Conditional Formatting:** 
  - Green background (`rgba(34,197,94,alpha)`) for positive percentage values
  - Red background (`rgba(239,68,68,alpha)`) for negative percentage values  
  - Alpha blending based on absolute value magnitude
- **Number Formatting:**
  - Price columns: Thousand separators with 2 decimal places (e.g., `1,234.56`)
  - Percentage columns: Display as numbers (e.g., `2.34` instead of `2.34%`)
  - All formatting handled via JavaScript formatters
- **Column Configuration:**
  - Sortable and filterable columns
  - Right-aligned numeric columns
  - Icon headers (🌍 Nation, 📈 Impact Stocks, 🏭 Sector, 📦 Commodity)
  - Resizable column widths (default 120px, minimum 100px)
- **Styling Details:**
  - Font family: Manrope, sans-serif
  - Cell padding: 6px 8px for compact layout
  - Row height: 32px, Header height: 40px
  - Font sizes: 13px (cells), 12px (headers)
  - Hover effects and professional borders

**Performance Chart Enhancements:**
- **Soft Color Palette:** Bar colors use 60% opacity for subtle appearance
  - Negative bars: `rgba(225, 29, 72, 0.6)` (soft red)
  - Positive bars: `rgba(16, 185, 129, 0.6)` (soft green)
- **Commodity Selection:** Alphabetically sorted multiselect for easy navigation
- **Interactive Features:** Standard Plotly hover and zoom, no click interactions

**Module Structure:**
- `styling.py` contains `display_aggrid_table()` function
- Comprehensive CSS theming for AG-Grid components
- JavaScript conditional formatting with JsCode
- Price and percentage formatters for consistent display
- to memorize