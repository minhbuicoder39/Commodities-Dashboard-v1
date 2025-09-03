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
  - `styling.py` - Clean CSS styling without background images
- `pages/` - Additional Streamlit pages (multi-page app structure)
- `data/` - CSV data files:
  - `Data.csv` - Historical commodity price data
  - `Commo_list.csv` - Commodity metadata (sectors, nations, impact descriptions)

**Key Data Flow:**
1. Data loaded via `load_data()` from CSV files with preprocessing and cleaning
2. Price changes calculated using `calculate_price_changes()` based on latest date
3. Advanced filters applied (sector, nation, change type, commodity)
4. Performance charts generated with tab-based interface
5. Charts use date range and interval selections for future line chart implementation

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

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
1. **Key Market Metrics** - 4 metric cards showing bullish/bearish commodities and averages
2. **Detailed Price Table** - Scrollable table with all commodity data
3. **Performance Chart & Impact** - Tab-based charts with split view (decreasing/increasing performance)

## Key Technical Details

**Data Processing:**
- Uses `@st.cache_data(ttl=3600)` for performance optimization
- All main sections use latest date from data
- Chart Options (date range/interval) prepared for future line chart implementation
- Robust data filtering with multiple criteria

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
  - `Commo_list.csv`: Commodities, Sector, Nation, Impact
- All date calculations based on latest available data
- Change type calculation uses weekly performance for classification
- add to memory