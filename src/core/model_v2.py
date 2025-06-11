import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentic_patterns.reflection_pattern.reflection_agent import ReflectionAgent
from agentic_patterns.planning_pattern.react_agent import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from pydantic import BaseModel, Field
from api_utils.AmadeusAPI import AmadeusClient
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from llama_index.vector_stores.hnswlib import HnswlibVectorStore
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    SimpleDirectoryReader
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    normalize=True,
)

hnswlib_vector_store = HnswlibVectorStore.from_params(
    space="ip",
    dimension=embed_model._model.get_sentence_embedding_dimension(),
    max_elements=1000,
)
        

hnswlib_storage_context = StorageContext.from_defaults(
    vector_store=hnswlib_vector_store
)

from typing import List, Dict
from rank_bm25 import BM25Okapi

class VectorDbWithBM25:
    def __init__(self, vectordb_docs, bm25_corpus):
        self.docs = vectordb_docs
        self.__bm25_corpus = bm25_corpus
        
        tokenized_corpus = [doc.split(" ") for doc in bm25_corpus]
        self.__bm25 = BM25Okapi(tokenized_corpus)
        
    def vector_db_search(self, query: str, k=3) -> Dict[str, float]:
        hnswlib_index = VectorStoreIndex.from_documents(
            self.docs,
            storage_context=hnswlib_storage_context,
            embed_model=embed_model,
            show_progress=True,
        )

        hnswlib_vector_retriever = hnswlib_index.as_retriever(similarity_top_k=1)
        nodes_with_scores = hnswlib_vector_retriever.retrieve(query)
            
        return {node.text: node.score for node in nodes_with_scores}
    
    def bm25_search(self, query: str, k=3) -> Dict[str, float]:
        tokenized_query = query.split(" ")
        doc_scores = self.__bm25.get_scores(tokenized_query)
        docs_with_scores = dict(zip(self.__bm25_corpus, doc_scores))
        sorted_docs_with_scores = sorted(docs_with_scores.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_docs_with_scores[:k])
        
    def combine_results(self, vector_db_search_results: Dict[str, float], 
                        bm25_search_results: Dict[str, float]) -> Dict[str, float]:
        
        def normalize_dict(input_dict):
            epsilon = 0.05
            min_value = min(input_dict.values())
            max_value = max(input_dict.values())
            a, b = 0.05, 1
            
            if max_value == min_value:
                return {k: b if max_value > 0.5 else a for k in input_dict.keys()}
    
            return {k: a + ((v - min_value) / (max_value - min_value)) * (b - a) for k, v in input_dict.items()}
        
        norm_vector_db_search_results = normalize_dict(vector_db_search_results)
        norm_bm25_search_results = normalize_dict(bm25_search_results)

        # Combine the dictionaries
        combined_dict = {}
        for k, v in norm_vector_db_search_results.items():
            combined_dict[k] = v

        for k, v in norm_bm25_search_results.items():
            if k in combined_dict:
                combined_dict[k] = max(combined_dict[k], v)
            else:
                combined_dict[k] = v

        return combined_dict

    def search(self, query: str, k=3, do_bm25_search=True) -> Dict[str, float]:
        vector_db_search_results = self.vector_db_search(query, k=k)
        
        if do_bm25_search:
            bm25_search_results = self.bm25_search(query, k=k)
            if bm25_search_results:
                combined_search_results = self.combine_results(vector_db_search_results, bm25_search_results)
                sorted_docs_with_scores = sorted(combined_search_results.items(), key=lambda x: x[1], reverse=True)
                return dict(sorted_docs_with_scores)
        return vector_db_search_results


CLIENT_ID = None
CLIENT_SECRET = None
client = None

BASE_SYSTEM_PROMPT = """
You are a travel agent that takes user input and calls the flight search tool after extracting relevant information.
You can only suggest travel plans, not book them.
You will then choose (choose not book) the best flight provided by the flights list and list the flight details only.
Convert the origin and destination to their respective iataCode.
Both origin and destination are required.

If the user asks for the details or policies of the flight, you will use the flight_policies_tool to search for the policies and return the relevant policies according to the user's query verbatim.
"""

def set_access_token(client_id, client_secret):
    global client, CLIENT_ID, CLIENT_SECRET
    CLIENT_ID = client_id
    CLIENT_SECRET = client_secret
    try:
        access_token = os.environ.get("AMADEUS_ACCESS_TOKEN")
        if access_token:
            client = AmadeusClient(client_id, client_secret, access_token)
        else:
            client = AmadeusClient(client_id, client_secret)
    except Exception as e:
        print(f"Client failed to connect: {e}")
        client = None

class TripPreferences(BaseModel):
    distance_from_airport: str
    ratings: str

class TripRequest(BaseModel):
    origin: str = Field(..., description="Departure city/airport code")
    destination: str = Field(..., description="Destination city/airport code")
    departure_date: str = Field(..., description="Departure date")
    adults: str = Field(..., description="Number of passengers")
    maxPrice: str = Field(..., description="Maximum price of flight")
    currencyCode: str = Field("USD", description="The currency code")
    hotelPrefs: TripPreferences

@tool
def flight_search_tool(
    originLocationCode: str,
    destinationLocationCode: str,
):
    """
        Gets the flight details provided the given details.

        Args:
            originLocationCode (str): The origin airport code
            destinationLocationCode (str): The origin airport code
        """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up to the common parent directory (src)
    parent_dir = os.path.dirname(current_dir)

    # Now navigate to the FlightData directory
    file_path = os.path.join(parent_dir, "FlightData", "Flights.json")
    with open(file_path, "r") as f:
        data = json.load(f)
        flights = data["Flights"]
        for flight in flights:
            if (flight["origin"] == originLocationCode and flight["destination"] == destinationLocationCode):
                return flight
        return "No flights found"
    
@tool
def flight_policies_tool(
    flight_name: str,
    query: str
):
    """
        Gets the flight policies provided the given flight number.

        Args:
            flight_name (str): The airline name
            query (str): The user's query
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up to the common parent directory (src)
    parent_dir = os.path.dirname(current_dir)

    # Now navigate to the FlightData directory
    file_path = os.path.join(parent_dir, "FlightData", "FlightPolicies", f"{flight_name}.pdf")
    documents_vectordb = SimpleDirectoryReader(input_files=[file_path]).load_data()

    text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
    
    doc_loader = PyPDFLoader(file_path)
    pages = doc_loader.load_and_split()
    docs = text_splitter.split_documents(pages)

    bm25_corpus = [doc.page_content for doc in docs]

    vector_db_with_bm25 = VectorDbWithBM25(documents_vectordb, bm25_corpus)
    search_results = vector_db_with_bm25.search(query, k=2, do_bm25_search=True)

    return list(search_results.keys())[0]

tools_list = [flight_search_tool, flight_policies_tool]

class IntelTravelModel:
    def trip_planning(self, conversation_id: int, request: str):
        """Trip planning using ReAct and Reflection patterns"""

        model = ReactAgent(tools_list, system_prompt=BASE_SYSTEM_PROMPT)
        response = model.run(
            conversation_id=conversation_id,
            user_msg=request,
            max_rounds=10
        )

        return response