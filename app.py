import subprocess
import json
from fastapi import FastAPI, File, UploadFile, Body
import mysql.connector
import pdfplumber  # Optimized PDF text extraction
from fastapi.responses import HTMLResponse
import os
from datetime import datetime

# Set environment variable to enforce UTF-8 encoding
os.environ["PYTHONIOENCODING"] = "utf-8"

# Initialize FastAPI application
app = FastAPI()

# MySQL connection setup with timeout & auto-reconnect handling
def get_db_connection():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="job_portal",
            connection_timeout=600,  # Set connection timeout
            pool_size=10,            # Use connection pooling
            autocommit=True           # Auto-commit transactions
        )
        cursor = db.cursor(buffered=True)
        print("Connected to database successfully.", flush=True)
        return db, cursor
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}", flush=True)
        return None, None

db, cursor = get_db_connection()

# Path to Ollama executable
OLLAMA_PATH = r"C:\Users\mahes\AppData\Local\Programs\Ollama\ollama.exe"

# Function to run Ollama with a prompt
def run_ollama(prompt):
    """Run Ollama model to extract structured data from resume text"""
    print(f"Running Ollama with prompt: {prompt[:50]}...", flush=True)
    command = [OLLAMA_PATH, "run", "gemma:2b", prompt]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        output = result.stdout.strip()
        return output if output else None
    except FileNotFoundError:
        print(f"Error: Ollama executable not found at {OLLAMA_PATH}", flush=True)
        return None
    except Exception as e:
        print(f"Subprocess Error: {e}", flush=True)
        return None

# Function to extract text from PDF using pdfplumber for better performance
def extract_pdf_data(file: UploadFile):
    print(f"Extracting text from PDF: {file.filename}", flush=True)
    try:
        with pdfplumber.open(file.file) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages[:5]])
        return text.replace('\x00', '').strip() if text else None
    except Exception as e:
        print(f"Error extracting PDF: {e}", flush=True)
        return None

# Function to process resume text using Ollama
def process_resume_with_ollama(text):
    print("Processing resume with Ollama...", flush=True)
    
    prompt = f"""
    Extract structured data from the given resume text only; if a field is not available, return an empty string. Return the result in JSON format with the following fields:

    - "firstName": The candidate's first name.
    - "middleName": The candidate's middle name (if available; otherwise, empty string).
    - "lastName": The candidate's last name.
    - "email": The candidate's email address.
    - "gender": The candidate's gender.
    - "DateOfBirth": The candidate's date of birth.
    - "address": The full address.
    - "country": The country name extracted from the address.
    - "state": The state name extracted from the address.
    - "district": The district name extracted from the address.
    - "pincode": The postal code.
    - "contactNo": Contact number(s) in a valid format.
    - "pancardNo": The PAN Card number.
    - "highSchool": The name of the high school (or SSC/10th grade).
    - "sscPercentage": The percentage/CGPA obtained in SSC/10th grade.
    - "sscYear": The SSC/10th passout year.
    - "collegeName": The name of the college for HSC/12th grade.
    - "hscPercentage": The percentage/CGPA obtained in HSC/12th grade.
    - "hscYear": The HSC/12th passout year.
    - "graduationCollege": The name of the college/university for graduation.
    - "graduationPercentage": The graduation/degree percentage or CGPA.
    - "graduationYear": The graduation passout year.
    - "skills": An array of skills.
    - "company": The company name where the candidate worked.
    - "workExperience": The number of years of work experience.
    - "location": The job location.
    - "postName": The job title or position.
    - "profilePhoto": A URL to the candidate's profile photo.

    Resume Text:
    {text}
    """
    response = run_ollama(prompt)

    if not response:
        print("Error: Ollama returned an empty response.", flush=True)
        return None

    try:
        cleaned_response = response.strip("`json").strip("`").strip()
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}", flush=True)
        return None

# Function to store the extracted resume data into the database
def store_resume_data(parsed_data, user_id):
    global db, cursor
    try:
        if not db.is_connected():
            db, cursor = get_db_connection()

        column_names = []
        values = []

        mapping = {
            "firstName": "firstname",
            "middleName": "middlename",
            "lastName": "lastname",
            "DateOfBirth": "dob",
            "email": "email",
            "gender": "gender",
            "address": "address",
            "country": "country",
            "state": "state",
            "district": "district",
            "pincode": "pincode",
            "contactNo": "contact_no",
            "pancardNo": "pancard_no",
            "highSchool": "ssc_highschool_name",
            "sscPercentage": "ssc_percentage",
            "sscYear": "ssc_passout_year",
            "collegeName": "hsc_college_name",
            "hscPercentage": "hsc_percentage",
            "hscYear": "hsc_passout_year",
            "graduationCollege": "graduation_college_name",
            "graduationPercentage": "graduation_percentage",
            "graduationYear": "graduation_passout_year",
            "skills": "skills",
            "company": "company_name",
            "workExperience": "work_experience",
            "location": "location",
            "postName": "postname",
            "profilePhoto": "profilephoto"
        }

        for json_key, db_column in mapping.items():
            if json_key in parsed_data:
                column_names.append(f"{db_column} = %s")
                values.append(parsed_data[json_key] if parsed_data[json_key] else None)

        values.extend([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id])  # Add timestamp and user_id

        update_sql = f"""
            UPDATE profiles 
            SET {', '.join(column_names)}, updated_at = %s 
            WHERE user_id = %s
        """

        cursor.execute(update_sql, values)
        db.commit()

        if cursor.rowcount == 0:  # If no rows were updated, insert a new one
            insert_sql = f"""
                INSERT INTO profiles (user_id, {', '.join(mapping.values())}, created_at, updated_at) 
                VALUES ({', '.join(['%s'] * (len(values) + 1))})
            """
            cursor.execute(insert_sql, [user_id] + values)
            db.commit()

        print("Data updated successfully!", flush=True)
    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}", flush=True)
    except Exception as e:
        print(f"General Error: {e}", flush=True)


# API endpoint for uploading and processing the PDF resume
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), user_id: int = Body(...)):
    print(f"Received PDF file: {file.filename} for user {user_id}", flush=True)

    resume_text = extract_pdf_data(file)
    if not resume_text:
        return {"error": "Failed to extract text from the PDF."}

    parsed_data = process_resume_with_ollama(resume_text)
    if not parsed_data:
        return {"error": "Failed to process the resume data."}

    store_resume_data(parsed_data, user_id)  # Pass user_id to store function

    return {"message": "Resume data extracted and stored successfully!", "extracted_data": parsed_data}

# Root endpoint to test the API
@app.get("/")
async def root():
    return HTMLResponse(content="Welcome to the Resume Parser API!", status_code=200)
