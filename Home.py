import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from modules.data_loader import load_data
from modules.calculations import calculate_price_changes
from modules.styling import configure_page_style, style_dataframe, display_market_metrics, display_aggrid_table
from modules.stock_data import fetch_multiple_stocks, get_stock_tickers_from_impact

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Commodity Dashboard",
    page_icon="💹",
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
        💹 Commodity Market Dashboard
    </h1>
""", unsafe_allow_html=True)


# --- DATA LOADING (with caching) ---
df_data, df_list = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.markdown("### 🔍 Advanced Filters")

if df_data is not None and df_list is not None:
    # Sector Filter
    unique_sectors = sorted(df_list['Sector'].astype(str).unique())
    selected_sectors = st.sidebar.multiselect(
        "Sector",
        options=unique_sectors,
        default=[]
    )

    # Nation Filter
    unique_nations = sorted(df_list['Nation'].astype(str).unique())
    selected_nations = st.sidebar.multiselect(
        "Nation",
        options=unique_nations,
        default=[]
    )

    # Change Type Filter
    change_type_options = ["Positive", "Negative", "Neutral"]
    selected_change_types = st.sidebar.multiselect(
        "Change Type",
        options=change_type_options,
        default=[]
    )

    # Commodity Filter
    if selected_sectors:
        commodity_options = sorted(df_list[df_list['Sector'].isin(selected_sectors)]['Commodities'].astype(str).unique())
    else:
        commodity_options = sorted(df_list['Commodities'].astype(str).unique())
    
    selected_commodities = st.sidebar.multiselect(
        "Commodity",
        options=commodity_options,
        default=[]
    )

    st.sidebar.markdown("---")
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
    
    # --- DATA CALCULATION ---
    # Use latest date for all current sections
    latest_date = df_data['Date'].max()
    analysis_df = calculate_price_changes(df_data, df_list, latest_date)

    # --- MAIN CONTENT ---
    

    if not analysis_df.empty:
        # --- Filter Data based on selection ---
        filtered_df = analysis_df.copy()
        
        if selected_sectors:
            filtered_df = filtered_df[filtered_df['Sector'].isin(selected_sectors)]
            
        if selected_nations:
            filtered_df = filtered_df[filtered_df['Nation'].isin(selected_nations)]
            
        if selected_change_types:
            filtered_df = filtered_df[filtered_df['Change type'].isin(selected_change_types)]
            
        if selected_commodities:
            filtered_df = filtered_df[filtered_df['Commodities'].isin(selected_commodities)]

        # --- Display Key Market Metrics ---
       
        display_market_metrics(filtered_df)
        

        # --- Display Data Table ---
        
        st.markdown("""
         <h2 style='
        color: #00816D; 
        font-size: 1rem; 
        font-weight: 400;
        text-align: left;
         '>
        Detailed Price Table
          </h2>
        """, unsafe_allow_html=True)
        
        if not filtered_df.empty:
            display_aggrid_table(filtered_df)
        else:
            st.warning("No data matches your filter criteria.")

        # --- DYNAMIC BAR CHART SECTION (using Plotly) ---
        st.markdown("""
         <h3 style='
        color: #00816D; 
        font-size: 1rem; 
        font-weight: 400;
        text-align: left;
         '>
        Performance Chart & Impact
          </h3>
        """, unsafe_allow_html=True)
       

        if not filtered_df.empty:
            # Create tabs for chart selection
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Daily", "📊 Weekly", "📅 Monthly", "🗓️ Quarterly", "📈 YTD"])
            
            chart_options = {
                "Daily": ("%Day", tab1),
                "Weekly": ("%Week", tab2), 
                "Monthly": ("%Month", tab3),
                "Quarterly": ("%Quarter", tab4),
                "YTD": ("%YTD", tab5)
            }
            
            for chart_label, (selected_column, tab) in chart_options.items():
                with tab:
                    if selected_column in filtered_df.columns:
                        chart_data = filtered_df[['Commodities', selected_column, 'Impact']].copy()
                        chart_data.dropna(subset=[selected_column], inplace=True)
                        
                        # Filter out commodities with 0% change
                        chart_data = chart_data[chart_data[selected_column] != 0]
                        
                        if not chart_data.empty:
                            # Separate positive and negative values
                            positive_data = chart_data[chart_data[selected_column] > 0].copy()
                            negative_data = chart_data[chart_data[selected_column] < 0].copy()
                            
                            # Sort positive data descending, negative data ascending (so worst performers are at top)
                            positive_data = positive_data.sort_values(by=selected_column, ascending=False)
                            negative_data = negative_data.sort_values(by=selected_column, ascending=True)
                            
                            # Balance the number of bars between both sides
                            max_items = max(len(positive_data), len(negative_data)) if len(positive_data) > 0 or len(negative_data) > 0 else 0
                            
                            # Pad shorter side with empty entries
                            if len(positive_data) < max_items:
                                padding_needed = max_items - len(positive_data)
                                empty_rows = pd.DataFrame({
                                    'Commodities': [''] * padding_needed,
                                    selected_column: [0] * padding_needed,
                                    'Impact': [''] * padding_needed
                                })
                                positive_data = pd.concat([positive_data, empty_rows], ignore_index=True)
                            
                            if len(negative_data) < max_items:
                                padding_needed = max_items - len(negative_data)
                                empty_rows = pd.DataFrame({
                                    'Commodities': [''] * padding_needed,
                                    selected_column: [0] * padding_needed,
                                    'Impact': [''] * padding_needed
                                })
                                negative_data = pd.concat([negative_data, empty_rows], ignore_index=True)
                            
                            # Create subplot with 2 columns: negative (left) and positive (right)
                            fig = make_subplots(
                                rows=1, cols=2,
                                horizontal_spacing=0.02,
                                column_widths=[0.49, 0.49]
                            )
                            
                            # Add negative performance bars (left side)
                            if len(negative_data) > 0:
                                # Create custom labels: impact + commodity + percentage (for decreasing)
                                negative_labels = []
                                for idx, row in negative_data.iterrows():
                                    if row['Commodities'] == '':
                                        negative_labels.append('')
                                    else:
                                        impact_text = f"({row['Impact']}) " if pd.notna(row['Impact']) and row['Impact'] != '' else ''
                                        negative_labels.append(f"{impact_text}{row['Commodities']}   {row[selected_column]:.1%}")
                                
                                fig.add_trace(go.Bar(
                                    y=list(range(len(negative_data))),
                                    x=negative_data[selected_column],
                                    orientation='h',
                                    marker_color=['rgba(225, 29, 72, 0.6)' if x != 0 else 'rgba(0,0,0,0)' for x in negative_data[selected_column]],
                                    text=negative_labels,
                                    textposition='outside',
                                    hovertemplate='<b>%{text}</b><br>Change: %{x:.1%}<extra></extra>',
                                    showlegend=False,
                                    name="Decreasing"
                                ), row=1, col=1)
                            
                            # Add positive performance bars (right side)
                            if len(positive_data) > 0:
                                # Create custom labels: percentage + commodity + impact (for increasing)
                                positive_labels = []
                                for idx, row in positive_data.iterrows():
                                    if row['Commodities'] == '':
                                        positive_labels.append('')
                                    else:
                                        impact_text = f" ({row['Impact']})" if pd.notna(row['Impact']) and row['Impact'] != '' else ''
                                        positive_labels.append(f"{row[selected_column]:.1%}   {row['Commodities']}{impact_text}")
                                
                                fig.add_trace(go.Bar(
                                    y=list(range(len(positive_data))),
                                    x=positive_data[selected_column],
                                    orientation='h',
                                    marker_color=['rgba(16, 185, 129, 0.6)' if x != 0 else 'rgba(0,0,0,0)' for x in positive_data[selected_column]],
                                    text=positive_labels,
                                    textposition='outside',
                                    hovertemplate='<b>%{text}</b><br>Change: %{x:.1%}<extra></extra>',
                                    showlegend=False,
                                    name="Increasing"
                                ), row=1, col=2)
                            
                            chart_height = max(300, max_items * 20)
                            
                            # Update layout
                            fig.update_layout(
                                template="plotly_white",
                                height=chart_height,
                                margin=dict(l=150, r=150, t=60, b=20),
                                font=dict(family="Manrope, sans-serif", size=11),
                                title=dict(
                                    text=f"<b>{chart_label} Performance </b>",
                                    x=0.5,
                                    xanchor='center',
                                    y=0.97
                                ),
                                showlegend=False
                            )
                            
                            # Update axes - Hide x-axis completely and set range for text display
                            # For negative values (left side), extend negative range, set positive to 0
                            min_negative = negative_data[selected_column].min() if len(negative_data) > 0 and negative_data[selected_column].min() < 0 else -0.01
                            fig.update_xaxes(
                                visible=False,
                                showgrid=False,
                                zeroline=False,
                                range=[min_negative * 1.8, 0],
                                row=1, col=1
                            )
                            # For positive values (right side), extend positive range, set negative to 0
                            max_positive = positive_data[selected_column].max() if len(positive_data) > 0 and positive_data[selected_column].max() > 0 else 0.01
                            fig.update_xaxes(
                                visible=False,
                                showgrid=False,
                                zeroline=False,
                                range=[0, max_positive * 1.8],
                                row=1, col=2
                            )
                            # Hide y-axis ticks and labels since we show info in text
                            fig.update_yaxes(
                                autorange="reversed", 
                                showticklabels=False, 
                                showgrid=False,
                                zeroline=False,
                                row=1, col=1
                            )
                            fig.update_yaxes(
                                autorange="reversed", 
                                showticklabels=False, 
                                showgrid=False,
                                zeroline=False,
                                row=1, col=2
                            )
                            
                            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
                        else:
                            st.info(f"No data available for {chart_label} performance with the selected filters (after removing 0% changes).")
                    else:
                        st.warning(f"Could not generate chart. The required data column '{selected_column}' is missing.")
        else:
            st.warning("No data to display in the chart with the current filters.")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- LINE CHART SECTION ---
        

        if not filtered_df.empty:
            # Filter data based on date range from sidebar
            date_filtered_data = df_data[
                (df_data['Date'] >= pd.to_datetime(start_date)) & 
                (df_data['Date'] <= pd.to_datetime(end_date))
            ].copy()
            
            # Get available commodities from filtered data and sort alphabetically
            available_commodities = date_filtered_data['Commodities'].unique()
            filtered_commodities = sorted([c for c in available_commodities if c in filtered_df['Commodities'].values])
            
            if filtered_commodities:
                # Allow user to select specific commodities for the line chart
                selected_line_commodities = st.multiselect(
                    "Select commodities to display in line chart:",
                    options=filtered_commodities,
                    default=filtered_commodities[:1] if len(filtered_commodities) >= 1 else filtered_commodities,
                    key="line_chart_commodities"
                )
                
                if selected_line_commodities:
                    # Get stock tickers for selected commodities
                    selected_stocks = set()
                    for commodity in selected_line_commodities:
                        commodity_row = filtered_df[filtered_df['Commodities'] == commodity]
                        if not commodity_row.empty and pd.notna(commodity_row['Impact'].iloc[0]):
                            impact = str(commodity_row['Impact'].iloc[0]).strip()
                            if impact:
                                # Split by comma in case multiple stocks
                                stock_list = [s.strip().upper() for s in impact.split(',')]
                                selected_stocks.update(stock_list)
                    
                    # Create layout - side by side if we have stocks
                    if selected_stocks:
                        col1, col2 = st.columns(2)
                    else:
                        col1 = st.container()
                        col2 = None
                    
                    with col1:
                        st.markdown(f"**{selected_interval} Commodity Prices**")
                        # Create commodity line chart
                        fig_line = go.Figure()
                        
                        # Color palette for different commodities - lighter colors
                        colors = ['#4ade80', '#f87171', '#60a5fa', '#fbbf24', '#a78bfa', '#fb7185', '#38bdf8', '#a3e635']
                        
                        for i, commodity in enumerate(selected_line_commodities):
                            commodity_data = date_filtered_data[date_filtered_data['Commodities'] == commodity].copy()
                            commodity_data = commodity_data.sort_values('Date')
                            
                            if not commodity_data.empty:
                                # Apply interval aggregation
                                if selected_interval == 'Daily':
                                    # Use all data points
                                    aggregated_data = commodity_data
                                elif selected_interval == 'Weekly':
                                    # Group by week and take the last price of each week
                                    commodity_data['Week'] = commodity_data['Date'].dt.to_period('W')
                                    aggregated_data = commodity_data.groupby('Week').last().reset_index()
                                    aggregated_data['Date'] = aggregated_data['Week'].dt.end_time
                                elif selected_interval == 'Monthly':
                                    # Group by month and take the last price of each month
                                    commodity_data['Month'] = commodity_data['Date'].dt.to_period('M')
                                    aggregated_data = commodity_data.groupby('Month').last().reset_index()
                                    aggregated_data['Date'] = aggregated_data['Month'].dt.end_time
                                elif selected_interval == 'Quarterly':
                                    # Group by quarter and take the last price of each quarter
                                    commodity_data['Quarter'] = commodity_data['Date'].dt.to_period('Q')
                                    aggregated_data = commodity_data.groupby('Quarter').last().reset_index()
                                    aggregated_data['Date'] = aggregated_data['Quarter'].dt.end_time
                                
                                color = colors[i % len(colors)]
                                fig_line.add_trace(go.Scatter(
                                    x=aggregated_data['Date'],
                                    y=aggregated_data['Price'],
                                    mode='lines',
                                    name=commodity,
                                    line=dict(color=color, width=2),
                                    hovertemplate=f'<b>{commodity}</b><br>Date: %{{x}}<br>Price: $%{{y:.2f}}<extra></extra>'
                                ))
                        
                        # Update commodity chart layout
                        fig_line.update_layout(
                            template="plotly_white",
                            height=500,
                            margin=dict(l=50, r=50, t=40, b=50),
                            font=dict(family="Manrope, sans-serif", size=12),
                            xaxis_title="Date",
                            yaxis_title="Price ($)",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            hovermode='x unified'
                        )
                        
                        # Style the axes with shorter dates
                        fig_line.update_xaxes(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='rgba(0,0,0,0.1)',
                            showline=True,
                            linewidth=1,
                            linecolor='rgba(0,0,0,0.2)',
                            tickformat='%b %y',
                            tickangle=-30
                        )
                        if hide_gaps:
                            # Hide weekends while preserving date axis
                            fig_line.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
                        fig_line.update_yaxes(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='rgba(0,0,0,0.1)',
                            showline=True,
                            linewidth=1,
                            linecolor='rgba(0,0,0,0.2)'
                        )
                        
                        st.plotly_chart(fig_line, use_container_width=True, config={"scrollZoom": True})
                    
                    # Stock impact chart in column 2
                    if col2 is not None and selected_stocks:
                        with col2:
                            st.markdown(f"**{selected_interval} Stock Impact**")
                            
                            # Fetch stock data for the selected date range
                            days_range = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 30  # Add buffer
                            stock_data = fetch_multiple_stocks(list(selected_stocks), days=days_range)
                            
                            if stock_data:
                                fig_stock = go.Figure()
                                stock_colors = ['#c084fc', '#f87171', '#67e8f9', '#bef264', '#fdba74']
                                
                                for j, (ticker, stock_df) in enumerate(stock_data.items()):
                                    if stock_df is not None and not stock_df.empty:
                                        # Filter by date range - handle timezone issues
                                        start_dt = pd.to_datetime(start_date).tz_localize(None) if pd.to_datetime(start_date).tz is None else pd.to_datetime(start_date).tz_convert(None)
                                        end_dt = pd.to_datetime(end_date).tz_localize(None) if pd.to_datetime(end_date).tz is None else pd.to_datetime(end_date).tz_convert(None)
                                        
                                        # Ensure stock_df tradingDate is timezone-naive
                                        stock_df_copy = stock_df.copy()
                                        if stock_df_copy['tradingDate'].dt.tz is not None:
                                            stock_df_copy['tradingDate'] = stock_df_copy['tradingDate'].dt.tz_convert(None)
                                        
                                        stock_filtered = stock_df_copy[
                                            (stock_df_copy['tradingDate'] >= start_dt) & 
                                            (stock_df_copy['tradingDate'] <= end_dt)
                                        ].copy()
                                        
                                        if not stock_filtered.empty:
                                            # Apply same interval aggregation as commodity
                                            if selected_interval == 'Daily':
                                                aggregated_stock = stock_filtered
                                            elif selected_interval == 'Weekly':
                                                stock_filtered['Week'] = stock_filtered['tradingDate'].dt.to_period('W')
                                                aggregated_stock = stock_filtered.groupby('Week').last().reset_index()
                                                aggregated_stock['tradingDate'] = aggregated_stock['Week'].dt.end_time
                                            elif selected_interval == 'Monthly':
                                                stock_filtered['Month'] = stock_filtered['tradingDate'].dt.to_period('M')
                                                aggregated_stock = stock_filtered.groupby('Month').last().reset_index()
                                                aggregated_stock['tradingDate'] = aggregated_stock['Month'].dt.end_time
                                            elif selected_interval == 'Quarterly':
                                                stock_filtered['Quarter'] = stock_filtered['tradingDate'].dt.to_period('Q')
                                                aggregated_stock = stock_filtered.groupby('Quarter').last().reset_index()
                                                aggregated_stock['tradingDate'] = aggregated_stock['Quarter'].dt.end_time
                                            
                                            color = stock_colors[j % len(stock_colors)]
                                            fig_stock.add_trace(go.Scatter(
                                                x=aggregated_stock['tradingDate'],
                                                y=aggregated_stock['close'],
                                                mode='lines',
                                                name=ticker,
                                                line=dict(color=color, width=2),
                                                hovertemplate=f'<b>{ticker}</b><br>Date: %{{x}}<br>Price: %{{y:,.0f}} VND<extra></extra>'
                                            ))
                                
                                # Update stock chart layout
                                fig_stock.update_layout(
                                    template="plotly_white",
                                    height=500,
                                    margin=dict(l=50, r=50, t=40, b=50),
                                    font=dict(family="Manrope, sans-serif", size=12),
                                    xaxis_title="Date",
                                    yaxis_title="Price (VND)",
                                    legend=dict(
                                        orientation="h",
                                        yanchor="bottom",
                                        y=1.02,
                                        xanchor="right",
                                        x=1
                                    ),
                                    hovermode='x unified'
                                )
                                
                                # Style stock chart axes with shorter dates
                                fig_stock.update_xaxes(
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='rgba(0,0,0,0.1)',
                                    showline=True,
                                    linewidth=1,
                                    linecolor='rgba(0,0,0,0.2)',
                                    tickformat='%b %y',
                                    tickangle=-30
                                )
                                if hide_gaps:
                                    # Hide weekends while preserving date axis
                                    fig_stock.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
                                fig_stock.update_yaxes(
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='rgba(0,0,0,0.1)',
                                    showline=True,
                                    linewidth=1,
                                    linecolor='rgba(0,0,0,0.2)'
                                )
                                
                                st.plotly_chart(fig_stock, use_container_width=True, config={"scrollZoom": True})
                            else:
                                st.info("No stock data available for the selected commodities.")
                else:
                    st.info("Please select at least one commodity to display in the line chart.")
            else:
                st.warning("No commodities available for the selected date range and filters.")
        else:
            st.warning("No data available for line chart with the current filters.")

else:
    st.error("Failed to load data files. Please check the 'data' directory.")
