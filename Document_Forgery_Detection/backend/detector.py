"""
DocumentAuthenticityDetector  — v3
===================================
Seven-layer Computer Vision pipeline: OpenCV + NumPy + Pillow.

Original 4 layers
-----------------
1. ELA      – JPEG re-compression artifact analysis
2. Edge     – Canny edge structure, border & blur checks
3. Noise    – Noise-pattern consistency + copy-move detection
4. Meta     – File-header / EXIF software fingerprinting

NEW layers (v3)
---------------
5. Face     – Detects face photos and checks for splice / swap artifacts
6. DocType  – Classifies document type and applies type-specific rules
7. Semantic – Text-region layout: font consistency, erased zones, DPI mismatch
"""

import io
import time
import base64
import struct
import os

import cv2
import numpy as np
from PIL import Image


# ─────────────────────────────────────────────────────────────────────────────
# Haar cascade paths — bundled with OpenCV, no download needed
# ─────────────────────────────────────────────────────────────────────────────
_CV2_DATA            = cv2.data.haarcascades
FACE_CASCADE_PATH    = os.path.join(_CV2_DATA, "haarcascade_frontalface_default.xml")
PROFILE_CASCADE_PATH = os.path.join(_CV2_DATA, "haarcascade_profileface.xml")
EYE_CASCADE_PATH     = os.path.join(_CV2_DATA, "haarcascade_eye.xml")


def _to_b64(img_bgr: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", img_bgr)
    if not ok:
        return ""
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode()


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


# ─────────────────────────────────────────────────────────────────────────────
class DocumentAuthenticityDetector:

    WEIGHTS = {
        "ela":      0.20,
        "edge":     0.15,
        "noise":    0.15,
        "meta":     0.10,
        "face":     0.15,
        "doctype":  0.13,
        "semantic": 0.12,
    }

    def __init__(self):
        self._face_cascade    = cv2.CascadeClassifier(FACE_CASCADE_PATH)
        self._profile_cascade = cv2.CascadeClassifier(PROFILE_CASCADE_PATH)
        self._eye_cascade     = cv2.CascadeClassifier(EYE_CASCADE_PATH)

    # =========================================================================
    # Public entry point
    # =========================================================================

    def analyze(self, image_bytes: bytes, filename: str = "document", is_pdf: bool = False) -> dict:
        t_start = time.time()
        self.is_pdf = is_pdf

        arr     = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Could not decode image.")
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        ela_score,     ela_vis,   ela_flags   = self._ela_analysis(image_bytes, img_bgr)
        edge_score,    edge_vis,  edge_flags  = self._edge_analysis(img_bgr, img_gray)
        noise_score,   noise_vis, noise_flags = self._noise_analysis(img_gray)
        meta_score,               meta_flags  = self._metadata_analysis(image_bytes)
        face_score,    face_vis,  face_flags  = self._face_analysis(img_bgr, img_gray)
        doctype_score, doc_label, doc_flags   = self._doctype_analysis(img_bgr, img_gray)
        sem_score,     sem_vis,   sem_flags   = self._semantic_analysis(img_bgr, img_gray)

        final = _clamp(
            ela_score     * self.WEIGHTS["ela"]     +
            edge_score    * self.WEIGHTS["edge"]    +
            noise_score   * self.WEIGHTS["noise"]   +
            meta_score    * self.WEIGHTS["meta"]    +
            face_score    * self.WEIGHTS["face"]    +
            doctype_score * self.WEIGHTS["doctype"] +
            sem_score     * self.WEIGHTS["semantic"]
        )
        final = round(final, 2)

        all_flags = (ela_flags + edge_flags + noise_flags + meta_flags +
                     face_flags + doc_flags + sem_flags)

        # Fatal flaw overriding: huge watermark overlays should tank the entire analysis
        if any("watermark overlay detected" in f.lower() for f in all_flags):
            final = _clamp(final - 40.0)

        elapsed = round(time.time() - t_start, 2)

        return {
            "authenticity_score": final,
            "verdict":            self._verdict(final),
            "confidence":         round(100 - final),
            "suspiciousRegions":  self._count_suspicious(
                ela_score, edge_score, noise_score, meta_score,
                face_score, doctype_score, sem_score),
            "documentType":  doc_label,
            "analysisTime":  elapsed,
            "flags":         all_flags if all_flags else ["No major anomalies detected"],
            "details":       self._build_details(
                ela_score,  ela_flags,
                edge_score, edge_flags,
                noise_score, noise_flags,
                meta_score, meta_flags,
                face_score, face_flags,
                doctype_score, doc_flags,
                sem_score, sem_flags,
            ),
            "breakdown": {
                "ela_score":      round(ela_score,     2),
                "edge_score":     round(edge_score,    2),
                "noise_score":    round(noise_score,   2),
                "meta_score":     round(meta_score,    2),
                "face_score":     round(face_score,    2),
                "doctype_score":  round(doctype_score, 2),
                "semantic_score": round(sem_score,     2),
            },
            "processedImages": {
                "ela":      ela_vis,
                "edges":    edge_vis,
                "texture":  noise_vis,
                "face":     face_vis,
                "semantic": sem_vis,
            },
        }

    # =========================================================================
    # Layer 1 — Error Level Analysis
    # =========================================================================

    def _ela_analysis(self, image_bytes: bytes, img_bgr: np.ndarray):
        flags = []
        score = 100.0
        if getattr(self, "is_pdf", False):
            return 100.0, _to_b64(np.zeros_like(img_bgr)), ["Digital PDF — ELA not applicable"]
        try:
            pil_orig = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            buf = io.BytesIO()
            pil_orig.save(buf, "JPEG", quality=95)
            buf.seek(0)
            pil_recomp = Image.open(buf).convert("RGB")

            orig_arr   = np.array(pil_orig,   dtype=np.float32)
            recomp_arr = np.array(pil_recomp, dtype=np.float32)
            ela_map    = np.abs(orig_arr - recomp_arr)

            mean_err      = ela_map.mean()
            std_err       = ela_map.std()
            hotspot_ratio = std_err / (mean_err + 1e-6)

            if mean_err < 3 and hotspot_ratio < 1.5:
                score = 90.0
            elif mean_err < 8 and hotspot_ratio < 3.0:
                score = 70.0
                flags.append("Moderate ELA activity — possible minor edits")
            elif mean_err < 15 and hotspot_ratio < 5.0:
                score = 45.0
                flags.append("Elevated ELA error — localised edits detected")
            else:
                score = 15.0
                flags.append("High ELA error — significant image manipulation detected")

            ela_vis_arr  = np.clip(ela_map * 10, 0, 255).astype(np.uint8)
            ela_gray     = cv2.cvtColor(cv2.cvtColor(ela_vis_arr, cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2GRAY)
            ela_coloured = cv2.applyColorMap(ela_gray, cv2.COLORMAP_JET)
            ela_coloured = self._annotate_hotspot(ela_coloured, ela_gray)
            vis = _to_b64(ela_coloured)
        except Exception as e:
            score = 50.0
            flags.append(f"ELA check incomplete: {e}")
            vis = ""
        return _clamp(score), vis, flags

    def _annotate_hotspot(self, vis, gray):
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        cnts, _   = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            largest = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(largest) > 50:
                x, y, w, h = cv2.boundingRect(largest)
                cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(vis, "Tampered Region", (x, max(y-8, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        return vis

    # =========================================================================
    # Layer 2 — Edge & Structural Analysis
    # =========================================================================

    def _edge_analysis(self, img_bgr, img_gray):
        flags = []
        score = 100.0
        edges = cv2.Canny(img_gray, 50, 150)
        h, w  = img_gray.shape

        density = edges.sum() / (edges.size * 255.0)
        if density < 0.01:
            score -= 30
            flags.append("Very low edge density — document may be over-smoothed")
        elif density > 0.35:
            score -= 15
            flags.append("Abnormally high edge density — possible noise injection")

        cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not getattr(self, "is_pdf", False):
            border_found = False
            for cnt in cnts:
                if cv2.contourArea(cnt) < h * w * 0.5:
                    continue
                peri   = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                if len(approx) == 4:
                    border_found = True
                    pts   = approx.reshape(4, 2).astype(np.float32)
                    angle = abs(cv2.minAreaRect(pts)[2])
                    if angle > 5:
                        score -= 20
                        flags.append(f"Border skewed {angle:.1f}° — possible manipulation")
                    break
            if not border_found:
                score -= 15

        quad_vals = []
        for r in range(2):
            for c in range(2):
                q = edges[r*h//2:(r+1)*h//2, c*w//2:(c+1)*w//2]
                quad_vals.append(q.sum() / max(q.size, 1))
        if np.var(quad_vals) > 0.002:
            score -= 20
            flags.append("Uneven edge distribution — splice boundary likely")

        lap_var = cv2.Laplacian(img_gray, cv2.CV_64F).var()
        if lap_var < 100:
            score -= 25
            flags.append("High blur — pasted region or low-quality screenshot")
        elif lap_var < 300:
            score -= 10

        vis = np.zeros_like(img_bgr)
        cv2.drawContours(vis, cnts, -1, (0, 255, 200), 1)
        combined = cv2.addWeighted(cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), 0.6, vis, 0.4, 0)
        return _clamp(score), _to_b64(combined), flags

    # =========================================================================
    # Layer 3 — Noise Consistency & Copy-Move Detection
    # =========================================================================

    def _noise_analysis(self, img_gray):
        flags = []
        score = 100.0
        h, w  = img_gray.shape

        block_sz     = 64
        noise_levels = []
        positions    = []
        for y in range(0, h - block_sz, block_sz):
            for x in range(0, w - block_sz, block_sz):
                blk = img_gray[y:y+block_sz, x:x+block_sz]
                if blk.std() > 5.0:
                    noise_levels.append(blk.std())
                    positions.append((x, y))

        noise_arr = np.array(noise_levels, dtype=np.float32)
        noise_vis = np.zeros((h, w, 3), dtype=np.uint8)

        if len(noise_levels) > 1:
            if not getattr(self, "is_pdf", False):
                noise_cv = noise_arr.std() / (noise_arr.mean() + 1e-6)
                if noise_cv > 1.2:
                    score -= 35
                    flags.append("Highly inconsistent noise — multi-source image likely")
                elif noise_cv > 0.8:
                    score -= 20
                    flags.append("Noise inconsistency — possible copy-paste detected")
                elif noise_cv > 0.5:
                    score -= 10

            n_min, n_max = noise_arr.min(), noise_arr.max()
            for idx, (bx, by) in enumerate(positions):
                nv = int(255 * (noise_arr[idx] - n_min) / (n_max - n_min + 1e-6))
                noise_vis[by:by+block_sz, bx:bx+block_sz] = (int(nv*0.2), int(255-nv), int(nv))

        small      = cv2.resize(img_gray, (256, 256))
        blk_sz     = 16
        seen       = {}
        clone_hits = 0
        clone_vis  = np.zeros((256, 256, 3), dtype=np.uint8)
        for y in range(0, 256 - blk_sz, blk_sz // 2):
            for x in range(0, 256 - blk_sz, blk_sz // 2):
                blk = small[y:y+blk_sz, x:x+blk_sz]
                if blk.std() < 5.0:
                    continue
                key = blk.tobytes()
                if key in seen and seen[key] != (y, x):
                    clone_hits += 1
                    cv2.rectangle(clone_vis, (x, y), (x+blk_sz, y+blk_sz), (0, 80, 255), 1)
                else:
                    seen[key] = (y, x)

        if clone_hits > 15:
            score -= 30
            flags.append(f"Copy-move detected ({clone_hits} matching blocks)")
        elif clone_hits > 8:
            score -= 15
            flags.append(f"Possible copy-move artifacts ({clone_hits} matching blocks)")

        clone_full = cv2.resize(clone_vis, (w, h))
        combined   = cv2.addWeighted(noise_vis, 0.7, clone_full, 0.3, 0)
        return _clamp(score), _to_b64(combined), flags

    # =========================================================================
    # Layer 4 — Metadata / File-Header Analysis
    # =========================================================================

    def _metadata_analysis(self, image_bytes: bytes):
        flags = []
        score = 100.0
        if getattr(self, "is_pdf", False):
            return 100.0, ["Digital PDF — Metadata not applicable"]

        SUSPICIOUS_TOOLS = [
            # Design software
            b"photoshop", b"gimp", b"canva", b"adobe",
            b"illustrator", b"inkscape", b"paint.net",
            b"pixelmator", b"affinity", b"coreldraw",
            # Generators
            b"tcpdf", b"fpdf", b"reportlab", b"html2pdf",
            b"template", b"generator",
            # Screen capture
            b"screenshot", b"snipping", b"snagit", b"screencapture", b"gyazo"
        ]
        header_lower = image_bytes[:8000].lower()
        found  = [t.decode() for t in SUSPICIOUS_TOOLS if t in header_lower]
        if found:
            score -= 40
            flags.append(f"Suspicious source/software signature in metadata: {', '.join(found).title()}")

        soi_count = image_bytes.count(b'\xff\xd8')
        if soi_count > 1:
            score -= 20
            flags.append(f"Multiple JPEG compression layers ({soi_count}) — re-saved after editing")

        if b'Exif' not in image_bytes[:500]:
            score -= 15
            flags.append("EXIF absent — metadata may have been stripped")

        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            score = self._check_png_chunks(image_bytes, score, flags)

        return _clamp(score), flags

    def _check_png_chunks(self, data, score, flags):
        pos = 8
        text_chunks = 0
        while pos < len(data) - 12:
            try:
                length     = struct.unpack('>I', data[pos:pos+4])[0]
                chunk_type = data[pos+4:pos+8]
                if chunk_type in (b'tEXt', b'zTXt', b'iTXt'):
                    text_chunks += 1
                pos += 12 + length
            except Exception:
                break
        if text_chunks > 3:
            score -= 10
            flags.append(f"Unusual PNG text chunks ({text_chunks}) — tool artefacts")
        return score

    # =========================================================================
    # Layer 5 — FACE DETECTION & SPLICE ANALYSIS  ← NEW
    # =========================================================================

    def _face_analysis(self, img_bgr: np.ndarray, img_gray: np.ndarray):
        """
        Detects faces using Haar cascades (frontal + profile) and runs four
        sub-checks on each detected face:

        Sub-check A — Eye presence
            A detected face region with no eyes is suspicious (non-face
            triggered the cascade, or the face is a printed mask).

        Sub-check B — Blur mismatch
            If the face region has a very different sharpness (Laplacian
            variance) compared to the surrounding document, it was likely
            sourced from a different image.

        Sub-check C — Colour boundary
            Computes mean BGR inside vs. just outside the face bounding box.
            A large colour jump (>80 units) signals a paste boundary.

        Sub-check D — ELA boundary ring
            Measures ELA error on a thin border around the face bbox vs. the
            face interior. Pasted faces always have a high-ELA seam.
        """
        flags = []
        score = 100.0
        h, w  = img_gray.shape
        vis   = img_bgr.copy()

        faces_front = self._face_cascade.detectMultiScale(
            img_gray, scaleFactor=1.1, minNeighbors=5,
            minSize=(40, 40), flags=cv2.CASCADE_SCALE_IMAGE)
        faces_profile = self._profile_cascade.detectMultiScale(
            img_gray, scaleFactor=1.1, minNeighbors=5,
            minSize=(40, 40), flags=cv2.CASCADE_SCALE_IMAGE)

        all_faces = (list(faces_front)   if len(faces_front)   > 0 else []) + \
                    (list(faces_profile) if len(faces_profile) > 0 else [])
        face_count = len(all_faces)

        if face_count == 0:
            aspect = w / (h + 1e-6)
            if 1.2 < aspect < 2.0:   # ID-card-like landscape doc
                score -= 10
                flags.append("No face detected on what appears to be an ID-style document")
            return _clamp(score), _to_b64(vis), flags

        if face_count > 2:
            score -= 20
            flags.append(f"Multiple faces detected ({face_count}) — unexpected on a personal document")

        for (fx, fy, fw, fh) in all_faces[:2]:
            cv2.rectangle(vis, (fx, fy), (fx+fw, fy+fh), (0, 255, 0), 2)
            cv2.putText(vis, "Face", (fx, max(fy-6, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            face_gray = img_gray[fy:fy+fh, fx:fx+fw]
            face_bgr  = img_bgr[fy:fy+fh, fx:fx+fw]

            # Sub-check A: eyes
            eyes = self._eye_cascade.detectMultiScale(
                face_gray, scaleFactor=1.1, minNeighbors=4, minSize=(15, 15))
            if len(eyes) == 0:
                score -= 15
                flags.append("Face detected but no eyes found — possible mask or non-face region")
                cv2.putText(vis, "No eyes!", (fx, fy+fh+14),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 80, 255), 1)

            # Sub-check B: blur mismatch
            face_lap = cv2.Laplacian(face_gray, cv2.CV_64F).var()
            mask = np.ones_like(img_gray, dtype=bool)
            mask[fy:fy+fh, fx:fx+fw] = False
            bg_sample = img_gray[mask].ravel()[:10000].astype(np.float32)
            bg_lap    = float(np.var(np.diff(bg_sample))) if len(bg_sample) > 1 else 1.0
            blur_ratio = face_lap / (bg_lap + 1e-6)
            if blur_ratio < 0.2:
                score -= 25
                flags.append("Face region significantly blurrier than document — possible paste from lower-res source")
                cv2.putText(vis, "Blur mismatch", (fx, fy+fh+28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 80, 255), 1)
            elif blur_ratio > 8.0:
                score -= 15
                flags.append("Face region abnormally sharp vs background — resolution mismatch")

            # Sub-check C: colour boundary
            pad    = max(5, min(10, fw//8, fh//8))
            y1o    = max(0, fy-pad);  y2o = min(h, fy+fh+pad)
            x1o    = max(0, fx-pad);  x2o = min(w, fx+fw+pad)
            outer  = img_bgr[y1o:y2o, x1o:x2o].copy()
            outer[pad:pad+fh, pad:pad+fw] = 0
            non_zero = outer[outer.sum(axis=2) > 0]
            outer_mean = non_zero.mean(axis=0) if len(non_zero) > 0 else np.zeros(3)
            face_mean  = face_bgr.reshape(-1, 3).mean(axis=0)
            colour_diff = np.linalg.norm(face_mean - outer_mean)
            if colour_diff > 80:
                score -= 20
                flags.append("Strong colour jump at face boundary — face likely pasted from different image")
                cv2.rectangle(vis, (fx-pad, fy-pad), (fx+fw+pad, fy+fh+pad), (0, 0, 255), 1)

            # Sub-check D: ELA boundary ring
            try:
                pil_img = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
                buf = io.BytesIO()
                pil_img.save(buf, "JPEG", quality=95)
                buf.seek(0)
                ela_map = np.abs(
                    np.array(pil_img, dtype=np.float32) -
                    np.array(Image.open(buf).convert("RGB"), dtype=np.float32)
                ).mean(axis=2)

                bw = max(3, fw // 10)
                border_mask = np.zeros_like(ela_map, dtype=bool)
                border_mask[fy:fy+bw, fx:fx+fw]       = True
                border_mask[fy+fh-bw:fy+fh, fx:fx+fw] = True
                border_mask[fy:fy+fh, fx:fx+bw]        = True
                border_mask[fy:fy+fh, fx+fw-bw:fx+fw]  = True

                border_ela   = ela_map[border_mask].mean()
                interior_ela = ela_map[fy+bw:fy+fh-bw, fx+bw:fx+fw-bw].mean()

                if border_ela > interior_ela * 2.5 and border_ela > 8:
                    score -= 25
                    flags.append("High ELA at face boundary — face was digitally inserted")
                    cv2.rectangle(vis, (fx+bw, fy+bw), (fx+fw-bw, fy+fh-bw), (255, 0, 255), 1)
            except Exception:
                pass

        return _clamp(score), _to_b64(vis), flags

    # =========================================================================
    # Layer 6 — DOCUMENT TYPE CLASSIFIER  ← NEW
    # =========================================================================

    def _doctype_analysis(self, img_bgr: np.ndarray, img_gray: np.ndarray):
        """
        Classifies the document as Certificate / ID Card / Medical Document /
        General Document, then applies type-specific structural checks.

        Certificate checks:
          - Clear outer border must exist
          - Central title region must have high contrast (bold text)
          - Colour saturation should be low (paper document)

        ID Card checks:
          - Face expected in left or right third
          - Dense text zone expected in remaining area

        Medical Document checks:
          - Letterhead (top 15%) must have high contrast (logo + name)
          - Body area must be light (white paper)
          - Circular stamp/seal is expected near the bottom
        """
        flags = []
        score = 100.0
        h, w  = img_gray.shape
        aspect = w / (h + 1e-6)

        doc_type = self._classify_document(img_bgr, img_gray, aspect)

        if doc_type == "Certificate":
            score, flags = self._check_certificate(img_bgr, img_gray, score, flags, h, w)
        elif doc_type == "ID Card":
            score, flags = self._check_id_card(img_bgr, img_gray, score, flags, h, w)
        elif doc_type == "Medical Document":
            score, flags = self._check_medical(img_bgr, img_gray, score, flags, h, w)
        else:
            edges = cv2.Canny(img_gray, 50, 150)
            if edges.sum() / (edges.size * 255.0) < 0.005:
                score -= 20
                flags.append("Document has almost no structure — may be blank or heavily altered")

        return _clamp(score), doc_type, flags

    def _classify_document(self, img_bgr, img_gray, aspect) -> str:
        h, w = img_gray.shape
        if aspect > 1.3:
            faces = self._face_cascade.detectMultiScale(
                img_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            if len(faces) > 0:
                return "ID Card"

        if aspect < 0.85:
            edges = cv2.Canny(img_gray, 30, 100)
            cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if any(cv2.contourArea(c) > h * w * 0.6 for c in cnts):
                return "Certificate"

        if aspect < 1.2:
            top  = img_gray[:int(h*0.18), :]
            body = img_gray[int(h*0.18):, :]
            if top.std() > 40 and body.mean() > 180:
                return "Medical Document"

        return "General Document"

    def _check_certificate(self, img_bgr, img_gray, score, flags, h, w):
        if not getattr(self, "is_pdf", False):
            edges = cv2.Canny(img_gray, 30, 100)
            cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not any(cv2.contourArea(c) > h * w * 0.55 for c in cnts):
                score -= 25
                flags.append("Certificate: expected border not found")

        central = img_gray[int(h*0.25):int(h*0.55), int(w*0.1):int(w*0.9)]
        if central.std() < 20:
            score -= 20
            flags.append("Certificate: central title area has very low contrast — text may be absent or erased")

        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        if hsv[:, :, 1].mean() > 80:
            score -= 15
            flags.append("Certificate: unusually high colour saturation — may be a photo-based fake")

        return score, flags

    def _check_id_card(self, img_bgr, img_gray, score, flags, h, w):
        left  = img_gray[:, :w//3]
        right = img_gray[:, 2*w//3:]
        fl    = self._face_cascade.detectMultiScale(left,  scaleFactor=1.1, minNeighbors=4, minSize=(20,20))
        fr    = self._face_cascade.detectMultiScale(right, scaleFactor=1.1, minNeighbors=4, minSize=(20,20))
        if len(fl) == 0 and len(fr) == 0:
            score -= 20
            flags.append("ID Card: no face photo detected in expected zones")

        text_zone   = img_gray[:, w//3:2*w//3]
        edges       = cv2.Canny(text_zone, 50, 150)
        txt_density = edges.sum() / (edges.size * 255.0 + 1e-6)
        if txt_density < 0.02:
            score -= 15
            flags.append("ID Card: expected text zone appears empty")

        return score, flags

    def _check_medical(self, img_bgr, img_gray, score, flags, h, w):
        letterhead = img_gray[:int(h*0.15), :]
        if letterhead.std() < 25:
            score -= 20
            flags.append("Medical document: letterhead area has low contrast — may be missing or replaced")

        body = img_gray[int(h*0.15):int(h*0.85), :]
        if body.mean() < 150:
            score -= 15
            flags.append("Medical document: body area unusually dark — may not be a genuine printed document")

        blurred = cv2.GaussianBlur(img_gray, (9, 9), 2)
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=h//4,
            param1=80, param2=40,
            minRadius=int(min(h,w)*0.04), maxRadius=int(min(h,w)*0.20))
        if circles is not None:
            for (cx, cy, r) in np.round(circles[0]).astype(int):
                if cy < h * 0.5:
                    score -= 10
                    flags.append("Medical document: circular stamp found in upper half — unusual position")

        return score, flags

    # =========================================================================
    # Layer 7 — SEMANTIC / TEXT-REGION ANALYSIS  ← NEW
    # =========================================================================

    def _semantic_analysis(self, img_bgr: np.ndarray, img_gray: np.ndarray):
        """
        Morphological text-region analysis — no OCR library required.

        Check 1 — Font-height consistency
            Real documents have 2-4 distinct font sizes. Fakes assembled from
            multiple sources have wildly varied text-block heights.

        Check 2 — Suspicious blank rectangles
            Erased/whited-out text leaves bright, unusually uniform rectangles
            between text lines. Detected via mean + std of adjacent zones.

        Check 3 — Mixed-DPI (Fourier grid analysis)
            Divides the image into a 3x3 grid and computes the high-frequency
            ring of each cell's 2D FFT. Pasted blocks have a distinct spatial
            frequency fingerprint.

        Check 4 — Text colour consistency
            All body text should be the same colour (dark ink on light paper).
            Mixed-colour text blocks suggest content from different sources.
        """
        flags = []
        score = 100.0
        h, w  = img_gray.shape
        vis   = img_bgr.copy()

        # Isolate text lines via morphological dilation
        _, binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel_h  = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 2))
        dilated   = cv2.dilate(binary, kernel_h, iterations=2)
        cnts, _   = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        text_boxes = [
            cv2.boundingRect(c) for c in cnts
            if w*0.05 < cv2.boundingRect(c)[2] and cv2.boundingRect(c)[3] < h*0.08 and cv2.boundingRect(c)[3] > 4
        ]

        if not text_boxes:
            score -= 25
            flags.append("No text regions detected — document may be blank or too low quality")
            return _clamp(score), _to_b64(vis), flags

        # Check 1: font-height consistency
        heights    = [bh for (_, _, _, bh) in text_boxes]
        height_cv  = np.std(heights) / (np.mean(heights) + 1e-6)
        if height_cv > 1.0:
            score -= 20
            flags.append("High variation in text-line heights — multiple font sizes or mixed document sources")
        elif height_cv > 0.6:
            score -= 10
            flags.append("Moderate text-height variation — may indicate mixed content")

        for (x, y, bw, bh) in text_boxes:
            cv2.rectangle(vis, (x, y), (x+bw, y+bh), (200, 200, 0), 1)

        # Check 2: suspicious blank rectangles
        suspicious_blanks = 0
        for (tx, ty, tw, th) in text_boxes:
            pad = max(5, th * 2)
            region = img_gray[max(0,ty-pad):min(h,ty+th+pad), max(0,tx):min(w,tx+tw)]
            if region.size == 0:
                continue
            if not getattr(self, "is_pdf", False) and region.mean() > 245 and region.std() < 5 and tw > w * 0.2:
                suspicious_blanks += 1
                cv2.rectangle(vis, (max(0,tx), max(0,ty-pad)), (min(w,tx+tw), min(h,ty+th+pad)), (0, 0, 255), 2)
                cv2.putText(vis, "Erased?", (max(0,tx), max(0,ty-pad)-4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        if suspicious_blanks > 0:
            score -= suspicious_blanks * 15
            flags.append(f"Suspicious blank zone(s) ({suspicious_blanks}) — content may have been erased")

        # Check 3: Fourier grid DPI check
        grid_freqs = []
        rows, cols = 3, 3
        ch, cw     = h // rows, w // cols
        for r in range(rows):
            for c in range(cols):
                cell = img_gray[r*ch:(r+1)*ch, c*cw:(c+1)*cw].astype(np.float32)
                mag  = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(cell))))
                cy2, cx2 = mag.shape[0]//2, mag.shape[1]//2
                Y, X = np.ogrid[:mag.shape[0], :mag.shape[1]]
                ring = ((Y-cy2)**2 + (X-cx2)**2)**0.5 > min(cy2, cx2) * 0.7
                grid_freqs.append(mag[ring].mean())

        freq_arr = np.array(grid_freqs)
        if freq_arr.size > 1 and not getattr(self, "is_pdf", False):
            freq_cv  = freq_arr.std() / (freq_arr.mean() + 1e-6)
            if freq_cv > 0.15:
                score -= 20
                flags.append("Spatial frequency mismatch between regions — possible DPI inconsistency from paste")
            elif freq_cv > 0.08:
                score -= 10
                flags.append("Mild spatial frequency variation across document")

        # Check 4: text colour consistency
        text_colours = []
        for (tx, ty, bw, bh) in text_boxes[:20]:
            roi  = img_bgr[ty:ty+bh, tx:tx+bw]
            dark = roi[roi.mean(axis=2) < 100]
            if len(dark) > 10:
                text_colours.append(dark.mean(axis=0))

        if len(text_colours) > 3:
            colour_std = np.array(text_colours).std(axis=0).mean()
            if colour_std > 40:
                score -= 20
                flags.append("Text colour inconsistency — different coloured text blocks suggest multiple document sources")
            elif colour_std > 20:
                score -= 10

        # Check 5: Faint watermark / Template overlay detection
        blurred = cv2.GaussianBlur(img_gray, (11, 11), 0)
        edges_wm = cv2.Canny(blurred, 10, 40)
        
        kernel = np.ones((5, 5), np.uint8)
        dilated_wm = cv2.dilate(edges_wm, kernel, iterations=2)
        cnts_wm, _ = cv2.findContours(dilated_wm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        watermark_letters = 0
        wm_area = 0
        for c in cnts_wm:
            cx, cy, cw, ch = cv2.boundingRect(c)
            # Watermark letters are huge (e.g. 5% to 40% of height) but not the whole page, and not full-width lines
            if h * 0.05 < ch < h * 0.4 and w * 0.02 < cw < w * 0.3:
                roi_std = img_gray[cy:cy+ch, cx:cx+cw].std()
                # Sharp black text has high variance. Faint background watermarks have low variance.
                if roi_std < 35:
                    watermark_letters += 1
                    wm_area += (cw * ch)
                    cv2.rectangle(vis, (cx, cy), (cx+cw, cy+ch), (0, 0, 255), 2)
                    cv2.putText(vis, "WM", (cx, max(cy-5, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        
        total_img_area = h * w
        if watermark_letters >= 4 and wm_area > total_img_area * 0.05:
            score -= 50
            flags.append(f"Faint watermark overlay detected ({watermark_letters} large ghost characters) — likely generated template")
        elif watermark_letters >= 2 and wm_area > total_img_area * 0.02:
            score -= 20
            flags.append("Possible faint watermark detected in background")

        return _clamp(score), _to_b64(vis), flags

    # =========================================================================
    # Verdict / helpers
    # =========================================================================

    def _verdict(self, score: float) -> str:
        if score >= 75:
            return "LIKELY GENUINE"
        elif score >= 45:
            return "INCONCLUSIVE – MANUAL REVIEW RECOMMENDED"
        else:
            return "LIKELY FAKE"

    def _count_suspicious(self, *scores) -> int:
        return sum(1 for s in scores if s < 50)

    def _build_details(self,
                        ela_score,    ela_flags,
                        edge_score,   edge_flags,
                        noise_score,  noise_flags,
                        meta_score,   meta_flags,
                        face_score,   face_flags,
                        doc_score,    doc_flags,
                        sem_score,    sem_flags) -> list:
        def sev(s):
            return "high" if s < 40 else ("medium" if s < 65 else "low")
        def top(flags, ok):
            return flags[0] if flags else ok

        return [
            {"technique": "ELA",             "finding": top(ela_flags,   "No compression anomalies detected"),           "severity": sev(ela_score),   "score": round(ela_score,   1)},
            {"technique": "Edge Detection",  "finding": top(edge_flags,  "Edge structure consistent and well-formed"),   "severity": sev(edge_score),  "score": round(edge_score,  1)},
            {"technique": "Texture / Noise", "finding": top(noise_flags, "Noise pattern uniform across document"),       "severity": sev(noise_score), "score": round(noise_score, 1)},
            {"technique": "Metadata",        "finding": top(meta_flags,  "No editing software signatures found"),        "severity": sev(meta_score),  "score": round(meta_score,  1)},
            {"technique": "Face Analysis",   "finding": top(face_flags,  "Face region (if present) appears unaltered"),  "severity": sev(face_score),  "score": round(face_score,  1)},
            {"technique": "Document Type",   "finding": top(doc_flags,   "Document structure matches expected type"),     "severity": sev(doc_score),   "score": round(doc_score,   1)},
            {"technique": "Semantic Layout", "finding": top(sem_flags,   "Text layout and font consistency look normal"), "severity": sev(sem_score),   "score": round(sem_score,   1)},
        ]
