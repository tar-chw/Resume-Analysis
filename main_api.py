from fastapi import FastAPI, UploadFile, File, Form
from google import genai
from google.genai import types
import os
import tempfile
import json
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

@app.post("/analyze")
async def analyze_resume_api(
    job_description: str = Form(...),
    file: UploadFile = File(...)
):
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    
    # Save Temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name

    try:
        # Upload & Process
        file_upload = client.files.upload(file=temp_path)
        
        prompt = f"""
        Act as Expert Recruiter. Analyze Resume against JD: {job_description}
        Output JSON with scores for Experience, Skills, Knowledge, Tools.
        """
        
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[file_upload, prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
        
    finally:
        os.remove(temp_path)

# Run with: uvicorn main_api:app --reload