from rag.mongo_client import MongoClient

OPEN_AI_ROLE_MAPPING = {
    "human": "user",
    "ai": "assistant"
}

class Reflection():
    def __init__(self,
        llm,
        mongodbUri: str,
        dbName: str,
        dbChatHistoryCollection: str,
    ):
        self.client = MongoClient().get_mongo_client(mongodbUri)
        self.db = self.client[dbName] 
        self.history_collection = self.db[dbChatHistoryCollection]
        self.llm = llm
    def __construct_session_messages__(self, session_messages: list):
        result = []
        for session_message in session_messages:
            #print(f"session_message: {session_message}")
            #print(f"session_message: {session_message['History']}")
            result.append({
                "role": session_message['History']['type'],
                "content": session_message['History']['data']['content']
            })
        return result
    def __call__(self, session_id: str, query: str = ''):
        human_prompt = [
            {
                "role": "user", 
                "content": query
            }
        ]
        summary_prompt = "Với lịch sử trò chuyện và câu hỏi mới nhất của người dùng có thể tham chiếu đến ngữ cảnh trong lịch sử trò chuyện, hãy xây dựng một câu hỏi độc lập bằng tiếng Việt cho câu hỏi mới nhất của người dùng để có thể hiểu được mà không cần lịch sử trò chuyện. KHÔNG trả lời câu hỏi, chỉ cần xây dựng lại câu hỏi nếu cần và nếu không thì trả về nguyên trạng. {chatHistory}"
        chat_session_query = { "SessionId": session_id }
        session_messages = self.history_collection.find(chat_session_query)
        formatted_session_messages = self.__construct_session_messages__(session_messages)
        print("chat history: ",formatted_session_messages)
        if len(formatted_session_messages) > 0:
            messages = formatted_session_messages + human_prompt
            summary_prompt = summary_prompt.format(chatHistory=messages)
            print(summary_prompt)
            completion = self.llm.generate_content(
                messages=[
                    {"role":"system","content":"Bạn là 1 trợ lý AI hữu ích cho việc viết lại tin nhắn một cách đầy đủ và dễ hiểu.Dựa vào lịch sử chat và tin nhắn mới được gửi đến,hãy viết lại tin nhắn được gửi đến bằng Tiếng Việt để đúng ngữ cảnh cuộc trò chuyện"},
                    {"role": "user","content": summary_prompt},
                ]
            )
        
            return completion.choices[0].message.content
        else :
            return query





