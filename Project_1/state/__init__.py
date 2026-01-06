from typing import Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, List
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
    
    alternative_types: List[str] = Field(description='Top 2 alternative classifications if confidence < 0.8')
    
    reasoning: str = Field(description='Brief explaination of why was the classification choosen')
    
    key_indicators: List[str] = Field(
        description="Specific text/fields that indicated this document type (e.g., 'INVOICE #', 'W-2', 'CLAIM NUMBER')"
    )





# Defining the State for the Classification Workflow
class TriageState(TypedDict):
    document_id: str
    file_path: str
    document_content: List[str] | List[Document] | None# Raw Text or OCR Output
    document_type: str | None  # Optional
    confidence_score: float
    classification_details: dict  # Stores full reasoning




DOCUMENT_VALIDATION_RULES = {
    "invoice": """
    - Should contain invoice number, vendor, and total amount.
    - Look for dates (issue/due), line items, and currency symbols.
    - Must clearly identify sender and recipient details.
    - Confidence threshold: >=0.8 to auto-route to Accounting.
    """,

    "contract": """
    - Should include parties involved, effective dates, and terms.
    - Look for legal clauses, signatures, and titles like 'Agreement' or 'Contract'.
    - Ensure the document is not a draft (check for 'DRAFT' watermark).
    - Confidence threshold: >=0.85 to auto-route to Legal.
    """,

    "w2_form": """
    - Must include employee name, SSN, and employer info.
    - Look for 'W-2' title, federal tax info, and wages.
    - Ensure all required fields are filled.
    - Confidence threshold: >=0.9 to auto-route to HR.
    """,

    "medical_record": """
    - Should contain patient info, medical history, and dates of service.
    - Look for headings like 'Diagnosis', 'Prescription', 'Lab Results'.
    - Ensure PHI compliance; anonymize if necessary.
    - Confidence threshold: >=0.8 to auto-route to Medical Records.
    """,

    "insurance_claim": """
    - Must include claim number, policy number, and claim type.
    - Look for accident dates, insured party, and supporting documents.
    - Ensure signatures or stamps are present if required.
    - Confidence threshold: >=0.8 to auto-route to Claims department.
    """,

    "purchase_order": """
    - Should include PO number, vendor info, and item list with quantities.
    - Look for delivery dates, pricing, and approval signatures.
    - Confidence threshold: >=0.85 to auto-route to Procurement.
    """,

    "unknown": """
    - Document type could not be determined with high confidence.
    - Route to Manual Review queue for human inspection.
    - No auto-routing allowed.
    """
}



class DocumentValidation(BaseModel):
    """
    Structured output for document classification validation.
    This model DOES NOT re-classify documents.
    """

    validated_label: Literal[
        "invoice",
        "contract",
        "w2_form",
        "medical_record",
        "insurance_claim",
        "purchase_order",
        "unknown"
    ] = Field(
        description="The label being validated. This must match the upstream classifier output."
    )

    classifier_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Original confidence score produced by the classifier."
    )

    validation_decision: Literal[
        "VALID",
        "WEAK",
        "INVALID"
    ] = Field(
        description="Validation result based on rule matching and contradictions."
    )

    matched_rules: List[str] = Field(
        description="Required rules that were clearly satisfied by the document."
    )

    missing_required_rules: List[str] = Field(
        description="Required rules that were expected but not found."
    )

    forbidden_rule_hits: List[str] = Field(
        description="Rules that should NOT appear for this document type but were detected."
    )

    justification: str = Field(
        description="Concise explanation referencing rules only. No reclassification."
    )

# Rules for Validating Documents
DOCUMENT_RULES = {
    "invoice": """
    - Should contain invoice number, vendor, and total amount.
    - Look for dates (issue/due), line items, and currency symbols.
    - Must clearly identify sender and recipient details.
    - Confidence threshold: >=0.8 to auto-route to Accounting.
    """,

    "contract": """
    - Should include parties involved, effective dates, and terms.
    - Look for legal clauses, signatures, and titles like 'Agreement' or 'Contract'.
    - Ensure the document is not a draft (check for 'DRAFT' watermark).
    - Confidence threshold: >=0.85 to auto-route to Legal.
    """,

    "w2_form": """
    - Must include employee name, SSN, and employer info.
    - Look for 'W-2' title, federal tax info, and wages.
    - Ensure all required fields are filled.
    - Confidence threshold: >=0.9 to auto-route to HR.
    """,

    "medical_record": """
    - Should contain patient info, medical history, and dates of service.
    - Look for headings like 'Diagnosis', 'Prescription', 'Lab Results'.
    - Ensure PHI compliance; anonymize if necessary.
    - Confidence threshold: >=0.8 to auto-route to Medical Records.
    """,

    "insurance_claim": """
    - Must include claim number, policy number, and claim type.
    - Look for accident dates, insured party, and supporting documents.
    - Ensure signatures or stamps are present if required.
    - Confidence threshold: >=0.8 to auto-route to Claims department.
    """,

    "purchase_order": """
    - Should include PO number, vendor info, and item list with quantities.
    - Look for delivery dates, pricing, and approval signatures.
    - Confidence threshold: >=0.85 to auto-route to Procurement.
    """,

    "unknown": """
    - Document type could not be determined with high confidence.
    - Route to Manual Review queue for human inspection.
    - No auto-routing allowed.
    """
}


RouteDecision = Literal[
    "ACCEPT",
    "RETRY_CLASSIFICATION",
    "RETRY_EXTRACTION",
    "HUMAN_REVIEW",
    "REJECT",
    "FAIL_PIPELINE",
]