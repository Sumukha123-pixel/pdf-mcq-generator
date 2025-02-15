import os
import fitz  # PyMuPDF for normal PDFs
import pytesseract  # OCR
from pdf2image import convert_from_path
import google.generativeai as genai
import streamlit as st
from PIL import Image

# Set up Google Gemini API
GOOGLE_API_KEY = "AIzaSyDRyu9YPw-vM5RKWqLHtnIaQ_ezbDLRPmQ"
genai.configure(api_key=GOOGLE_API_KEY)

# Function to extract text from normal PDFs
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

# Function to extract text from image PDFs using OCR
def extract_text_from_image_pdf(pdf_path):
    images = convert_from_path(pdf_path)  # Convert PDF pages to images
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text.strip()

# Function to generate MCQs using Gemini
def generate_mcq(text):
    prompt = f"""
    Generate multiple-choice questions (MCQs) from the given text. Convert each sentence into a question with four options and indicate the correct answer.

    Text: "{text}"

    Response format:
    - Question:
    - Options: A) ..., B) ..., C) ..., D) ...
    - Answer:
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text if response else "Failed to generate questions."

# Streamlit App
st.title("PDF to MCQ Quiz Generator (Now Supports OCR!)")
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Extract text from both normal and image-based PDFs
    text = extract_text_from_pdf("temp.pdf")
    if not text.strip():  # If no text is found, try OCR
        text = extract_text_from_image_pdf("temp.pdf")

    st.write("Extracted Text:", text[:500])  # Show a preview

    if st.button("Generate MCQs"):
        mcq_output = generate_mcq(text)
        st.write(mcq_output)
