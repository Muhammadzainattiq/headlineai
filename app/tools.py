
from typing import TypedDict
from app.ai.llm import llm
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
import os
from typing import Dict, List
from typing import Annotated
import operator
from app import config
os.environ['TAVILY_API_KEY'] = config.TAVILY_API_KEY
from langgraph.constants import Send

class SubState(TypedDict):
  query: str
  single_or_multiple:str
  tavily_news: List[Dict[str, str]]
  tavily_urls: List[str]
  scrapped_news: Annotated[list, operator.add]
  final_news: list[Dict[str, str]]

class UrlState(TypedDict):
  url: str

class News(TypedDict):
  news:str


def combine_news(state:SubState) -> list[dict]:
    """
    Combine tavily_news and scrapped_news into a final news list.

    Args:
        tavily_news (list[dict]): List of dictionaries containing 'url' and 'content'.
        scrapped_news (list[str]): List of scrapped news details corresponding to each URL.

    Returns:
        list[dict]: A combined list of dictionaries with 'url', 'content', and 'details'.
    """
    final_news = []

    # Ensure both lists have the same length before combining
    if len(state['tavily_news']) != len(state['scrapped_news']):
        raise ValueError("The length of tavily_news and scrapped_news must be the same.")

    # Iterate over both lists and combine them into a single list of dictionaries
    for i in range(len(state['tavily_news'])):
        final_news.append({
            "url": state['tavily_news'][i]['url'],
            "content": state['tavily_news'][i]['content'],
            "details": state['scrapped_news'][i]
        })

    return {"final_news": final_news}




def web_loader(state: UrlState) -> list[News]:
    """
    Retrieve the full content of a web page, article, or blog post from the given URL.
    This function uses the WebBaseLoader to fetch and extract the entire content of the web
    page and returns the cleaned textual content by removing unnecessary spaces and
    excessive newlines.

    Args:
        state (UrlState): The state containing the URL of the web page.

    Returns:
        list[News]: A list containing a dictionary with the cleaned text content of the web page.
    """
    loader = WebBaseLoader(state['url'])
    data = loader.load()
    text = data[0].page_content

    # Step 1: Replace multiple newlines and tabs with a single space to remove excessive blank spaces
    cleaned_text = text.replace('\n', ' ').replace('\t', ' ')

    # Step 2: Replace multiple consecutive spaces with a single space
    cleaned_text = " ".join(cleaned_text.split())

    # Step 3: Optionally, strip any leading or trailing spaces
    cleaned_text = cleaned_text.strip()

    return {"scrapped_news": [cleaned_text]}


def tavily_search(state: SubState) -> SubState:
    """
    Perform a web search for news articles based on the user's query.

    This function utilizes the TavilySearchResults tool to search for news articles
    related to the given query. It retrieves up to 10 results and returns the relevant
    information, including article content, images, and additional context where available.

    Args:
        state (State): The state containing the search query input provided by the user.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary contains information
        about a single news article. The details may include the article content, any
        associated images, and additional contextual information (if available).
    """
    max_results = 3
    if state["single_or_multiple"] == "single":
        max_results = 2
    elif state["single_or_multiple"] == "multiple":
        max_results = 4
    tool = TavilySearchResults(
        max_results=max_results,
        include_answer=True,
        include_raw_content=True,
        include_images=True,

    )
    response = tool.invoke({'query': state['query']})

    urls = [item['url'] for item in response]

    return {"tavily_news": response, 'tavily_urls': urls}


def continue_to_url_loads(state: SubState):
    return [Send("web_loader", {"url": u}) for u in state["tavily_urls"]]



def check_single_or_multiple(state: SubState) ->SubState:
  prompt = """You are an assistant responsible for analyzing user queries about news. Your task is to determine whether the query pertains to a single specific news item or multiple potential news items.
Respond with only one word: "single" or "multiple", without any additional information.

Here is the user query: {query}

**Examples:**
1. User Query: "What happened in the latest match between Pakistan and England?"
   - Response: single
2. User Query: "Can you give me all the latest updates on climate change?"
   - Response: multiple
3. User Query: "Tell me about the recent policy changes in the education sector."
   - Response: single
4. User Query: "What are the current headlines in sports and entertainment?"
   - Response: multiple
5. User Query: "Who won the last football world cup?"
   - Response: single
6. User Query: "What are the latest news articles about tech innovations?"
   - Response: multiple>
"""
  formatted_prompt = prompt.format(query = state['query'])
  response = llm.invoke(formatted_prompt).content.strip()
  return {"single_or_multiple": response}