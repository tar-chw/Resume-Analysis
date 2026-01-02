import streamlit as st
import os
import time
import json
import pandas as pd
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load env var from .env
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Core function
def analyze_resume(file_bytes, job_desc):
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    try:
        # we have to save a file (be a temporary file) because the SDK expects a file path or file-like object
        
        temp_filename = "temp_resume.pdf"
        with open(temp_filename, "wb") as f:
            f.write(file_bytes.getbuffer())

        file_upload = client.files.upload(file=temp_filename)
        
        # Process
        while file_upload.state.name == "PROCESSING":
            time.sleep(1)
            file_upload = client.files.get(name=file_upload.name)
        
        if file_upload.state.name == "FAILED":
            return {"error": "File upload failed"}

    except Exception as e:
        return {"error": str(e)}

    # Prompt
    prompt_text = f"""
    Act as an Expert Technical Recruiter.
    Analyze the attached Resume PDF against the provided Job Description.
    
    JOB DESCRIPTION:
    {job_desc}
    
    # 4 parts to evaluate:
    INSTRUCTIONS:
    Evaluate based on 4 criteria: Experience, Skills, Knowledge, Tools.
    Provide Score (0-100) and Thai Reasoning.
    
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

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest", # หรือ gemini-flash-latest
            contents=[file_upload, prompt_text],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        # Clean up temp file (optional)
        # os.remove(temp_filename) 
        
        return json.loads(response.text)
        
    except Exception as e:
        return {"error": str(e)}

# --- STREAMLIT UI ---
st.set_page_config(page_title="AI Resume Screener", layout="wide")

st.title("Resume Analysis")
st.write("เครื่องมือช่วยวิเคราะห์ Resume")

# Inputs
with st.sidebar:
    st.header("1. Job Description")
    job_description = st.text_area("รายละเอียดเกี่ยวกับตำแหน่งงาน", height=300)
    
    st.header("2. Upload Resumes")
    uploaded_files = st.file_uploader("อัพโหลดไฟล์ PDF", type=["pdf"], accept_multiple_files=True)
    
    process_btn = st.button("เริ่มวิเคราะห์", type="primary")

# Results
if process_btn and job_description and uploaded_files:
    st.success(f"กำลังวิเคราะห์ {len(uploaded_files)} ไฟล์")
    
    results = []
    progress_bar = st.progress(0)
    
    for i, uploaded_file in enumerate(uploaded_files):
        # show current status
        st.toast(f"กำลังวิเคราะห์: {uploaded_file.name}")
        
        # call function AI
        data = analyze_resume(uploaded_file, job_description)
        
        if "error" not in data:
            # store results in list to make a table later
            results.append({
                "File Name": uploaded_file.name,
                "Candidate Name": data.get("candidate_name", "Unknown"),
                "Total Score": data.get("total_score", 0),
                "Skills Score": data["analysis"]["skills"]["score"],
                "Summary": data.get("summary", ""),
                "Full Data": data # เก็บ Raw Data ไว้ดูละเอียด
            })
        else:
            st.error(f"Error analyzing {uploaded_file.name}: {data['error']}")
        
        # Update Progress Bar
        progress_bar.progress((i + 1) / len(uploaded_files))

    # show the results
    st.divider()
    
    if results:
        # convert to DataFrame 
        df = pd.DataFrame(results)
        
        # sort by Total Score
        df = df.sort_values(by="Total Score", ascending=False)
        
        # show summary table
        st.subheader("ตารางอันดับผู้สมัคร")
        st.dataframe(
            df[["Candidate Name", "Total Score", "Skills Score", "Summary"]],
            use_container_width=True,
            hide_index=True
        )

        # show detailed information
        st.subheader("รายละเอียดข้อมูล")
        for index, row in df.iterrows():
            with st.expander(f"{row['Candidate Name']} (Score: {row['Total Score']})"):
                col1, col2 = st.columns(2)

                # get analysis data
                analysis = row["Full Data"]["analysis"]
                
                with col1:
                    st.markdown(f"**Skills ({analysis['skills']['score']}/100):**\n{analysis['skills']['reasoning']}")
                    st.markdown(f"**Experience ({analysis['experience_education']['score']}/100):**\n{analysis['experience_education']['reasoning']}")
                with col2:
                    st.markdown(f"**Knowledge ({analysis['knowledge']['score']}/100):**\n{analysis['knowledge']['reasoning']}")
                    st.markdown(f"**Tools ({analysis['tools']['score']}/100):**\n{analysis['tools']['reasoning']}")