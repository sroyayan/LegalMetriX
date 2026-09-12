# ⚖️ LegalMetriX

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![Gemini](https://img.shields.io/badge/Google-Gemini-orange?style=for-the-badge&logo=google)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

### AI-Powered Packaged Commodity Compliance Analysis

*Upload a product label → Extract compliance data → Generate structured legal insights.*

</div>

---

## 🚀 Overview

LegalMetriX is an AI-powered compliance analysis platform designed to automate the extraction of mandatory product-label information from packaged commodity images.

The system leverages **Google Gemini Vision** and **FastAPI** to analyze uploaded product labels and extract key compliance-related fields such as:

- Product Name
- Manufacturer Details
- Manufacturer Address
- Net Quantity
- MRP (Maximum Retail Price)
- Packing Date
- Import Date
- Customer Care Information
- FSSAI License Number

Instead of manually reviewing labels, users can upload an image and instantly receive structured compliance-ready data.

---

## 🎯 Problem Statement

Regulatory compliance verification for packaged commodities is often:

- Manual
- Time-consuming
- Error-prone
- Difficult to scale

LegalMetriX aims to simplify this process through AI-powered document understanding and structured data extraction.

---

## ✨ Features

### 📸 Image Upload & Validation

- Secure image upload endpoint
- Image type verification
- File size restrictions
- Automatic cleanup after processing

### 🤖 Gemini Vision Analysis

- Product label OCR
- Structured information extraction
- JSON-only output enforcement
- Retry & fallback mechanisms

### 🔒 Security

- API Key Authentication
- Input validation
- Upload sanitization
- Error handling & logging

### 🧪 Verification Suite

Comprehensive automated tests covering:

- Authentication
- File validation
- Upload limits
- Cleanup checks
- Gemini integration
- JSON parsing robustness

---

## 🏗️ System Architecture

```text
                ┌──────────────────┐
                │ Product Image    │
                └─────────┬────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ FastAPI Backend  │
                └─────────┬────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ Image Validation │
                └─────────┬────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ Gemini Vision AI │
                └─────────┬────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ Structured JSON  │
                └─────────┬────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ API Response     │
                └──────────────────┘
```

---

## 📂 Project Structure

```text
LegalMetriX/
│
└── backend/
    │
    ├── app/
    │   ├── api/
    │   │   └── scan.py
    │   │
    │   ├── services/
    │   │   └── gemini_service.py
    │   │
    │   ├── schemas.py
    │   └── main.py
    │
    ├── uploads/
    ├── reports/
    │
    ├── requirements.txt
    ├── verify.py
    ├── .env.template
    └── .gitignore
```

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/sroyayan/LegalMetriX.git

cd LegalMetriX/backend
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file inside the backend directory:

```env
GEMINI_API_KEY=YOUR_GEMINI_KEY

LEGALMETRIX_API_KEY=YOUR_API_KEY

GEMINI_MODEL=gemini-3.8-flash
```

---

## ▶️ Running the Application

```bash
uvicorn app.main:app --reload
```

Server:

```text
http://127.0.0.1:8000
```

Swagger Docs:

```text
http://127.0.0.1:8000/docs
```

---

## 📡 API Usage

### Upload Image

```http
POST /scan/upload
```

Headers:

```http
X-API-Key: YOUR_API_KEY
```

Request:

```bash
curl -X POST http://127.0.0.1:8000/scan/upload ^
-H "X-API-Key: YOUR_API_KEY" ^
-F "file=@label.jpg"
```

---

## 📄 Example Response

```json
{
  "success": true,
  "filename": "label.jpg",
  "analysis": {
    "product_name": "PARLE PLATINA HIDE & SEEK BISCUITS",
    "manufacturer_name": "PARLE BISCUITS PVT LTD",
    "manufacturer_address": "MUMBAI, INDIA",
    "net_quantity": "200 g",
    "mrp": "Rs 60.00",
    "packing_date": "",
    "import_date": "",
    "customer_care": "Consumer Care Cell...",
    "fssai_number": "10013022002253"
  }
}
```

---

## 🧪 Verification

Run the automated verification suite:

```bash
python verify.py
```

Expected result:

```text
RESULT: 10/10 passed
```

---

## 🛡️ Security Measures

- API Key Authentication
- File Size Limits
- MIME Type Validation
- Image Verification using Pillow
- Automatic Upload Cleanup
- Structured JSON Parsing
- Gemini Retry & Fallback Logic

---

## 📈 Current Status

### ✅ Completed

- FastAPI Backend
- Gemini Vision Integration
- Authentication Layer
- Upload Validation
- OCR Extraction
- Structured JSON Responses
- Automated Verification Suite

### 🚧 Planned

- Compliance Scoring Engine
- Violation Detection
- Batch Image Analysis
- Dashboard Analytics
- Scan History
- Report Generation

---

## 🧰 Tech Stack

| Component | Technology |
|------------|------------|
| Backend | FastAPI |
| AI Model | Google Gemini Vision |
| Validation | Pydantic |
| Image Processing | Pillow |
| Testing | Pytest / Verify Suite |
| Language | Python |

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a Pull Request

---

## 📜 License

This project is licensed under the MIT License.

---

<div align="center">

### ⚖️ LegalMetriX

**Turning Product Labels into Compliance Intelligence**

*"Because manually reading every tiny line on packaging is apparently how humanity decided to spend regulatory effort."*

</div>