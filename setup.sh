#!/bin/bash

echo "🚀 Setting up Interview Agent Environment..."

# -------------------------

# 1. Create Conda Env

# -------------------------

echo "📦 Creating conda environment..."
conda create -n interview-agent python=3.10 -y
conda activate interview-agent

# -------------------------

# 2. Core Dependencies (Conda)

# -------------------------

echo "🔧 Installing core dependencies..."
conda install -c conda-forge pip setuptools wheel ffmpeg libsndfile -y

# -------------------------

# 3. Python Packages

# -------------------------

echo "🐍 Installing Python packages..."
python -m pip install --upgrade pip

python -m pip install 
numpy
streamlit 
crewai 
faster-whisper 
av 
soundfile 
pydub 
requests 
pyyaml 
silero-vad

# -------------------------

# 4. Install Piper (Mac)

# -------------------------

echo "🔊 Installing Piper TTS..."
if command -v brew &> /dev/null
then
brew install piper
else
echo "⚠️ Homebrew not found. Please install Piper manually."
fi

# -------------------------

# 5. Download TTS Model

# -------------------------

echo "📥 Downloading Piper voice model..."
mkdir -p models/piper

curl -L -o models/piper/en_US-lessac-medium.onnx 
https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx

# -------------------------

# 6. Ollama Model

# -------------------------

echo "🤖 Pulling Ollama model..."
ollama pull mistral

echo "✅ Setup complete!"
echo "👉 Run: streamlit run app/main.py"
