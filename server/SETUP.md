# SmartStudy AI - Server Setup Guide

## Installation

1. Install Tesseract OCR:
   - **Windows**: 
     - **Option 1 (Recommended)**: Download the installer from [UB Mannheim Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)
       - Download the latest `.exe` installer (e.g., `tesseract-ocr-w64-setup-5.x.x.exe`)
       - Run the installer and follow the setup wizard
       - **Important**: During installation, check the box to "Add to PATH" or note the installation path (usually `C:\Program Files\Tesseract-OCR\`)
     - **Option 2**: If you have Chocolatey installed: `choco install tesseract`
     - **After installation**: If Tesseract is not in your system PATH, uncomment and set the path in `main.py`:
       ```python
       pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
       ```
   - **Linux (Ubuntu/Debian)**: `sudo apt-get install tesseract-ocr`
   - **Mac**: `brew install tesseract`

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Gemini API Setup

To use the summarization and MCQ generation features with Gemini 2.5 Flash (v1beta), you need to:

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. Create a `.env` file in the server directory:
   - Copy `env_template.txt` to `.env` (or create a new `.env` file)
   - Add your API key:
     ```
     GEMINI_API_KEY=your-actual-api-key-here
     ```

3. The `.env` file is automatically loaded when you start the server. Make sure not to commit this file to version control!

## Running the Server

```bash
uvicorn main:app --reload
```

The server will run on `http://127.0.0.1:8000`

## API Endpoints

- `POST /process-image` - Upload an image to extract text using OCR (Tesseract) and generate a summary using Gemini 2.5 Flash (v1beta)

## How It Works

1. **Text Extraction**: Uses Tesseract OCR (open-source, no pretrained vision model) to extract text from uploaded images
2. **Summarization**: Uses Gemini 2.5 Flash API to generate concise summaries from extracted text
3. **MCQ Generation**: Uses Gemini 2.5 Flash API to generate multiple-choice questions based on the summary

