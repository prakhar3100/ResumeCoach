import streamlit as st
import json
import io
from docx import Document
import pdfplumber
import os

# Import Groq SDK
from groq import Groq

st.set_page_config(page_title="ResumeCoach AI", layout="wide")
st.title("🎯 ResumeCoach AI")
st.subheader("Your AI-powered mentor for a perfect resume.")

# --- Load API key from Streamlit Secrets ---
groq_api_key = st.secrets.get("GROQ_API_KEY")
if not groq_api_key:
    st.error("❌ GROQ_API_KEY not found in Streamlit Secrets. Please add it and restart.")
    st.stop()

# --- Initialize Groq client ---
try:
    client = Groq(api_key=groq_api_key)
except Exception as e:
    st.error(f"Error initializing Groq client: {e}")
    st.stop()


# --- Helper functions ---
def get_resume_text(uploaded_file):
    """Extract text from PDF, DOCX, or TXT."""
    ext = uploaded_file.name.split('.')[-1].lower()

    if ext == "pdf":
        try:
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return None

    elif ext == "docx":
        try:
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            st.error(f"Error reading DOCX: {e}")
            return None

    else:  # TXT or other text-based
        try:
            return io.TextIOWrapper(uploaded_file, encoding='utf-8').read()
        except Exception as e:
            st.error(f"Error reading text file: {e}")
            return None


def get_ai_feedback(resume_text, job_description):
    """Get JSON feedback from Groq LLM."""
    system_prompt = """
You are an AI-powered resume coach. Analyze the resume and provide actionable feedback as a JSON object:
{
  "match_score": <0-100>,
  "summary": "<short positive summary>",
  "missing_keywords": ["<bullet1>", "<bullet2>"],
  "formatting_suggestions": ["<bullet1>", "<bullet2>"],
  "experience_improvements": ["<bullet1>", "<bullet2>"],
  "overall_tips": ["<bullet1>", "<bullet2>"]
}
"""
    user_prompt = f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}"

    try:
        # Use latest Groq endpoint
        response = client.completions.create(
            model="llama-3.1-8b-instant",
            input=f"{system_prompt}\n{user_prompt}"
        )

        feedback_str = response.output_text
        st.text_area("🛠️ Raw API Response (Feedback)", feedback_str, height=300)
        return json.loads(feedback_str)

    except json.JSONDecodeError as e:
        st.error(f"JSON decoding error: {e}")
        return None
    except Exception as e:
        st.error(f"API call error: {e}")
        return None


def create_optimized_draft(resume_text, job_description):
    """Generate optimized resume draft."""
    system_prompt = """
You are a professional resume writer. Rewrite the resume to match the job description.
Provide a markdown-formatted resume including:
- Name (bold)
- Contact info
- Professional Summary
- Experience (bullet points with keywords and quantified achievements)
- Skills
- Education
- Optional sections: Projects, Certifications, Awards
"""
    user_prompt = f"Original Resume:\n{resume_text}\n\nJob Description:\n{job_description}"

    try:
        response = client.completions.create(
            model="llama-3.1-8b-instant",
            input=f"{system_prompt}\n{user_prompt}"
        )

        draft = response.output_text
        st.text_area("🛠️ Raw API Response (Draft)", draft, height=300)
        return draft

    except Exception as e:
        st.error(f"API call error: {e}")
        return None


# --- Streamlit UI ---
st.markdown("Upload your resume and paste a job description. AI will provide feedback and an optimized draft.")

col1, col2 = st.columns(2)

with col1:
    uploaded_resume = st.file_uploader("Upload your resume", type=["pdf","docx","txt"])

with col2:
    job_description = st.text_area("Paste Job Description here", height=300)

col_buttons = st.columns(2)

with col_buttons[0]:
    if st.button("✨ Get My Feedback"):
        if not uploaded_resume or not job_description:
            st.warning("Upload a resume and paste a job description first.")
        else:
            with st.spinner("Analyzing resume..."):
                text = get_resume_text(uploaded_resume)
                if text:
                    feedback = get_ai_feedback(text, job_description)

            if feedback:
                st.markdown("---")
                st.header("📋 Personalized Feedback")
                st.metric("Resume Match Score", f"{feedback.get('match_score',0)}%")
                st.success(f"*Summary:* {feedback.get('summary','No summary')}")
                for section, title in [("missing_keywords", "🔑 Missing Keywords & Skills"),
                                       ("formatting_suggestions", "📝 Formatting & Clarity"),
                                       ("experience_improvements", "🚀 Experience Improvements"),
                                       ("overall_tips", "✨ Overall Tips")]:
                    st.markdown(f"### {title}")
                    for item in feedback.get(section, []):
                        st.write(f"• {item}")
                st.balloons()

with col_buttons[1]:
    if st.button("📝 Create Optimized Draft"):
        if not uploaded_resume or not job_description:
            st.warning("Upload a resume and paste a job description first.")
        else:
            with st.spinner("Creating optimized draft..."):
                text = get_resume_text(uploaded_resume)
                if text:
                    draft = create_optimized_draft(text, job_description)

            if draft:
                st.markdown("---")
                st.header("✍️ Optimized Resume Draft")
                st.info("Review and personalize before using!")
                st.markdown(draft)
                st.download_button("Download as Markdown", draft, file_name="optimized_resume.md", mime="text/markdown")
