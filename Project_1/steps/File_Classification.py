from langchain_groq import ChatGroq
from typing_extensions import TypedDict
from langgraph.graph import START, StateGraph, END
from langchain_classic.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage, SystemMessage
from prompts import CLASSIFICAION_PROMPT
from state import DocumentClassification, TriageState




def create_classificatioN_workflow(llm, system_prompt):

    classifier = llm.with_structured_output(DocumentClassification)

    def classify_with_fallback(state: TriageState) -> dict:
        """
        Two-pass classification: simple first, then detailed if uncertain.
        """
        
        # Extract text from Document objects
        
        # PASS 1: Quick classification
        quick_classification = classifier.invoke(
            [
                SystemMessage(content="Classify this document type quickly. Choose the best match."),
                HumanMessage(content=state['document_content'][:2000])  # First 2000 chars
            ]
        )
        
        # If confidence is good, return it
        if quick_classification.confidence >= 0.8:
            return {
                "document_type": quick_classification.document_type,
                "confidence_score": quick_classification.confidence,
                "classification_details": {
                    "reasoning": quick_classification.reasoning,
                    "key_indicators": quick_classification.key_indicators,
                    "alternatives": quick_classification.alternative_types,
                    "pass": 1  # Track which pass succeeded
                }
            }
        
        # PASS 2: Detailed analysis for low-confidence documents
        detailed_classification = classifier.invoke(
            [
                SystemMessage(
                    content="""Analyze this document CAREFULLY for classification.

                        Read the ENTIRE document. Look for:
                        
                        1. Header/Title information
                        2. Identifiers (Invoice #, Claim #, PO #, Form Type)
                        3. Key fields specific to each document type
                        4. Company logos or official stamps
                        5. Legal language or contract terminology
                        
                        Be specific about what you found."""
                ),
                HumanMessage(content=state['document_content'])  # Full content
            ]
        )
        
        return {
            "document_type": detailed_classification.document_type,
            "confidence_score": detailed_classification.confidence,
            "classification_details": {
                "reasoning": detailed_classification.reasoning,
                "key_indicators": detailed_classification.key_indicators,
                "alternatives": detailed_classification.alternative_types,
                "pass": 2,  # Indicates we needed detailed analysis
            }
        }
        


    # Add to your graph
    builder = StateGraph(TriageState)
    builder.add_node("classify", classify_with_fallback)
    builder.add_edge(START, "classify")

    return builder.compile()


# if __name__=='__main__':
    
    
#     llm = ChatGroq(model='llama-3.3-70b-versatile')
    
#     agent = create_classificatioN_workflow(llm, CLASSIFICAION_PROMPT)
    
#     initial_state: TriageState = {
#         "document_id": "doc_001",
#         "document_content": "Invoice #1234\nTotal Amount: $450\nDue Date: 10 Jan 2026",
#         "document_type": None,
#         "confidence_score": 0.0,
#         "classification_details": {}
#     }

#     result = agent.invoke(initial_state)

#     print(result)