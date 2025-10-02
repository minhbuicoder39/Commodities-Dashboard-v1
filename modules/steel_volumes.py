import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_steel_volumes_section(price_pivot=None):
    """Render the Steel Volumes Analysis section in the Steel Industry page"""
    
    if not isinstance(price_pivot, pd.DataFrame):
        st.error("Invalid price_pivot data provided")
        return
        
    required_columns = ['Long_Steel_Profit', 'HRC_Profit', 'China Long steel', 'China HRC']
    missing_columns = [col for col in required_columns if col not in price_pivot.columns]
    if missing_columns:
        st.error(f"Missing required columns in price_pivot: {', '.join(missing_columns)}")
        return

    st.markdown("""
        <div style='background-color: #f0f7f4; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <h4 style='margin:0; color: #00816D;'>Overview</h4>
            <p>Analysis of production volumes and market share across different steel products and manufacturers.</p>
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
            selected_product = st.selectbox("Select Product", products, key="volumes_product_selector")
        with col2:
            selected_companies = st.multiselect("Select Companies", companies, default=companies, key="volumes_companies_selector")

        # Filter data based on selection
        market_col = f"{selected_product} - Market"
        company_cols = [col for col in volumes_df.columns 
                       if col.startswith(selected_product) and 
                       'Market' not in col and
                       any(company in col for company in selected_companies)]
        
        # Get the data
        market_data = volumes_df[[market_col]] if market_col in volumes_df.columns else None
        company_data = volumes_df[company_cols]
        
        # Remove any leading null values
        company_data = company_data.dropna(how='all')
        if market_data is not None:
            market_data = market_data.dropna(how='all')
            
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

            # Get HPG volumes for Rebar and Coil (from 2016)
            hpg_rebar = volumes_df['Rebar - HPG'] if 'Rebar - HPG' in volumes_df.columns else pd.Series(0, index=volumes_df.index)
            hpg_coil = volumes_df['Coil - HPG'] if 'Coil - HPG' in volumes_df.columns else pd.Series(0, index=volumes_df.index)

            # Get profit per ton from price_pivot (30-day moving average)
            if price_pivot is not None and 'Long_Steel_Profit' in price_pivot.columns and 'HRC_Profit' in price_pivot.columns:
                # Use volumes data full date range as the common index
                common_index = hpg_rebar.index
                
                # Get ASP (Average Selling Price) for rebar and HRC
                rebar_price = price_pivot['China Long steel'].rolling(window=30).mean().reindex(common_index, method='ffill')
                coil_price = price_pivot['China HRC'].rolling(window=30).mean().reindex(common_index, method='ffill')
                
                # Get profit margins per ton
                rebar_profit = price_pivot['Long_Steel_Profit'].rolling(window=30).mean().reindex(common_index, method='ffill')
                coil_profit = price_pivot['HRC_Profit'].rolling(window=30).mean().reindex(common_index, method='ffill')
                
                # Calculate individual product revenues using ASP
                rebar_revenue_usd = hpg_rebar * rebar_price
                hrc_revenue_usd = hpg_coil * coil_price
                total_revenue_usd = rebar_revenue_usd + hrc_revenue_usd

                # Calculate individual product gross profits
                rebar_gross_profit_usd = hpg_rebar * rebar_profit
                hrc_gross_profit_usd = hpg_coil * coil_profit
                total_gross_profit_usd = rebar_gross_profit_usd + hrc_gross_profit_usd

                # Calculate deductions (allocated proportionally by revenue)
                sga_usd = total_revenue_usd * 0.03  # 3% of total revenue for SG&A
                depreciation_per_ton = 35  # $35 per ton fixed depreciation
                total_volume = hpg_rebar + hpg_coil
                depreciation_usd = total_volume * depreciation_per_ton

                # Calculate EBIT
                ebit_usd = total_gross_profit_usd - sga_usd - depreciation_usd

                # Calculate tax
                tax_usd = ebit_usd * 0.12  # 12% corporate income tax

                # Calculate net profit (allocated proportionally by gross profit)
                net_profit_total_usd = ebit_usd - tax_usd
                
                # Allocate net profit proportionally by gross profit contribution
                rebar_profit_share = rebar_gross_profit_usd / (total_gross_profit_usd + 1e-10)  # Add small value to avoid division by zero
                hrc_profit_share = hrc_gross_profit_usd / (total_gross_profit_usd + 1e-10)
                
                rebar_net_profit_usd = net_profit_total_usd * rebar_profit_share
                hrc_net_profit_usd = net_profit_total_usd * hrc_profit_share

                # Create exchange rate series matching the volumes index (full range from 2016)
                exchange_rate_series = pd.Series(index=common_index, dtype=float)
                
                for year in range(2016, 2026):  # Extended range to cover from 2016
                    mask = common_index.map(lambda x: x.year) == year
                    if year <= 2021:
                        exchange_rate_series[mask] = 22500  # Historical rate for 2016-2021
                    else:
                        exchange_rate_series[mask] = exchange_rates.get(year, 26500)

                # Convert to VND using year-specific exchange rates
                rebar_revenue_vnd = rebar_revenue_usd * exchange_rate_series
                hrc_revenue_vnd = hrc_revenue_usd * exchange_rate_series
                rebar_net_profit_vnd = rebar_net_profit_usd * exchange_rate_series
                hrc_net_profit_vnd = hrc_net_profit_usd * exchange_rate_series

                # Display profit analysis
                # Define constant for billion VND
                billion_vnd = 1_000_000_000

                st.subheader("Monthly Revenue and Profit Analysis")
                
                # Add period selector
                view_period = st.radio("Select View Period", ["Monthly", "Quarterly"], horizontal=True)

                # Create revenue dataframe by product
                revenue_df = pd.DataFrame({
                    'Rebar Revenue': rebar_revenue_vnd,
                    'HRC Revenue': hrc_revenue_vnd
                }, index=common_index)

                # Create profit dataframe by product
                profit_df = pd.DataFrame({
                    'Rebar Net Profit': rebar_net_profit_vnd,
                    'HRC Net Profit': hrc_net_profit_vnd
                }, index=common_index)

                # Convert to quarterly if selected
                if view_period == "Quarterly":
                    revenue_df = revenue_df.resample('QE').sum()
                    profit_df = profit_df.resample('QE').sum()
                
                # Convert values to billions for display
                revenue_df = revenue_df / billion_vnd
                profit_df = profit_df / billion_vnd

                # Revenue stacked column chart
                fig_revenue = go.Figure()
                colors_revenue = ['#4ade80', '#22c55e']
                
                for i, column in enumerate(revenue_df.columns):
                    fig_revenue.add_trace(
                        go.Bar(
                            name=column,
                            x=revenue_df.index,
                            y=revenue_df[column],
                            marker_color=colors_revenue[i]
                        )
                    )
                
                fig_revenue.update_layout(
                    title="HPG Revenue by Product (from 2016)",
                    template="plotly_white",
                    barmode='stack',
                    height=400,
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
                st.plotly_chart(fig_revenue, use_container_width=True)

                # Profit stacked column chart
                fig_profit = go.Figure()
                colors_profit = ['#f59e0b', '#ec4899']
                
                for i, column in enumerate(profit_df.columns):
                    fig_profit.add_trace(
                        go.Bar(
                            name=column,
                            x=profit_df.index,
                            y=profit_df[column],
                            marker_color=colors_profit[i]
                        )
                    )
                
                fig_profit.update_layout(
                    title="HPG Net Profit by Product (from 2016)",
                    template="plotly_white",
                    barmode='stack',
                    height=400,
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
                latest_month = revenue_df.index[-1]
                col1, col2, col3, col4, col5 = st.columns(5)
            
                with col1:
                    total_revenue_latest = revenue_df.iloc[-1].sum()
                    total_revenue_prev = revenue_df.iloc[-2].sum()
                    st.metric(
                        "Total Revenue",
                        f"{total_revenue_latest:,.0f}B VND",
                        f"{(total_revenue_latest - total_revenue_prev):,.0f}B"
                    )
                
                with col2:
                    total_profit_latest = profit_df.iloc[-1].sum()
                    total_profit_prev = profit_df.iloc[-2].sum()
                    st.metric(
                        "Total Net Profit",
                        f"{total_profit_latest:,.0f}B VND",
                        f"{(total_profit_latest - total_profit_prev):,.0f}B"
                    )
                
                with col3:
                    rebar_revenue_latest = revenue_df['Rebar Revenue'].iloc[-1]
                    rebar_revenue_prev = revenue_df['Rebar Revenue'].iloc[-2]
                    st.metric(
                        "Rebar Revenue",
                        f"{rebar_revenue_latest:,.0f}B VND",
                        f"{(rebar_revenue_latest - rebar_revenue_prev):,.0f}B"
                    )
                
                with col4:
                    hrc_revenue_latest = revenue_df['HRC Revenue'].iloc[-1]
                    hrc_revenue_prev = revenue_df['HRC Revenue'].iloc[-2]
                    st.metric(
                        "HRC Revenue",
                        f"{hrc_revenue_latest:,.0f}B VND",
                        f"{(hrc_revenue_latest - hrc_revenue_prev):,.0f}B"
                    )
                
                with col5:
                    net_margin = (total_profit_latest / total_revenue_latest * 100) if total_revenue_latest != 0 else 0
                    prev_net_margin = (total_profit_prev / total_revenue_prev * 100) if total_revenue_prev != 0 else 0
                    st.metric(
                        "Net Margin",
                        f"{net_margin:.1f}%",
                        f"{net_margin - prev_net_margin:.1f}%"
                    )
    else:
        st.error("Failed to load steel volumes data. Please check the data file.")
