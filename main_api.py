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
    job_desc: str = Form(...),
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
        Act as an Expert Technical Recruiter.
        Analyze the attached Resume PDF against the provided Job Description.
        
        JOB DESCRIPTION:
        {job_desc}
        
        INSTRUCTIONS:
        1. Extract relevant information from the resume correctly.
        2. Evaluate the candidate based on 4 criteria: Experience, Skills, Knowledge, Tools.
        3. Provide a Score (0-100) for each criteria.
        4. Provide Reasoning:
       - Detect the language used in the JOB DESCRIPTION.
       - WRITE THE REASONING IN THE SAME LANGUAGE as the Job Description.
        
        OUTPUT FORMAT (JSON Only):
        {{
            "candidate_name": "String",
            "total_score": Integer,
            "analysis": {{
                "experience_education": {{ "score": Integer, "reasoning": "String" }},
                "skills": {{ "score": Integer, "reasoning": "String" }},
                "knowledge": {{ "score": Integer, "reasoning": "String" }},
                "tools": {{ "score": Integer, "reasoning": "String" }}
            }},
            "summary": "String"
        }}
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