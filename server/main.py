import json
import numpy as np
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List

from utils.rag import enhanced_retrieval, generate_queries, retrieval
from utils.data import data_store
from datetime import datetime
from fastapi.responses import StreamingResponse

import nltk
nltk.download('punkt')
import asyncio
from utils.client_setup import client


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

messages_history = []

_rag_query_text = """
You are an AI assistant helps answering users' questions about scholars and their papers. 
You are given a user question, and please write clean, concise and accurate answer to the question like what are the related research being done. 
You will be given a set of related contexts to the question, each starting with a reference number like [[citation:xx]], where xx is a referenced number. Please use the context and cite the context at the end of each sentence if related.

Your answer must be correct, accurate and written by an expert using an unbiased and professional tone. Please limit to 2048 tokens.

Please cite the contexts with the reference numbers, in the format [citation:xx] (for example: 68 => [citation: 68]). If a sentence comes from multiple contexts, please list all applicable citations, like [citation:32][citation:51]. Other than code and specific names and citations, your answer must be written in the same language as the question.

Here are the set of contexts:

{context}

Remember, don't blindly repeat the contexts verbatim. And here is the user question:
"""


_summarize_chat_history_prompt = """Progressively summarize the lines of conversation provided, adding onto the previous summary returning a new summary.

EXAMPLE
Current summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good.

New lines of conversation:
Human: Why do you think artificial intelligence is a force for good?
AI: Because artificial intelligence will help humans reach their full potential.

New summary:
The human asks what the AI thinks of artificial intelligence. The AI thinks artificial intelligence is a force for good because it will help humans reach their full potential.
END OF EXAMPLE

Current summary:
{summary}

New lines of conversation:
{new_lines}

New summary:"""

database_query_prompt = """You are an assistant that answers questions related to academic research topics.

User Query: The user will ask a question related to academic research topics.

If you need more information from the user, respond with a query like this:

[[column_name]]: [["value1", "value2", ...]]

Example:

[[AuthorNames]]: [["John Doe", "Jane Smith"]]

Note that the values in the query should be based on the user query and the database columns. The databse columns are:

- Conference
- Year
- Title
- DOI
- Link
- FirstPage
- LastPage
- PaperType
- Abstract
- AuthorNames-Deduped
- AuthorNames
- AuthorAffiliation
- InternalReferences
- AuthorKeywords
- AminerCitationCount
- CitationCount_CrossRef
- PubsCited_CrossRef
- Downloads_Xplore
- Award
- GraphicsReplicabilityStamp
- embeddings
- umap_x
- umap_y
- cluster
- top_keywords

Example User Query: "Find papers related to neural networks by John Doe."

Example Output:

[[AuthorNames]]: [["John Doe"]]
[[Abstract]]: [["neural networks"]]

Example User Query: "Find papers related to neural networks by John Doe."

Example Output:

[[AuthorNames]]: [["John Doe"]]
[[Abstract]]: [["neural networks"]]
"""

class DataResponse(BaseModel):
    df: list[dict[str, Any]]
    date: str

@app.get("/data")
async def data():
    global messages_history
    messages_history = []
    
    embeddings_df = data_store.get_data()
    print(embeddings_df.shape)
    embeddings_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    embeddings_df.fillna("", inplace=True)  # replace NaN values with an arbitrary number
    embeddings_df = embeddings_df.to_dict(orient="records")
    return {"df": embeddings_df, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


class UpdateParams(BaseModel):
    binsNum: int
    clusterNum: int
    
@app.post("/update")
async def update(update_params: UpdateParams):
    bins_num = update_params.binsNum
    cluster_num = update_params.clusterNum
    
    print(bins_num, cluster_num)
    
    embeddings_df = data_store.update_params(bins_num, cluster_num)
    
    return {"df": embeddings_df.to_dict(orient="records"), "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


class RetrievalRequest(BaseModel):
    query: str


@app.post("/retrieval")
async def semantic_retrieval(retrieval_request: RetrievalRequest):
    ranked_results = retrieval(retrieval_request.query)

    return json.dumps(ranked_results, default=str)



@app.get("/clear_memory")
async def clear_memory():
    global messages_history
    messages_history = []


async def memory_handler():
    global messages_history
    
    if len(messages_history) < 5:
        return
    
    # 2 + 2 + 2
    # 1 + 2 + 2
    
    system_prompt = _summarize_chat_history_prompt.format(
        summary=messages_history[0]["content"] if len(messages_history) > 4 else "",
        new_lines="\n".join([m["content"] for m in messages_history[1:3]]) if len(messages_history) > 4 else "\n".join([m["content"] for m in messages_history[:2]])
    )
    
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": system_prompt}],
        max_tokens=1024,
        temperature=0.1,
        stream=False,
    )
    
    print('Generate New Summary', len(res.choices[0].message.content))
    
    messages_history = [
        {"role": "system", "content": res.choices[0].message.content},
    ] + messages_history[-2:]


class MessageRequest(BaseModel):
    prompt: str
    related_queries: str
    context: str
    
    
@app.post("/rag")
async def rag(message_request: MessageRequest): 
    prompt = message_request.prompt
    context = message_request.context
    related_queries = message_request.related_queries

    async def response_stream():
        global messages_history
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            # model="gpt-4-turbo-preview",
            messages= messages_history + [
                {"role": "system", "content": "below are the related queries you can reference to answer the question: " + related_queries + context},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
            temperature=1,
            stream=True,
        )
        
        assistant_message = ""
        try:
            for chunk in response:
                current_content = chunk.choices[0].delta.content
                assistant_message += f"{current_content if current_content else ''}"
                
                if chunk.choices[0].finish_reason == "stop":
                    messages_history += [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": assistant_message}
                    ]
                    assistant_message = ""
                    await memory_handler()
                    print(len(messages_history))
                    
                yield f"{current_content if current_content else ''}"
                await asyncio.sleep(0.01)
        except Exception as e:
            print("OpenAI Response (Streaming) Error: " + str(e))
    
    return StreamingResponse(response_stream(), media_type="text/event-stream")

class QueryRequest(BaseModel):
    prompt: str
    context: List[dict[str, str]]

@app.post("/preprocess")
async def preprocess(query_request: QueryRequest): 
    prompt = query_request.prompt
    context = query_request.context

    system_prompt = _rag_query_text.format(
        context="\n\n".join(
            [f"[[citation:{c['id']}]] Author: {c['author']}\n Title: {c['title']}\n Abstract: {c['text']}" for i, c in enumerate(context)]
        )
    )

    message = ""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            # model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt + database_query_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
            temperature=1,
            stream=True,
        )
        
        for chunk in response:
            current_content = chunk.choices[0].delta.content
            message += f"{current_content if current_content else ''}"


        result = enhanced_retrieval(message)
        json_context = json.dumps(result, default=str)
        result_queries = generate_queries(prompt, json_context)
        
        return result_queries, json_context
    
    except Exception as e:
        print("OpenAI Response (Streaming) Error: " + str(e))
        return ""