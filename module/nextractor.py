import requests
import os 
from typing import List, Dict, Any


NEWS_API_KEY = "c69c9e3ea4f745ab8aa85e23da919738"
NEWS_API_ENDPOINT = "https://newsapi.org/v2/everything"
# =========================================================================

# Define the News class
class News:
    def __init__(self, headline, url, publisher, description="", content="", pubDate=""):
        self.headline = headline
        self.url = url
        self.publisher = publisher
        self.description = description
        self.content = content
        self.pubDate = pubDate
    
    def __repr__(self):
        return (f"headline={self.headline},\n url={self.url},\n "
                f"publisher={self.publisher},\n description={self.description},\n "
                f"content={self.content},\n pubDate={self.pubDate}\n")

# --- Main API Scraper Function (Synchronous) ---
def get_news_list(query: str, limit: int = 5) -> List[News]:
    
    # 1. Define API Call Parameters
    params = {
        'q': query,
        'apiKey': NEWS_API_KEY,
        'sortBy': 'relevancy',
        'language': 'en', # Focus on English results for LLM comparison
        'pageSize': limit
    }
    
    results = []
    
    try:
        # 2. Make simple synchronous API request
        response = requests.get(NEWS_API_ENDPOINT, params=params, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        
        # 3. Process API results into your News class objects
        if data['status'] == 'ok' and data['articles']:
            for article in data['articles']:
                results.append(
                    News(
                        headline=article.get('title', 'N/A'),
                        url=article.get('url', 'N/A'),
                        publisher=article.get('source', {}).get('name', 'N/A'),
                        description=article.get('description', ''),
                        content=article.get('content', ''), # API often provides summary/content snippet
                        pubDate=article.get('publishedAt', 'N/A')
                    )
                )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from NewsAPI: {e}")
    except Exception as e:
        print(f"General error processing API response: {e}")
        
    return results

# Note: The original Playwright helper functions (extract_article_content, _get_news_list_async) 
# are entirely removed as they are no longer necessary.
