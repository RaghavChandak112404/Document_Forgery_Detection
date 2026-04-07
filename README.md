# 🔍 Document Forgery Detection

<div align="center">

![TypeScript](https://img.shields.io/badge/TypeScript-80.3%25-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/Python-17.6%25-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

**An AI-powered full-stack web application that detects forged or tampered documents using advanced image forensic techniques and deep learning.**

[Features](#-features) · [Tech Stack](#-tech-stack) · [Getting Started](#-getting-started) · [How It Works](#-how-it-works) · [Project Structure](#-project-structure) · [Screenshots](#-screenshots) · [Contributing](#-contributing)

</div>

---

## 📌 Overview

Document forgery is a growing threat in legal, financial, and government sectors. This project provides an automated solution that analyses uploaded document images and flags potential manipulations — including splicing, copy-move, and region retouching — using a combination of:

- **Error Level Analysis (ELA)**
- **Copy-Move Forgery Detection**
- **CNN-based Deep Learning Classification**
- **Weighted Decision Fusion**

Results are served through a clean, responsive web interface where users can upload a document and get an instant verdict with visual heatmap overlays.

---

## ✨ Features

- 📄 **Multi-format support** — Accepts JPEG, PNG, and PDF-rendered document images
- 🧠 **AI-powered detection** — Fine-tuned EfficientNet-B0 for high-accuracy classification
- 🗺️ **Visual forensics** — ELA heatmaps and copy-move region masks overlaid on the original document
- ⚡ **Fast inference** — End-to-end analysis in under 2 seconds
- 📊 **Confidence scoring** — Probability score alongside the Authentic / Forged verdict
- 📥 **Downloadable reports** — Export a PDF summary of the analysis
- 📱 **Responsive UI** — Works seamlessly on desktop, tablet, and mobile

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS |
| **Backend / API** | FastAPI (Python) |
| **ML / Image Processing** | Python, OpenCV, NumPy, Pillow, TensorFlow / PyTorch |
| **Deep Learning Model** | EfficientNet-B0 (fine-tuned) |
| **Storage** | Local filesystem / AWS S3 |
| **Containerisation** | Docker |

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** ≥ 18.x
- **Python** ≥ 3.10
- **npm** or **yarn**
- **pip**

---

### 1. Clone the Repository

```bash
git clone https://github.com/RaghavChandak112404/Document_Forgery_Detection.git
cd Document_Forgery_Detection
```

---

### 2. Backend Setup (Python)

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn api.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

---

### 3. Frontend Setup (Next.js)

```bash
cd Document_Forgery_Detection   # frontend directory

# Install dependencies
npm install

# Set environment variable
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:3000`.

---

### 4. Run with Docker (Optional)

```bash
# From the project root
docker-compose up --build
```

This starts both the frontend and backend in isolated containers.

---

## 🔬 How It Works

The detection pipeline runs in four stages:

```
Document Upload
      │
      ▼
 Preprocessing
 (resize, normalise, estimate JPEG quality)
      │
      ├──────────────────────────────────┐──────────────────────────────┐
      ▼                                  ▼                              ▼
Error Level Analysis (ELA)     Copy-Move Detection            CNN Classification
  Detects spliced regions        Finds duplicated areas        EfficientNet-B0
  via JPEG compression           within the document           probability score
  anomalies
      │                                  │                              │
      └──────────────────────────────────┴──────────────────────────────┘
                                         │
                                         ▼
                              Weighted Decision Fusion
                         S = w₁·ELA + w₂·CopyMove + w₃·CNN
                                         │
                                         ▼
                             Verdict: Authentic / Forged
                             + Confidence Score + Overlays
```

### Detection Methods

| Method | Detects | How |
|---|---|---|
| **Error Level Analysis** | Splicing, region replacement | JPEG re-compression differential |
| **Copy-Move Detection** | Duplicated regions | ORB keypoints + RANSAC + DCT block comparison |
| **CNN Classification** | General manipulations | Fine-tuned EfficientNet-B0 |

---

## 📁 Project Structure

```
Document_Forgery_Detection/
│
├── Document_Forgery_Detection/     # Next.js frontend (TypeScript)
│   ├── app/                        # App router pages
│   │   ├── page.tsx                # Home / Upload page
│   │   ├── results/page.tsx        # Results visualisation page
│   │   └── history/page.tsx        # Past analyses
│   ├── components/                 # Reusable UI components
│   ├── lib/                        # API client, utilities
│   ├── public/                     # Static assets
│   └── package.json
│
├── backend/                        # Python ML service
│   ├── api/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── routers/detect.py       # /detect endpoint
│   │   └── schemas.py              # Pydantic models
│   ├── ml/
│   │   ├── ela.py                  # Error Level Analysis
│   │   ├── copy_move.py            # Copy-Move detection
│   │   ├── cnn_model.py            # EfficientNet inference
│   │   └── fusion.py               # Decision fusion
│   ├── utils/
│   │   └── image_utils.py          # Preprocessing helpers
│   └── requirements.txt
│
├── package-lock.json
└── README.md
```

---

## 📊 Performance

| Method | Accuracy | Precision | Recall | F1 | AUC |
|---|---|---|---|---|---|
| ELA only | 74.2% | 0.71 | 0.79 | 0.75 | 0.81 |
| Copy-Move only | 69.8% | 0.68 | 0.73 | 0.70 | 0.76 |
| CNN only | 88.6% | 0.87 | 0.90 | 0.88 | 0.94 |
| **Ensemble (Proposed)** | **91.3%** | **0.90** | **0.93** | **0.91** | **0.96** |

> Evaluated on a 20% holdout test set combining CASIA v2.0, Columbia, and custom document data.

---

## 📸 Screenshots

> _Add screenshots of your UI here by placing images in a `/screenshots` folder and updating the paths below._

| Upload Page | Results Page |
|---|---|
| ![Upload](screenshots/upload.png) | ![Results](screenshots/results.png) |

---

## 🌐 API Reference

### `POST /detect`

Analyse a document image for forgery.

**Request**

```
Content-Type: multipart/form-data

file: <document image>
```

**Response**

```json
{
  "verdict": "forged",
  "score": 0.87,
  "ela_map": "<base64 encoded heatmap>",
  "cm_mask": "<base64 encoded mask>",
  "processing_time_ms": 812
}
```

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to your branch: `git push origin feature/your-feature-name`
5. Open a Pull Request



---

## 👤 Author

**Raghav Chandak**

[![GitHub](https://img.shields.io/badge/GitHub-RaghavChandak112404-181717?style=flat&logo=github)](https://github.com/RaghavChandak112404)

---

<div align="center">
  <sub>If you found this project helpful, consider giving it a ⭐</sub>
</div>
