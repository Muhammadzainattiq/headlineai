import requests
from langgraph.graph import MessagesState
from langchain_core.messages import  HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import MessagesState
import requests
import os
from datetime import datetime
from IPython.display import Image, display
from langchain_openai import ChatOpenAI
from app.ai.sub_agent import compile_sub_agent
from app.tools import SubState, llm

os.environ['TAVILY_API_KEY'] = "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"


def compile_main_agent(compiled_sub_agent):
    def fetch_news(query:str) ->str:
        """
            Perform a search for news articles based on the user's query.

            This function utilizes the TavilySearchResults tool, web scrapers and different News APIs to search for news articles
            related to the given query. It retrieves up to 5 results and returns the relevant
            information, including article content, images, and additional context where available.

            Arg:
                query (str): The search query input provided by the user, representing the topic
                or keywords for which news articles are being requested.

            Returns:
                list[dict]: A list of dictionaries, where each dictionary contains information
                about news articles. The details may include the url which which be the url of the source, content and details.
            """
        initial_state = SubState(
            query= query,
            single_or_multiple = "",
            tavily_news = [],
            tavily_urls = [],
            scrapped_news = [],
            final_news = []
        )
        messages = compiled_sub_agent.invoke(initial_state)
        return messages['final_news']

    today = datetime.today()
    date = today.strftime("%B %d, %Y")

    sys_msg = SystemMessage(content=f"""
    You are a news assistant, tasked with helping users find the most relevant news articles, whether they are recent or from the past, based on their queries. You will respond with the clarity and precision of a seasoned news reporter, maintaining an engaging and authoritative tone.

    ### Responsibilities:
    - **Fetch News Articles**: Utilize the **fetch_news** tool to conduct a web search for up to 5 articles related to the user's query. Construct the search query thoughtfully. If the user asks for the latest news, include today's date {date} in your search to ensure the results are timely. Always refine the query by adding additional context or keywords to enhance clarity and maximize the relevance of the articles retrieved. This tool will return the following for each article:
    - **URL**: Direct link to the article.
    - **Content**: A brief snippet of the article's main idea.
    - **Details**: Comprehensive information, including full article content, images, and additional context when available.

    ### Structure of News:
    - **Titles**: Extract or generate clear, concise titles for each article.
    - **Details**: Present the full content of the articles without omitting any information, including key facts, images, and additional relevant details.
    - **Source URL**: Clearly link to the article's source for easy access.

    ### Best Practices:
    - Organize responses using structured headings and bullet points for clarity.
    - Ensure all articles are well-formatted and complete, providing users with a thorough understanding of the topic. Don't miss any information. 
    - Maintain an informative and neutral tone throughout your responses.
    - If the first attempt does not yield sufficient details, refine the search and scrape for additional information.
    Always leverage the **fetch_news** tool to provide users with detailed, up-to-date news articles tailored to their interests. Do not claim a lack of access to real-time news; consistently utilize the **fetch_news** tool.
    """)


    # Define the LLM with tools
    tools = [fetch_news]
    llm_with_tools = llm.bind_tools(tools)

    # Node definition
    def assistant(state: MessagesState):
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"][-6:])]}

    builder = StateGraph(MessagesState)


    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")

    memory = MemorySaver()
    main_agent = builder.compile(checkpointer=memory)
    return main_agent


def call_main_agent(query: str, thread_id: str, main_agent):
    """
    Function to fetch detailed news articles based on the user's query
    and a thread ID for tracking purposes.
    
    Args:
        query (str): The search query provided by the user.
        thread_id (str): The ID of the thread for maintaining conversation context.
    
    Returns:
        None: The function will print out the messages with detailed articles.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Create a HumanMessage using the query input
    messages = [HumanMessage(content=f"{query}")]
    
    # Call the agent with the messages and thread-specific config
    response = main_agent.invoke({"messages": messages}, config)
    
    return response

