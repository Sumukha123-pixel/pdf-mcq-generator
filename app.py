import streamlit as st
import google.generativeai as genai
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import json
import os

# Load API key from Streamlit Secrets
api_key = st.secrets["GEMINI_API_KEY"]

if not api_key:
    raise ValueError("⚠️ API Key is missing! Set GEMINI_API_KEY in Streamlit Secrets.")

genai.configure(api_key=api_key)

# Function to extract text from normal PDFs
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() if page.extract_text() else ""
    return text.strip()

# Function to extract text from image-based (scanned) PDFs using OCR
def extract_text_from_image_pdf(pdf_path):
    text = ""
    images = convert_from_path(pdf_path)
    for image in images:
        text += pytesseract.image_to_string(image)
    return text.strip()

# Function to generate MCQs using Gemini 2.0 Flash
def generate_mcq(text):
    """Generate MCQs from text using Gemini 2 Flash."""
    prompt = f"""
    Convert the following text into multiple-choice questions.
    Each question should have 4 options, with only one correct answer.
    Return output in this format (JSON, without markdown):
    {{
      "mcqs": [
        {{
          "question": "<question>",
          "options": ["option1", "option2", "option3", "option4"],
          "answer": "<correct option>"
        }},
        ...
      ]
    }}

    Text: {text}
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    if response and hasattr(response, "text"):
        raw_text = response.text.strip()
        
        # ✅ Remove markdown code block (` ```json `)
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]  # Remove first 7 characters (```json)
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]  # Remove last 3 characters (```)

        try:
            return json.loads(raw_text)["mcqs"]
        except json.JSONDecodeError:
            return []
    
    return []


# Streamlit UI
st.title("📄 AI-Powered PDF Quiz Generator 🎯")
st.write("Upload a PDF and play an MCQ quiz generated from its content!")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("✅ PDF uploaded successfully!")

    # Extract text from PDF
    extracted_text = extract_text_from_pdf("temp.pdf") or extract_text_from_image_pdf("temp.pdf")

    if not extracted_text:
        st.error("⚠️ Could not extract text. Try another PDF!")
    else:
        st.write("✅ Extracted text successfully! Generating MCQs...")

        mcqs = generate_mcq(extracted_text)

        if not mcqs:
            st.error("⚠️ AI failed to generate MCQs. Try another PDF!")
        else:
            st.session_state.mcqs = mcqs
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.quiz_active = True

# Quiz UI
if "mcqs" in st.session_state and st.session_state.quiz_active:
    mcqs = st.session_state.mcqs
    q_idx = st.session_state.current_question

    if q_idx < len(mcqs):
        question_data = mcqs[q_idx]
        st.subheader(f"**Q{q_idx+1}: {question_data['question']}**")

        selected_option = st.radio("Choose an option:", question_data["options"], key=f"q{q_idx}")

        if st.button("Submit Answer"):
            correct_answer = question_data["answer"]
            if selected_option == correct_answer:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error(f"❌ Wrong! Correct answer: {correct_answer}")

            st.session_state.current_question += 1

    else:
        st.success(f"🎉 Quiz Complete! Your Score: {st.session_state.score}/{len(mcqs)}")
        st.session_state.quiz_active = False



