from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from state import DocumentClassification, TriageState
from unstructured.partition.pdf import partition_pdf  # optional OCR if needed
from langchain_classic.schema import Document
import tempfile as tf
import os

def run_ocr(path: str) -> str:
    """
    Simple OCR fallback using unstructured or any OCR library.
    Returns the full extracted text as a string.
    """
    try:
        elements = partition_pdf(filename=path)
        text = "\n".join([el.text for el in elements if hasattr(el, "text")])
        return text
    except Exception as e:
        print(f"OCR failed: {e}")
        return ""  # empty fallback if OCR completely fails


def file_extraction_workflow(path: str) -> list[Document]:
    """
    Extracts text from a PDF and splits it into Document chunks.
    Falls back to OCR if PDF text extraction fails or produces too little text.
    """
    # Save the file as a temporary PDF
    with open(path, 'rb') as f:
        data = f.read()

    with tf.NamedTemporaryFile(suffix='.pdf', mode='wb', delete=True) as tmp_file:
        tmp_file.write(data)
        tmp_path = tmp_file.name

        # 1️⃣ Attempt normal PDF text extraction
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()

        # Combine all text to check if extraction was successful
        full_text = "\n".join([doc.page_content for doc in documents])
        if len(full_text.strip()) < 20:
            # 2️⃣ Fallback to OCR if too little text
            print("PDF text extraction too low, running OCR fallback...")
            ocr_text = run_ocr(tmp_path)
            if not ocr_text.strip():
                raise ValueError("OCR failed: document could not be read")
            # Wrap OCR text into a single Document
            documents = [Document(page_content=ocr_text)]

    # 3️⃣ Split documents into chunks for classification
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    return splitter.split_documents(documents)


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
                    content=system_prompt
                ),
                HumanMessage(content=state['document_content'])  # Full content
            ]
        )
        
        # Used to show ambiguity if present in pass 2
        ambiguous = (
            detailed_classification.confidence < 0.8 or 
            len(detailed_classification.alternative_types) > 1
        )
        
        return {
            "document_type": detailed_classification.document_type,
            "confidence_score": detailed_classification.confidence,
            "ambiguous": ambiguous,
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
    builder.add_edge("classify", END)

    return builder.compile()


def classify_docs(file_path,llm, system_prompt, input: TriageState):
    # Loading Document Splits of the File
    doc_splits = file_extraction_workflow(path=file_path)
    
    # Creating the Agentic Workflow
    agent = create_classificatioN_workflow(llm, system_prompt)
    
    # Putting the splits in document_content
    input['document_content'] = input['document_content'] = "\n".join([doc.page_content for doc in doc_splits])
    
    return agent.invoke(input=input)


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