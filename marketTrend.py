from azuremodels import llm, embeddings


from pydantic import BaseModel
from typing import List

class GeneratedQuestions(BaseModel):
    questions: List[str]

prompt = """You are a financial research agent. Your task is to generate 10 sharp, analytical questions that help extract ONLY those details which impact financial markets, asset pricing, risk sentiment, regulatory direction, and investment allocations.

Input Topic: {USER_TOPIC}

Generate questions that:
1. Focus on measurable financial impacts.
2. Help determine current market conditions in equity, debt, commodities, real estate, and crypto.
3. Extract signals relevant to inflation, interest rates, risk appetite, liquidity, geopolitics, regulatory stance, taxation, supply-demand cycles, institutional flows, corporate earnings, and long-term structural trends.
4. Are specific enough to allow extraction of facts from reliable news sources or research reports.
5. Avoid vague social, medical, humanitarian, or philosophical aspects unless they have direct financial implications.

Sample framework for question types:
- Central bank policy stance
- Inflation projections
- Fiscal or taxation shifts
- Institutional equity/debt flows
- Commodity cycle behavior
- Real estate liquidity, demand, or yields
- Credit conditions and bond yield movements
- Geopolitical risk triggers
- Regulatory tightening or easing
- Corporate earnings health
- Sector rotation trends

Output Format:
[
  "question-1",
  "question-2",
  ...
  "question-10"
]

The questions MUST depend on the given topic.

Examples:
If topic is "COVID pandemic", ask things like:
- "How did pandemic restrictions affect corporate earnings, layoffs, and demand recovery?"
- "What emergency rate cuts, liquidity injections, or fiscal stimulus were deployed by central banks/governments?"

If topic is "Cross-border military conflict":
- "How are defense budgets changing?"
- "What sanctions are affecting currency flows, commodity pricing, and corporate earnings exposure?"

Now generate 10 such questions for the topic above.
"""
USER_TOPIC = "Current Market Trend"

prompt.format(USER_TOPIC=USER_TOPIC)

structured_llm = llm.with_structured_output(GeneratedQuestions)

questions = structured_llm.invoke(prompt)
questions = questions.questions
# print(type(questions))
# print(questions)
import os

os.environ["TAVILY_API_KEY"] = "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"

from langchain_community.retrievers import TavilySearchAPIRetriever

serachRe = TavilySearchAPIRetriever(k=2,    
    search_depth="advanced",
    # include_images=True,
    news=True,
    include_domains=[
        "economictimes.indiatimes.com",
        "moneycontrol.com",
        "business-standard.com",
        "bloomberg.com",
        "livemint.com",
        "finance.yahoo.com",
        "cnbc.com",
        "nse.com",
        "bse.com",
    ])
results = []
for query in questions:
    res = serachRe.invoke(query)
    results.append(res)
newslist = []
for i in results:
    newslist.append(i[0].page_content)
    newslist.append(i[1].page_content)


trend_analyzer_agent = """You are analyzing global and domestic financial market news to understand macro conditions. 

Given the articles provided, produce a single concise summary (max 220 words) that captures only macro-economic signals related to:
- inflation direction
- central bank stance on interest rates
- liquidity conditions in credit markets
- corporate earnings strength or weakness
- geopolitical conflicts or sanctions affecting markets
- commodity cycles (especially crude and gold)
- regulatory actions affecting risk assets
- recession risks based on GDP, employment, and consumption trends
- investor risk sentiment, valuation trend, and capital flows

Focus on extracting concrete signals, trends, and directional outlook. 
Do NOT include generic investment education, definitions, individual company news, or product info.

Output should be neutral, fact-pattern based, and capture the economic tone. Use language that naturally includes phrases like tightening, loosening, stimulus, risk-off, rate hike, inflation surge, liquidity squeeze, slowdown, earnings expansion, regulatory crackdown, commodity strength, or similar.

Return ONLY the summary text. No bullet points, no explanations, no headers.
{newslist}
"""
trend_analyzer_agent = trend_analyzer_agent.format(newslist=newslist)
summary = llm.invoke(trend_analyzer_agent)
summary  = summary.content
from langchain_community.vectorstores import Chroma

PERSIST_DIR = "marketCondtions"  # folder name on disk

vectorstore = Chroma(
    embedding_function=embeddings,
    collection_name="marketCondtions",
    persist_directory="marketCondtions"
)

db = vectorstore.as_retriever()
print(summary)
res = db.invoke(summary)
print(res)
import pandas as pd

def apply_instrument_deltas(strategy_csv, output_csv, deltas: dict):
    """
    Applies instrument-level deltas directly and normalizes totals back to 100%.
    
    Assumptions:
    - strategy.csv contains all instrument columns as numeric weights summing to 100.
    - 'Client Type' remains untouched.
    - deltas dict keys must match exact CSV column names.
    """
    df = pd.read_csv(strategy_csv)

    # instrument columns = all except Client Type
    instrument_cols = [c for c in df.columns if c != "Client Type"]

    # Validate column presence
    missing = [k for k in deltas if k not in instrument_cols]
    if missing:
        raise ValueError(f"Delta keys not found in strategy columns: {missing}")

    # ---- Apply deltas ----
    for inst_col in instrument_cols:
        if inst_col in deltas:
            base = df[inst_col].astype(float)
            pct = deltas[inst_col]
            df[f"{inst_col}_adj"] = base + (base * pct/100.0)
        else:
            df[f"{inst_col}_adj"] = df[inst_col].astype(float)

    adj_cols = [f"{c}_adj" for c in instrument_cols]

    # ---- Normalize so total remains 100 ----
    df["row_total"] = df[adj_cols].sum(axis=1)
    df["row_total"] = df["row_total"].replace(0, 1.0)

    for col in instrument_cols:
        df[f"{col}_final"] = df[f"{col}_adj"] / df["row_total"] * 100.0

    # ---- Keep CLEAN output ----
    final_cols = ["Client Type"] + [f"{c}_final" for c in instrument_cols]

    df[final_cols].to_csv(output_csv, index=False)
    return df[final_cols]

deltas = res[0].metadata

updated = apply_instrument_deltas(
    "generalStrategyStandard.csv",
    "strategy_updated.csv",
    deltas
)

print(updated)

