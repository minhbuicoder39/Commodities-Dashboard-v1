import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data(ttl=3600)
def calculate_price_changes(df_data, df_list, selected_date):
    """
    Calculates price changes and key metrics based on a selected date.
    """
    if df_data is None or df_list is None:
        return pd.DataFrame()

    # Convert selected_date to Pandas Timestamp for robust comparison
    selected_date = pd.to_datetime(selected_date)

    # --- Initial Data Snapshot ---
    df_snapshot = df_data[df_data['Date'] <= selected_date].copy()
    if df_snapshot.empty:
        return pd.DataFrame()

    # --- Get Current Price (most recent price on or before selected_date) ---
    current_data = df_snapshot.sort_values(by=['Commodities', 'Date'], ascending=[True, False])
    current_data = current_data.drop_duplicates(subset='Commodities', keep='first').set_index('Commodities')

    # --- Calculate Price at different past points ---
    end_of_last_day = selected_date - pd.DateOffset(days=1)
    end_of_last_week = selected_date - pd.offsets.Week(weekday=4)
    end_of_last_month = selected_date - pd.offsets.MonthEnd(1)
    end_of_last_quarter = selected_date - pd.offsets.QuarterEnd(1)
    end_of_last_year = selected_date - pd.offsets.YearEnd(1)

    def get_price_at(date_cutoff):
        past_data = df_snapshot[df_snapshot['Date'] <= date_cutoff]
        if past_data.empty:
            return pd.Series(dtype=float)
        return past_data.sort_values('Date', ascending=False).drop_duplicates(subset='Commodities', keep='first').set_index('Commodities')['Price']

    # --- Calculate Percentage Changes ---
    current_data['%Day'] = current_data['Price'].div(get_price_at(end_of_last_day)).subtract(1)
    current_data['%Week'] = current_data['Price'].div(get_price_at(end_of_last_week)).subtract(1)
    current_data['%Month'] = current_data['Price'].div(get_price_at(end_of_last_month)).subtract(1)
    current_data['%Quarter'] = current_data['Price'].div(get_price_at(end_of_last_quarter)).subtract(1)
    current_data['%YTD'] = current_data['Price'].div(get_price_at(end_of_last_year)).subtract(1)

    # --- Calculate New Metrics ---
    fifty_two_weeks_ago = selected_date - pd.DateOffset(weeks=52)
    df_52w = df_snapshot[df_snapshot['Date'] >= fifty_two_weeks_ago]
    stats_52w = df_52w.groupby('Commodities')['Price'].agg(['max', 'min']).rename(columns={'max': '52W High', 'min': '52W Low'})

    thirty_days_ago = selected_date - pd.DateOffset(days=30)
    df_30d = df_snapshot[df_snapshot['Date'] >= thirty_days_ago]
    avg_30d = df_30d.groupby('Commodities')['Price'].mean().rename('30D Avg')
    
    current_data['Change type'] = np.where(current_data['%Week'] > 0, 'Positive', np.where(current_data['%Week'] < 0, 'Negative', 'Neutral'))

    # --- ROBUST MERGE SECTION ---
    current_data.rename(columns={'Price': 'Current Price'}, inplace=True)
    final_df = current_data.join(stats_52w, how='left').join(avg_30d, how='left')
    final_df.reset_index(inplace=True) # Turn 'Commodities' index into a column

    # Prepare df_list for a clean merge
    list_subset = df_list[['Commodities', 'Sector', 'Nation', 'Impact']].drop_duplicates(subset='Commodities', keep='first').copy()

    # Defensive cleaning: ensure join keys are clean strings
    final_df['Commodities'] = final_df['Commodities'].astype(str).str.strip()
    list_subset['Commodities'] = list_subset['Commodities'].astype(str).str.strip()
    
    # Perform a robust left merge
    final_df = pd.merge(final_df, list_subset, on='Commodities', how='left')

    # --- Define and order final columns for display ---
    display_cols = [
        'Commodities', 'Sector', 'Nation', 'Current Price',
        '%Day', '%Week', '%Month', '%Quarter', '%YTD',
        '30D Avg', '52W High', '52W Low',
        'Change type', 'Impact'
    ]
    
    for col in display_cols:
        if col not in final_df.columns:
            final_df[col] = np.nan

    return final_df[display_cols]
