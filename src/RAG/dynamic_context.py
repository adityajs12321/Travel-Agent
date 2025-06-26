import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Agents.RouterAgent import Context
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
from typing import Dict

text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )

def bm25_search(bm25: BM25Okapi, bm25_corpus: list[str], query: str, k=1) -> Dict[str, float]:
        tokenized_query = query.split(" ")
        doc_scores = bm25.get_scores(tokenized_query)
        docs_with_scores = dict(zip(bm25_corpus, doc_scores))
        sorted_docs_with_scores = sorted(docs_with_scores.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_docs_with_scores[:k])

def load_context(context: Context):
    messages = []
    bm25_corpus = [json.dumps(doc) for doc in context.history[context.conversation_id]][::-1]
    tokenized_corpus = [doc.split(" ") for doc in bm25_corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    results = bm25_search(bm25, bm25_corpus, "'FLIGHT DETAILS LISTED'")

    print(f"\n\nRESULTS: {json.loads(list(results.keys())[0])}\n\n")

    messages.append(json.loads(list(results.keys())[0]))
    i, count = 2, 1
    temp_list = [context.history[context.conversation_id][-1]]
    while (i < len(context.history[context.conversation_id])):
        if (context.history[context.conversation_id][-i]['content'][:10] == "<question>"):
            count += 1
            temp_list.append({"role": "assistant", "content": ""})
            temp_list.append(context.history[context.conversation_id][-i])
        i += 1
        if (count >= 2): break
    messages.extend(temp_list[::-1])

    return messages