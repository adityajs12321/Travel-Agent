from ollama import chat
from pydantic import BaseModel

class ResponseFormat(BaseModel):
    users_query: str
    assistant_response: str

response = chat(
  messages=[
    {
      'role': 'user',
      'content': '''
        hello how are you?
      ''',
    }
  ],
  model='llama3.1:8b',
  format=ResponseFormat.model_json_schema(),
)

pets = ResponseFormat.model_validate_json(response.message.content)
print(pets)