const API_URL = "http://127.0.0.1:8000/extract";

// Element references
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const filePreview = document.getElementById("file-preview");
const fileNameEl = document.getElementById("file-name");
const removeFileBtn = document.getElementById("remove-file-btn");
const extractBtn = document.getElementById("extract-btn");
const newUploadBtn = document.getElementById("new-upload-btn");
const emptyUploadBtn = document.getElementById("empty-upload-btn");
const errorUploadBtn = document.getElementById("error-upload-btn");

const uploadSection = document.getElementById("upload-section");
const loadingSection = document.getElementById("loading-section");
const errorSection = document.getElementById("error-section");
const emptySection = document.getElementById("empty-section");
const resultsSection = document.getElementById("results-section");

const errorMessageEl = document.getElementById("error-message");
const resultCountEl = document.getElementById("result-count");
const resultsTbody = document.getElementById("results-tbody");

let selectedFile = null;

// ---------- State Management ----------
function showOnly(sectionToShow) {
  [uploadSection, loadingSection, errorSection, emptySection, resultsSection].forEach((section) => {
    section.classList.add("hidden");
  });
  sectionToShow.classList.remove("hidden");
}

function resetToUpload() {
  selectedFile = null;
  fileInput.value = "";
  filePreview.classList.add("hidden");
  extractBtn.disabled = true;
  showOnly(uploadSection);
}

// ---------- File Selection ----------
function handleFileSelected(file) {
  if (!file) return;

  const validExtensions = [".pdf", ".txt"];
  const lowerName = file.name.toLowerCase();
  const isValid = validExtensions.some((ext) => lowerName.endsWith(ext));

  if (!isValid) {
    showError("Unsupported file type", "Only PDF and TXT files are supported. Please choose a different file.");
    return;
  }

  selectedFile = file;
  fileNameEl.textContent = file.name;
  filePreview.classList.remove("hidden");
  extractBtn.disabled = false;
}

dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
  handleFileSelected(e.target.files[0]);
});

removeFileBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  selectedFile = null;
  fileInput.value = "";
  filePreview.classList.add("hidden");
  extractBtn.disabled = true;
});

// ---------- Drag & Drop ----------
["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
  });
});

dropZone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  handleFileSelected(file);
});

// ---------- Extract Button ----------
extractBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  await extractAddresses(selectedFile);
});

newUploadBtn.addEventListener("click", resetToUpload);
emptyUploadBtn.addEventListener("click", resetToUpload);
errorUploadBtn.addEventListener("click", resetToUpload);

// ---------- API Call ----------
async function extractAddresses(file) {
  showOnly(loadingSection);

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const message = data?.error?.message || "Something went wrong. Please try again.";
      showError("Couldn't process this file", message);
      return;
    }

    renderResults(data.addresses);
  } catch (err) {
    showError("Connection error", "Couldn't reach the server. Make sure the backend is running and try again.");
  }
}

// ---------- Rendering ----------
function showError(title, message) {
  document.getElementById("error-title").textContent = title;
  errorMessageEl.textContent = message;
  showOnly(errorSection);
}

function renderResults(addresses) {
  if (!addresses || addresses.length === 0) {
    showOnly(emptySection);
    return;
  }

  resultCountEl.textContent = addresses.length;
  resultsTbody.innerHTML = "";

  addresses.forEach((addr) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${escapeHtml(addr.input_text)}</td>
      <td>${escapeHtml(addr.primary_number)}</td>
      <td>${escapeHtml(addr.street_name)} ${escapeHtml(addr.street_suffix)}</td>
      <td>${escapeHtml(addr.city_name)}</td>
      <td>${escapeHtml(addr.state_abbreviation)}</td>
      <td>${escapeHtml(addr.zipcode)}</td>
    `;
    resultsTbody.appendChild(row);
  });

  showOnly(resultsSection);
}

// ---------- Utility ----------
function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}