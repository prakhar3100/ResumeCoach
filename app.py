import streamlit as st
import json
import io
import os
import requests
from dotenv import load_dotenv
from docx import Document
import pdfplumber

# --- Load environment variables ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Fallback: Streamlit Cloud secrets
if not api_key:
    api_key = st.secrets.get("GROQ_API_KEY", None)

# --- Streamlit Page Config ---
st.set_page_config(page_title="ResumeCoach AI", layout="wide")
st.title("🎯 ResumeCoach AI")
st.subheader("Your AI-powered mentor for a perfect resume.")

# Check API Key
if api_key:
    st.success("🔑 API key loaded successfully!")
else:
    st.error("❌ API key not found! Set GROQ_API_KEY in `.env` or Streamlit Secrets.")
    st.stop()


# ---------------- File Processing ----------------
def get_resume_text(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext == ".pdf":
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                return "\n".join([page.extract_text() or "" for page in pdf.pages])
        except Exception as e:
            st.error(f"PDF reading error: {e}")
            return None
    elif ext == ".docx":
        try:
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            st.error(f"DOCX reading error: {e}")
            return None
    else:
        try:
            return io.TextIOWrapper(uploaded_file, encoding="utf-8").read()
        except Exception as e:
            st.error(f"Text reading error: {e}")
            return None


# ---------------- Groq API Call ----------------
def call_groq_api(prompt, model="llama-3.1-8b-instant"):
    """
    Make a direct request to Groq's chat completions API using requests.
    """
    url = "https://api.groq.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"API call error: {e}")
        return None


# ---------------- AI Feedback ----------------
def get_ai_feedback(resume_text, job_description):
    system_prompt = f"""
You are an AI resume coach. Analyze this resume against the job description and return a JSON object:
{{
  "match_score": <0-100>,
  "summary": "<Short positive summary>",
  "missing_keywords": ["<Bullet point>"],
  "formatting_suggestions": ["<Bullet point>"],
  "experience_improvements": ["<Bullet point>"],
  "overall_tips": ["<Bullet point>"]
}}

Resume:
---
{resume_text}
---

Job Description:
---
{job_description}
---
"""
    result = call_groq_api(system_prompt)
    if result:
        st.text_area("🛠️ Raw API Response", result, height=300)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            st.error("API returned invalid JSON.")
            return None
    return None


# ---------------- Draft Resume ----------------
def create_optimized_draft(resume_text, job_description):
    system_prompt = f"""
Rewrite the resume in Markdown format, optimized for this job description:

Original Resume:
---
{resume_text}
---

Job Description:
---
{job_description}
---
"""
    draft = call_groq_api(system_prompt)
    if draft:
        st.text_area("🛠️ Raw API Response (Draft)", draft, height=300)
        return draft
    return None


# ---------------- Streamlit UI ----------------
st.markdown("Upload your resume and paste a job description. AI will provide feedback and generate a draft.")

col1, col2 = st.columns(2)
with col1:
    uploaded_resume = st.file_uploader("Upload your resume", type=["pdf","docx","txt"])

with col2:
    job_description = st.text_area("Paste Job Description", height=300)

col_buttons = st.columns(2)

with col_buttons[0]:
    if st.button("✨ Get My Feedback"):
        if not uploaded_resume or not job_description:
            st.warning("Upload resume and paste job description first.")
        else:
            with st.spinner("Analyzing..."):
                resume_text = get_resume_text(uploaded_resume)
                if resume_text:
                    feedback = get_ai_feedback(resume_text, job_description)

            if feedback:
                st.markdown("---")
                st.header("📋 Personalized Feedback")
                st.metric("Match Score", f"{feedback.get('match_score', 0)}%")
                st.success(f"Summary: {feedback.get('summary', '')}")
                for section, items in [
                    ("Missing Keywords & Skills", feedback.get("missing_keywords", [])),
                    ("Formatting Suggestions", feedback.get("formatting_suggestions", [])),
                    ("Experience Improvements", feedback.get("experience_improvements", [])),
                    ("Overall Tips", feedback.get("overall_tips", []))
                ]:
                    st.markdown(f"### {section}")
                    for item in items:
                        st.write(f"• {item}")
                st.balloons()

with col_buttons[1]:
    if st.button("📝 Create Optimized Draft"):
        if not uploaded_resume or not job_description:
            st.warning("Upload resume and paste job description first.")
        else:
            with st.spinner("Creating draft..."):
                resume_text = get_resume_text(uploaded_resume)
                if resume_text:
                    draft = create_optimized_draft(resume_text, job_description)

            if draft:
                st.markdown("---")
                st.header("✍️ Optimized Resume Draft")
                st.info("Review and personalize before use.")
                st.markdown(draft)
                st.download_button("Download Draft", draft, file_name="optimized_resume.md", mime="text/markdown")
