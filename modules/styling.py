import streamlit as st
import pandas as pd
import os


def configure_page_style():
    """
    Applies custom CSS for the page with clean styling without background image.
    """
    page_style = f"""
    <style>
    
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700&display=swap');

    /* Define color palette */
    :root {{
        --primary-teal: #00816D;
        --secondary-red: #e11d48;
        --accent-green: #10b981;
        --bg-light: #f8fafc;
        --bg-white: #ffffff;
    }}

    /* Apply font and base styles */
    html, body, .st-emotion-cache-10trblm {{
        font-family: 'Manrope', sans-serif;
    }}
    
    /* Main App Background - Clean light background */
    .stApp {{
        background-color: var(--bg-light);
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] > div:first-child {{
        background-color: var(--primary-teal);
    }}
    
    /* Sidebar text styling */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .st-emotion-cache-16txtl3,
    [data-testid="stSidebar"] .st-emotion-cache-10trblm {{
        color: #FFFFFF;
    }}
    [data-testid="stSidebar"] .st-emotion-cache-1g8p9hb {{
         color: #E0E0E0;
    }}
    
    /* Sidebar navigation links */
    [data-testid="stSidebarNav"] a span {{
        color: #FFFFFF;
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"] span {{
        color: #FFFFFF;
    }}
    
    /* Hide sidebar collapse button text */
    [data-testid="stSidebarCollapseButton"] p {{
        display: none;
    }}

    /* Main Content Styling */
    .block-container {{
        background-color: var(--bg-white);
        padding: 2rem 3rem;
        border-radius: 0.75rem;
        margin: 1rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
    }}
    
    /* Header styles */
    h1, h2, h3 {{
        color: var(--primary-teal);
        font-weight: 700;
    }}
    .st-emotion-cache-10trblm, .st-emotion-cache-16txtl3 {{
        color: var(--primary-teal);
    }}
   
    /* Content wrapper styles */
    .metric-container-wrapper, .chart-wrapper {{
        background-color: var(--bg-white);
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        margin-bottom: 2rem;
        border: 1px solid #e2e8f0;
    }}
    
    </style>
    """
    st.markdown(page_style, unsafe_allow_html=True)

def display_market_metrics(df: pd.DataFrame):
    """
    Displays the Key Market Metrics with smaller cards.
    """
    if df.empty:
        st.info("No data available to display Key Market Metrics for the selected filters.")
        return

    css_style = """
    <style>
        .metrics-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        .metric-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        .metric-card {
            background-color: #FFFFFF;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 90px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-top: 4px solid;
            color: #333;
        }
        
        .metric-card .title {
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .metric-card .commodity-name {
            font-size: 14px;
            font-weight: 600;
            margin: auto 0;
            line-height: 1.1;
        }
        .metric-card .value {
            font-size: 13px;
            font-weight: 600;
        }
        .empty-card {
            background-color: #f8fafc;
            border: 2px dashed #cbd5e1;
            color: #64748b;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 500;
        }
        .bullish-card .title { color: var(--accent-green); }
        .bullish-card { border-color: var(--accent-green); }
        .bullish-card .value { color: var(--accent-green); }
        .bearish-card .title { color: var(--secondary-red); }
        .bearish-card { border-color: var(--secondary-red); }
        .bearish-card .value { color: var(--secondary-red); }

        .avg-card .title { color: #ea580c; }
        .avg-card { border-color: #ea580c; }
        .avg-card .value { color: #ea580c; }

        .leader-card .title { color: #7c3aed; }
        .leader-card { border-color: #7c3aed; }
        .leader-card .value { color: #7c3aed; }
    </style>
    """
    
    # Section headers
    headers_html = """
    <div class="metrics-section">
        <div>
            <h3 style='
                color: #00816D; 
                font-size: 1.3rem; 
                font-weight: 500;
                text-align: left;
                margin-bottom: 15px;
            '>
                Key Market Metrics
            </h3>
        </div>
        <div>
            <h3 style='
                color: #00816D; 
                font-size: 1.3rem; 
                font-weight: 500;
                text-align: left;
                margin-bottom: 15px;
            '>
                Sector Metrics
            </h3>
        </div>
    </div>
    """
    
    # Calculations
    most_bullish = df.loc[df['%Week'].idxmax()] if not df['%Week'].empty and df['%Week'].notna().any() else None
    most_bearish = df.loc[df['%Week'].idxmin()] if not df['%Week'].empty and df['%Week'].notna().any() else None
    avg_weekly_change = df['%Week'].mean() if not df['%Week'].empty else 0
    monthly_leader = df.loc[df['%Month'].idxmax()] if not df['%Month'].empty and df['%Month'].notna().any() else None

    # HTML Content
    html_content = f"""
    <div class="metrics-section">
        <div class="metric-container">
            <div class="metric-card bullish-card">
                <div class="title">↑ Most Bullish</div>
                <div class="commodity-name">{most_bullish['Commodities'] if most_bullish is not None else 'N/A'}</div>
                <div class="value">{f"{most_bullish['%Week']:.1%}" if most_bullish is not None and pd.notna(most_bullish['%Week']) else 'N/A'}</div>
            </div>
            <div class="metric-card bearish-card">
                <div class="title">↓ Most Bearish</div>
                <div class="commodity-name">{most_bearish['Commodities'] if most_bearish is not None else 'N/A'}</div>
                <div class="value">{f"{most_bearish['%Week']:.1%}" if most_bearish is not None and pd.notna(most_bearish['%Week']) else 'N/A'}</div>
            </div>
            <div class="metric-card avg-card">
                <div class="title">Weekly Average</div>
                <div class="commodity-name" style="font-size: 20px;">{f"{avg_weekly_change:.1%}" if pd.notna(avg_weekly_change) else 'N/A'}</div>
                <div class="value">All Selected</div>
            </div>
            <div class="metric-card leader-card">
                <div class="title">🏆 Monthly Leader</div>
                <div class="commodity-name">{monthly_leader['Commodities'] if monthly_leader is not None else 'N/A'}</div>
                <div class="value">{f"{monthly_leader['%Month']:.1%}" if monthly_leader is not None and pd.notna(monthly_leader['%Month']) else 'N/A'}</div>
            </div>
        </div>
        <div class="metric-container">
            <div class="metric-card empty-card">
                <div>Sector 1</div>
            </div>
            <div class="metric-card empty-card">
                <div>Sector 2</div>
            </div>
            <div class="metric-card empty-card">
                <div>Sector 3</div>
            </div>
            <div class="metric-card empty-card">
                <div>Sector 4</div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(css_style + headers_html + html_content, unsafe_allow_html=True)

def style_dataframe(df: pd.DataFrame):
    df_to_style = df.copy()

    # Định dạng hiển thị (giữ nguyên)
    format_dict = {
        'Current Price': '{:,.0f}',
        '30D Avg': '{:,.0f}',
        '52W High': '{:,.0f}',
        '52W Low': '{:,.0f}',
        '%Day': '{:.1%}',
        '%Week': '{:.1%}',
        '%Month': '{:.1%}',
        '%Quarter': '{:.1%}',
        '%YTD': '{:.1%}',
    }
    percent_cols = ['%Day', '%Week', '%Month', '%Quarter', '%YTD']

    # Hàm style (giữ nguyên)
    def style_percent_cell(val):
        if pd.isna(val):
            return 'font-weight: 300;'
        
        if val > 0:
            bg_intensity = min(abs(val) * 10, 1.5)
            return f'background-color: rgba(16, 185, 129, {bg_intensity}); font-weight: 300;'
        elif val < 0:
            bg_intensity = min(abs(val) * 10, 1.5)
            return f'background-color: rgba(225, 29, 72, {bg_intensity}); font-weight: 300;'
        else:
            return 'background-color: #FFFFFF; font-weight: 300;'

    styler = df_to_style.style.format(format_dict, na_rep='—')
    
    for col in percent_cols:
        if col in df_to_style.columns:
            styler = styler.applymap(style_percent_cell, subset=[col])
    
    text_columns = ['Commodities', 'Sector', 'Nation', 'Change type', 'Impact']
    
    table_styles = [
        {
            'selector': '',
            'props': [
                ('font-family', 'Manrope, sans-serif'),
                ('color', '#000000'),
                ('font-size', '12px'),
            ]
        },
        # ĐÃ XÓA selector 'table' khỏi đây
        {
            'selector': 'td',
            'props': [
                ('padding', '8px'),
                ('border-bottom', '1px solid #f0f0f0'),
                ('font-weight', '400'),
                ('text-align', 'right'),
            ]
        },
        {
            'selector': 'th',
            'props': [
                # 1. Các dòng mới để cố định header
                ('position', 'sticky'),
                ('top', '0'),
                ('z-index', '1'), # Đảm bảo header luôn nằm trên các dòng khác
                
                # 2. Các style cũ (giữ nguyên và rất quan trọng)
                ('font-weight', '600'),
                ('padding', '10px'),
                ('background-color', '#00816D'), # Màu nền là bắt buộc cho sticky header
                ('color', '#f5f5f5'),
                ('text-align', 'center'),
            ]
        },
        {
            'selector': 'tr:hover',
            'props': [('background-color', '#f5f5f5')]
        }
    ]

    for i, col_name in enumerate(df_to_style.columns):
        if col_name in text_columns:
            table_styles.append({
                'selector': f'td:nth-child({i + 1})',
                'props': [('text-align', 'left')]
            })

    styler = styler.set_table_styles(table_styles)

    # --- THAY ĐỔI QUAN TRỌNG NHẤT TẠI ĐÂY ---
    # Gắn style trực tiếp vào thẻ <table> để đảm bảo được áp dụng
    styler = styler.set_table_attributes('style="width:100%; background-color:white; border-collapse: collapse;"')
    
    styler = styler.hide(axis="index")
    
    return styler