import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from clients.smarty_client import SmartyClient
from services.address_extraction_service import AddressExtractionService, AddressExtractionError

# Load environment variables from .env
load_dotenv()

SMARTY_AUTH_ID = os.getenv("SMARTY_AUTH_ID")
SMARTY_AUTH_TOKEN = os.getenv("SMARTY_AUTH_TOKEN")

if not SMARTY_AUTH_ID or not SMARTY_AUTH_TOKEN:
    raise RuntimeError("SMARTY_AUTH_ID and SMARTY_AUTH_TOKEN must be set in .env")

app = FastAPI(title="Address Extraction Web App")

# Allow the frontend (served separately) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for local dev; tighten this for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build our objects once, at startup — reused across requests
smarty_client = SmartyClient(auth_id=SMARTY_AUTH_ID, auth_token=SMARTY_AUTH_TOKEN)
extraction_service = AddressExtractionService(smarty_client=smarty_client)


MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB cap on the raw uploaded file

@app.post("/extract")
async def extract_addresses(file: UploadFile = File(...)):
    file_bytes = await file.read()

    if len(file_bytes) > MAX_UPLOAD_BYTES:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "This file is too large. Please upload a file under 5MB.", "code": "UPLOAD_TOO_LARGE"}},
        )

    try:
        addresses = extraction_service.process(filename=file.filename, file_bytes=file_bytes)
    except AddressExtractionError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": {"message": e.message, "code": e.code}},
        )

    return {"addresses": addresses}