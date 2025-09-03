import streamlit as st
import pandas as pd
import os

@st.cache_data(ttl=3600)
def load_data():
    """
    Loads and preprocesses data from CSV files.
    This function is cached to improve performance.
    """
    data_path = os.path.join("data", "Data.csv")
    list_path = os.path.join("data", "Commo_list.csv")

    try:
        df_data = pd.read_csv(data_path)
        df_list = pd.read_csv(list_path)

        # --- PREPROCESSING ---
        # 1. Clean column names by stripping whitespace
        df_data.columns = [col.strip() for col in df_data.columns]
        df_list.columns = [col.strip() for col in df_list.columns]

        # 2. KEY FIX: Clean the 'Commodities' column in BOTH dataframes immediately upon loading
        if 'Commodities' in df_data.columns:
            df_data['Commodities'] = df_data['Commodities'].astype(str).str.strip()
        if 'Commodities' in df_list.columns:
            df_list['Commodities'] = df_list['Commodities'].astype(str).str.strip()

        # 3. Clean 'Price' column
        if 'Price' in df_data.columns:
            df_data['Price'] = df_data['Price'].astype(str).str.replace(',', '').str.strip()
            df_data['Price'] = pd.to_numeric(df_data['Price'], errors='coerce')

        # 4. Convert 'Date' column to datetime objects
        if 'Date' in df_data.columns:
            df_data['Date'] = pd.to_datetime(df_data['Date'], errors='coerce')
        
        # 5. Drop rows where essential data is missing
        df_data.dropna(subset=['Date', 'Commodities', 'Price'], inplace=True)
        df_list.dropna(subset=['Commodities'], inplace=True)

        return df_data, df_list
    except FileNotFoundError:
        st.error(f"Error: Make sure `Data.csv` and `Commo_list.csv` are in the 'data' directory.")
        return None, None
