from dotenv import load_dotenv
import base64
import streamlit as st
import os
import io
from PIL import Image
import fitz
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_gemini_response(input, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input, pdf_content[0], prompt])
    return response.text

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        first_page = pdf_document.load_page(0)
        pix = first_page.get_pixmap()
        img_byte_arr = io.BytesIO(pix.tobytes("jpeg"))
        img_byte_arr = img_byte_arr.getvalue()
        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

def scrape_job_description(link):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
    }
    
    try:
        response = requests.get(link, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Assuming the job description is in a <div> with class "description"
        job_description = soup.find('div', class_='description')
        
        if job_description:
            return job_description.get_text(strip=True)
        else:
            st.write("Job description not found on the page. Please check the link.")
            return None
    except requests.exceptions.HTTPError as http_err:
        st.write(f"HTTP error occurred: {http_err}")  # Print HTTP error
        return None
    except requests.exceptions.RequestException as req_err:
        st.write(f"Request error occurred: {req_err}")  # Print general request error
        return None
    except Exception as e:
        st.write(f"An error occurred: {e}")  # Print any other exceptions
        return None

st.set_page_config(page_title="ATS Resume Expert")
st.header("ATS Tracking System")

input_text = st.text_area("Job Description: ", key="input")
job_link = st.text_input("LinkedIn Job Posting URL:", placeholder="Enter job link...")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if uploaded_file is not None:
    st.write("PDF Uploaded Successfully")

submit1 = st.button("Tell Me About the Resume")
submit2 = st.button("Percentage match")

input_prompt1 = """
You are an experienced Technical Human Resource Manager, your task is to review the provided resume against the job description. 
Please share your professional evaluation on whether the candidate's profile aligns with the role. 
Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
"""

input_prompt2 = """
You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality, 
your task is to evaluate the resume against the provided job description. Give me the percentage of match if the resume matches
the job description. First the output should come as percentage and then keywords missing and last final thoughts.
"""

if submit1 or submit2:
    if job_link:
        input_text = scrape_job_description(job_link) or input_text  # Update input_text with scraped job description
    if uploaded_file is not None:
        pdf_content = input_pdf_setup(uploaded_file)
        if submit1:
            response = get_gemini_response(input_prompt1, pdf_content, input_text)
        else:
            response = get_gemini_response(input_prompt2, pdf_content, input_text)
        st.subheader("The Response is")
        st.write(response)
    else:
        st.write("Please upload the resume")
