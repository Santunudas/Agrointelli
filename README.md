# 🌿 AgroIntelli — AI Plant Disease Diagnostics & Bilingual Smart Farm Assistant

> **Next-Gen Offline Plant Pathology AI + AgroBot (কৃষি মিত্র) — Bilingual Farming Advisor**

AgroIntelli is a fully offline, field-deployable plant disease diagnostic platform powered by a quantized **MobileNetV3-Small (TFLite)** deep learning backend, a **FastAPI** server, and a modern nature-themed **glassmorphism web UI**. It is now bundled with **AgroBot (কৃষি মিত্র)** — a bilingual (English & Bangla) smart farm assistant that provides instant agronomic advice, fertilizer dosages, pest management, and irrigation guidance — all without an internet connection.

---

## 📋 Folder Structure

```text
AgroIntelli/
├── notebooks/
│   └── AgroIntelli_Training_and_Export.ipynb   # Full MobileNetV3 training pipeline
├── app/
│   ├── __init__.py
│   ├── inference.py          # TFLite inference engine (quality check + severity proxy)
│   ├── agrobot.py            # Bilingual (English & Bangla) offline agronomy chatbot engine
│   ├── auth.py               # Optional MongoDB-backed user accounts and sessions
│   ├── batches.py            # Saved crop visits, batch inference, and history API
│   ├── data/
│   │   └── agrobot_knowledge.json
│   └── artifacts/            # Model + label assets (used by the web app)
│       ├── agrointelli_quant.tflite   # INT8 quantized model (~1.2 MB)
│       ├── labels.txt                 # 38-class label list
│       ├── class_names.json           # Human-readable class names
│       └── advice.json                # Rule-based treatment advice per disease
├── static/                   # Frontend Assets
│   ├── index.html            # Glassmorphism UI — diagnostic dashboard + AgroBot chat widget
│   ├── style.css             # Modern dark glassmorphism theme, mobile-responsive
│   └── app.js                # Upload, drag-drop, voice recognition, AgroBot chat logic
│   ├── account.html          # Optional sign-in, registration, and profile page
│   └── account.js            # Account page interactions
├── server.py                 # FastAPI entry point (/predict, /batches, /chat)
├── requirements.txt          # Project dependencies
├── .gitignore
└── README.md
```

---

## 🛠️ Requirements & Installation

> [!IMPORTANT]
> **Python 3.11 is strictly required!**
> TensorFlow and `tflite-runtime` on Windows have strict compatibility constraints and run most stably on **Python 3.11**. Please ensure you use a Python 3.11 virtual environment.

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Santunudas/Agrointelli.git
cd Agrointelli
```

### Step 2 — Create a Python 3.11 Virtual Environment

```powershell
# Windows (PowerShell)
py -3.11 -m venv venv311
```

> *If `py` is not recognized, specify the path directly:*
> `C:\Path\To\Python311\python.exe -m venv venv311`

### Step 3 — Activate the Virtual Environment

```powershell
.\venv311\Scripts\activate
```

### Step 4 — Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Once the environment is set up, starting the server is straightforward:

1. **Activate the Environment:**
   ```powershell
   .\venv311\Scripts\activate
   ```

2. **Launch the FastAPI Server:**
   ```powershell
   python server.py
   ```

3. **Open in Browser:**
   - **Local PC:** [http://localhost:8000](http://localhost:8000)
   - **Android / Mobile (same Wi-Fi):** `http://<your-computer-ip>:8000` *(e.g., `http://192.168.1.15:8000`)*

### Optional User Accounts

AgroBot and plant diagnosis remain available without signing in. Registration and profiles use MongoDB; account endpoints return `503` until `MONGODB_URI` is configured.

Set these environment variables before starting the server:

```powershell
$env:MONGODB_URI = "mongodb://localhost:27017"
$env:MONGODB_DATABASE = "agrointelli"
$env:AUTH_COOKIE_SECURE = "false" # Local HTTP development only; set true when served over HTTPS.
python server.py
```

The local MongoDB service must already be installed and running for that example to work. Alternatively, use a MongoDB Atlas connection string stored in `MONGODB_URI`.

For deployment, use a MongoDB connection string protected by your hosting provider's secret manager and set `AUTH_COOKIE_SECURE=true` while serving the site over HTTPS. Do not expose MongoDB directly to the internet or commit credentials into the repository. The account page is available at `/account.html`. The app also supports batch crop visits when signed in: choose a crop and field, analyze up to 20 photos per visit, and review timestamped results from earlier visits in the field timeline. Results are stored in the `diagnostic_batches` collection and are only returned to the account that created them. Each image is limited to 10 MB. Visitors can still use image analysis without signing in, but guest results are not saved. The first version supports registration, sign-in, sign-out, and editing a user's name, Indian state/union territory, and crop list. It does not yet include email verification, password reset, account deletion, or login rate limiting; add those before opening account registration to the public internet.

### Temporary Sharing with Pinggy

To share a temporary HTTPS link while the app runs on your computer:

1. Configure `MONGODB_URI` and start the app in one PowerShell terminal. Set `AUTH_COOKIE_SECURE=true` for the Pinggy HTTPS link. Use `false` only when accessing the app directly over local HTTP.
  ```powershell
  $env:MONGODB_URI = "mongodb://localhost:27017"
  $env:MONGODB_DATABASE = "agrointelli"
  $env:AUTH_COOKIE_SECURE = "true"
  python server.py
  ```
  The local MongoDB service must be running. You can use Atlas instead by setting `MONGODB_URI` to its connection string.
2. In a second terminal, start the Pinggy tunnel:
  ```powershell
  ssh -p 443 -R0:localhost:8000 a.pinggy.io
  ```
3. Share the HTTPS URL printed by Pinggy. Keep both terminals open while your friends use the site. Anyone with the link can reach the app, so share it only with people you trust; never share your MongoDB connection string.

The server trusts forwarded protocol headers only from loopback, where the local SSH tunnel connects. If using MongoDB Atlas, ensure its network access rules allow connections from the computer running this app.

---

## 🧠 Model & Engine Specifications

| Property | Value |
|----------|-------|
| **Architecture** | MobileNetV3-Small |
| **Format** | INT8 Quantized TFLite |
| **Model Size** | ~1.2 MB |
| **Input Resolution** | 160 × 160 px |
| **Disease Classes** | 38 distinct plant-disease classes |
| **Inference Backend** | `tflite-runtime` (or `tf.lite` fallback) |
| **Preprocessing** | Raw [0–255] float32 (internal Rescaling layer handles normalization) |

---

## 🌿 Diagnostic Features

| Feature | Description |
|---------|-------------|
| **Disease Prediction** | MobileNetV3-Small classifies across **38** plant-disease classes in milliseconds. |
| **Field / Lab Mode** | Toggle adaptive confidence thresholds — Field Mode (≥ 85% = High, ≥ 55% = Medium) vs. raw Lab Mode. |
| **Top-3 Alternate Diagnoses** | Animated confidence bars show the top 3 differential diagnoses side-by-side. |
| **Severity Proxy (Lesion Ratio)** | Green-channel pixel analysis estimates lesion-to-leaf ratio — rated as *Healthy/Very Mild*, *Early/Moderate*, or *Severe*. Rendered as an animated radial progress ring. |
| **Image Quality Check** | Real-time checks for **Brightness**, **Contrast**, and **Sharpness** — warns user about blurry, too-dark, or overexposed captures before inference. |
| **Agronomic Care Advice** | Per-disease rule-based treatment recommendation cards with organic and chemical treatment notes. |
| **Drag-and-Drop Upload** | Modern drag-and-drop zone with image preview and one-click removal. |
| **Skeleton Loader** | Animated skeleton screens displayed while inference is running for a polished UX. |

---

## 🤖 AgroBot (কৃষি মিত্র) — Bilingual AI Farm Assistant

AgroBot is a **fully offline, bilingual smart farming advisor** embedded in the AgroIntelli web UI. It auto-detects the user's language from Bangla script, Romanized Banglish keywords, or English and responds accordingly.

### AgroBot Capabilities

| Capability | Details |
|------------|---------|
| **Bilingual Chat (EN + বাংলা)** | Full support for English and Bangla — auto-detected from script or Banglish keywords. |
| **Language Switcher** | In-chat pill to lock to `Auto`, `EN`, or `বাংলা`. |
| **38 Disease Class Coverage** | Detailed organic & chemical treatment protocols for all 38 plant-disease classes detected by the AI model. |
| **Pest & Disease Management** | Rice (stem borer, blast, BPH), Potato (late/early blight), Tomato (leaf curl, mosaic), Mustard, Brinjal, Wheat, and more. |
| **Fertilizer Dosage Guide** | Precise Urea, DAP, Potash, Zinc, Boron, and Compost dosages per crop type and growth stage. |
| **AWD Irrigation (সেচ)** | Alternate Wetting and Drying guidance with field water management advice. |
| **Acidic Soil & Liming** | Soil pH correction schedules and lime application dosages. |
| **Organic Bio-Pesticides** | Step-by-step preparation for Neem oil spray and Trichoderma application. |
| **Weather Precautions** | Guidance for rain, storm, frost, and dense fog crop protection. |
| **Helpline Numbers** | Official agricultural helplines — **1800-180-1551** (India) & **16123** (Bangladesh). |
| **Optional LLM Integration** | Falls back to Gemini / Groq API if API keys are configured for complex queries. |
| **Diagnosis Context Linking** | After a scan, AgroBot is automatically primed with the detected disease context for targeted step-by-step advice. |
| **Quick Topic Chips** | One-tap action chips in both English and Bangla for common farming problems (Rice Stem Borer, Potato Blight, Fertilizer, Neem Spray, AWD Irrigation, Helplines, etc.). |
| **Voice Input (Mic)** | Web Speech Recognition — ask questions by voice in Bangla or English. |
| **Audio Readout** | AgroBot reads its replies aloud using the Web Speech Synthesis API. |
| **Typing / Thinking Indicator** | Animated brain icon with thinking dots shown during response generation. |
| **Chat History Clear** | One-click chat reset with a rotating icon button. |

### Maintaining the Knowledge Base

AgroBot's general advisory responses are stored in [`app/data/agrobot_knowledge.json`](app/data/agrobot_knowledge.json), separately from the matching and response code. The file has a `schema_version`, a `dataset_version`, and a target geography (`IN-WB`, India—West Bengal). Each bilingual entry includes its source, applicable region, review status, and review date under `provenance`. The separate disease-class advice map remains in `app/agrobot.py` and must also be source-reviewed as part of future expansion.

When adding or updating advice:

1. Add focused, independently searchable entries and useful English, Bangla, and Banglish keywords.
2. Cite a trustworthy agricultural source and URL; scope regional or state-specific guidance in `provenance.region`.
3. Mark advice `reviewed` only after checking it against that source. Keep legacy material `unverified` until its original recommendations have been validated.
4. Include units and safety qualifications for any dosage, and verify the current product label and local approvals before giving pesticide recommendations.
5. Run `python -m unittest discover -s tests` to check the dataset and retrieval behavior.

The entries migrated from the original in-code knowledge base are intentionally marked `unverified`: their original sources were not recorded. This data migration preserves existing responses; it does not certify the recommendations. New India-specific material should be added only after verification against appropriate Indian agricultural-extension sources.

---

## 🖥️ UI Design & Frontend

The frontend is built with **Vanilla HTML, CSS, and JavaScript** — no frameworks required.

- **Design Language:** Dark glassmorphism with animated glow background orbs.
- **Typography:** [Outfit](https://fonts.google.com/specimen/Outfit) (Google Fonts) — weights 300–800.
- **Icons:** Font Awesome 6.4.
- **Mobile Responsive:** Designed for both desktop browsers and Android phones on the same local network.
- **Floating AgroBot Button (FAB):** Pulsing animated action button with live status indicator.
- **AgroBot Panel:** Slide-in drawer modal with full chat interface, language switcher, diagnosis context bar, and quick topic chip rail.

---

## 🔌 API Endpoints

The FastAPI server exposes these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict` | Upload a leaf image. Returns prediction, confidence, top-3 alternates, severity proxy, image quality metrics, and care advice. Accepts `field_mode` query parameter. |
| `POST` | `/chat` | Send a farming question (with optional `language` and `diagnosis_context`). Returns a bilingual reply with follow-up suggestions. |
| `GET` | `/chat/quick-topics` | Returns localized quick-action topic chips for English and Bangla. |
| `GET` | `/auth/status` | Reports whether MongoDB-backed accounts are configured. |
| `POST` | `/auth/register` | Create an account with name, email, password, state, and crops. |
| `POST` | `/auth/login` | Sign in and create a server-side session. |
| `GET` | `/auth/me` | Return the signed-in user's profile. |
| `PATCH` | `/auth/me` | Update the signed-in user's name, state, and crops (CSRF token required). |
| `POST` | `/auth/logout` | Revoke the current session (CSRF token required). |
| `GET` | `/` | Serves the static frontend (`index.html`). |

### Example `/predict` Response

```json
{
  "prediction": "Tomato___Early_blight",
  "confidence": 0.974,
  "top3": [
    ["Tomato___Early_blight", 0.974],
    ["Tomato___Septoria_leaf_spot", 0.018],
    ["Tomato___Target_Spot", 0.005]
  ],
  "mode": "high confidence",
  "quality": {
    "ok": true,
    "brightness": 118.4,
    "contrast": 32.1,
    "sharpness": 21.8,
    "warnings": []
  },
  "severity_proxy": {
    "severity": "early/moderate",
    "lesion_ratio": 0.14
  },
  "advice": "Apply copper-based fungicide early morning. Ensure plant spacing for ventilation..."
}
```

---

## 🌾 AgroBot Quick Topics (Built-in)

| English Chip | Bangla Chip |
|--------------|-------------|
| 🌾 Rice Stem Borer | 🌾 ধানের মাজরা পোকা |
| 🥔 Potato Late Blight | 🥔 আলুর নাবি ধসা |
| 🧪 Fertilizer Dosage | 🧪 ইউরিয়া ও সারের নিয়ম |
| 🌾 Rice Blast Disease | 🌾 ধানের ব্লাস্ট রোগ |
| 🍅 Leaf Curl Virus | 🍅 পাতা কোঁকড়ানো রোগ |
| 🌿 Neem Bio-Pesticide | 🌿 নিম তেল তৈরি |
| 💧 Smart Irrigation / AWD | 💧 সেচ ও পানি পদ্ধতি |
| 📞 Agri Helplines | 📞 কিষাণ হেল্পলাইন |

---

## 🔒 Privacy & Performance

- ✅ **Local-First** — Diagnostics and built-in advice run locally. Optional LLM calls send questions to the configured provider; optional account registration sends profile and authentication data to the configured MongoDB service.
- ✅ **Millisecond Inference** — INT8 quantized TFLite model runs in under 100ms on CPU.
- ✅ **Local Network Ready** — Deployable on your PC; accessible from any phone on the same Wi-Fi.
- ✅ **No Framework Lock-in** — Pure HTML/CSS/JS frontend; no Node.js or bundler required.

---

## 📦 Dependencies

```text
# Training (Notebook / Colab)
tensorflow>=2.15
scikit-learn
pandas
matplotlib
pillow
opencv-python
numpy

# Web Server
fastapi
uvicorn
python-multipart
pymongo
argon2-cffi
```

> [!NOTE]
> For lightweight deployment (inference-only, no training), replace `tensorflow` with `tflite-runtime` to significantly reduce the install footprint.

---

## 📄 License

© 2026 AgroIntelli Diagnostics. Designed for local, robust, and accessible smart farming.