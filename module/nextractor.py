import requests
from bs4 import BeautifulSoup
import json
from typing import List
import streamlit as st
from openai import OpenAI

# =========================================================
# STREAMLIT SECRETS CHECK
# =========================================================

required_secrets = ["NVIDIA_API_KEY", "NEWS_API_KEY"]

missing_secrets = [key for key in required_secrets if key not in st.secrets]

if missing_secrets:
    st.error(f"Missing Streamlit secrets: {missing_secrets}")
    st.stop()

# =========================================================
# NVIDIA CLIENT
# =========================================================

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=st.secrets["NVIDIA_API_KEY"],
    timeout=120
)

# =========================================================
# NEWSAPI CONFIG
# =========================================================

NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

NEWS_API_ENDPOINT = "https://newsapi.org/v2/everything"

# =========================================================
# DATA CLASS
# =========================================================

class News:
    def __init__(
        self,
        headline,
        url,
        publisher,
        description="",
        content="",
        pubDate=""
    ):
        self.headline = headline
        self.url = url
        self.publisher = publisher
        self.description = description
        self.content = content
        self.pubDate = pubDate

    def __repr__(self):
        return (
            f"headline={self.headline}\n"
            f"url={self.url}\n"
            f"publisher={self.publisher}\n"
            f"description={self.description}\n"
            f"content={self.content}\n"
            f"pubDate={self.pubDate}"
        )

# =========================================================
# GOOGLE ARTICLE CONTENT EXTRACTION
# =========================================================

def _extract_google_content(url):

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            allow_redirects=True
        )

        if response.status_code != 200:
            return {}

        soup = BeautifulSoup(response.content, "html.parser")

        masterjson = {}

        scripts = soup.find_all(
            "script",
            {"type": "application/ld+json"}
        )

        for script in scripts:

            if not script.string:
                continue

            try:
                data = json.loads(script.string)

                if isinstance(data, dict):
                    masterjson.update(data)

            except Exception:
                continue

        return masterjson

    except Exception as e:
        print(f"Google content extraction error: {e}")
        return {}

# =========================================================
# GOOGLE NEWS SCRAPER
# =========================================================

def _scrape_google_news(query: str, limit: int = 5) -> List[News]:

    query = query.replace(" ", "%20")

    url = (
        f"https://news.google.com/search?"
        f"q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    )

    results = []

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, "html.parser")

        articles = soup.find_all("article")

        for article in articles[:limit]:

            try:
                title_tag = article.find("a")

                if not title_tag:
                    continue

                headline = title_tag.text.strip()

                partial_link = title_tag.get("href")

                if not partial_link:
                    continue

                if partial_link.startswith("./"):
                    full_link = (
                        "https://news.google.com/"
                        + partial_link[2:]
                    )
                else:
                    full_link = partial_link

                article_content = _extract_google_content(full_link)

                results.append(
                    News(
                        headline=headline,
                        url=full_link,
                        publisher="Google News",
                        description=article_content.get(
                            "description",
                            ""
                        ),
                        content=article_content.get(
                            "articleBody",
                            ""
                        ),
                        pubDate=article_content.get(
                            "datePublished",
                            ""
                        )
                    )
                )

            except Exception as e:
                print(f"Article parse error: {e}")

        return results

    except Exception as e:
        print(f"Google News scrape error: {e}")
        return []

# =========================================================
# SCRAPE FULL ARTICLE
# =========================================================

def _scrape_full_article_body(url: str) -> str:

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        article_block = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div")
        )

        if article_block:
            paragraphs = article_block.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        full_text = " ".join(
            [
                p.get_text(strip=True)
                for p in paragraphs
                if len(p.get_text(strip=True).split()) > 10
            ]
        )

        return full_text.strip()

    except Exception as e:
        print(f"Article scrape error: {e}")
        return ""

# =========================================================
# NEWSAPI FETCH
# =========================================================

def _api_fetch_articles(query: str, limit: int = 5) -> List[News]:

    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": limit
    }

    results = []

    try:
        response = requests.get(
            NEWS_API_ENDPOINT,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if data["status"] == "ok":

            for article in data["articles"]:

                url = article.get("url", "")

                full_content = _scrape_full_article_body(url)

                results.append(
                    News(
                        headline=article.get("title", ""),
                        url=url,
                        publisher=article.get(
                            "source",
                            {}
                        ).get("name", ""),
                        description=article.get(
                            "description",
                            ""
                        ),
                        content=(
                            full_content
                            or article.get("content", "")
                        ),
                        pubDate=article.get(
                            "publishedAt",
                            ""
                        )
                    )
                )

        return results

    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []

# =========================================================
# MAIN NEWS FUNCTION
# =========================================================

def get_news_list(query: str, limit: int = 5):

    print(f"Searching Google News for: {query}")

    google_results = _scrape_google_news(query, limit)

    if google_results:
        return google_results

    print("Google News failed. Using NewsAPI fallback.")

    api_results = _api_fetch_articles(query, limit)

    return api_results

# =========================================================
# NVIDIA SUMMARIZER
# =========================================================

def summarize_text(text):

    if not text.strip():
        return "No text available for summarization."

    try:

        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that "
                        "summarizes news articles."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Summarize this article:\n\n{text}"
                    )
                }
            ],
            temperature=0.3,
            max_tokens=300
        )

        return response.choices[0].message.content

    except Exception as e:

        import traceback

        traceback.print_exc()

        return f"Summarization failed: {str(e)}"

# =========================================================
# STREAMLIT UI
# =========================================================

st.title("NetShield Context Analyzer")

query = st.text_input(
    "Enter video title or topic"
)

if st.button("Analyze"):

    if not query.strip():
        st.warning("Please enter a query.")
        st.stop()

    with st.spinner("Extracting related context..."):

        articles = get_news_list(query)

    if not articles:
        st.error("No articles found.")
        st.stop()

    for idx, article in enumerate(articles, start=1):

        st.subheader(f"Article {idx}")

        st.write(f"### {article.headline}")

        st.write(f"Publisher: {article.publisher}")

        st.write(f"Published: {article.pubDate}")

        st.write(f"URL: {article.url}")

        content = (
            article.content
            or article.description
        )

        if not content:
            st.warning("No article content found.")
            continue

        with st.spinner("Summarizing article..."):

            summary = summarize_text(content)

        st.success(summary)

        st.divider()
