from langchain_groq import ChatGroq
from state import TriageState
from fastapi import FastAPI
from steps.File_Classification import create_classificatioN_workflow
from prompts import CLASSIFICAION_PROMPT
from logger import logger
import uvicorn



app = FastAPI()

@app.post("/items/")
async def create_item(item: TriageState):
    llm = ChatGroq(model='llama-3.3-70b-versatile')
    
    agent = create_classificatioN_workflow(llm, CLASSIFICAION_PROMPT)
    
    initial_state: TriageState = {
        "document_id": "doc_001",
        "document_content": "Invoice #1234\nTotal Amount: $450\nDue Date: 10 Jan 2026",
        "document_type": None,
        "confidence_score": 0.0,
        "classification_details": {}
    }

    result = agent.invoke(initial_state)
    
    logger.info(f'✅ Successfully Comepleted Request: Document_ID: {item['document_id']}\n Classification{result['document_type']}\nConfidence Score: {result['confidence_score']}\n Details: {result['classification_details']}')
    
    return result



if __name__=='__main__':
    uvicorn.run(app=app, port=5000, reload=True)
    logger.info('Done ')
    

