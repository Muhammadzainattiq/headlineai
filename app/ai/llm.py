from langchain_openai import ChatOpenAI
from app import config
llm = ChatOpenAI(
      model="gpt-4o",
      temperature=0.7,
      max_tokens=None,
      timeout=None,
      max_retries=2,
      api_key=config.OPENAI_API_KEY)