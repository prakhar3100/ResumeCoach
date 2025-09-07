import streamlit as st
import json
import io
import os
from dotenv import load_dotenv
from docx import Document
import pdfplumber
import openai

# --- Load environment variables ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="ResumeCoach AI", layout="wide")
st.title("🎯 ResumeCoach AI")
st.subheader("Your AI-powered mentor for a perfect resume.")

# Check API key
if not api_key:
    st.error("❌ API key not found! Please set GROQ_API_KEY in your .env file or Streamlit secrets.")
    st.stop()

# Initialize OpenAI client for Groq API
openai.api_key = api_key
openai.api_base = "https://api.groq.com/openai/v1"

# --- Functions ---
def get_resume_text(uploaded_file):
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_extension == '.pdf':
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading PDF file: {e}")
            return None

    elif file_extension == '.docx':
        try:
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            st.error(f"Error reading DOCX file: {e}")
            return None

    else:
        try:
            return io.TextIOWrapper(uploaded_file, encoding='utf-8').read()
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return None

def get_ai_feedback(resume_text, job_description):
    system_prompt = """
    You are an AI-powered resume and career coach. Analyze a resume based on a job description and provide actionable feedback in this JSON format:
    {
      "match_score": <0-100>,
      "summary": "<short positive summary>",
      "missing_keywords": ["<suggestion1>", "<suggestion2>"],
      "formatting_suggestions": ["<suggestion1>", "<suggestion2>"],
      "experience_improvements": ["<suggestion1>", "<suggestion2>"],
      "overall_tips": ["<suggestion1>", "<suggestion2>"]
    }
    """
    user_prompt = f"""
    Resume:
    ---
    {resume_text}
    ---
    
    Job Description:
    ---
    {job_description}
    ---
    """
    try:
        response = openai.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        feedback_json_str = response.choices[0].message.content
        st.text_area("🛠️ Raw API Response (Feedback)", feedback_json_str, height=300)
        return json.loads(feedback_json_str)
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON decoding error: {e}")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def create_optimized_draft(resume_text, job_description):
    system_prompt = """
    You are a professional resume writer. Rewrite a resume optimized for the given job description. Respond only with a Markdown-formatted resume.
    """
    user_prompt = f"""
    Original Resume:
    ---
    {resume_text}
    ---
    
    Job Description:
    ---
    {job_description}
    ---
    """
    try:
        response = openai.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        draft = response.choices[0].message.content
        st.text_area("🛠️ Raw API Response (Draft)", draft, height=300)
        return draft
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# --- Streamlit UI ---
st.markdown("Upload your resume and paste a job description. The AI will provide feedback and an optimized draft.")

col1, col2 = st.columns(2)
with col1:
    uploaded_resume = st.file_uploader("Upload your resume", type=["pdf","txt","docx"])
with col2:
    job_description = st.text_area("Paste Job Description", height=300)

col_buttons = st.columns(2)
with col_buttons[0]:
    if st.button("✨ Get My Feedback"):
        if not uploaded_resume or not job_description:
            st.warning("Upload resume and job description first.")
        else:
            with st.spinner("Analyzing..."):
                resume_text = get_resume_text(uploaded_resume)
                if resume_text:
                    feedback = get_ai_feedback(resume_text, job_description)
            if feedback:
                st.header("📋 Personalized Feedback")
                st.metric("Resume Match Score", f"{feedback.get('match_score',0)}%")
                st.success(f"Summary: {feedback.get('summary','No summary')}")
                st.markdown("### 🔑 Missing Keywords")
                for item in feedback.get("missing_keywords", []): st.write(f"• {item}")
                st.markdown("### 📝 Formatting Suggestions")
                for item in feedback.get("formatting_suggestions", []): st.write(f"• {item}")
                st.markdown("### 🚀 Experience Improvements")
                for item in feedback.get("experience_improvements", []): st.write(f"• {item}")
                st.markdown("### ✨ Overall Tips")
                for item in feedback.get("overall_tips", []): st.write(f"• {item}")
                st.balloons()

with col_buttons[1]:
    if st.button("📝 Create Optimized Draft"):
        if not uploaded_resume or not job_description:
            st.warning("Upload resume and job description first.")
        else:
            with st.spinner("Creating optimized draft..."):
                resume_text = get_resume_text(uploaded_resume)
                if resume_text:
                    draft = create_optimized_draft(resume_text, job_description)
            if draft:
                st.header("✍️ Optimized Resume Draft")
                st.info("Review and personalize before using.")
                st.markdown(draft)
                st.download_button("Download Draft", draft, "optimized_resume_draft.md", "text/markdown")
