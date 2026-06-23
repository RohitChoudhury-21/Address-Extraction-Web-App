# Address Extraction Web App

A single-page web application that extracts US addresses from uploaded documents (PDF or TXT) using the Smarty US Extract API.

## How It Works

1. User uploads a PDF or TXT file through the web page.
2. The backend converts the file into plain text.
3. The plain text is sent to the Smarty US Extract API.
4. Smarty returns any US addresses found in the text.
5. The page displays the extracted addresses in a table.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Address Extraction:** [Smarty US Extract API](https://www.smarty.com/products/apis/us-extract-api)

## Project Structure

project/

├── backend/

│   ├── app.py                              # FastAPI app + POST /extract route

│   ├── services/

│   │   └── address_extraction_service.py   # Coordinates extraction + Smarty call

│   ├── extractors/

│   │   └── file_text_extractor.py          # Converts PDF/TXT to plain text

│   ├── clients/

│   │   └── smarty_client.py                # Talks to the Smarty API

│   ├── .env                                # Real credentials (not committed)

│   ├── .env.example                        # Template for required env vars

│   └── requirements.txt

├── frontend

│   ├── index.html

│   ├── style.css

│   └── script.js

├── .gitignore

└── README.md

## Setup & Installation

### Prerequisites
- Python 3.9+
- A Smarty account with a **secret key pair** (`auth-id` and `auth-token`) for the US Extract API — get one at [smarty.com](https://www.smarty.com)

### 1. Clone the repository
```bash
git clone <https://github.com/RohitChoudhury-21/Address-Extraction-Web-App>
cd address-extraction-app
```

### 2. Set up the backend
```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

### 3. Configure environment variables
Copy `.env.example` to `.env` and fill in your real Smarty credentials:
```bash
copy .env.example .env          # Windows
# cp .env.example .env          # Mac/Linux
```


### 4. Run the backend
```bash
uvicorn app:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`. Interactive API docs at `http://127.0.0.1:8000/docs`.

### 5. Run the frontend
Open `frontend/index.html` using a local server (e.g., VS Code's **Live Server** extension) — opening it directly via `file://` will cause CORS issues with `fetch()`.

## API Reference

### `POST /extract`

**Request:** `multipart/form-data` with a single field `file` (PDF or TXT)

**Success response (200):**
```json
{
  "addresses": [
    {
      "input_text": "1600 Amphitheatre Pkwy, Mountain View, CA 94043",
      "primary_number": "1600",
      "street_name": "Amphitheatre",
      "street_suffix": "Pkwy",
      "city_name": "Mountain View",
      "state_abbreviation": "CA",
      "zipcode": "94043"
    }
  ]
}
```

**Error response:**
```json
{
  "error": {
    "message": "Human-readable message",
    "code": "ERROR_CODE"
  }
}
```

## Known Limitations

- Smarty's US Extract API limits request bodies to 64KB of text (not 1MB).
- Scanned/image-only PDFs with no text layer will return an empty result rather than an error.
- Only PDF and TXT files are supported.

## Author
Rohit Choudhury