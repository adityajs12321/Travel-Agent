from pydantic import BaseModel
from fastapi import FastAPI
import model
import api_utils.utils as utils

answer = ""

app = FastAPI()

@app.get("/")
def read_root():
    return "LLM Backend"

@app.post("/question")
def answer_question(question: str):
    global answer
    answer_ = model.llm.invoke(question)
    answer = str(answer_.content)
    return answer

@app.get("/answer")
def return_answer():
    return utils.return_results(utils.params)