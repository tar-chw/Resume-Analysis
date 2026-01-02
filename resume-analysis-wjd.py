import os
import time
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# 1. ใส่ API Key
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# 2. จำลอง Job Description (เป้าหมายที่เรามองหา)
# คุณสามารถเปลี่ยนข้อความตรงนี้เพื่อทดสอบเกณฑ์รับคนต่างๆ ได้
target_job_description = """
Position: AI & Data Solution Internship
Responsibilities
ทำงานร่วมกับผู้ใช้งานหรือทีมพัฒนาธุรกิจ เพื่อรวบรวมและทำความเข้าใจความต้องการของระบบ
ออกแบบ พัฒนา และปรับแต่งคำสั่ง prompt เพื่อเพิ่มประสิทธิภาพการทำงานของ AI
ออกแบบโครงสร้างระบบ กระบวนการทำงาน และการใช้งานของ AI application
ใช้ Large Language Models (LLMs) เพื่อพัฒนา AI application
ทดสอบการทำงานและประเมินประสิทธิภาพของ AI application
ทำงานร่วมกับทีมวิศวกรซอฟต์แวร์อย่างใกล้ชิด เพื่อนำ AI application ไปใช้ในระบบจริง

Qualifications
ชำนาญในการเขียนโปรแกรมด้วย Python, prompt engineering, และ context engineering
มีทักษะในการคิดวิเคราะห์และแก้ไขปัญหาได้อย่างดีเยี่ยม
มีความสนใจในด้าน AI ระบบอัตโนมัติ (automation) และ data-driven solutions
มีความเข้าใจพื้นฐานเกี่ยวกับการ Natural Language Processing - NLP และแนวคิดของ machine learning
มีประสบการณ์ในการทำงานกับ API, JSON หรือ automation pipelines
หากมีประสบการณ์การใช้งานเครื่องมือหรือเทคโนโลยี เช่น n8n, SQL, Docker หรือ แพลตฟอร์ม Cloud จะได้รับการพิจารณาเป็นพิเศษ
"""

def analyze_resume_matching(file_path, job_desc):
    print(f"--- Matching Resume with Job Description ---")
    
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    # Upload File
    try:
        print("Uploading file...")
        file_upload = client.files.upload(file=file_path)
        
        while file_upload.state.name == "PROCESSING":
            time.sleep(1)
            file_upload = client.files.get(name=file_upload.name)

        if file_upload.state.name == "FAILED":
            print("File upload failed.")
            return

    except Exception as e:
        print(f"Upload Error: {e}")
        return

    # --- Prompt ที่ปรับปรุงเพื่อการให้คะแนน ---
    prompt_text = f"""
    Act as an Expert Technical Recruiter.
    
    YOUR GOAL:
    Analyze the attached Resume PDF against the provided Job Description.
    
    JOB DESCRIPTION:
    {job_desc}
    
    INSTRUCTIONS:
    1. Extract relevant information from the resume correctly (ignoring layout issues).
    2. Evaluate the candidate based on 4 criteria:
       - Experience/Education (Matches years of experience and degree?)
       - Skills (Matches programming languages and tech stack?)
       - Knowledge (Domain knowledge, concepts, e.g., RAG, LLMs?)
       - Tools (Specific tools used e.g., FAISS, Git, Docker?)
    3. Provide a Score (0-100) for each criteria.
    4. Provide specific Reasoning (Thai Language) why you gave that score.
    
    OUTPUT FORMAT (JSON Only):
    {{
        "candidate_name": "String",
        "total_score": Integer (Average of 4 criteria),
        "analysis": {{
            "experience_education": {{ "score": Integer, "reasoning": "String (Thai)" }},
            "skills": {{ "score": Integer, "reasoning": "String (Thai)" }},
            "knowledge": {{ "score": Integer, "reasoning": "String (Thai)" }},
            "tools": {{ "score": Integer, "reasoning": "String (Thai)" }}
        }},
        "summary": "String (Thai summary of fit)"
    }}
    """

    print("Analyzing matching score...")
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[file_upload, prompt_text],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # แสดงผลลัพธ์
        print("\n" + "="*30)
        # จัดรูปแบบ JSON ให้สวยงามอ่านง่าย
        parsed_json = json.loads(response.text)
        print(json.dumps(parsed_json, indent=4, ensure_ascii=False))
        print("="*30)
        
    except Exception as e:
        print(f"Generation Error: {e}")

# --- RUN ---
file_path = "/Users/tartartar/Resume-Analysis/ChewinGrerasitsirt_Resume.pdf"
analyze_resume_matching(file_path, target_job_description)