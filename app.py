import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF for normal PDFs
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import json

# Configure API Key from Streamlit Secrets
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# Function to extract text from normal PDFs
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text("text")
    return text.strip()

# Function to extract text from image-based PDFs using OCR
def extract_text_from_image_pdf(pdf_path):
    text = ""
    images = convert_from_path(pdf_path)
    for image in images:
        text += pytesseract.image_to_string(image)
    return text.strip()

# Function to generate MCQs using Gemini 2 Flash
def generate_mcq(text):
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
    
    if response and hasattr(response, "text") and response.text.strip():
        raw_text = response.text.strip()
        
        # Remove markdown JSON formatting
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        try:
            return json.loads(raw_text).get("mcqs", [])
        except json.JSONDecodeError:
            return []
    return []

# Streamlit UI
st.title("📄 AI-Powered PDF Quiz Game 🎯")
st.write("Upload a PDF and play a quiz generated from its content!")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("PDF uploaded successfully!")
    
    extracted_text = extract_text_from_pdf("temp.pdf") or extract_text_from_image_pdf("temp.pdf")

    if not extracted_text:
        st.error("Could not extract text. Try another PDF!")
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
            st.session_state.selected_option = None
            st.session_state.show_feedback = False

if "mcqs" in st.session_state and st.session_state.quiz_active:
    mcqs = st.session_state.mcqs
    q_idx = st.session_state.current_question

    if q_idx < len(mcqs):
        question_data = mcqs[q_idx]
        st.subheader(f"**Q{q_idx+1}: {question_data['question']}**")

        selected_option = st.radio("Choose an option:", question_data["options"], key=f"q{q_idx}")

        if st.button("Submit Answer"):
            st.session_state.selected_option = selected_option
            st.session_state.show_feedback = True

        if st.session_state.show_feedback:
            correct_answer = question_data["answer"]
            if st.session_state.selected_option == correct_answer:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error(f"❌ Wrong! Correct answer: {correct_answer}")
            
            if st.button("Next"):
                if st.session_state.current_question < len(mcqs) - 1:
                    st.session_state.current_question += 1
                    st.session_state.show_feedback = False
                    st.session_state.selected_option = None  # Reset selection
                    st.experimental_rerun()  # Ensure Streamlit refreshes with the new question
                else:
                    st.success(f"🎉 Quiz Complete! Your Score: {st.session_state.score}/{len(mcqs)}")
                    st.session_state.quiz_active = False




    



