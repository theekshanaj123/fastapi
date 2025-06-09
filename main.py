from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
from openai import OpenAI

app = FastAPI()

# Initialize OpenAI client
client = OpenAI(
    api_key="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"
)

def generate_quiz_from_chunk(chunk: str) -> str:
    prompt = f"""Read the following text and generate 3 quiz questions with answers:

\"\"\"{chunk}\"\"\"

Format:
1. Question
   - a. Option
   - b. Option
   - c. Option
   - d. Option
Answer: [correct letter]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a helpful quiz generation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating quiz: {str(e)}"


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()  # Close the document to free memory
    return text

def chunk_text(text: str, max_chars: int = 500) -> list:
    """Chunk text into pieces no longer than `max_chars`."""
    import re
    paragraphs = re.split(r'\n\s*\n', text)  # Split by empty lines
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chars:
            current_chunk += para + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return JSONResponse(content={"error": "Only PDF files allowed."}, status_code=400)

    file_bytes = await file.read()
    try:
        text = extract_text_from_pdf(file_bytes)
        chunks = chunk_text(text)
        return {"filename": file.filename, "chunks": chunks}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    

@app.post("/upload-pdf-with-quiz/")
async def upload_pdf_with_quiz(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return JSONResponse(content={"error": "Only PDF files allowed."}, status_code=400)

    try:
        file_bytes = await file.read()
        text = extract_text_from_pdf(file_bytes)
        chunks = chunk_text(text)
        
        quiz_results = []
        print("Processing chunks for quiz generation...")
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}")
            questions = generate_quiz_from_chunk(chunk)
            quiz_results.append(questions)
        
        return {
            "filename": file.filename,
            "quiz": quiz_results
        }
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)