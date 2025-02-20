# Resume Parser using OpenAI

## Introduction
This project is a **Resume Parsing** tool that extracts structured data from resumes using **OpenAI** and other NLP techniques. It can parse resumes in various formats like **PDF, DOCX, TXT**, and convert them into structured JSON data.

## Features
- 📝 Extracts Name, Contact Details, Skills, Experience, and Education
- 📄 Supports PDF formats
- 🤖 Uses **Ollama** for text processing
- ⚡ Fast and accurate parsing
- 📊 Outputs structured JSON format

## Installation
### Prerequisites
Ensure you have **Python 3.8+** installed and set up a virtual environment:

```sh
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### Install Dependencies
```sh
pip install -r requirements.txt
```

## Usage
### Run the Parser
```sh
python app.py --file resume.pdf
```

### Example Output
```json
{
    "name": "John Doe",
    "email": "johndoe@example.com",
    "phone": "+1-234-567-890",
    "skills": ["Python", "Machine Learning", "NLP"],
    "experience": [
        {
            "company": "XYZ Corp",
            "role": "Software Engineer",
            "duration": "2019 - 2023"
        }
    ]
}
```
```

## Configuration
Edit the `config.yaml` file to customize settings.

## API Integration
You can integrate this tool into your project as an API. Example:
```sh
curl -X POST -F "file=@resume.pdf" http://localhost:5000/parse
```

## Security Note
- **Do not commit sensitive API keys** (e.g., OpenAI keys) to the repository.
- Use **.gitignore** to prevent uploading sensitive files.

## License
MIT License

---

⭐ **Star this repo if you find it useful!**

