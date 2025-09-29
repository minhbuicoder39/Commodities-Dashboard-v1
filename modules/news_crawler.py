import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

def fetch_spglobal_news():
    """
    Fetch news from S&P Global Commodity Insights
    """
    url = "https://www.spglobal.com/commodity-insights/en/news-research/latest-news"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_items = []
        # Specific selectors will need to be adjusted based on the website's structure
        articles = soup.find_all('article', class_='search-result')
        
        for article in articles:
            try:
                title = article.find('h3').text.strip()
                date_str = article.find('time').get('datetime', '')
                link = article.find('a')['href']
                if not link.startswith('http'):
                    link = 'https://www.spglobal.com' + link
                
                # Filter for relevant keywords
                keywords = ['steel', 'iron ore', 'met coal', 'metallurgical coal', 
                          'coking coal', 'hrc', 'long steel']
                
                if any(keyword in title.lower() for keyword in keywords):
                    news_items.append({
                        'title': title,
                        'date': pd.to_datetime(date_str),
                        'source': 'S&P Global',
                        'link': link
                    })
            except Exception as e:
                print(f"Error processing article: {e}")
                continue
        
        return pd.DataFrame(news_items)
    except Exception as e:
        print(f"Error fetching S&P Global news: {e}")
        return pd.DataFrame()

def fetch_fastmarkets_news():
    """
    Fetch news from Fastmarkets
    """
    url = "https://www.fastmarkets.com/metal-bulletin-is-part-of-fastmarkets"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_items = []
        # Specific selectors will need to be adjusted based on the website's structure
        articles = soup.find_all('article')
        
        for article in articles:
            try:
                title = article.find('h2').text.strip()
                date_str = article.find('time').get('datetime', '')
                link = article.find('a')['href']
                if not link.startswith('http'):
                    link = 'https://www.fastmarkets.com' + link
                
                # Filter for relevant keywords
                keywords = ['steel', 'iron ore', 'met coal', 'metallurgical coal', 
                          'coking coal', 'hrc', 'long steel']
                
                if any(keyword in title.lower() for keyword in keywords):
                    news_items.append({
                        'title': title,
                        'date': pd.to_datetime(date_str),
                        'source': 'Fastmarkets',
                        'link': link
                    })
            except Exception as e:
                print(f"Error processing article: {e}")
                continue
        
        return pd.DataFrame(news_items)
    except Exception as e:
        print(f"Error fetching Fastmarkets news: {e}")
        return pd.DataFrame()

def get_steel_news():
    """
    Combine news from all sources and return sorted by date
    """
    # Fetch news from all sources
    spglobal_news = fetch_spglobal_news()
    fastmarkets_news = fetch_fastmarkets_news()
    
    # Combine all news sources
    all_news = pd.concat([spglobal_news, fastmarkets_news], ignore_index=True)
    
    # Sort by date, most recent first
    if not all_news.empty:
        all_news = all_news.sort_values('date', ascending=False)
    
    return all_news
