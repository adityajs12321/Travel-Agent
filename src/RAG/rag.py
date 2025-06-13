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

from typing import List, Dict
from rank_bm25 import BM25Okapi

class VectorDbWithBM25:
    def __init__(self, vectordb_docs, bm25_corpus):
        self.docs = vectordb_docs
        self.__bm25_corpus = bm25_corpus
        
        tokenized_corpus = [doc.split(" ") for doc in bm25_corpus]
        self.__bm25 = BM25Okapi(tokenized_corpus)

        hnswlib_vector_store = HnswlibVectorStore.from_params(
            space="ip",
            dimension=embed_model._model.get_sentence_embedding_dimension(),
            max_elements=1000,
            M=64,
            ef_construction=200,
            ef=100
        )

        self.hnswlib_storage_context = StorageContext.from_defaults(
            vector_store=hnswlib_vector_store
        )
        
        # Create index once during initialization
        self.index = VectorStoreIndex.from_documents(
            self.docs,
            storage_context=self.hnswlib_storage_context,
            embed_model=embed_model,
            show_progress=True,
        )
        self.index.storage_context.persist(index_store_fname="rag_index")
        
    def vector_db_search(self, query: str, k=3) -> Dict[str, float]:
        retriever = self.index.as_retriever(similarity_top_k=k)
        nodes_with_scores = retriever.retrieve(query)
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
    
class RAG:
    def __init__(self, file_path):
        self.file_path = file_path
    
    def search(self, query: str, k=3, do_bm25_search=True) -> Dict[str, float]:
        documents_vectordb = SimpleDirectoryReader(input_files=[self.file_path]).load_data()

        text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
    
        doc_loader = PyPDFLoader(self.file_path)
        pages = doc_loader.load_and_split()
        docs = text_splitter.split_documents(pages)

        bm25_corpus = [doc.page_content for doc in docs]

        vector_db_with_bm25 = VectorDbWithBM25(documents_vectordb, bm25_corpus)
        search_results = vector_db_with_bm25.vector_db_search(query, k)
        return search_results