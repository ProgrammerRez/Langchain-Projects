from typing import Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain_classic.schema import Document



# Define what classification looks like (this is your contract)``
class DocumentClassification(BaseModel):
    """Structured output for document classification"""
    document_type: Literal[
        "invoice",
        "contract", 
        "w2_form",
        "medical_record",
        "insurance_claim",
        "purchase_order",
        "unknown"
    ] = Field(description="The primary document type")
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0) for the classification"
    )
    
    alternative_types: list[str] = Field(description='Top 2 alternative classifications if confidence < 0.8')
    
    reasoning: str = Field(description='Brief explaination of why was the classification choosen')
    
    key_indicators: list[str] = Field(
        description="Specific text/fields that indicated this document type (e.g., 'INVOICE #', 'W-2', 'CLAIM NUMBER')"
    )





# Defining the State for the Classification Workflow
class TriageState(TypedDict):
    document_id: str
    document_content: str | Document | list[str] | list[Document] | None# Raw Text or OCR Output
    document_type: str | None  # Optional
    confidence_score: float
    classification_details: dict  # Stores full reasoning
