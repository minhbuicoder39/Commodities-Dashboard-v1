import openai
import streamlit as st

def init_openai_client():
    """Initialize OpenAI client with API key from Streamlit secrets"""
    if 'OPENAI_API_KEY' not in st.secrets:
        st.error('OpenAI API key not found in secrets. Please add it to your secrets.toml file.')
        return None
    
    client = openai.OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
    return client

def get_commodity_analysis(client, commodity_data, commodity_name, analysis_type="comprehensive"):
    """Get ChatGPT analysis for a specific commodity with different analysis types"""
    if client is None:
        return {"error": "OpenAI client not initialized"}
    
    try:
        # Calculate additional metrics
        latest_price = commodity_data['Price'].iloc[-1]
        avg_price = commodity_data['Price'].mean()
        std_price = commodity_data['Price'].std()
        max_price = commodity_data['Price'].max()
        min_price = commodity_data['Price'].min()
        price_volatility = std_price / avg_price
        
        # Define different analysis types
        analysis_prompts = {
            "comprehensive": f"""
            Analyze the following commodity data for {commodity_name}:
            Latest price: ${latest_price:.2f}
            Average price: ${avg_price:.2f}
            Price volatility: {price_volatility:.2%}
            52-week range: ${min_price:.2f} - ${max_price:.2f}
            
            Price changes:
            1D: {f"{commodity_data['%Day'].iloc[-1]:.2%}" if '%Day' in commodity_data.columns else "N/A"}
            1W: {f"{commodity_data['%Week'].iloc[-1]:.2%}" if '%Week' in commodity_data.columns else "N/A"}
            1M: {f"{commodity_data['%Month'].iloc[-1]:.2%}" if '%Month' in commodity_data.columns else "N/A"}
            YTD: {f"{commodity_data['%YTD'].iloc[-1]:.2%}" if '%YTD' in commodity_data.columns else "N/A"}

            Please provide:
            1. Comprehensive market analysis
            2. Key factors affecting the price
            3. Technical analysis insights
            4. Short-term and medium-term outlook
            5. Key price levels to watch
            Keep the response structured and actionable.
            """,
            
            "technical": f"""
            Provide technical analysis for {commodity_name} based on:
            Current price: ${latest_price:.2f}
            Moving averages: 
            - Price vs Average: {(latest_price/avg_price - 1):.2%}
            - Volatility: {price_volatility:.2%}
            - Price Range: ${min_price:.2f} - ${max_price:.2f}
            
            Focus on:
            1. Technical indicators and patterns
            2. Support and resistance levels
            3. Trading volume analysis
            4. Price momentum
            5. Risk levels
            """,
            
            "risk": f"""
            Analyze risk factors for {commodity_name}:
            Current price: ${latest_price:.2f}
            Volatility: {price_volatility:.2%}
            Price deviation from mean: {(latest_price/avg_price - 1):.2%}
            
            Provide:
            1. Key risk factors
            2. Market exposure assessment
            3. Volatility analysis
            4. Correlation with major markets
            5. Risk mitigation strategies
            """
        }

        # Get response from ChatGPT
        selected_prompt = analysis_prompts.get(analysis_type, analysis_prompts["comprehensive"])
        
        response = client.chat.completions.create(
            model="gpt-4",  # or gpt-3.5-turbo
            messages=[
                {"role": "system", "content": "You are a commodity market expert providing concise, data-driven analysis."},
                {"role": "user", "content": selected_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        # Create response dict with content and token usage
        analysis_response = {
            'content': response.choices[0].message.content,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'estimated_cost': f"${(response.usage.total_tokens / 1000) * 0.03:.4f}"  # $0.03 per 1K tokens
            }
        }

        return analysis_response

    except Exception as e:
        return f"Error getting analysis: {str(e)}"

def chat_with_commodity_expert(client, user_question, commodity_context=None):
    """Chat with GPT about commodities with context"""
    if client is None:
        return "Error: OpenAI client not initialized"
    
    try:
        # Prepare the system message with context
        system_message = """You are a commodity market expert assistant. 
        Provide clear, concise, and accurate information about commodity markets, 
        trends, and analysis. Use data when available to support your responses."""

        messages = [{"role": "system", "content": system_message}]
        
        # Add context if available
        if commodity_context:
            messages.append({
                "role": "system", 
                "content": f"Current context: {commodity_context}"
            })
        
        # Add user question
        messages.append({"role": "user", "content": user_question})

        # Get response from ChatGPT
        response = client.chat.completions.create(
            model="gpt-4",  # or gpt-3.5-turbo
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"
