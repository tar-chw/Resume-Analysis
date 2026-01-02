import streamlit as st
import os
import time
import json
import pandas as pd
import tempfile 
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load env var from .env
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# --- CORE FUNCTION ---
def analyze_resume(file_bytes, job_desc):
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    temp_path = None

    try:
        # use tempfile to save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes.getbuffer())
            temp_path = tmp.name  # เก็บ Path ไว้ใช้และลบทีหลัง

        # upload
        file_upload = client.files.upload(file=temp_path)
        
        # process loop
        while file_upload.state.name == "PROCESSING":
            time.sleep(1)
            file_upload = client.files.get(name=file_upload.name)
        
        if file_upload.state.name == "FAILED":
            return {"error": "File upload failed"}

        # prompt
        prompt_text = f"""
        Act as an Expert Technical Recruiter.
        Analyze the attached Resume PDF against the provided Job Description.
        
        JOB DESCRIPTION:
        {job_desc}
        
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

        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=[file_upload, prompt_text],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)

    except Exception as e:
        return {"error": str(e)}
        
    finally:
        # 4. Cleanup: ลบไฟล์ temp ทิ้งเสมอ ไม่ว่าจะ error หรือไม่
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# STREAMLIT UI
st.set_page_config(page_title="AI Resume Screener", layout="wide")

st.title("📄 Resume Analysis AI")
st.markdown("เครื่องมือวิเคราะห์และให้คะแนน Resume ตาม Job Description")

# Inputs
with st.sidebar:
    st.header("1. Job Description")
    job_description = st.text_area("รายละเอียดงาน", height=300, placeholder="Position: Data Scientist...")
    
    st.header("2. Upload Resumes")
    uploaded_files = st.file_uploader("อัพโหลดไฟล์ PDF", type=["pdf"], accept_multiple_files=True)
    
    process_btn = st.button("Start Analysis / เริ่มวิเคราะห์ ", type="primary")

# Results
if process_btn and job_description and uploaded_files:
    st.info(f"Processing {len(uploaded_files)} file(s)")
    
    results = []
    progress_bar = st.progress(0)
    
    for i, uploaded_file in enumerate(uploaded_files):
        st.toast(f"reading {uploaded_file.name}")
        
        data = analyze_resume(uploaded_file, job_description)
        
        if "error" not in data:
            results.append({
                "File Name": uploaded_file.name,
                "Candidate Name": data.get("candidate_name", "Unknown"),
                "Total Score": data.get("total_score", 0),
                "Skills Score": data["analysis"]["skills"]["score"],
                "Summary": data.get("summary", ""),
                # For detailed view
                "Exp Score": data["analysis"]["experience_education"]["score"],
                "Know Score": data["analysis"]["knowledge"]["score"],
                "Tools Score": data["analysis"]["tools"]["score"],
                "Full Data": data 
            })
        else:
            st.error(f"Error analyzing {uploaded_file.name}: {data['error']}")
        
        progress_bar.progress((i + 1) / len(uploaded_files))

    st.success("Done!")
    st.divider()
    
    if results:
        # Create DataFrame
        df = pd.DataFrame(results)
        df = df.sort_values(by="Total Score", ascending=False)
        
        # Highlight High Scores
        def highlight_score(val):
            color = 'green' if val >= 80 else 'orange' if val >= 50 else 'red'
            return f'color: {color}; font-weight: bold'

        # Show Table
        st.subheader("Results Summary")
        
        # Apply highlighting
        st.dataframe(
            df[["Candidate Name", "Total Score", "Skills Score", "Summary"]]
            .style.applymap(highlight_score, subset=['Total Score', 'Skills Score']),
            use_container_width=True
        )

        # Export Button
        col_dl1, col_dl2 = st.columns([1, 4])
        with col_dl1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name='resume_analysis_results.csv',
                mime='text/csv',
            )
        
        # Detailed View
        st.subheader("Detailed Analysis per Candidate")
        for index, row in df.iterrows():
            with st.expander(f"Rank {index+1}: {row['Candidate Name']} (Total: {row['Total Score']})"):
                col1, col2 = st.columns(2)
                analysis = row["Full Data"]["analysis"]
                
                with col1:
                    st.markdown(f"Skills ({analysis['skills']['score']}/100):")
                    st.info(analysis['skills']['reasoning'])
                    
                    st.markdown(f"Experience ({analysis['experience_education']['score']}/100):")
                    st.write(analysis['experience_education']['reasoning'])
                    
                with col2:
                    st.markdown(f"Knowledge ({analysis['knowledge']['score']}/100):")
                    st.write(analysis['knowledge']['reasoning'])

                    st.markdown(f"Tools ({analysis['tools']['score']}/100):")
                    st.write(analysis['tools']['reasoning'])