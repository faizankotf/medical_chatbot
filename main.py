from fastapi import FastAPI
from pydantic import BaseModel
from rag import run_query

app = FastAPI()

class QueryRequest(BaseModel):
    mrd_number: str
    query: str

@app.post("/query")
def query_endpoint(req: QueryRequest):
    response = run_query(req.mrd_number, req.query)
    return response