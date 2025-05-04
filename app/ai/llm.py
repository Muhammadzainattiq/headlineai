from langchain_google_genai import ChatGoogleGenerativeAI
from app import config
llm = ChatGoogleGenerativeAI(
      model="gemini-2.0-flash",
      temperature=0.7,
      api_key=config.GOOGLE_API_KEY)