import streamlit as st
import json
import io
import os
from groq import Groq
import pdfplumber
from dotenv import load_dotenv
from docx import Document
import re

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="ResumeCoach AI", layout="wide")
st.title("🎯 ResumeCoach AI")
st.subheader("Your AI-powered mentor for a perfect resume.")

# Check API key
if groq_api_key:
    st.success("🔑 API key loaded successfully!")
else:
    st.error("❌ API key not found! Please set GROQ_API_KEY in your .env file.")
    st.stop()

# Initialize Groq client
try:
    client = Groq(api_key=groq_api_key)
except Exception as e:
    st.error(f"Error initializing Groq client: {e}")
    st.stop()

# ----------------------------
# Helper functions
# ----------------------------
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
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            st.error(f"Error reading DOCX file: {e}")
            return None

    else:  # TXT or other text-based formats
        try:
            return io.TextIOWrapper(uploaded_file, encoding='utf-8').read()
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return None

def sanitize_json(raw_text):
    """Remove accidental characters that break JSON"""
    return re.sub(r'\)\s*([\],])', r'\1', raw_text)

def get_ai_feedback(resume_text, job_description):
    system_prompt = """
    You are an AI-powered resume and career coach. Your task is to analyze a resume based on a provided job description and offer actionable, constructive feedback.

    Return a single JSON object with keys:
    match_score, summary, missing_keywords, formatting_suggestions, experience_improvements, overall_tips.
    """

    user_prompt = f"""
Resume:
{resume_text}

Job Description:
{job_description}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        feedback_json_str = response.choices[0].message.content
        st.text_area("🛠️ Raw API Response (Feedback)", feedback_json_str, height=300)

        cleaned = sanitize_json(feedback_json_str)
        return json.loads(cleaned)

    except json.JSONDecodeError as e:
        st.error(f"❌ JSON decoding error: {e}")
        st.error("The API response was not valid JSON. See raw response above.")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def create_optimized_draft(resume_text, job_description):
    system_prompt = """
    You are a world-class professional resume writer. Rewrite a resume to be highly optimized for a specific job description.
    Return a single markdown-formatted resume draft.
    """

    user_prompt = f"""
Original Resume:
{resume_text}

Job Description:
{job_description}
"""

    try:
        response = client.chat.completions.create(
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

# ----------------------------
# Streamlit UI
# ----------------------------
st.markdown("""
Upload your resume and paste a job description. Our AI will provide tailored feedback and generate an optimized resume draft.
""")

col1, col2 = st.columns(2)

with col1:
    uploaded_resume = st.file_uploader(
        "Upload your resume",
        type=["pdf", "txt", "docx"],
        help="Accepted formats: PDF, TXT, DOCX"
    )

with col2:
    job_description = st.text_area(
        "Paste the Job Description here",
        height=300,
        placeholder="E.g., 'We are looking for a Data Scientist with experience in Python...'"
    )

col_buttons = st.columns(2)

with col_buttons[0]:
    if st.button("✨ Get My Feedback", use_container_width=True):
        if not uploaded_resume or not job_description:
            st.warning("Please upload a resume and paste a job description to get started.")
        else:
            with st.spinner("Analyzing your resume..."):
                resume_text = get_resume_text(uploaded_resume)
                if resume_text:
                    feedback = get_ai_feedback(resume_text, job_description)

            if feedback:
                st.markdown("---")
                st.header("📋 Personalized Feedback")
                st.metric("Resume Match Score", f"{feedback.get('match_score', 0)}%")
                st.success(f"*Summary:* {feedback.get('summary', 'No summary provided.')}")
                for section, items in [
                    ("🔑 Missing Keywords & Skills", feedback.get('missing_keywords', [])),
                    ("📝 Formatting & Clarity Suggestions", feedback.get('formatting_suggestions', [])),
                    ("🚀 Experience & Achievement Improvements", feedback.get('experience_improvements', [])),
                    ("✨ Overall Tips", feedback.get('overall_tips', []))
                ]:
                    st.markdown(f"### {section}")
                    for item in items:
                        st.write(f"• {item}")
                st.balloons()

with col_buttons[1]:
    if st.button("📝 Create Optimized Draft", use_container_width=True):
        if not uploaded_resume or not job_description:
            st.warning("Please upload a resume and paste a job description to get started.")
        else:
            with st.spinner("Creating your optimized resume draft..."):
                resume_text = get_resume_text(uploaded_resume)
                if resume_text:
                    draft = create_optimized_draft(resume_text, job_description)

            if draft:
                st.markdown("---")
                st.header("✍️ Optimized Resume Draft")
                st.info("This is a starting draft. Review and personalize it before using!")
                st.markdown(draft)
                st.download_button(
                    label="Download Draft as Markdown",
                    data=draft,
                    file_name="optimized_resume_draft.md",
                    mime="text/markdown"
                )
