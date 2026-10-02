# AgroIntelli — AI Plant Disease Diagnostics Web App

Offline plant-disease detection dashboard using a quantized MobileNetV3-Small (TFLite) backend + FastAPI + Modern Nature-Themed Web UI.

---

## 📋 Folder Structure

```text
AgroIntelli_Web_Project/
├── notebooks/
│   └── AgroIntelli_Training_and_Export.ipynb   # Full training pipeline (cleaned)
├── app/
│   ├── __init__.py
│   ├── inference.py      # TFLite-only inference engine
│   ├── agrobot.py        # Bilingual (English & Bangla) offline agronomy chatbot engine
│   └── artifacts/        # Model + labels (used by web app)
│       ├── agrointelli_quant.tflite
│       ├── labels.txt
│       ├── class_names.json
│       └── advice.json
├── static/               # Frontend Assets
│   ├── index.html        # Plant UI structure & AgroBot chat widget
│   ├── style.css         # Modern glassmorphism & Android-responsive rules
│   └── app.js            # Client upload, voice recognition & chat logic
├── server.py             # FastAPI entry point (/predict & /chat endpoints)
├── requirements.txt      # Project dependencies
├── .gitignore            # Excludes local venv311 and checkpoints
└── README.md
```

---

## 🛠️ Requirements & Installation

> [!IMPORTANT]
> **Python 3.11 is strictly required!**
> TensorFlow and `tflite-runtime` packages on Windows have strict compatibility rules and run most stably on **Python 3.11**. Please ensure you use a Python 3.11 virtual environment to build and run this project.

### Step 1 — Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/rahulkr90930/Agrointelli.git
cd Agrointelli
```

### Step 2 — Create a Python 3.11 Virtual Environment
Initialize a clean Python 3.11 virtual environment inside the project directory:
```powershell
# Windows (PowerShell)
py -3.11 -m venv venv311
```
*(If `py` is not recognized, make sure Python 3.11 is added to your environment variables or specify the path to your python.exe directly: `C:\Path\To\Python311\python.exe -m venv venv311`)*

### Step 3 — Activate the Virtual Environment
Activate your newly created environment:
```powershell
# Windows (PowerShell)
.\venv311\Scripts\activate
```

### Step 4 — Install Dependencies
Install all required libraries, including TensorFlow, Pillow, NumPy, and FastAPI:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Starting the Project Everytime

Once the environment is set up, starting the application is simple. Simply open your terminal in the project directory and run:

1. **Activate the Environment**:
   ```powershell
   .\venv311\Scripts\activate
   ```
2. **Launch the FastAPI Server**:
   ```powershell
   python server.py
   ```
3. **Open in Browser**:
   * On your computer: Open **[http://localhost:8000](http://localhost:8000)**
   * On your Android Phone: Make sure your phone is on the same Wi-Fi network, and open `http://<your-computer-ip-address>:8000` (e.g. `http://192.168.1.15:8000`).

---

## 🌿 UI Features & Diagnostic Capabilities

| Feature | Description |
|---------|-------------|
| **Disease Prediction** | MobileNetV3-Small model matching 38 distinct plant-disease classes. |
| **Field/Lab Mode** | Adaptive confidence thresholds customized for real-world usage. |
| **Top-3 Alternate Diagnoses** | Shows alternate diagnoses with animated confidence charts. |
| **Image Quality Check** | Live checks for Brightness, Contrast, and Sharpness, alerting user of blurry or bad captures. |
| **Severity Proxy** | Estimates lesion-to-healthy leaf ratio from green-channel analysis. |
| **Agronomic Care Advice** | Rule-based treatment recommendation cards per disease. |
| **AgroBot (কৃষি মিত্র)** | Bilingual AI farm assistant in **English & Bangla** for daily farming problems (pests, blast/blight diseases, fertilizers, AWD irrigation, voice speech recognition & audio readout). |
| **Full Local Privacy & Speed** | Runs completely offline locally on your device in milliseconds. |