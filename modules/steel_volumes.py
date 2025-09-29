import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_steel_volumes_section(price_pivot=None):
    """Render the Steel Volumes Analysis section in the Steel Industry page"""
    
    st.markdown("""
        <div style='background-color: #f0f7f4; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <h3 style='margin:0; color: #00816D;'>Steel Volumes Analysis</h3>
            <p>Analysis of production volumes across different steel products and manufacturers</p>
        </div>
    """, unsafe_allow_html=True)

    # Load volumes data
    @st.cache_data
    def load_volumes_data():
        try:
            df = pd.read_csv('data/steel_volumes.csv', parse_dates=['Date'], index_col='Date')
            return df
        except Exception as e:
            st.error(f"Error loading volumes data: {str(e)}")
            return None

    volumes_df = load_volumes_data()

    if volumes_df is not None:
        # Define constants
        billion_vnd = 1_000_000_000
        exchange_rates = {
            2022: 23000,
            2023: 24500,
            2024: 25000,
            2025: 26500
        }

        # Get unique products and companies
        products = sorted(list(set([col.split(' - ')[0] for col in volumes_df.columns])))
        companies = sorted(list(set([col.split(' - ')[1] for col in volumes_df.columns])))

        # Create filters
        col1, col2 = st.columns(2)
        with col1:
            selected_product = st.selectbox("Select Product", products)
        with col2:
            selected_companies = st.multiselect("Select Companies", companies, default=companies)

        # Filter data based on selection
        market_col = f"{selected_product} - Market"
        company_cols = [col for col in volumes_df.columns 
                       if col.startswith(selected_product) and 
                       'Market' not in col and
                       any(company in col for company in selected_companies)]
        
        # Get the data
        market_data = volumes_df[[market_col]] if market_col in volumes_df.columns else None
        company_data = volumes_df[company_cols]
        
        # Set start date to 2021
        start_date = pd.to_datetime('2021-01-01')
        
        # Filter data from 2021 onwards and remove any leading null values
        company_data = company_data[start_date:]
        if market_data is not None:
            market_data = market_data[start_date:]
            
        # Find the first non-null value date after 2021
        first_valid_date = company_data.first_valid_index()
        if first_valid_date:
            company_data = company_data[first_valid_date:]
            if market_data is not None:
                market_data = market_data[first_valid_date:]

        # Rename columns to show only company names
        renamed_df = company_data.rename(columns=lambda x: x.split(' - ')[1])

        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Volume Trends", "Market Share", "Growth Analysis"])

        with tab1:
            # Volume trends column chart
            fig = go.Figure()
            
            # Add bars for each company
            for company in renamed_df.columns:
                fig.add_trace(
                    go.Bar(
                        name=company,
                        x=renamed_df.index,
                        y=renamed_df[company],
                        hovertemplate="%{x}<br>" +
                                    f"{company}: %{{y:,.0f}}<extra></extra>"
                    )
                )
            
            fig.update_layout(
                title=f"{selected_product} Volumes Over Time",
                template="plotly_white",
                barmode='group',
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis_title="Date",
                yaxis_title="Volume"
            )
            
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            # Market share analysis using market volume as denominator
            if market_data is not None:
                market_volume = market_data[market_col]
                market_share_df = renamed_df.div(market_volume, axis=0) * 100
            else:
                # Fallback to using sum of companies if market data is not available
                market_share_df = renamed_df.div(renamed_df.sum(axis=1), axis=0) * 100

            # Market share area chart
            fig_share = px.area(market_share_df, 
                               title=f"{selected_product} Market Share (%)",
                               labels={'value': 'Market Share (%)', 'Date': 'Date', 'variable': 'Company'},
                               height=500)
            
            fig_share.update_layout(
                template="plotly_white",
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig_share, use_container_width=True)

            # Current market share pie chart
            latest_date = market_share_df.index[-1]
            latest_shares = market_share_df.iloc[-1]
            
            fig_pie = px.pie(values=latest_shares.values, 
                            names=latest_shares.index,
                            title=f"Current Market Share ({latest_date.strftime('%B %Y')})")
            
            st.plotly_chart(fig_pie, use_container_width=True)

        with tab3:
            # Growth analysis
            st.subheader("Growth Analysis")
            
            # Calculate YoY growth
            yoy_df = renamed_df.pct_change(periods=12) * 100
            current_month = renamed_df.index[-1]
            
            # YoY growth metrics
            cols = st.columns(len(selected_companies))
            for i, company in enumerate(renamed_df.columns):
                current_vol = renamed_df[company].iloc[-1]
                yoy_growth = yoy_df[company].iloc[-1]
                
                with cols[i]:
                    st.metric(
                        label=company,
                        value=f"{current_vol:,.0f}",
                        delta=f"{yoy_growth:.1f}%"
                    )

            # Growth trends chart
            fig_growth = px.line(yoy_df,
                                title=f"Year-over-Year Growth Rate (%)",
                                labels={'value': 'YoY Growth (%)', 'Date': 'Date', 'variable': 'Company'},
                                height=500)
            
            fig_growth.update_layout(
                template="plotly_white",
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig_growth, use_container_width=True)

        # Add HPG Profit Analysis Section
        if 'HPG' in selected_companies:
            st.markdown("""
                <div style='background-color: #f0f7f4; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
                    <h3 style='margin:0; color: #00816D;'>HPG Monthly Profit Analysis</h3>
                    <p>Estimated monthly profit based on sales volumes and profit margins</p>
                </div>
            """, unsafe_allow_html=True)

            # Define exchange rates by year
            exchange_rates = {
                2022: 23000,
                2023: 24500,
                2024: 25000,
                2025: 26500
            }

            # Display current exchange rate
            current_month = volumes_df.index[-1]
            current_year = current_month.year
            current_rate = exchange_rates.get(current_year, 26500)  # default to 2025 rate if year not found
            st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
                    <p style='margin:0; font-size: 0.9rem;'>
                        <strong>Exchange Rates:</strong> 
                        2022: 23,000 VND/USD | 
                        2023: 24,500 VND/USD | 
                        2024: 25,000 VND/USD | 
                        2025: 26,500 VND/USD
                    </p>
                    <p style='margin:0; font-size: 0.9rem;'>
                        <strong>Current Rate ({current_year}):</strong> {current_rate:,} VND/USD
                    </p>
                </div>
            """, unsafe_allow_html=True)

            # Get HPG volumes for Rebar and Coil
            hpg_rebar = volumes_df['Rebar - HPG'] if 'Rebar - HPG' in volumes_df.columns else pd.Series(0, index=volumes_df.index)
            hpg_coil = volumes_df['Coil - HPG'] if 'Coil - HPG' in volumes_df.columns else pd.Series(0, index=volumes_df.index)

            # Get profit per ton from price_pivot (30-day moving average)
            if 'price_pivot' in locals():
                rebar_profit = price_pivot['Long_Steel_Profit'].rolling(window=30).mean()
                coil_profit = price_pivot['HRC_Profit'].rolling(window=30).mean()

                # Calculate revenue (using selling prices from price_pivot)
                common_index = hpg_rebar.index
                rebar_price = price_pivot['China Long steel'].rolling(window=30).mean().reindex(common_index)
                coil_price = price_pivot['China HRC'].rolling(window=30).mean().reindex(common_index)
                rebar_profit = rebar_profit.reindex(common_index)
                coil_profit = coil_profit.reindex(common_index)
                
                revenue = (hpg_rebar * rebar_price + hpg_coil * coil_price)
                # Calculate gross profit
                gross_profit = (hpg_rebar * rebar_profit + hpg_coil * coil_profit)

                # Calculate deductions
                sga = revenue * 0.03  # 3% of revenue for SG&A
                depreciation_per_ton = 35  # $35 per ton fixed depreciation
                total_volume = hpg_rebar + hpg_coil
                depreciation = total_volume * depreciation_per_ton  # Fixed depreciation per ton

                # Calculate EBIT
                ebit = gross_profit - sga - depreciation

                # Calculate tax
                tax = ebit * 0.12  # 12% corporate income tax

                # Calculate net profit
                net_profit = ebit - tax

                # Define exchange rates by year
                exchange_rates = {
                    2022: 23000,
                    2023: 24500,
                    2024: 25000,
                    2025: 26500
                }
                
                # Create exchange rate series matching the index
                exchange_rate_series = pd.Series(index=revenue.index, dtype=float)
                # Ensure index is datetime
                if not isinstance(revenue.index, pd.DatetimeIndex):
                    revenue.index = pd.to_datetime(revenue.index)
                
                for year in range(2022, 2026):
                    mask = revenue.index.map(lambda x: x.year) == year
                    exchange_rate_series[mask] = exchange_rates.get(year, 26500)
                
                # Ensure all series have the same index before multiplication
                common_index = revenue.index
                exchange_rate_series = exchange_rate_series.reindex(common_index)
                
                # Convert to VND using year-specific exchange rates
                revenue_vnd = revenue.reindex(common_index) * exchange_rate_series
                gross_profit_vnd = gross_profit.reindex(common_index) * exchange_rate_series
                sga_vnd = sga.reindex(common_index) * exchange_rate_series
                depreciation_vnd = depreciation.reindex(common_index) * exchange_rate_series
                tax_vnd = tax.reindex(common_index) * exchange_rate_series
                net_profit_vnd = net_profit.reindex(common_index) * exchange_rate_series

                # Ensure all series have the same index type
                common_index = revenue_vnd.index
                
                # Create profit waterfall chart (in VND)
                profit_df = pd.DataFrame({
                    'Revenue': revenue_vnd,
                    'Cost of Goods': -(revenue_vnd - gross_profit_vnd).reindex(common_index),
                    'Gross Profit': gross_profit_vnd.reindex(common_index),
                    'SG&A': -sga_vnd.reindex(common_index),
                    'Depreciation': -depreciation_vnd.reindex(common_index),
                    'Tax': -tax_vnd.reindex(common_index),
                    'Net Profit': net_profit_vnd.reindex(common_index)
                }, index=common_index)

                # Display profit analysis
                # Define constant for billion VND
                billion_vnd = 1_000_000_000

                st.subheader("Monthly Profit Breakdown")
                fig_profit = go.Figure()

                # Add bars for each component
                colors = ['#4ade80', '#ef4444', '#f59e0b', '#6366f1', '#22c55e', '#8b5cf6', '#ec4899']
                for i, column in enumerate(profit_df.columns):
                    fig_profit.add_trace(
                        go.Bar(
                            name=column,
                            x=profit_df.index,
                            y=profit_df[column],
                            marker_color=colors[i % len(colors)]  # Use modulo to prevent index out of range
                        )
                    )

                # Convert values to billions for display
                for col in profit_df.columns:
                    profit_df[col] = profit_df[col] / billion_vnd
                    
                fig_profit.update_layout(
                    title="HPG Monthly Profit Components",
                    template="plotly_white",
                    barmode='relative',
                    height=500,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    xaxis_title="Date",
                    yaxis_title="Amount (Billion VND)"
                )
                st.plotly_chart(fig_profit, use_container_width=True)

                # Display key metrics
                latest_month = profit_df.index[-1]
                col1, col2, col3, col4, col5 = st.columns(5)
            
                with col1:
                    st.metric(
                        "Revenue",
                        f"{revenue_vnd.iloc[-1]/billion_vnd:,.0f}B VND",
                        f"{(revenue_vnd.iloc[-1] - revenue_vnd.iloc[-2])/billion_vnd:,.0f}B"
                    )
                
                with col2:
                    st.metric(
                        "Gross Profit",
                        f"{profit_df['Gross Profit'].iloc[-1]:,.0f}B VND",
                        f"{(profit_df['Gross Profit'].iloc[-1] - profit_df['Gross Profit'].iloc[-2]):,.0f}B"
                    )
                
                with col3:
                    st.metric(
                        "EBIT",
                        f"{(profit_df['Gross Profit'].iloc[-1] - profit_df['SG&A'].iloc[-1] - profit_df['Depreciation'].iloc[-1]):,.0f}B VND",
                        f"{(profit_df['Gross Profit'].iloc[-1] - profit_df['SG&A'].iloc[-1] - profit_df['Depreciation'].iloc[-1]) - (profit_df['Gross Profit'].iloc[-2] - profit_df['SG&A'].iloc[-2] - profit_df['Depreciation'].iloc[-2]):,.0f}B"
                    )
                
                with col4:
                    st.metric(
                        "Net Profit",
                        f"{profit_df['Net Profit'].iloc[-1]:,.0f}B VND",
                        f"{(profit_df['Net Profit'].iloc[-1] - profit_df['Net Profit'].iloc[-2]):,.0f}B"
                    )
                
                with col5:
                    net_margin = (profit_df['Net Profit'].iloc[-1] / profit_df['Revenue'].iloc[-1] * 100) if profit_df['Revenue'].iloc[-1] != 0 else 0
                    prev_net_margin = (profit_df['Net Profit'].iloc[-2] / profit_df['Revenue'].iloc[-2] * 100) if profit_df['Revenue'].iloc[-2] != 0 else 0
                    st.metric(
                        "Net Margin",
                        f"{net_margin:.1f}%",
                        f"{net_margin - prev_net_margin:.1f}%"
                    )
    else:
        st.error("Failed to load steel volumes data. Please check the data file.")
