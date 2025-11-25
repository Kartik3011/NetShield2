from openai import OpenAI
import streamlit as st

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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" ,
  timeout=60.0
)
 
def trans(a):
   
    con = """You are an advanced language model tasked with creating a highly effective search query for a news API. 
    Your final output must consist only of clear, relevant, space-separated English keywords. 
    
    CRITICAL RULE: The final output must be a single phrase optimized for a news search engine. 
    1. Translate the core topic, main nouns, places, and numbers (e.g., India Air Pollution).
    2. Discard all video format terms, channel names, organization names not directly relevant to the news event, and specific titles (e.g., REMOVE 'IAS', 'NEXT IAS', 'Vlog', 'Unboxing', 'Boxer', 'Game', 'Explained').
    3. DO NOT use any quotes, punctuation, or Boolean operators (AND, OR, NOT). 
    4. The final output must contain a MAXIMUM of 10 keywords.

    Just return the keywords.
    The text to analyze is as follows:
    """ + str(a)

    completion = client.chat.completions.create(
    model="mistralai/mistral-7b-instruct-v0.3", # Using the larger model for better filtering
    messages=[{"role":"user","content":con}],
    temperature=0.2,
    top_p=0.7,
    max_tokens=1024,
    stream=True
    )
    ss=""

    for chunk in completion:
     if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
        ss+=chunk.choices[0].delta.content
    return ss
