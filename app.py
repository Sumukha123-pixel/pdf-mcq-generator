import streamlit as st
import google.generativeai as genai
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import json
import os

# Load API Key from Environment Variable
API_KEY = os.getenv("AIzaSyAsosAfTOQ_DZ4XNTngcC2QQWIEZRjtHiU")
if not API_KEY:
    st.error("⚠️ API Key is missing! Set GEMINI_API_KEY as an environment variable.")
    st.stop()

# Configure Google Gemini API
genai.configure(api_key=API_KEY)

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
    """Generate MCQs from text using Google Gemini 2.0 Flash AI."""
    prompt = f"""
    Convert the following text into multiple-choice questions.
    Each question should have 4 options, with only one correct answer.
    Return output in JSON format:
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

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        if response and response.text:
            try:
                mcq_data = json.loads(response.text)
                return mcq_data.get("mcqs", [])
            except json.JSONDecodeError:
                return []
    except Exception as e:
        st.error(f"⚠️ AI Error: {e}")
        return []

# Streamlit UI
st.title("📄 AI-Powered PDF 


