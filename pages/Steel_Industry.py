import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from modules.data_loader import load_data
from modules.calculations import calculate_price_changes
from modules.styling import configure_page_style
from modules.stock_data import fetch_multiple_stocks
from modules.news_crawler import get_steel_news
from modules.steel_volumes import render_steel_volumes_section  # Add volumes analysis

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Steel Industry Analysis",
    page_icon="⚒️",
    layout="wide"
)

# --- APPLY CUSTOM STYLES ---
configure_page_style()

# --- HEADER ---
st.markdown("""
    <h1 style='
        color: #00816D; 
        font-size: 2.5rem; 
        font-weight: 700;
        text-align: left;
         '>
        ⚒️ Steel Industry Analysis
    </h1>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
df_data, df_list = load_data()

if df_data is not None and df_list is not None:
    # Create price pivot table for the entire dataset
    price_pivot = df_data.pivot(index='Date', columns='Commodities', values='Price')
    price_pivot.index = pd.to_datetime(price_pivot.index)

    # Calculate 30-day moving averages for input materials
    price_pivot['Ore_30d_MA'] = price_pivot['Ore 62'].rolling(window=30, min_periods=1).mean()
    price_pivot['Coal_30d_MA'] = price_pivot['Aus Met Coal'].rolling(window=30, min_periods=1).mean()
    price_pivot['Scrap_30d_MA'] = price_pivot['Scrap'].rolling(window=30, min_periods=1).mean()
    
    # Calculate raw material cost using 30-day moving averages for inputs
    price_pivot['Raw_Material_Cost'] = (
        price_pivot['Ore_30d_MA'] * 1.6 +  # Iron ore component (30-day MA)
        price_pivot['Coal_30d_MA'] * 0.6 +  # Met coal component (30-day MA)
        price_pivot['Scrap_30d_MA'] * 0.1   # Scrap component (30-day MA)
    )

    # Add fixed costs
    price_pivot['Depreciation'] = 35  # 850k VND/ton ≈ 35 USD/ton
    price_pivot['SGA'] = 19  # 450k VND/ton ≈ 19 USD/ton

    # Calculate total production cost
    price_pivot['Production_Cost'] = (
        price_pivot['Raw_Material_Cost'] +
        price_pivot['Depreciation'] +
        price_pivot['SGA']
    )

    # Calculate profits
    price_pivot['HRC_Profit_PreTax'] = price_pivot['China HRC'] - price_pivot['Production_Cost']
    price_pivot['Long_Steel_Profit_PreTax'] = price_pivot['China Long steel'] - price_pivot['Production_Cost']
    price_pivot['HRC_Profit'] = price_pivot['HRC_Profit_PreTax'] * (1 - 0.12)  # After 12% tax
    price_pivot['Long_Steel_Profit'] = price_pivot['Long_Steel_Profit_PreTax'] * (1 - 0.12)  # After 12% tax
    
    # Define input and output commodities
    input_commodities = [
        'Ore 62',
        'Aus Met Coal',
        'Scrap'
    ]
    
    output_commodities = [
        'China HRC',
        'China Long steel'
    ]
    
    # Combine all commodities
    steel_commodities = input_commodities + output_commodities
    
    # Filter the data
    steel_df_list = df_list[df_list['Commodities'].isin(steel_commodities)]
    
    # --- SIDEBAR FILTERS ---
    st.sidebar.markdown("### 📊 Chart Options")
    
    # Date Range
    min_date = df_data['Date'].min()
    max_date = df_data['Date'].max()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Interval Selection
    interval_options = ["Daily", "Weekly", "Monthly", "Quarterly"]
    selected_interval = st.sidebar.selectbox(
        "Interval",
        options=interval_options,
        index=1  # Default to Weekly
    )
    # Toggle to hide/show non-trading gaps (weekends/holidays)
    hide_gaps = st.sidebar.checkbox("Hide non-trading gaps", value=True)

    # --- MAIN CONTENT ---
    st.markdown("""
        <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <h3 style='margin:0; color: #00816D;'>Steel Industry Overview</h3>
            <p>This dashboard tracks key commodities in the steel industry:</p>
            <div style='margin-bottom: 1rem;'>
                <h4 style='color: #00816D;'>Input Materials:</h4>
                <ul>
                    <li><strong>Iron Ore (Ore 62)</strong>: The primary raw material for steel production</li>
                    <li><strong>Metallurgical Coal</strong>: Used in the steel-making process as a reducing agent</li>
                    <li><strong>Steel Scrap</strong>: Recycled steel used in electric arc furnaces</li>
                </ul>
            </div>
            <div>
                <h4 style='color: #00816D;'>Output Products:</h4>
                <ul>
                    <li><strong>HRC (Hot Rolled Coil)</strong>: The most common form of steel used in manufacturing</li>
                    <li><strong>Long Steel</strong>: Products like rebars used in construction</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Filter data based on date range
    date_filtered_data = df_data[
        (df_data['Date'] >= pd.to_datetime(start_date)) & 
        (df_data['Date'] <= pd.to_datetime(end_date))
    ].copy()

    # Create price trend charts section
    st.markdown("### 📈 Price Trends")

    # Input Materials Section
    st.markdown("""
        <div style='background-color: #f0f7f4; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <h4 style='margin:0; color: #00816D;'>Input Materials</h4>
            <p>Raw materials used in steel production</p>
        </div>
    """, unsafe_allow_html=True)
    
    selected_inputs = st.multiselect(
        "Select input materials to display:",
        options=input_commodities,
        default=input_commodities,
        key="input_commodities"
    )

    # Display Input Materials Performance Table
    if selected_inputs:
        st.markdown("#### Performance Summary")
        
        # Create performance table for inputs
        performance_data = []
        for commodity in selected_inputs:
            # Get commodity data and ensure datetime index
            commodity_data = date_filtered_data[date_filtered_data['Commodities'] == commodity].copy()
            commodity_data['Date'] = pd.to_datetime(commodity_data['Date'])
            commodity_data.set_index('Date', inplace=True)
            commodity_data = commodity_data.sort_index()
            
            if not commodity_data.empty:
                latest_price = commodity_data['Price'].iloc[-1]
                latest_date = commodity_data.index[-1]
                
                # Calculate YTD change
                start_of_year = pd.Timestamp(latest_date.year, 1, 1)
                ytd_data = commodity_data[commodity_data.index >= start_of_year]
                ytd_start_price = ytd_data['Price'].iloc[0] if not ytd_data.empty else latest_price
                ytd_change = ((latest_price - ytd_start_price) / ytd_start_price) * 100
                
                # Calculate MTD change
                start_of_month = pd.Timestamp(latest_date.year, latest_date.month, 1)
                mtd_data = commodity_data[commodity_data.index >= start_of_month]
                mtd_start_price = mtd_data['Price'].iloc[0] if not mtd_data.empty else latest_price
                mtd_change = ((latest_price - mtd_start_price) / mtd_start_price) * 100
                
                # Calculate WTD change
                week_start = commodity_data.index[-1] - pd.Timedelta(days=commodity_data.index[-1].weekday())
                wtd_start_price = commodity_data[commodity_data.index >= week_start]['Price'].iloc[0]
                wtd_change = ((latest_price - wtd_start_price) / wtd_start_price) * 100
                
                performance_data.append({
                    'Commodity': commodity,
                    'Current Price': f"${latest_price:.2f}",
                    'WTD': f"{wtd_change:+.1f}%",
                    'MTD': f"{mtd_change:+.1f}%",
                    'YTD': f"{ytd_change:+.1f}%"
                })
        
        if performance_data:
            df_performance = pd.DataFrame(performance_data)
            
            # Style the dataframe
            def color_negative_positive(val):
                try:
                    if isinstance(val, str) and '%' in val:
                        num = float(val.replace('%', '').replace('+', ''))
                        if num < 0:
                            color = '#dc2626'  # red for negative
                        elif num > 0:
                            color = '#16a34a'  # green for positive
                        else:
                            color = '#6b7280'  # gray for zero
                        return f'color: {color}'
                except:
                    return ''
                return ''
            
            styled_df = df_performance.style\
                .apply(lambda x: ['background-color: #f8f9fa' if i % 2 == 0 else '' 
                                for i in range(len(x))], axis=0)\
                .applymap(color_negative_positive)
            
            st.dataframe(styled_df, use_container_width=True)
        
        # Display Input Materials Charts
        st.markdown("#### Price Charts")
        # Calculate number of rows needed for input charts
        num_rows_inputs = (len(selected_inputs) + 1) // 2
        
        fig_inputs = make_subplots(
            rows=num_rows_inputs,
            cols=2,
            subplot_titles=selected_inputs,
            vertical_spacing=0.2,  # Increased vertical spacing
            horizontal_spacing=0.15  # Increased horizontal spacing
        )
        
        # Create separate ranges for each input material due to different price scales
        price_ranges = {}
        for commodity in selected_inputs:
            commodity_data = date_filtered_data[date_filtered_data['Commodities'] == commodity].copy()
            if not commodity_data.empty:
                prices = commodity_data['Price'].tolist()
                min_price = min(prices)
                max_price = max(prices)
                # Add padding (5% below min, 5% above max)
                price_ranges[commodity] = {
                    'min': min_price * 0.95,
                    'max': max_price * 1.05
                }
        
        # Create individual charts for input materials
        for i, commodity in enumerate(selected_inputs):
            row = (i // 2) + 1
            col = (i % 2) + 1
            
            commodity_data = date_filtered_data[date_filtered_data['Commodities'] == commodity].copy()
            commodity_data = commodity_data.sort_values('Date')
            
            if not commodity_data.empty:
                # Apply interval aggregation
                if selected_interval == 'Daily':
                    aggregated_data = commodity_data
                elif selected_interval == 'Weekly':
                    commodity_data['Week'] = commodity_data['Date'].dt.to_period('W')
                    aggregated_data = commodity_data.groupby('Week').last().reset_index()
                    aggregated_data['Date'] = aggregated_data['Week'].dt.end_time
                elif selected_interval == 'Monthly':
                    commodity_data['Month'] = commodity_data['Date'].dt.to_period('M')
                    aggregated_data = commodity_data.groupby('Month').last().reset_index()
                    aggregated_data['Date'] = aggregated_data['Month'].dt.end_time
                elif selected_interval == 'Quarterly':
                    commodity_data['Quarter'] = commodity_data['Date'].dt.to_period('Q')
                    aggregated_data = commodity_data.groupby('Quarter').last().reset_index()
                    aggregated_data['Date'] = aggregated_data['Quarter'].dt.end_time
                
                fig_inputs.add_trace(
                    go.Scatter(
                        x=aggregated_data['Date'],
                        y=aggregated_data['Price'],
                        mode='lines',
                        name=commodity,
                        line=dict(color='#4ade80', width=2),
                        hovertemplate=f'Date: %{{x}}<br>Price: ${{"y:.2f"}}<extra></extra>',
                        showlegend=False
                    ),
                    row=row,
                    col=col
                )
                
                fig_inputs.update_xaxes(
                    title_text="Date",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(0,0,0,0.1)',
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(0,0,0,0.2)',
                    row=row,
                    col=col
                )
                # Get the specific range for this commodity
                y_range = price_ranges.get(commodity, {'min': 0, 'max': 100})
                
                fig_inputs.update_yaxes(
                    title_text="Price ($)",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(0,0,0,0.1)',
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(0,0,0,0.2)',
                    range=[y_range['min'], y_range['max']],
                    row=row,
                    col=col
                )
        
        height_per_row = 300
        total_height = num_rows_inputs * height_per_row
        
        fig_inputs.update_layout(
            template="plotly_white",
            height=total_height + 100,  # Added more height for spacing
            margin=dict(l=50, r=50, t=80, b=50),  # Increased top margin further
            font=dict(family="Manrope, sans-serif", size=12),
            showlegend=False,
            hovermode='x unified'
        )
        # Shorten date labels and optionally hide weekend gaps
        fig_inputs.update_xaxes(tickformat='%b %y', tickangle=-30)
        if hide_gaps:
            fig_inputs.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
        
        st.plotly_chart(fig_inputs, use_container_width=True, config={"scrollZoom": True})

    # Output Products Section
    st.markdown("""
        <div style='background-color: #f0f7f4; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <h4 style='margin:0; color: #00816D;'>Output Products</h4>
            <p>Finished steel products</p>
        </div>
    """, unsafe_allow_html=True)
    
    selected_outputs = st.multiselect(
        "Select output products to display:",
        options=output_commodities,
        default=output_commodities,
        key="output_commodities"
    )

    # Display Output Products Performance Table
    if selected_outputs:
        st.markdown("#### Performance Summary")
        
        # Create performance table for outputs
        performance_data = []
        for commodity in selected_outputs:
            # Get commodity data and ensure datetime index
            commodity_data = date_filtered_data[date_filtered_data['Commodities'] == commodity].copy()
            commodity_data['Date'] = pd.to_datetime(commodity_data['Date'])
            commodity_data.set_index('Date', inplace=True)
            commodity_data = commodity_data.sort_index()
            
            if not commodity_data.empty:
                latest_price = commodity_data['Price'].iloc[-1]
                latest_date = commodity_data.index[-1]
                
                # Calculate YTD change
                start_of_year = pd.Timestamp(latest_date.year, 1, 1)
                ytd_data = commodity_data[commodity_data.index >= start_of_year]
                ytd_start_price = ytd_data['Price'].iloc[0] if not ytd_data.empty else latest_price
                ytd_change = ((latest_price - ytd_start_price) / ytd_start_price) * 100
                
                # Calculate MTD change
                start_of_month = pd.Timestamp(latest_date.year, latest_date.month, 1)
                mtd_data = commodity_data[commodity_data.index >= start_of_month]
                mtd_start_price = mtd_data['Price'].iloc[0] if not mtd_data.empty else latest_price
                mtd_change = ((latest_price - mtd_start_price) / mtd_start_price) * 100
                
                # Calculate WTD change
                week_start = commodity_data.index[-1] - pd.Timedelta(days=commodity_data.index[-1].weekday())
                wtd_start_price = commodity_data[commodity_data.index >= week_start]['Price'].iloc[0]
                wtd_change = ((latest_price - wtd_start_price) / wtd_start_price) * 100
                
                performance_data.append({
                    'Commodity': commodity,
                    'Current Price': f"${latest_price:.2f}",
                    'WTD': f"{wtd_change:+.1f}%",
                    'MTD': f"{mtd_change:+.1f}%",
                    'YTD': f"{ytd_change:+.1f}%"
                })
        
        if performance_data:
            df_performance = pd.DataFrame(performance_data)
            
            # Style the dataframe
            def color_negative_positive(val):
                try:
                    if isinstance(val, str) and '%' in val:
                        num = float(val.replace('%', '').replace('+', ''))
                        if num < 0:
                            color = '#dc2626'  # red for negative
                        elif num > 0:
                            color = '#16a34a'  # green for positive
                        else:
                            color = '#6b7280'  # gray for zero
                        return f'color: {color}'
                except:
                    return ''
                return ''
            
            styled_df = df_performance.style\
                .apply(lambda x: ['background-color: #f8f9fa' if i % 2 == 0 else '' 
                                for i in range(len(x))], axis=0)\
                .applymap(color_negative_positive)
            
            st.dataframe(styled_df, use_container_width=True)
        
        # Display Output Products Charts
        st.markdown("#### Price Charts")
        # Calculate number of rows needed for output charts
        num_rows_outputs = (len(selected_outputs) + 1) // 2
        
        fig_outputs = make_subplots(
            rows=num_rows_outputs,
            cols=2,
            subplot_titles=selected_outputs,
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Track min and max values for output products
        output_prices = []
        for commodity in selected_outputs:
            commodity_data = date_filtered_data[date_filtered_data['Commodities'] == commodity].copy()
            if not commodity_data.empty:
                output_prices.extend(commodity_data['Price'].tolist())
        
        y_min_outputs = min(output_prices) * 0.95 if output_prices else 0
        y_max_outputs = max(output_prices) * 1.05 if output_prices else 100
        
        # Create individual charts for output products
        for i, commodity in enumerate(selected_outputs):
            row = (i // 2) + 1
            col = (i % 2) + 1
            
            commodity_data = date_filtered_data[date_filtered_data['Commodities'] == commodity].copy()
            commodity_data = commodity_data.sort_values('Date')
            
            if not commodity_data.empty:
                # Apply interval aggregation
                if selected_interval == 'Daily':
                    aggregated_data = commodity_data
                elif selected_interval == 'Weekly':
                    commodity_data['Week'] = commodity_data['Date'].dt.to_period('W')
                    aggregated_data = commodity_data.groupby('Week').last().reset_index()
                    aggregated_data['Date'] = aggregated_data['Week'].dt.end_time
                elif selected_interval == 'Monthly':
                    commodity_data['Month'] = commodity_data['Date'].dt.to_period('M')
                    aggregated_data = commodity_data.groupby('Month').last().reset_index()
                    aggregated_data['Date'] = aggregated_data['Month'].dt.end_time
                elif selected_interval == 'Quarterly':
                    commodity_data['Quarter'] = commodity_data['Date'].dt.to_period('Q')
                    aggregated_data = commodity_data.groupby('Quarter').last().reset_index()
                    aggregated_data['Date'] = aggregated_data['Quarter'].dt.end_time
                
                fig_outputs.add_trace(
                    go.Scatter(
                        x=aggregated_data['Date'],
                        y=aggregated_data['Price'],
                        mode='lines',
                        name=commodity,
                        line=dict(color='#f87171', width=2),
                        hovertemplate=f'Date: %{{x}}<br>Price: ${{"y:.2f"}}<extra></extra>',
                        showlegend=False
                    ),
                    row=row,
                    col=col
                )
                
                fig_outputs.update_xaxes(
                    title_text="Date",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(0,0,0,0.1)',
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(0,0,0,0.2)',
                    tickformat='%b %y',
                    tickangle=-30,
                    row=row,
                    col=col
                )
                # Optionally hide weekend gaps
                if hide_gaps:
                    fig_outputs.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], row=row, col=col)
                fig_outputs.update_yaxes(
                    title_text="Price ($)",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(0,0,0,0.1)',
                    showline=True,
                    linewidth=1,
                    linecolor='rgba(0,0,0,0.2)',
                    range=[y_min_outputs, y_max_outputs],
                    row=row,
                    col=col
                )
        
        height_per_row = 300
        total_height = num_rows_outputs * height_per_row
        
        fig_outputs.update_layout(
            template="plotly_white",
            height=total_height,
            margin=dict(l=50, r=50, t=40, b=50),
            font=dict(family="Manrope, sans-serif", size=12),
            showlegend=False,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_outputs, use_container_width=True, config={"scrollZoom": True})

        # Add Steel Volumes Analysis right after output prices
        st.markdown("""
            <div style='background-color: #f0f7f4; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
                <h3 style='margin:0; color: #00816D;'>Steel Volumes Analysis</h3>
                <p>Production volumes and market share analysis</p>
            </div>
        """, unsafe_allow_html=True)
    # Combine selected commodities for further analysis

    # Combine selected commodities for further analysis
    selected_commodities = selected_inputs + selected_outputs

    # Add Production Cost and Profit Analysis
    st.markdown("""
        <div style='background-color: #f0f7f4; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <h3 style='margin:0; color: #00816D;'>Steel Production Cost & Profit Analysis</h3>
            <p>Cost formula per ton of steel:</p>
            <ul>
                <li>Iron Ore: 1.6 tons (30-day moving average price)</li>
                <li>Metallurgical Coal: 0.6 tons (30-day moving average price)</li>
                <li>Scrap: 0.1 tons (30-day moving average price)</li>
            </ul>
            <p><em>Note: Input costs use 30-day moving averages to reflect inventory accumulation, while output prices use spot rates.</em></p>
        </div>
    """, unsafe_allow_html=True)

    # Calculate production cost and profit
    if not date_filtered_data.empty:
        # Update price_pivot with filtered data
        filtered_price_pivot = price_pivot[
            (price_pivot.index >= pd.to_datetime(start_date)) & 
            (price_pivot.index <= pd.to_datetime(end_date))
        ].copy()
        
        # Calculate 30-day moving averages for input materials
        filtered_price_pivot['Ore_30d_MA'] = filtered_price_pivot['Ore 62'].rolling(window=30, min_periods=1).mean()
        filtered_price_pivot['Coal_30d_MA'] = filtered_price_pivot['Aus Met Coal'].rolling(window=30, min_periods=1).mean()
        filtered_price_pivot['Scrap_30d_MA'] = filtered_price_pivot['Scrap'].rolling(window=30, min_periods=1).mean()
        
        # Calculate raw material cost using 30-day moving averages for inputs
        price_pivot['Raw_Material_Cost'] = (
            price_pivot['Ore_30d_MA'] * 1.6 +  # Iron ore component (30-day MA)
            price_pivot['Coal_30d_MA'] * 0.6 +  # Met coal component (30-day MA)
            price_pivot['Scrap_30d_MA'] * 0.1   # Scrap component (30-day MA)
        )
        
        # Add depreciation and SGA costs (converted from VND to USD)
        price_pivot['Depreciation'] = 35  # 850k VND/ton ≈ 35 USD/ton
        price_pivot['SGA'] = 19  # 450k VND/ton ≈ 19 USD/ton
        
        # Calculate total production cost
        price_pivot['Production_Cost'] = (
            price_pivot['Raw_Material_Cost'] +
            price_pivot['Depreciation'] +
            price_pivot['SGA']
        )
        
        # Calculate pre-tax profits using spot prices for outputs
        price_pivot['HRC_Profit_PreTax'] = price_pivot['China HRC'] - price_pivot['Production_Cost']
        price_pivot['Long_Steel_Profit_PreTax'] = price_pivot['China Long steel'] - price_pivot['Production_Cost']
        
        # Calculate after-tax profits (12% corporate tax)
        price_pivot['HRC_Profit'] = price_pivot['HRC_Profit_PreTax'] * (1 - 0.12)  # After 12% tax
        price_pivot['Long_Steel_Profit'] = price_pivot['Long_Steel_Profit_PreTax'] * (1 - 0.12)  # After 12% tax

        # Add Steel Volumes Analysis after profit calculations
        st.markdown("### 📊 Steel Volumes Analysis")
        # Create a copy of price_pivot to avoid modifying the original
        volumes_data = price_pivot.copy()
        st.markdown("### 📊 Steel Volumes Analysis")
        render_steel_volumes_section(volumes_data)
        
        # Load volumes data
        volumes_df = pd.read_csv('data/steel_volumes.csv', parse_dates=['Date'], index_col='Date')
        
        # Get HPG volumes for Coil (HRC) and Rebar
        hpg_rebar = volumes_df['Rebar - HPG']
        hpg_coil = volumes_df['Coil - HPG']
        
        # Align volume data with price_pivot index
        common_index = price_pivot.index.intersection(volumes_df.index)
        price_pivot = price_pivot.loc[common_index]
        hpg_rebar = hpg_rebar.loc[common_index]
        hpg_coil = hpg_coil.loc[common_index]
        
        # Calculate total NPAT by product
        price_pivot['HRC_NPAT'] = price_pivot['HRC_Profit'] * hpg_coil
        price_pivot['Long_Steel_NPAT'] = price_pivot['Long_Steel_Profit'] * hpg_rebar
        price_pivot['Total_NPAT'] = price_pivot['HRC_NPAT'] + price_pivot['Long_Steel_NPAT']
        
        # Create monthly profit chart
        monthly_profit_fig = go.Figure()
        monthly_profit_fig.add_trace(go.Bar(
            name='HRC Profit',
            x=price_pivot.index,
            y=price_pivot['HRC_NPAT'],
            marker_color='rgb(55, 83, 109)'
        ))
        monthly_profit_fig.add_trace(go.Bar(
            name='Long Steel Profit',
            x=price_pivot.index,
            y=price_pivot['Long_Steel_NPAT'],
            marker_color='rgb(26, 118, 255)'
        ))
        
        monthly_profit_fig.update_layout(
            title='HPG Monthly Profit Breakdown',
            xaxis_title='Month',
            yaxis_title='Profit (USD)',
            barmode='stack',
            showlegend=True,
            template='plotly_white'
        )
        
        # Calculate quarterly profits
        price_pivot['Quarter'] = price_pivot.index.quarter
        quarterly_profits = price_pivot.groupby('Quarter').agg({
            'HRC_NPAT': 'sum',
            'Long_Steel_NPAT': 'sum',
            'Total_NPAT': 'sum'
        }).reset_index()
        
        # Create quarterly profit chart
        quarterly_profit_fig = go.Figure()
        quarterly_profit_fig.add_trace(go.Bar(
            name='HRC Profit',
            x=quarterly_profits['Quarter'].apply(lambda x: f'Q{x}'),
            y=quarterly_profits['HRC_NPAT'],
            marker_color='rgb(55, 83, 109)'
        ))
        quarterly_profit_fig.add_trace(go.Bar(
            name='Long Steel Profit',
            x=quarterly_profits['Quarter'].apply(lambda x: f'Q{x}'),
            y=quarterly_profits['Long_Steel_NPAT'],
            marker_color='rgb(26, 118, 255)'
        ))
        
        quarterly_profit_fig.update_layout(
            title='HPG Quarterly Profit Breakdown',
            xaxis_title='Quarter',
            yaxis_title='Profit (USD)',
            barmode='stack',
            showlegend=True,
            template='plotly_white'
        )
        
        # Add currency selection
        st.subheader("HPG's Profit Analysis")
        currency = st.selectbox(
            "Select Currency",
            ["USD", "VND (billion)"],
            key="profit_currency"
        )
        
        # Define FX rates by year
        fx_rates = {
            2023: 23500,
            2024: 24000,
            2025: 25300
        }
        
        # Create FX rate series based on date index
        price_pivot['fx_rate'] = price_pivot.index.year.map(fx_rates)
        
        # Convert to VND billion if selected
        if currency == "VND (billion)":
            price_pivot['HRC_NPAT_display'] = price_pivot['HRC_NPAT'] * price_pivot['fx_rate'] / 1e9
            price_pivot['Long_Steel_NPAT_display'] = price_pivot['Long_Steel_NPAT'] * price_pivot['fx_rate'] / 1e9
            
            # For quarterly data, calculate weighted average FX rate per quarter
            quarterly_fx = price_pivot.groupby('Quarter').agg({
                'fx_rate': 'mean',
                'HRC_NPAT': 'sum',
                'Long_Steel_NPAT': 'sum'
            }).reset_index()
            
            quarterly_profits['HRC_NPAT_display'] = quarterly_fx['HRC_NPAT'] * quarterly_fx['fx_rate'] / 1e9
            quarterly_profits['Long_Steel_NPAT_display'] = quarterly_fx['Long_Steel_NPAT'] * quarterly_fx['fx_rate'] / 1e9
            currency_label = "Profit (VND billion)"
        else:
            price_pivot['HRC_NPAT_display'] = price_pivot['HRC_NPAT']
            price_pivot['Long_Steel_NPAT_display'] = price_pivot['Long_Steel_NPAT']
            quarterly_profits['HRC_NPAT_display'] = quarterly_profits['HRC_NPAT']
            quarterly_profits['Long_Steel_NPAT_display'] = quarterly_profits['Long_Steel_NPAT']
            currency_label = "Profit (USD)"


        
        # Create quarterly profit chart
        quarterly_profit_fig = go.Figure()
        quarterly_profit_fig.add_trace(go.Bar(
            name='HRC Profit',
            x=quarterly_profits['Quarter'].apply(lambda x: f'Q{x}'),
            y=quarterly_profits['HRC_NPAT_display'],
            marker_color='rgb(55, 83, 109)'
        ))
        quarterly_profit_fig.add_trace(go.Bar(
            name='Long Steel Profit',
            x=quarterly_profits['Quarter'].apply(lambda x: f'Q{x}'),
            y=quarterly_profits['Long_Steel_NPAT_display'],
            marker_color='rgb(26, 118, 255)'
        ))
        
        quarterly_profit_fig.update_layout(
            title='HPG Quarterly Profit Breakdown',
            xaxis_title='Quarter',
            yaxis_title=currency_label,
            barmode='stack',
            showlegend=True,
            template='plotly_white'
        )

        # Display total profit for the current period
        current_month = price_pivot.index[-1]
        current_quarter = current_month.quarter
        current_year = current_month.year
        
        # Display FX Rate Information
        st.sidebar.subheader("Exchange Rate Information")
        st.sidebar.markdown(f"""
        **Current FX Rates (VND/USD):**
        - 2023: 23,500
        - 2024: 24,000
        - 2025: 25,300
        
        **Active Rate:** {fx_rates[current_year]:,} VND/USD
        """)
        
        # Create three columns for metrics
        col1, col2, col3 = st.columns(3)
        
        # Get current rates and profits
        current_fx_rate = price_pivot['fx_rate'].iloc[-1]
        quarter_fx_rate = price_pivot[price_pivot.index.quarter == current_quarter]['fx_rate'].mean()
        
        with col1:
            st.markdown("### Current Month")
            if currency == "VND (billion)":
                current_month_profit = price_pivot['Total_NPAT'].iloc[-1] * current_fx_rate / 1e9
                st.metric("Profit", f"{current_month_profit:,.1f} VND bn")
                # Also show USD value for reference
                st.metric("USD Equivalent", f"${price_pivot['Total_NPAT'].iloc[-1]:,.0f}")
            else:
                current_month_profit = price_pivot['Total_NPAT'].iloc[-1]
                st.metric("Profit", f"${current_month_profit:,.0f}")
                # Show VND value for reference
                st.metric("VND Equivalent", f"{current_month_profit * current_fx_rate / 1e9:,.1f} bn")
        
        with col2:
            st.markdown(f"### Q{current_quarter}")
            quarter_total = quarterly_profits[quarterly_profits['Quarter'] == current_quarter]['Total_NPAT'].values[0]
            if currency == "VND (billion)":
                current_quarter_profit = quarter_total * quarter_fx_rate / 1e9
                st.metric("Profit", f"{current_quarter_profit:,.1f} VND bn")
                st.metric("USD Equivalent", f"${quarter_total:,.0f}")
            else:
                st.metric("Profit", f"${quarter_total:,.0f}")
                st.metric("VND Equivalent", f"{quarter_total * quarter_fx_rate / 1e9:,.1f} bn")
        
        with col3:
            st.markdown("### Year to Date")
            ytd_total_usd = price_pivot[price_pivot.index.year == current_year]['Total_NPAT'].sum()
            ytd_avg_fx = price_pivot[price_pivot.index.year == current_year]['fx_rate'].mean()
            if currency == "VND (billion)":
                ytd_total_vnd = ytd_total_usd * ytd_avg_fx / 1e9
                st.metric("Profit", f"{ytd_total_vnd:,.1f} VND bn")
                st.metric("USD Equivalent", f"${ytd_total_usd:,.0f}")
            else:
                st.metric("Profit", f"${ytd_total_usd:,.0f}")
                st.metric("VND Equivalent", f"{ytd_total_usd * ytd_avg_fx / 1e9:,.1f} bn")
        
        # Display the quarterly profit chart
        st.plotly_chart(quarterly_profit_fig, use_container_width=True)

        # Reset index to make Date a column
        price_pivot = price_pivot.reset_index()

        # Create profit analysis charts
        st.markdown("### 📈 Profit Analysis")
        
        # Ensure we have all required columns
        required_columns = ['China HRC', 'China Long steel', 'Production_Cost']
        missing_cols = [col for col in required_columns if col not in price_pivot.columns]
        
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
        else:
            # Calculate profit per ton
            price_pivot['HRC_Profit_per_Ton'] = (
                price_pivot['China HRC'] - price_pivot['Production_Cost']
            ).fillna(0)
            
            price_pivot['Rebar_Profit_per_Ton'] = (
                price_pivot['China Long steel'] - price_pivot['Production_Cost']
            ).fillna(0)
            
            # Calculate profit margins (as percentages)
            price_pivot['HRC_Margin'] = np.where(
                price_pivot['China HRC'] > 0,
                (price_pivot['HRC_Profit_per_Ton'] / price_pivot['China HRC']) * 100,
                0
            )
            
            price_pivot['Rebar_Margin'] = np.where(
                price_pivot['China Long steel'] > 0,
                (price_pivot['Rebar_Profit_per_Ton'] / price_pivot['China Long steel']) * 100,
                0
            )
            
            # Replace any remaining infinities with 0
            price_pivot = price_pivot.replace([np.inf, -np.inf], 0)
        
        # Create two columns for the charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Profit per Ton")
            fig_profit_abs = go.Figure()
            
            # Sort data by date for proper line display
            plot_data = price_pivot.sort_index()
            
            # Add profit per ton lines
            fig_profit_abs.add_trace(
                go.Scatter(
                    x=plot_data.index,
                    y=plot_data['HRC_Profit_per_Ton'],
                    name='HRC Profit/ton',
                    line=dict(color='#f87171', width=2),
                    customdata=plot_data['HRC_Profit_per_Ton'],
                    hovertemplate="<b>%{x}</b><br>" +
                                "Profit/ton: $%{customdata:.2f}<extra></extra>"
                )
            )
            
            fig_profit_abs.add_trace(
                go.Scatter(
                    x=plot_data.index,
                    y=plot_data['Rebar_Profit_per_Ton'],
                    name='Rebar Profit/ton',
                    line=dict(color='#fb923c', width=2),
                    customdata=plot_data['Rebar_Profit_per_Ton'],
                    hovertemplate="<b>%{x}</b><br>" +
                                "Profit/ton: $%{customdata:.2f}<extra></extra>"
                )
            )
            
            # Update profit per ton layout
            fig_profit_abs.update_layout(
                height=400,
                template='plotly_white',
                margin=dict(l=50, r=50, t=20, b=50),
                font=dict(family="Manrope, sans-serif", size=12),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified',
                xaxis_title="Date",
                yaxis_title="Profit per Ton (USD)"
            )
            # Add zero line for reference
            fig_profit_abs.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            # Shorten date labels and optionally hide weekend gaps
            fig_profit_abs.update_xaxes(tickformat='%b %y', tickangle=-30)
            if hide_gaps:
                fig_profit_abs.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
            
            st.plotly_chart(fig_profit_abs, use_container_width=True, config={"scrollZoom": True})
            
        with col2:
            st.markdown("#### Profit Margin (%)")
            fig_profit_margin = go.Figure()
            
            # Add margin lines using sorted data
            fig_profit_margin.add_trace(
                go.Scatter(
                    x=plot_data.index,
                    y=plot_data['HRC_Margin'],
                    name='HRC Margin',
                    line=dict(color='#f87171', width=2),
                    customdata=plot_data['HRC_Margin'],
                    hovertemplate="<b>%{x}</b><br>" +
                                "Margin: %{customdata:.1f}%<extra></extra>"
                )
            )
            
            fig_profit_margin.add_trace(
                go.Scatter(
                    x=plot_data.index,
                    y=plot_data['Rebar_Margin'],
                    name='Rebar Margin',
                    line=dict(color='#fb923c', width=2),
                    customdata=plot_data['Rebar_Margin'],
                    hovertemplate="<b>%{x}</b><br>" +
                                "Margin: %{customdata:.1f}%<extra></extra>"
                )
            )
            
            # Update margin layout
            fig_profit_margin.update_layout(
                height=400,
                template='plotly_white',
                margin=dict(l=50, r=50, t=20, b=50),
                font=dict(family="Manrope, sans-serif", size=12),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified',
                xaxis_title="Date",
                yaxis_title="Profit Margin (%)"
            )
            # Add zero line for reference
            fig_profit_margin.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            # Shorten date labels and optionally hide weekend gaps
            fig_profit_margin.update_xaxes(tickformat='%b %y', tickangle=-30)
            if hide_gaps:
                fig_profit_margin.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
            # Set y-axis range to show margins clearly
            fig_profit_margin.update_yaxes(range=[-20, 40])
            
            st.plotly_chart(fig_profit_margin, use_container_width=True, config={"scrollZoom": True})

        # Add profit metrics
        col1, col2, col3 = st.columns(3)
        
        # Get latest values
        latest_date = price_pivot['Date'].max()
        latest_data = price_pivot[price_pivot['Date'] == latest_date].iloc[0]
        
        with col1:
            st.metric(
                "Latest Production Cost",
                f"${latest_data['Production_Cost']:.2f}/ton",
                delta=f"{(latest_data['Production_Cost'] - price_pivot['Production_Cost'].shift(1).iloc[-1]):.2f}"
            )
        
        with col2:
            st.metric(
                "Latest HRC Profit",
                f"${latest_data['HRC_Profit']:.2f}/ton",
                delta=f"{(latest_data['HRC_Profit'] - price_pivot['HRC_Profit'].shift(1).iloc[-1]):.2f}"
            )
        
        with col3:
            st.metric(
                "Latest Long Steel Profit",
                f"${latest_data['Long_Steel_Profit']:.2f}/ton",
                delta=f"{(latest_data['Long_Steel_Profit'] - price_pivot['Long_Steel_Profit'].shift(1).iloc[-1]):.2f}"
            )
        
        # Add price changes table
        st.markdown("### 📊 Price Changes")
        latest_date = df_data['Date'].max()
        analysis_df = calculate_price_changes(df_data, df_list, latest_date)
    steel_analysis = analysis_df[analysis_df['Commodities'].isin(selected_commodities)].copy()
    
    if not steel_analysis.empty:
        # Create a clean table with specific columns
        display_df = steel_analysis[['Commodities', '%Day', '%Week', '%Month', '%Quarter', '%YTD']].copy()
        
        # Format percentage columns
        for col in ['%Day', '%Week', '%Month', '%Quarter', '%YTD']:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")
        
        # Display the table
        st.dataframe(
            display_df.style.apply(lambda x: ['background-color: #f8f9fa' if i % 2 == 0 else '' for i in range(len(x))], axis=0),
            use_container_width=True
        )
        
        # Add impact analysis
        st.markdown("### 🔄 Impact Analysis")
        impact_df = steel_analysis[['Commodities', 'Impact']].copy()
        impact_df = impact_df[impact_df['Impact'].notna()]
        
        if not impact_df.empty:
            st.markdown("""
                <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem;'>
                    <h4 style='margin-top:0;'>Market Impact</h4>
                    <p>The following stocks are impacted by these commodities:</p>
            """, unsafe_allow_html=True)
            
            for _, row in impact_df.iterrows():
                st.markdown(f"- **{row['Commodities']}**: {row['Impact']}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No price change data available for the selected commodities.")

    # Add Steel Companies Stock Performance
    st.markdown("""
        <div style='background-color: #f0f7f4; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <h3 style='margin:0; color: #00816D;'>Steel Companies Stock Performance</h3>
            <p>Performance comparison of major Vietnamese steel manufacturers</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Fetch stock data for steel companies
    steel_companies = ['HPG', 'HSG', 'NKG']
    
    # Technical overlay and indicator controls
    st.markdown("#### Stock Chart Tools")
    col_ma, col_ind = st.columns(2)
    with col_ma:
        ma_options = ["MA9", "MA50", "MA200"]
        selected_ma = st.multiselect("Moving Averages", options=ma_options, default=["MA50"])
    with col_ind:
        ind_options = ["MACD", "RSI"]
        selected_ind = st.multiselect("Indicators", options=ind_options, default=[])

    stock_data = fetch_multiple_stocks(steel_companies)
    
    if stock_data:
        # Render candlestick + volume charts per company in tabs
        tabs = st.tabs(steel_companies)
        for idx, ticker in enumerate(steel_companies):
            data = stock_data.get(ticker)
            if data is None or data.empty:
                continue

            with tabs[idx]:
                # Determine subplot structure based on selected indicators
                rows = 2 + (1 if "MACD" in selected_ind else 0) + (1 if "RSI" in selected_ind else 0)
                row_heights = [0.6, 0.25]
                if "MACD" in selected_ind:
                    row_heights.append(0.15)
                if "RSI" in selected_ind:
                    row_heights.append(0.15)

                fig_candle = make_subplots(
                    rows=rows,
                    cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    row_heights=row_heights
                )

                # Candlestick
                fig_candle.add_trace(
                    go.Candlestick(
                        x=data['tradingDate'],
                        open=data['open'],
                        high=data['high'],
                        low=data['low'],
                        close=data['close'],
                        name=ticker,
                        increasing_line_color="#16a34a",
                        decreasing_line_color="#dc2626"
                    ),
                    row=1,
                    col=1
                )

                # Volume bars (colored by up/down day)
                if 'volume' in data.columns:
                    vol_colors = [
                        'rgba(22, 163, 74, 0.6)' if c >= o else 'rgba(220, 38, 38, 0.6)'
                        for o, c in zip(data['open'], data['close'])
                    ]
                    fig_candle.add_trace(
                        go.Bar(
                            x=data['tradingDate'],
                            y=data['volume'],
                            name='Volume',
                            marker_color=vol_colors
                        ),
                        row=2,
                        col=1
                    )

                # Moving Averages on price panel
                close = data['close']
                if "MA9" in selected_ma:
                    ma9 = close.rolling(window=9, min_periods=1).mean()
                    fig_candle.add_trace(
                        go.Scatter(x=data['tradingDate'], y=ma9, name='MA9', line=dict(color='#22c55e', width=1.5)),
                        row=1, col=1
                    )
                if "MA50" in selected_ma:
                    ma50 = close.rolling(window=50, min_periods=1).mean()
                    fig_candle.add_trace(
                        go.Scatter(x=data['tradingDate'], y=ma50, name='MA50', line=dict(color='#3b82f6', width=1.5)),
                        row=1, col=1
                    )
                if "MA200" in selected_ma:
                    ma200 = close.rolling(window=200, min_periods=1).mean()
                    fig_candle.add_trace(
                        go.Scatter(x=data['tradingDate'], y=ma200, name='MA200', line=dict(color='#f59e0b', width=1.5)),
                        row=1, col=1
                    )

                # Indicators panels
                current_row = 3
                if "MACD" in selected_ind:
                    ema12 = close.ewm(span=12, adjust=False).mean()
                    ema26 = close.ewm(span=26, adjust=False).mean()
                    macd = ema12 - ema26
                    signal = macd.ewm(span=9, adjust=False).mean()
                    hist = macd - signal
                    hist_colors = ['rgba(34,197,94,0.6)' if h >= 0 else 'rgba(239,68,68,0.6)' for h in hist]
                    fig_candle.add_trace(go.Bar(x=data['tradingDate'], y=hist, marker_color=hist_colors, name='MACD Hist'), row=current_row, col=1)
                    fig_candle.add_trace(go.Scatter(x=data['tradingDate'], y=macd, name='MACD', line=dict(color='#111827', width=1.5)), row=current_row, col=1)
                    fig_candle.add_trace(go.Scatter(x=data['tradingDate'], y=signal, name='Signal', line=dict(color='#f43f5e', width=1.2, dash='dot')), row=current_row, col=1)
                    fig_candle.update_yaxes(title_text="MACD", row=current_row, col=1)
                    current_row += 1
                if "RSI" in selected_ind:
                    delta = close.diff()
                    gain = delta.where(delta > 0, 0.0)
                    loss = -delta.where(delta < 0, 0.0)
                    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    fig_candle.add_trace(go.Scatter(x=data['tradingDate'], y=rsi, name='RSI(14)', line=dict(color='#06b6d4', width=1.5)), row=current_row, col=1)
                    # Overbought/oversold reference lines
                    fig_candle.add_trace(go.Scatter(x=data['tradingDate'], y=[70]*len(rsi), name='70', line=dict(color='rgba(156,163,175,0.7)', width=1, dash='dash')), row=current_row, col=1)
                    fig_candle.add_trace(go.Scatter(x=data['tradingDate'], y=[30]*len(rsi), name='30', line=dict(color='rgba(156,163,175,0.7)', width=1, dash='dash')), row=current_row, col=1)
                    fig_candle.update_yaxes(title_text="RSI", range=[0, 100], row=current_row, col=1)

                fig_candle.update_layout(
                    height=520,
                    template='plotly_white',
                    margin=dict(l=50, r=50, t=20, b=40),
                    font=dict(family="Manrope, sans-serif", size=12),
                    showlegend=False,
                    hovermode='x unified',
                    dragmode='pan',
                    uirevision='candlestick',
                    xaxis_rangeslider_visible=False,
                    xaxis2_rangeslider_visible=False
                )

                # Axis titles and short date ticks
                fig_candle.update_yaxes(title_text="Price (VND)", row=1, col=1)
                fig_candle.update_yaxes(title_text="Volume", row=2, col=1)
                # Label bottom-most x-axis only
                fig_candle.update_xaxes(title_text="Date", tickformat='%b %y', tickangle=-30, row=rows, col=1)

                # Optionally hide weekends and ensure no range slider appears
                if hide_gaps:
                    for r in range(1, rows+1):
                        fig_candle.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], row=r, col=1)
                # Explicitly disable range slider on all subplots
                for r in range(1, rows+1):
                    fig_candle.update_xaxes(rangeslider_visible=False, row=r, col=1)

                st.plotly_chart(fig_candle, use_container_width=True, config={"scrollZoom": True})
        
        # Add current stock prices and changes
        stock_cols = st.columns(3)
        
        for i, (ticker, data) in enumerate(stock_data.items()):
            if data is not None and not data.empty:
                current_price = data['close'].iloc[-1]
                prev_price = data['close'].iloc[-2]
                price_change = ((current_price - prev_price) / prev_price) * 100
                
                with stock_cols[i]:
                    st.metric(
                        f"{ticker}",
                        f"{current_price:,.0f} VND",
                        f"{price_change:+.1f}%"
                    )
    else:
        st.warning("Unable to fetch stock data for steel companies.")

else:
    st.error("Failed to load data files. Please check the 'data' directory.")
