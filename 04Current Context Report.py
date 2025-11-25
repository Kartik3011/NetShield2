import streamlit as st
import csv
from module import nextractor as nx 
import pandas as pd
from module import translate as tst
import os 
from module.nextractor import News
from typing import List
import re 
from concurrent.futures import ThreadPoolExecutor, TimeoutError

st.set_page_config(page_title="Actual Context Report", layout="wide", initial_sidebar_state="expanded")


st.markdown("""
    <style>
        /* 1. GAP REDUCTION & MAIN CONTAINER STYLING */
        .block-container {
            padding-top: 0rem !important; 
            padding-bottom: 0rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* 2. SIDEBAR BACKGROUND */
        [data-testid="stSidebar"] {
            background-color: #1f2937; /* Dark background remains for contrast */
            color: white;
        }

        /* 3. FIXED LOGO INJECTION (Top Left Sidebar) */
        [data-testid="stSidebar"]::before {
            content: "NetShield 🛡️";
            display: block;
            font-size: 26px;
            font-weight: bold;
            color: #ffffff;
            text-align: left;
            padding: 20px 0 10px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
            margin-bottom: 10px;
        }
        
        /* 4. SIDEBAR FOOTER (Navigation Text at Bottom) */
        [data-testid="stSidebar"]::after {
            content: "Use the sidebar to navigate through NetShield features.";
            position: absolute;
            bottom: 10px; 
            left: 0;
            right: 0;
            padding: 10px 15px;
            text-align: center;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.5); 
            z-index: 10000;
        }
        
        /* Custom style for the Description Box (MATCHING Content Forensic style) */
        .context-description-box {
            background-color: #333d47; /* Matching dark background */
            padding: 15px;
            border-radius: 5px;
            border-left: 5px solid #ffa500; /* Matching orange accent */
            margin-bottom: 30px; 
        }
        
        .context-description-box strong {
            font-size: 18px;
            display: block; 
            margin-bottom: 5px; 
            color: #ffffff; /* Matching light text color */
        }
        
        .context-description-box ul {
            margin: 5px 0 0 0; 
            color: #f0f0f0; /* Light text color for list items */
            padding-left: 20px;
            list-style-type: disc;
            font-size: 16px;
        }
        
        /* Custom style for article separator between articles in the expander */
        .article-separator {
            margin-top: 10px;
            margin-bottom: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.1); 
        }
    </style>
""", unsafe_allow_html=True)


st.markdown("""
    <div style="display: none;">
        NetShield 🛡️
    </div>
""", unsafe_allow_html=True)



st.title("Actual Context Report")


st.markdown("""
    <div class="context-description-box">
        <strong>Contextual Analysis Overview:</strong>
        <ul>
            <li>This page uses the video titles to search for related news articles from external web sources.</li>
            <li>The process involves translating the title (using LLMs).</li>
            <li>Videos that yield matching news articles are displayed below, providing a factual baseline against which the video content can be compared.</li>
        </ul>
    </div>
""", unsafe_allow_html=True)


# page logic
try:
    file_path = os.path.join(os.getcwd(), "video_data.csv") 
    
    if not os.path.exists(file_path):
        st.error("Data file (video_data.csv) not found. Please ensure data has been fetched on the previous analysis page.")
        st.stop()
        
    df = pd.read_csv(file_path) 
    
    # Check if expected columns exist or infer
    video_titles = df.iloc[:, df.columns.get_loc('Video Title')] if 'Video Title' in df.columns else df.iloc[:, 1]
    
    if video_titles.empty:
         st.warning("The data file is empty or missing expected column for video titles.")
         st.stop()


    video_title_list=[]
    newslist=[]
    
    st.subheader("Related Context Extraction Results")
    st.markdown("---")
    
    # Use enumerate to get index (k) and value (i)
    for k, i in enumerate(video_titles):
        final_query = None
        ns = None
        
        # --- Display video title with counter (k+1) ---
        st.markdown(f"### Video {k+1}: {i}") 
        
        # --- PHASE 1: QUERY GENERATION (LLM API) ---
        with st.spinner(f"Phase 1: Translating and building query for video {k+1}..."):
            try:
                # 1. Translate Title to get the core topic
                core_topic_query = tst.trans(i).strip()
                
                # 2. Clean the query robustly of commas, quotes, and multiple spaces
                cleaned_query_no_quotes = core_topic_query.replace('"', '').replace("'", "")
                cleaned_query_no_commas = re.sub(r'[,\n]', ' ', cleaned_query_no_quotes)
                keywords = re.sub(r'\s+', ' ', cleaned_query_no_commas).strip().split(' ')
                
                # 🛑 OR-SEARCH EXPANSION (Maximizes volume, filtering handles relevance) 🛑
                if len(keywords) > 2:
                    # Take the first 3 keywords OR the last 3 keywords to maximize retrieval volume
                    final_query = ' OR '.join(keywords[:3] + keywords[-3:])
                else:
                    # If the query is already short, use it as is
                    final_query = ' '.join(keywords)
                
               
            except Exception as e:
                # 🔴 CRASH HANDLING: If LLM fails, display the error and skip this video
                st.error(f"**[CRASH] Phase 1 (Translation/LLM) failed.** Check API key/Network.")
                st.exception(e) 
                st.markdown("---")
                continue # Move to the next video

        # --- PHASE 2: NEWS API CALL (SIMPLE AND STABLE) ---
        with st.spinner(f"Phase 2: Fetching news context via API for video {k+1}..."):
            try:
                # Direct synchronous API call
                ns = nx.get_news_list(final_query, limit=5) 
                
            except Exception as e:
                # 🔴 CRASH HANDLING: If API fails, display the error and skip this video
                st.error(f"**[CRASH] Phase 2 (News API) failed.** Check API keys or network connection.")
                st.exception(e) 
                st.markdown("---")
                continue # Move to the next video


        # --- PHASE 3: KEYWORD FILTERING AND DISPLAY ---
        filtered_news = []
        if ns:
            original_keywords = set(final_query.replace(' OR ', ' ').lower().split())
            
            scored_results = []
            for news_obj in ns:
                # Combine title and description for scoring
                text_to_check = (news_obj.headline + " " + news_obj.description).lower()
                
                # Calculate score based on original keywords present
                score = sum(1 for keyword in original_keywords if keyword in text_to_check)
                
                # Only keep articles that score above the relevance threshold (score >= 2)
                if score >= 2:
                    scored_results.append((score, news_obj))

            # Sort results by score (highest score first)
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            # Use the filtered and sorted list for display
            filtered_news = [item[1] for item in scored_results][:5]

        # --- Display Final Results ---
        if filtered_news:
            st.success(f"Context found! Total Articles Filtered: {len(filtered_news)}") 
            st.markdown("**Related News Articles (Click to expand):**")
            
            # ORGANIZED ARTICLE DISPLAY
            for idx, news_obj in enumerate(filtered_news):
                
                # Format date
                raw_date = news_obj.pubDate if news_obj.pubDate else 'N/A'
                date_published = raw_date.split('T')[0].split(' ')[0] if raw_date and 'T' in raw_date else raw_date
                
                with st.expander(f"**Article {idx + 1}:** {news_obj.headline}", expanded=False):
                    st.markdown(f"* **Source:** {news_obj.publisher}")
                    st.markdown(f"* **Date Published:** {date_published}") 
                    st.markdown(f"* **URL:** [View Full Article]({news_obj.url})")
                    
                    # Ensure unique key for the text area
                    unique_key = f"content_area_{news_obj.url}_{i}_{idx}"
                    
                    # Combine description and content for maximum displayed text
                    full_content = news_obj.description + "\n\n" + news_obj.content
                    
                    st.markdown(f"#### Article Content")
                    # Display the model's grounded summary
                    st.text_area(f"Content for {news_obj.headline[:50]}...", 
                                 full_content, # Display the combined content
                                 height=400, # Increased height for better reading
                                 key=unique_key)
                    

                # Separator is outside the expander
                if idx < len(filtered_news) - 1:
                     st.markdown('<div class="article-separator"></div>', unsafe_allow_html=True)

            # - Data Storage
            video_title_list.append(i)
            newslist.append(filtered_news)
        else:
             st.warning(f"No relevant context found. ")

        st.markdown("---") # Final separator after the entire video block


    # FINAL DATA STORAGE confirmation
    data={
       'video title':video_title_list,
       'news':newslist
    }
    
    if video_title_list:
        st.success(f"Contextual data extracted for {len(video_title_list)} videos.")


except FileNotFoundError:
    st.error("Critical error: Could not load data file.")
except Exception as e:
    # This catches errors outside the loop (like pandas loading)
    st.error(f"An unhandled application error occurred outside the loop: {e}. Check the logs for the full traceback.")
    st.exception(e)