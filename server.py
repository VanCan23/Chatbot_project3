from flask import Flask, request, jsonify
from flask_cors import CORS
from openai_client import OpenAIClient
from rag.core import RAG
from semantic_router import SemanticRouter, Route
from semantic_router.samples import productSample, chitchatSample
from reflection.core import Reflection
from semantic_cache.core import SemanticCache
from embedding_model.core import EmbeddingModel
from chatbot.core import Chatbot
import time


import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
api_key = os.getenv('OPENAI_API_KEY')
mongo_uri = os.getenv('MONGO_URI')
db_name = os.getenv('DB_NAME')
db_collection = os.getenv('DB_COLLECTION')
db_chat_history_collection = os.getenv('DB_CHAT_HISTORY_COLLECTION')
semantic_cache_collection = os.getenv('SEMANTIC_CACHE_COLLECTION')
vector_index_name = os.getenv('VECTOR_INDEX_NAME')
keyword_index_name = os.getenv('KEYWORD_INDEX_NAME')
semantic_cache_index_name = os.getenv('SEMANTIC_CACHE_INDEX_NAME')


app = Flask(__name__)

CORS(app)

# Initialize embedding model
embedding_model = EmbeddingModel()

# Initialize RAG
llm = OpenAIClient(api_key)
rag = RAG(
    mongodb_uri=mongo_uri,
    db_name=db_name,
    db_collection=db_collection,
    vector_index_name=vector_index_name,
    keyword_index_name=keyword_index_name
)

# Setup Semantic Router
PRODUCT_ROUTE_NAME = 'products'
CHITCHAT_ROUTE_NAME = 'chitchat'

productRoute = Route(name=PRODUCT_ROUTE_NAME, samples=productSample)
chitchatRoute = Route(name=CHITCHAT_ROUTE_NAME, samples=chitchatSample)
semanticRouter = SemanticRouter(routes=[productRoute, chitchatRoute])

# Setup Reflection
reflection = Reflection(
    llm=llm,
    mongodbUri=mongo_uri,
    dbName=db_name,
    dbChatHistoryCollection=db_chat_history_collection,
)

# Setup Semantic Cache
semantic_cache = SemanticCache(
    mongodb_uri=mongo_uri,
    db_name=db_name,
    db_collection=semantic_cache_collection,
    index_name=semantic_cache_index_name
)
#Setup ChatBot
chatbot=Chatbot(
    llm=llm,
    mongodbUri=mongo_uri,
    db_name=db_name,
    dbChatHistoryCollection=db_chat_history_collection,
    semanticCacheCollection=semantic_cache_collection

)

@app.route('/api/v1/chat', methods=['POST'])
def chat():

    start_time=time.time()

    data = request.get_json()
    # session_id can be anything identified with the user or the user session initiating the conversation
    # this can differ per app and user credentials can be retrieved after authentication
    # passing this to the request params is for ease of demo purpose only
    session_id = data.get('session_id', '')

    query = data.get('query', '')
    query_embedding = embedding_model.get_embedding(query)
    cached_result = semantic_cache.retrieve_cached_result(query_embedding)
    if cached_result:
        print(f'Cache hit: {cached_result}')
        response = cached_result
    else:
        #query_embedding = embedding_model.get_embedding(query)
        reflected_query= reflection(session_id=session_id,query=query)
        reflected_query_embedding=embedding_model.get_embedding(reflected_query)
        print("reflected_query: ",reflected_query)
        guided_route = semanticRouter.guide(reflected_query)[1]
        print(f"semantic route: {guided_route}")

    # semantic router is products, so we will use RAG 
        if guided_route == PRODUCT_ROUTE_NAME:
        
            source_information = rag.enhance_prompt(reflected_query,reflected_query_embedding).replace('<br>', '\n')
            print("enhance_context: ",source_information)
            combined_information = f"Câu hỏi : {query}, \ntrả lời khách hàng sử dụng thông tin sản phẩm sau:\n###Sản Phẩm###\n{source_information}."
            response = chatbot(session_id=session_id,
                               cache_response=True,
                               query=query,
                               enhanced_message=combined_information,
                               query_embedding=query_embedding
                               )
        else:
        # semantic router is chitchat, so we will just call LLM without RAG
            response = chatbot(session_id=session_id,
                               cache_response=False,
                               query=query,
                               enhanced_message=query,
                               query_embedding=query_embedding
                               )
    end_time=time.time()

    response_time=end_time-start_time

    print("answer: ",response)
    print("Thời gian xử lý: ",response_time)
    return jsonify({
        "role": "assistant",
        "content": response,
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
