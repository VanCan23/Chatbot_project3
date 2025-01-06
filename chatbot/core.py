from rag.mongo_client import MongoClient

class Chatbot:
    def __init__(self,
        llm,
        mongodbUri: str,
        db_name: str,
        dbChatHistoryCollection: str,
        semanticCacheCollection: str,
    ):
        self.client = MongoClient().get_mongo_client(mongodbUri)
        self.db = self.client[db_name] 
        self.history_collection = self.db[dbChatHistoryCollection]
        self.semantic_cache_collection = self.db[semanticCacheCollection]
        self.llm = llm
    def __call__(self, session_id: str, query: str, enhanced_message: str, cache_response: bool = False, query_embedding: list[float]=[]):
        if query != enhanced_message:
            '''data=[
                {"role":"system","content":"bạn là 1 trợ lý AI hữu ích của cửa hàng bán điện thoại di động,hãy đưa ra tư vấn đầy đủ và cụ thể cho câu hỏi của khách hàng.Nếu thông tin của về sản phẩm không có sẵn trong cửa hàng thì hãy bảo khách hàng liên hệ thêm để biết chi tiết,KHÔNG được trả lời lan man mà không liên quan đến thông tin sản phẩm được cung cấp."},
                {"role":"user","content":enhanced_message }
            ]'''
            data=[
                {"role":"system","content":"bạn là 1 trợ lý AI hữu ích của cửa hàng bán điện thoại di động,hãy trả lời ngắn gọn và đúng trọng tâm câu hỏi của khách hàng.Nếu thông tin của về sản phẩm không có sẵn trong cửa hàng thì hãy bảo khách hàng liên hệ thêm để biết chi tiết,KHÔNG được trả lời lan man mà không liên quan câu hỏi của khách hàng."},
                {"role":"user","content":enhanced_message }
            ]

        else :
            data=[
                {"role":"system","content":"bạn là 1 trợ lý AI hữu ích,hãy trả lời câu hỏi của người dùng một cách đầy đủ và chắc chắn.Nếu không biết thì hãy trả lời là không biết,KHÔNG trả lời lan man và không liên quan đến câu hỏi."},
                {"role":"user","content":query}
            ]
        response = self.llm.generate_content(data)
        response_content = response.choices[0].message.content

        self.history_collection.insert_one({
           "SessionId": session_id,
            "History": {
                "type": "user",
                "data":  {
                    "type": "user",
                    "content": query,
                }
            }
        })

        self.history_collection.insert_one({
           "SessionId": session_id,
            "History": {
                "type": "assistant",
                "data":  {
                    "type": "assistant",
                    "content": response_content,
                }
            }
        })
        if cache_response:
            embedding = query_embedding
            self.semantic_cache_collection.insert_one({
                "embedding": embedding,
                "text": [
                    {
                        "type": "human",
                        "content": query,
                        "enhanced_content": enhanced_message,
                    }
                ],
                "llm_string": {
                    "model_name": response.model,
                    "name": "ChatOpenAI"
                },
                "return_val": [
                    {
                        "type": "assistant",
                        "content": response_content,
                        "enhanced_content": None,
                        "id": response.id,
                        "usage_metadata": {
                            "input_tokens": response.usage.prompt_tokens,
                            "output_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        },
                        "response_metadata": {
                            "usage": response.usage.to_json(),
                            "model_name": response.model,
                            "finish_reason": response.choices[0].finish_reason,
                            "logprobs": response.choices[0].logprobs
                        },
                    }
                ]
            })
        return response_content