import streamlit as st
import fitz  # PyMuPDF for text-based PDFs
import pytesseract
from pdf2image import convert_from_path
import google.generativeai as genai
import random

# Set up Google Gemini API
GOOGLE_API_KEY = "AIzaSyDRyu9YPw-vM5RKWqLHtnIaQ_ezbDLRPmQ"
genai.configure(api_key=GOOGLE_API_KEY)

def extract_text_from_pdf(pdf_path):
    """Extract text from a text-based PDF."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text

def extract_text_from_image_pdf(pdf_path):
    """Extract text from an image-based PDF using OCR."""
    images = convert_from_path(pdf_path)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text

def generate_mcq(text):
    """Generate MCQs using Google Gemini AI (Flash 2.0)."""
    prompt = f\"\"\"
    Convert the following text into multiple-choice questions.
    Each question should have 4 options, with only one correct answer.
    Return output in this format:
    Question: <question>
    Options: ["option1", "option2", "option3", "option4"]
    Answer: <correct option>

    Text: {text}
    \"\"\"

    model = genai.GenerativeModel("gemini-1.5-flash")  # ✅ Using Flash 2.0
    response = model.generate_content(prompt)

    if response and hasattr(response, "text"):
        return parse_mcq(response.text)
    else:
        st.error("AI failed to generate questions. Try another PDF!")
        return []

def parse_mcq(response_text):
    """Parse AI-generated MCQs into structured data."""
    questions = []
    lines = response_text.split("\n")
    q, options, answer = None, [], ""
    
    for line in lines:
        if line.startswith("Question:"):
            q = line.replace("Question:", "").strip()
        elif line.startswith("Options:"):
            options = eval(line.replace("Options:", "").strip())
        elif line.startswith("Answer:"):
            answer = line.replace("Answer:", "").strip()
            if q and options and answer:
                questions.append({"question": q, "options": options, "answer": answer})
    return questions

# Streamlit UI
st.title("📖 PDF MCQ Quiz Game 🎮")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Extract text
    text = extract_text_from_pdf("temp.pdf") or extract_text_from_image_pdf("temp.pdf")
    st.success("Text extracted successfully!")
    
    # Generate MCQs
    mcqs = generate_mcq(text)
    if not mcqs:
        st.error("Could not generate MCQs. Try another PDF.")
    else:
        st.session_state.mcqs = mcqs
        st.session_state.current_question = 0
        st.session_state.score = 0

if "mcqs" in st.session_state and st.session_state.current_question < len(st.session_state.mcqs):
    q_data = st.session_state.mcqs[st.session_state.current_question]
    
    st.subheader(f"Q{st.session_state.current_question + 1}: {q_data['question']}")
    user_answer = st.radio("Choose an answer:", q_data["options"], index=None)
    
    if st.button("Submit Answer"):
        if user_answer:
            if user_answer == q_data["answer"]:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error(f"❌ Wrong! Correct answer: {q_data['answer']}")
            
            st.session_state.current_question += 1
            if st.session_state.current_question >= len(st.session_state.mcqs):
                st.balloons()
                st.write(f"🎉 Game Over! Your Score: {st.session_state.score}/{len(st.session_state.mcqs)}")
                st.session_state.clear()  # Reset game
            else:
                st.experimental_rerun()
        else:
            st.warning("Please select an answer before submitting!")
