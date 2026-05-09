#!/bin/bash

echo "🚀 Setting up AI Interview Agent (FastAPI + React)..."

# -------------------------

# 1. Create Conda Environment

# -------------------------

echo "📦 Creating conda environment..."
conda create -n interview-agent python=3.10 -y

# Activate (works in most shells)

source $(conda info --base)/etc/profile.d/conda.sh
conda activate interview-agent

# -------------------------

# 2. Install Backend Dependencies

# -------------------------

echo "🐍 Installing Python dependencies..."

pip install --upgrade pip

pip install 
fastapi 
uvicorn[standard] 
crewai 
faster-whisper 
soundfile 
pyttsx3
pyyaml

# -------------------------

# 4. Install Node.js and Frontend Dependencies

# -------------------------

echo "📦 Installing Node.js dependencies..."

cd frontend
npm install
cd ..

# Save to .env (optional)

cat <<EOF > .env
OPENAI_API_KEY=dummy
OLLAMA_BASE_URL=http://localhost:11434
EOF

# -------------------------

# 4. Install Node + Frontend

# -------------------------

echo "⚛️ Setting up React frontend..."

if ! command -v node &> /dev/null
then
echo "❌ Node.js not found. Please install Node.js first."
else
cd frontend
npm install
cd ..
fi

# -------------------------

# 5. Install Piper (Mac)

# -------------------------

echo "🔊 Installing Piper..."

if command -v brew &> /dev/null
then
brew install piper
else
echo "⚠️ Homebrew not found. Install Piper manually."
fi

# -------------------------

# 6. Create Required Folders

# -------------------------

echo "📁 Creating project folders..."

mkdir -p models/piper
mkdir -p outputs

# -------------------------

# 7. Download Piper Model (if missing)

# -------------------------

MODEL_PATH="models/piper/en_US-lessac-medium.onnx"

if [ ! -f "$MODEL_PATH" ]; then
echo "⬇️ Downloading Piper model..."
curl -L -o $MODEL_PATH 
https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
else
echo "✅ Piper model already exists"
fi

# -------------------------

# 8. Setup Ollama Model

# -------------------------

echo "🤖 Checking Ollama..."

if command -v ollama &> /dev/null
then
ollama pull mistral
else
echo "⚠️ Ollama not installed. Install from https://ollama.com"
fi

# -------------------------

# 9. Done

# -------------------------

echo ""
echo "✅ Setup Complete!"
echo ""
echo "👉 Run backend:"
echo "   uvicorn backend.main:app --reload"
echo ""
echo "👉 Run frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "👉 Make sure Ollama is running:"
echo "   ollama run mistral"
echo ""
