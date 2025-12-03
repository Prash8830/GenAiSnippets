import os

os.environ["TAVILY_API_KEY"] = "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"
from langchain_community.retrievers import TavilySearchAPIRetriever

retriever = TavilySearchAPIRetriever(k=10,    
    search_depth="advanced",
    include_images=True,
    include_domains=[
        "tripadvisor.com",
        "lonelyplanet.com",
        "booking.com",
        "airbnb.com",
        "expedia.com",
        "kayak.com",
        "skyscanner.com",
        "travelandleisure.com",
        "conde nast.com",
        "nomadicmatt.com"
    ])
query = "best hotel in chennai"

res = retriever.invoke(query)
