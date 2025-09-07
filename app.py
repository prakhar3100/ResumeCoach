# app.py
import os
import streamlit as st
from dotenv import load_dotenv
import openai
from groq import Groq
import pdfplumber
from docx import Document

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ----------------------------
# Initialize APIs
# ----------------------------
openai.api_key = OPENAI_API_KEY
groq_client = Groq(api_key=GROQ_API_KEY)

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="🎯 ResumeCoach AI", layout="wide")
st.title("🎯 ResumeCoach AI")
st.subheader("Your AI-powered mentor for a perfect resume.")

# ----------------------------
# Resume Upload
# ----------------------------
resume_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

resume_text = ""
if resume_file:
    if resume_file.type == "application/pdf":
        with pdfplumber.open(resume_file) as pdf:
            for page in pdf.pages:
                resume_text += page.extract_text() + "\n"
    elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(resume_file)
        for para in doc.paragraphs:
            resume_text += para.text + "\n"

st.text_area("Your Resume Text", value=resume_text, height=200)

# ----------------------------
# Job Role Input
# ----------------------------
job_role = st.text_input("Enter target job role", "")

# ----------------------------
# Generate Feedback
# ----------------------------
if st.button("Get AI Feedback"):
    if not resume_text or not job_role:
        st.warning("Please upload your resume and enter a job role.")
    else:
        with st.spinner("Generating feedback..."):
            # ---------- OpenAI Feedback ----------
            try:
                openai_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a resume coach AI."},
                        {"role": "user", "content": f"Review this resume for a {job_role} role:\n\n{resume_text}"}
                    ],
                    max_tokens=500
                )
                feedback_openai = openai_response.choices[0].message.content
                st.subheader("OpenAI Feedback")
                st.write(feedback_openai)
            except Exception as e:
                st.error(f"OpenAI API Error: {e}")

            # ---------- Groq Feedback ----------
            try:
                # Example Groq query – modify as needed
                groq_query = f"Analyze this resume for a {job_role} role:\n{resume_text}"
                groq_result = groq_client.query(groq_query)
                st.subheader("Groq Feedback")
                st.write(groq_result)
            except Exception as e:
                st.error(f"Groq API Error: {e}")

# ----------------------------
# API Key Test (Optional)
# ----------------------------
if st.checkbox("Test API Keys"):
    try:
        openai.Model.list()
        st.success("✅ OpenAI API key is valid!")
    except Exception as e:
        st.error(f"❌ OpenAI error: {e}")

    try:
        groq_client.health()
        st.success("✅ Groq API key is valid!")
    except Exception as e:
        st.error(f"❌ Groq error: {e}")
