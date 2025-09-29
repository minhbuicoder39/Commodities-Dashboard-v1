import streamlit as st
import pandas as pd
from modules.data_loader import load_data
from modules.chatgpt_helper import init_openai_client, get_commodity_analysis, chat_with_commodity_expert

# Page config
st.set_page_config(
    page_title="ChatGPT Commodity Analysis",
    page_icon="🤖",
    layout="wide"
)

# Title
st.title("🤖 ChatGPT Commodity Analysis")

# Initialize OpenAI client
client = init_openai_client()

if client is None:
    st.error("Please configure your OpenAI API key in the secrets.toml file.")
    st.stop()

# Load data
df_data, df_list = load_data()

# Sidebar options
st.sidebar.markdown("### 📊 Chart Options")
hide_gaps = st.sidebar.checkbox("Hide non-trading gaps", value=True)

if df_data is not None and df_list is not None:
    # Create two tabs
    tab1, tab2 = st.tabs(["📊 Commodity Analysis", "💬 Chat with Expert"])
    
    with tab1:
        st.subheader("AI-Powered Commodity Analysis")
        
        # Create two columns for layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Commodity selector
            available_commodities = sorted(df_data['Commodities'].unique())
            selected_commodity = st.selectbox(
                "Select a commodity",
                options=available_commodities
            )
            
            # Analysis type selector
            analysis_type = st.radio(
                "Analysis Type",
                ["comprehensive", "technical", "risk"],
                format_func=lambda x: x.title()
            )
            
            generate_button = st.button("🔄 Generate Analysis", use_container_width=True)
            
            # Add save to PDF button (placeholder for future feature)
            if st.button("💾 Save Analysis", use_container_width=True):
                st.info("PDF export feature coming soon!")
        
        with col2:
            if generate_button:
                with st.spinner("Analyzing data..."):
                    # Get data for selected commodity
                    commodity_data = df_data[df_data['Commodities'] == selected_commodity].copy()
                    
                    if not commodity_data.empty:
                        # Create tabs for different views
                        analysis_tab, data_tab, viz_tab = st.tabs(["📊 Analysis", "📈 Data", "🔍 Visualization"])
                        
                        with analysis_tab:
                            # Get analysis from ChatGPT
                            analysis_response = get_commodity_analysis(
                                client, 
                                commodity_data, 
                                selected_commodity,
                                analysis_type
                            )
                            
                            if isinstance(analysis_response, dict):
                                if 'error' in analysis_response:
                                    st.error(analysis_response['error'])
                                else:
                                    # Display analysis in a nice format
                                    st.markdown("### Analysis Results")
                                    st.markdown(analysis_response['content'])
                                    
                                    # Create a container for token usage
                                    token_container = st.container()
                                    
                                    # Display token usage metrics
                                    token_container.markdown("### 📊 Token Usage")
                                    cols = token_container.columns(4)
                                    
                                    # Display metrics in columns
                                    cols[0].metric(
                                        "Prompt Tokens",
                                        analysis_response['usage']['prompt_tokens']
                                    )
                                    cols[1].metric(
                                        "Completion Tokens",
                                        analysis_response['usage']['completion_tokens']
                                    )
                                    cols[2].metric(
                                        "Total Tokens",
                                        analysis_response['usage']['total_tokens']
                                    )
                                    cols[3].metric(
                                        "Estimated Cost",
                                        analysis_response['usage']['estimated_cost']
                                    )
                                    
                                    # Add a divider
                                    st.markdown("---")
                            else:
                                # Display error message
                                st.error(f"Unexpected response format: {analysis_response}")
                        
                        with data_tab:
                            # Show recent price data
                            st.markdown("### Recent Price Data")
                            recent_data = commodity_data.tail(10).sort_index(ascending=False)
                            
                            # Get available columns
                            available_columns = ['Date', 'Price']
                            for col in ['%Day', '%Week', '%Month', '%YTD']:
                                if col in recent_data.columns:
                                    available_columns.append(col)
                            
                            # Format the data for display
                            display_data = recent_data[available_columns].copy()
                            
                            # Format percentage columns
                            for col in available_columns:
                                if col.startswith('%'):
                                    display_data[col] = display_data[col].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")
                                elif col == 'Price':
                                    display_data[col] = display_data[col].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
                            
                            st.dataframe(display_data, use_container_width=True)
                            
                            # Show basic statistics
                            st.markdown("### Basic Statistics")
                            stats = pd.DataFrame({
                                'Metric': [
                                    'Current Price',
                                    'Average Price',
                                    'Std Dev',
                                    'Min Price',
                                    'Max Price',
                                    'Price Volatility'
                                ],
                                'Value': [
                                    f"${commodity_data['Price'].iloc[-1]:.2f}",
                                    f"${commodity_data['Price'].mean():.2f}",
                                    f"${commodity_data['Price'].std():.2f}",
                                    f"${commodity_data['Price'].min():.2f}",
                                    f"${commodity_data['Price'].max():.2f}",
                                    f"{(commodity_data['Price'].std() / commodity_data['Price'].mean()):.2%}"
                                ]
                            })
                            st.dataframe(stats, use_container_width=True)
                        
                        with viz_tab:
                            # Create price chart with moving averages
                            st.markdown("### Price Chart with Moving Averages")
                            
                            # Calculate moving averages
                            commodity_data['MA20'] = commodity_data['Price'].rolling(window=20).mean()
                            commodity_data['MA50'] = commodity_data['Price'].rolling(window=50).mean()
                            
                            # Create the chart using Plotly
                            import plotly.graph_objects as go
                            from plotly.subplots import make_subplots
                            
                            fig = make_subplots(rows=2, cols=1, 
                                              shared_xaxes=True,
                                              vertical_spacing=0.03,
                                              row_heights=[0.7, 0.3])
                            
                            # Price and MA lines
                            fig.add_trace(
                                go.Scatter(x=commodity_data['Date'], 
                                         y=commodity_data['Price'],
                                         name='Price',
                                         line=dict(color='#2563eb')),
                                row=1, col=1
                            )
                            
                            fig.add_trace(
                                go.Scatter(x=commodity_data['Date'],
                                         y=commodity_data['MA20'],
                                         name='20-day MA',
                                         line=dict(color='#f59e0b',
                                                 dash='dash')),
                                row=1, col=1
                            )
                            
                            fig.add_trace(
                                go.Scatter(x=commodity_data['Date'],
                                         y=commodity_data['MA50'],
                                         name='50-day MA',
                                         line=dict(color='#10b981',
                                                 dash='dash')),
                                row=1, col=1
                            )
                            
                            # Add daily returns
                            commodity_data['Returns'] = commodity_data['Price'].pct_change()
                            fig.add_trace(
                                go.Bar(x=commodity_data['Date'],
                                      y=commodity_data['Returns'],
                                      name='Daily Returns',
                                      marker_color='#3b82f6'),
                                row=2, col=1
                            )
                            
                            fig.update_layout(
                                height=600,
                                title=f"{selected_commodity} Price Analysis",
                                showlegend=True,
                                legend=dict(
                                    yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01
                                )
                            )
                            
                            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
                            fig.update_yaxes(title_text="Returns (%)", row=2, col=1)
                            # Shorter date labels and optional weekend breaks
                            fig.update_xaxes(tickformat='%b %d', tickangle=-30)
                            if hide_gaps:
                                fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
                            
                            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
                            
                    else:
                        st.error("No data available for selected commodity")
    
    with tab2:
        st.subheader("Chat with Commodity Expert")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about commodity markets..."):
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get context from current commodity data
            latest_data = df_data[df_data['Date'] == df_data['Date'].max()].copy()
            context = f"""
            Latest commodity prices and changes:
            {latest_data[['Commodities', 'Price', '%Day']].to_string()}
            """
            
            # Get response from ChatGPT
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chat_with_commodity_expert(client, prompt, context)
                    st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.error("Failed to load data. Please check your data files.")
