# Document Guard — Setup & Run

## Stack
- **Frontend**: React + TypeScript + Vite + Tailwind (shadcn/ui)
- **Backend**: Python · FastAPI · OpenCV · NumPy · Pillow

---

## 1. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py                  # runs on http://localhost:8000
```

### What the backend does
Four CV analysis layers run on every uploaded image:

| Layer | Tool | What it catches |
|---|---|---|
| **ELA** | Pillow + NumPy | JPEG re-compression hotspots — edited regions have a different compression history |
| **Edge Detection** | OpenCV Canny | Inconsistent borders, blurry pasted regions, skewed layout |
| **Noise Analysis** | OpenCV + NumPy | Copy-move artifacts, cloned signatures/seals, uneven noise across regions |
| **Metadata** | Raw bytes | Photoshop/GIMP/Canva signatures, missing EXIF, multiple re-saves |

Each layer scores 0-100 (100 = genuine). Final score = ELA 35% + Edge 25% + Noise 25% + Metadata 15%.

The API also returns base64-encoded processed images (ELA heatmap, edge overlay, noise heatmap) for the UI slider.

---

## 2. Frontend setup

```bash
npm install
npm run dev        # http://localhost:5173
```

---

## API — POST /verify-document

Multipart form, field name: `file` (JPG/PNG, max 10MB).

Response fields:
- authenticity_score (0-100, higher = more genuine)
- verdict: "LIKELY GENUINE" | "INCONCLUSIVE..." | "LIKELY FAKE"
- confidence, suspiciousRegions, analysisTime
- details[]: technique, finding, severity, score
- breakdown: per-layer scores
- processedImages: ela/edges/texture as base64 PNG data-URIs
