import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
import httpx
import re
import json
from openai import OpenAI
from typing import Annotated, List, Generator, Optional
import leptonai
from leptonai.util import tool

from utils.client_setup import client
from utils.data import data_store

from langchain.text_splitter import NLTKTextSplitter
text_splitter = NLTKTextSplitter(chunk_size=250)

model = SentenceTransformer('all-MiniLM-L6-v2')

_rag_query_text = """
You are a large language AI assistant. You are given a user question, and please write clean, concise and accurate answer to the question. You will be given a set of related contexts to the question, each starting with a reference number like [[citation:x]], where x is a number. Please use the context and cite the context at the end of each sentence if applicable.

Your answer must be correct, accurate and written by an expert using an unbiased and professional tone. Please limit to 1024 tokens. Do not give any information that is not related to the question, and do not repeat. Say "information is missing on" followed by the related topic, if the given context do not provide sufficient information.

Please cite the contexts with the reference numbers, in the format [citation:x]. If a sentence comes from multiple contexts, please list all applicable citations, like [citation:3][citation:5]. Other than code and specific names and citations, your answer must be written in the same language as the question.

Here are the set of contexts:

{context}

Remember, don't blindly repeat the contexts verbatim. And here is the user question:
"""

_generate_more_queries_prompt = """
You are a helpful assistant that helps the user to generate 4~6 search queries based on a single input query, based on user's original question and your own knowledge. Please identify worthwhile topics that can be follow-ups, and write questions no longer than 20 words each. 
Please make sure that specifics, like events, names, locations, are included in follow up questions so they can be asked standalone. For example, if the original question asks about "the Manhattan project", in the follow up question, do not just say "the project", but use the full name "the Manhattan project". Your related questions must be in the same language as the original question.

And here is the user query, generate 4 to 6 related queries based on this query:
"""


def generate_queries_chatgpt(original_query):

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": _generate_more_queries_prompt},
            {"role": "user", "content": f"{original_query}"},
        ]
    )

    generated_queries = response.choices[0].message.content
    return generated_queries


def generate_queries(original_query):
    """
    Generate related questions based on the original question and the context.
    """
    
    def ask_related_questions(
        queries: Annotated[
            List[str],
            [(
                "query",
                Annotated[
                    str, "related query to the original query and context."
                ],
            )],
        ]
    ):
        """
        Ask related questions based on the original question and the context.
        """
        
        pass

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": _generate_more_queries_prompt
                },
                {
                    "role": "user",
                    "content": f"{original_query}",
                },
            ],
            tools=[{
                "type": "function",
                "function": tool.get_tools_spec(ask_related_questions),
            }],
            max_tokens=512,
        )
        
        print(f"Generated related questions: {response.choices[0].message.tool_calls[0].function.arguments}")
        related = response.choices[0].message.tool_calls[0].function.arguments
        if isinstance(related, str):
            related = json.loads(related)
        
        return related["queries"][:]
    
    except Exception as e:
        # For any exceptions, we will just return an empty list.
        print(f"encountered error while generating related questions:\n{e}")
        return []



def reciprocal_rank_fusion(search_results_dict, df, k=60):
    index_fused_scores = {}
    
    for query, index_doc_scores in search_results_dict.items():
        for rank, (index, (doc, score)) in enumerate(sorted(index_doc_scores.items(), key=lambda x: x[1][1], reverse=True)):
            if index not in index_fused_scores:
                paper_id = df.loc[df['abstract'] == doc]['paper_id'].values[0]
                index_fused_scores[index] = {'abstract': doc, 'score': 0, 'paper_id': paper_id, 'title': df.loc[paper_id]['title'], 'name': df.loc[paper_id]['first_name'] + ' ' + df.loc[paper_id]['last_name']}
            previous_score = index_fused_scores[index]['score']
            # Update the score based on the reciprocal rank fusion algorithm
            index_fused_scores[index]['score'] += 1 / (rank + k)
            # print(f"Updating score for index {index}, doc {doc} from {previous_score} to {index_fused_scores[index]['score']} based on rank {rank} in query '{query}'")

    # Sort the results by the fused score and then by the index
    reranked_results = {index: index_fused_scores[index] for index in sorted(index_fused_scores, key=lambda x: (index_fused_scores[x]['score'], x), reverse=False)}
    # print("Final reranked results:", reranked_results)
    return reranked_results


def compute_fused_results(original_query, matrix, df, generate_queries=False):
    search_results_dict = {}
    queries = []
    
    # 1. Generate Multiple Queries using ChatGPT
    if generate_queries:
        queries = generate_queries(original_query)
        # 2. Embed and Perform Vector Similarity Search
        for query in queries:
            query = query['query']
            
            query_embedding = model.encode(query, convert_to_tensor=True)
            query_embedding = query_embedding.cpu().detach().numpy()

            distances = np.linalg.norm(matrix - query_embedding, axis=1)
            search_results_dict[query] = dict(zip(df.index, zip(df['content'], distances)))

        # 3. Reciprocal Rank Fusion
        reranked_results = reciprocal_rank_fusion(search_results_dict, df)
        
    else:
        query_embedding = model.encode(original_query, convert_to_tensor=True)
        query_embedding = query_embedding.cpu().detach().numpy()

        distances = np.linalg.norm(matrix - query_embedding, axis=1)
        search_results_dict[original_query] = dict(zip(df.index, zip(df['abstract'], distances)))
        reranked_results = reciprocal_rank_fusion(search_results_dict, df)
        queries = [original_query]
        
    
    top_k = determine_top_k([result['score'] for result in reranked_results.values()])
    top_results = list(reranked_results.values())[:top_k]
    print(f"Top K: {top_k}")
    
    top_results_sentences_scores = []

    for result in top_results:
        paper_id = result['paper_id']
        row = df.loc[paper_id]
        sentences = text_splitter.split_text(row['abstract'])

        for i, sentence in enumerate(sentences):
            sentence_embedding = model.encode(sentence, convert_to_tensor=True)
            sentence_embedding = sentence_embedding.cpu().detach().numpy()
            # Calculate the cosine similarity between the query and the sentence
            similarity = np.dot(query_embedding, sentence_embedding.T) / (np.linalg.norm(query_embedding) * np.linalg.norm(sentence_embedding))
            top_results_sentences_scores.append((paper_id, i, sentence, similarity))
            
    top_results_sentences_scores = sorted(top_results_sentences_scores, key=lambda x: x[3], reverse=True)

    top_results_sentences_scores = top_results_sentences_scores[:5]
    top_results_sentences_scores = sorted(top_results_sentences_scores, key=lambda x: x[3], reverse=True)

    for i, result in enumerate(top_results):
        paper_id = result['paper_id']
        top_results[i]['sentences'] = [x[2] for x in top_results_sentences_scores if x[0] == paper_id]
        
    
    return top_results


def determine_top_k(scores):
    # Calculate the differences between consecutive scores
    differences = [scores[i] - scores[i+1] for i in range(len(scores) - 1)]
    differences = [abs(diff) for diff in differences]

    # Calculate the standard deviation of the differences
    threshold = np.std(differences) * 0.8

    # Find the index of the first difference that is greater than the threshold
    k = next((i for i, diff in enumerate(differences) if diff > threshold), len(scores))
    k = np.clip(k, 2, 10)
    return k



def retrieval(query):
    query = re.sub(r"\[/?INST\]", "", query)
    
    embeddings_df = data_store.get_data()
    top_results = compute_fused_results(query, np.array(embeddings_df['embeddings'].tolist()), embeddings_df)
    
    return top_results
    
    
async def RAG(prompt, context):
    # TODO: Add the ability to pass in the context and prompt
    system_prompt = _rag_query_text.format(
        context="\n\n".join(
            [f"[[citation:{c['id']}]] {c['text']}" for i, c in enumerate(context)]
        )
    )
    
    llm_response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
        # stop=stop_words,
        # stream=True,
        temperature=0.9,
    )
    # list all the citations
    citations_objects = [{'id': c['id'], 'content': c['text']} for c in context]
    
    return {"response": llm_response.choices[0].message.content, "citations": citations_objects}
