import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.core import RAG
from embedding_model.core import EmbeddingModel
from ragas import evaluate
from dotenv import load_dotenv
from chatbot.core import Chatbot
from openai_client import OpenAIClient
import pandas as pd
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

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

embedding_model = EmbeddingModel()
llm = OpenAIClient(api_key)

rag=RAG(
    mongodb_uri=mongo_uri,
    db_name=db_name,
    db_collection=db_collection,
    vector_index_name=vector_index_name,
    keyword_index_name=keyword_index_name
)

chatbot=Chatbot(
    llm=llm,
    mongodbUri=mongo_uri,
    db_name=db_name,
    dbChatHistoryCollection=db_chat_history_collection,
    semanticCacheCollection=semantic_cache_collection

)
def get_retrieved_reponse(query):
    query_embedding=embedding_model.get_embedding(query)
    retrieved_doc= rag.hybrid_search(query,query_embedding,5)
    source_information = rag.enhance_prompt(query,query_embedding).replace('<br>', '\n')
    combined_information = f"Câu hỏi : {query}, \ntrả lời khách hàng sử dụng thông tin sản phẩm sau:\n###Sản Phẩm###\n{source_information}."
    response = chatbot(session_id=1,
                               cache_response=True,
                               query=query,
                               enhanced_message=combined_information,
                               query_embedding=query_embedding
                               )

    return retrieved_doc,response




def load_evaluation_data(path):
    questions = []
    expected_answers = []
    # Đọc dữ liệu từ file trong path
    # Ví dụ nếu là file CSV:
    df = pd.read_csv(f"{path}")
    questions = df['question'].tolist()
    expected_answers = df['answer'].tolist()
    return questions, expected_answers

# Sử dụng
local_path = "/Users/vancan23/Downloads/qa_dataset-3.csv"
questions, expected_answers = load_evaluation_data(local_path)
questions=questions[:100]
expected_answers=expected_answers[:100]
results_data = []
for question, expected_answer in zip(questions, expected_answers):
    retrieved_docs, generated_response = get_retrieved_reponse(question)
    
    results_data.append({
        "question": question,
        "contexts": [doc for doc in retrieved_docs],  
        "answer": generated_response,
        "ground_truth": expected_answer
    })
dataset_dict = {
    "question": [item["question"] for item in results_data],
    "contexts": [[str(doc) for doc in item["contexts"]] for item in results_data],
    "answer": [item["answer"] for item in results_data],
    "ground_truth": [item["ground_truth"] for item in results_data]
}
# Tạo Dataset object từ results
dataset = Dataset.from_dict(dataset_dict)

# Định nghĩa metrics
metrics = [faithfulness,answer_relevancy,context_precision,context_recall]

# Đánh giá
scores = evaluate(
    dataset=dataset,  
    metrics=metrics
)

print(scores)   
