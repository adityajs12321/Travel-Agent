import sys
import os
import json
import ast

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

def load_flight_context(system_prompt: str, context: Context):
    messages = [{"role": "user", "content": system_prompt}]
    bm25_corpus = [json.dumps(doc) for doc in context.history[context.conversation_id]][::-1]
    tokenized_corpus = [doc.split(" ") for doc in bm25_corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    results = bm25_search(bm25, bm25_corpus, "'FLIGHT DETAILS LISTED'")

    flights_list = None
    if ("FLIGHT DETAILS LISTED" in list(results.keys())[0]):
        _message = json.loads(list(results.keys())[0])
        string = _message["content"]
        json_data = ast.literal_eval(string)
        flights_list = ast.literal_eval(json_data[0])["FLIGHT DETAILS LISTED"]
        print(f"\n\n Flgiht details: {flights_list}")
        messages.append(_message)

    results = bm25_search(bm25, bm25_corpus, "'CHOSEN FLIGHT DETAILS'")

    if ("CHOSEN FLIGHT DETAILS" in list(results.keys())[0]):
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

    return messages, flights_list

def load_flight_context2(context: Context):
    messages = []
    bm25_corpus = [json.dumps(doc) for doc in context.history[context.conversation_id]][::-1]
    tokenized_corpus = [doc.split(" ") for doc in bm25_corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    results = bm25_search(bm25, bm25_corpus, "'FLIGHT DETAILS LISTED'")

    flights_list = []
    if ("FLIGHT DETAILS LISTED" in list(results.keys())[0]):
        _message = json.loads(list(results.keys())[0])
        string = _message["content"]
        json_data = ast.literal_eval(string)
        # print(json_data[0])
        flights_list = json_data[0]["FLIGHT DETAILS LISTED"]
        print(f"\n\n Flgiht details: {flights_list}")
        messages.append(_message)

    results = bm25_search(bm25, bm25_corpus, "'CHOSEN FLIGHT DETAILS'")

    if ("CHOSEN FLIGHT DETAILS" in list(results.keys())[0]):
        messages.append(json.loads(list(results.keys())[0]))

    i, count = 2, 1
    temp_list = [context.history[context.conversation_id][-1]]
    while (i < len(context.history[context.conversation_id])):
        if (context.history[context.conversation_id][-i]['content'][:10] == "<question>" and context.history[context.conversation_id][-i]['content'][:15] != "<question>Agent"):
            count += 1
            temp_list.append({"role": "assistant", "content": ""})
            temp_list.append(context.history[context.conversation_id][-i])
        i += 1
        if (count >= 2): break
    messages.extend(temp_list[::-1])

    return messages, flights_list

def load_context(context: Context):
    messages = []
    bm25_corpus = [json.dumps(doc) for doc in context.history[context.conversation_id]][::-1]
    tokenized_corpus = [doc.split(" ") for doc in bm25_corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    results = bm25_search(bm25, bm25_corpus, "'CHOSEN FLIGHT DETAILS'")

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

def load_restaurant_context(context: Context, current_hotel_details: dict = {}, hotels_list = []):
    messages = []
    bm25_corpus = [json.dumps(doc) for doc in context.history[context.conversation_id]][::-1]
    tokenized_corpus = [doc.split(" ") for doc in bm25_corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    if (hotels_list != []): destination = list(hotels_list.keys())[0]

    results = bm25_search(bm25, bm25_corpus, "'CHOSEN FLIGHT DETAILS'")
    if ("CHOSEN FLIGHT DETAILS" not in list(results.keys())[0]):
        print("\n\n No Existing Flights Found\n\n")
    else :
        string = json.loads(list(results.keys())[0])["content"]
        json_data = ast.literal_eval(string)
        # print(json_data)
        destination = json_data[0]["CHOSEN FLIGHT DETAILS"]["itineraries"][0]["segments"][-1]["arrival"]["airport"]
        destination_details = "Destination (Use if not mentioned): " + str(destination)
        messages.append({"role": "user", "content": destination_details})

    if (hotels_list != []): 
        if (destination == list(hotels_list.keys())[0]):
            messages.append({"role": "user", "content": f"Hotels List: {json.dumps(hotels_list[destination])}"})
    i, count = 2, 1
    temp_list = [context.history[context.conversation_id][-1]]
    if (current_hotel_details != {}): temp_list.append(current_hotel_details)
    while (i < len(context.history[context.conversation_id])):
        if (context.history[context.conversation_id][-i]['content'][:10] == "<question>"):
            count += 1
            temp_list.append(context.history[context.conversation_id][-i])
        i += 1
        if (count >= 2): break
    messages.extend(temp_list[::-1])

    return messages

def load_activities_context(context: Context, current_hotel_details: dict = {}, hotels_list = []):
    messages = []
    bm25_corpus = [json.dumps(doc) for doc in context.history[context.conversation_id]][::-1]
    tokenized_corpus = [doc.split(" ") for doc in bm25_corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    if (hotels_list != []): destination = list(hotels_list.keys())[0]

    results = bm25_search(bm25, bm25_corpus, "'CHOSEN FLIGHT LISTED'")
    if ("CHOSEN FLIGHT DETAILS" not in list(results.keys())[0]):
        print("\n\n No Existing Flights Found\n\n")
    else :
        string = json.loads(list(results.keys())[0])["content"]
        json_data = ast.literal_eval(string)
        destination = json_data[0]["CHOSEN FLIGHT DETAILS"]["itineraries"][0]["segments"][-1]["arrival"]["airport"]
        destination_details = "Destination (Use if not mentioned): " + str(destination)
        messages.append({"role": "user", "content": destination_details})

    if (hotels_list != []): 
        if (destination == list(hotels_list.keys())[0]):
            messages.append({"role": "user", "content": f"Activities List: {json.dumps(hotels_list[destination])}"})
    i, count = 2, 1
    temp_list = [context.history[context.conversation_id][-1]]
    if (current_hotel_details != {}): temp_list.append(current_hotel_details)
    while (i < len(context.history[context.conversation_id])):
        if (context.history[context.conversation_id][-i]['content'][:10] == "<question>"):
            count += 1
            temp_list.append(context.history[context.conversation_id][-i])
        i += 1
        if (count >= 2): break
    messages.extend(temp_list[::-1])

    return messages