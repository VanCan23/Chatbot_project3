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
        summary_prompt = "Using the user's conversation history and their latest question, which may reference the context within the chat history, construct a standalone question for the user's latest query. This standalone question should be understandable without requiring the chat history. DO NOT answer the question; only reconstruct it if necessary. If no reconstruction is needed, leave it unchanged. {chatHistory}"
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
                    {"role":"system","content":"You are a helpful AI assistant specializing in rewriting messages to make them complete and easy to understand. Based on the chat history and the latest message received, rewrite the received message to ensure it fits the context of the conversation."},
                    {"role": "user","content": summary_prompt},
                ]
            )
        
            return completion.choices[0].message.content
        else :
            return query





