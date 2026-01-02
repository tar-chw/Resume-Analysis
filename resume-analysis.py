import os
import time
from google import genai
from google.genai import types

# 1. ใส่ API Key ของคุณตรงนี้
os.environ["GOOGLE_API_KEY"] = "AIzaSyB8nOkqgaHHJRAA5GV-ptxJZ26lq9LTKyI"

def analyze_resume_new_sdk(file_path):
    print(f"--- Processing: {file_path} ---")

    # 2. สร้าง Client
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    # 3. Upload File
    try:
        print("Uploading file to Gemini...")
        
        # --- จุดที่แก้ไข (เปลี่ยน path เป็น file) ---
        file_upload = client.files.upload(file=file_path)
        
        print(f"Uploaded: {file_upload.name}")
        
        # รอให้ไฟล์พร้อมใช้งาน
        while file_upload.state.name == "PROCESSING":
            print("Waiting for file processing...")
            time.sleep(2)
            file_upload = client.files.get(name=file_upload.name)

        if file_upload.state.name == "FAILED":
            print("File upload failed.")
            return

    except Exception as e:
        print(f"Upload Error: {e}")
        return

    # 4. Prompt
    prompt_text = """
    Analyze this resume strictly based on the visible layout.
    
    Role: Senior Technical Recruiter.
    Task: Extract and Analyze the resume content.
    
    Output Format: JSON only.
    Structure:
    {
        "candidate_info": { "name": "", "email": "", "phone": "" },
        "education": [ {"institution": "", "year": "", "degree": ""} ],
        "experience": [ {"role": "", "company": "", "duration": "", "details": ""} ],
        "skills": [],
        "projects": [],
        "summary_analysis": "Give a short comment on this candidate strengths"
    }
    """

    # 5. Generate Content
    print("Analyzing content...")
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[file_upload, prompt_text],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # 6. แสดงผล
        print("\n" + "="*30)
        print(response.text)
        print("="*30)
        
    except Exception as e:
        print(f"Generation Error: {e}")

# --- RUN ---
file_path = "/Users/tartartar/Resume-Analysis/ChewinGrerasitsirt_Resume.pdf"
analyze_resume_new_sdk(file_path)