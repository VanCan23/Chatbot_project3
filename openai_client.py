import openai

class OpenAIClient:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)

    def generate_content(self, messages):
        completion = self.client.chat.completions.create(
            model="gpt-4o mini",
            messages=messages
        )
        return completion
