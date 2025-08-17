# GAIA Benchmark Agent with Gemini 2.5 Pro

A Gradio-based agent powered by Google's Gemini 2.5 Pro model to solve GAIA (General AI Assistants) benchmark questions.

## 🎯 Performance
- **Current Score**: 12/20 correct (60%) on GAIA Level 1 questions
- **Model**: Gemini 2.5 Pro with dynamic reasoning capabilities

## ✨ Features
- 🔍 **Google Search Integration** - Access to current information
- 💻 **Code Execution** - Solve computational problems
- 🌐 **URL Context** - Read and analyze web pages
- 🧠 **Dynamic Reasoning** - Unlimited thinking capability for complex problems
- 📁 **File Processing** - Handles various file types associated with tasks

## 🚀 Setup

### Prerequisites
- Python 3.8+
- Google Cloud API Key with Gemini API access
- Hugging Face account (for submission)

### Installation
```bash
pip install gradio requests pandas google-genai
```

### Configuration
1. Set your Google API key as an environment variable:
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

2. For Hugging Face Spaces deployment, add `GOOGLE_API_KEY` to your Space secrets.

## 📖 Usage

### Local Development
```bash
python app.py
```

### How to Use
1. **Login** to Hugging Face using the login button
2. Click **"🚀 Run Evaluation & Submit All Answers"**
3. The agent will:
   - Fetch all GAIA questions
   - Process each question using Gemini 2.5 Pro
   - Submit answers automatically
   - Display results in a table

## 🛠️ Technical Details
- **Framework**: Gradio
- **Model**: Gemini 2.5 Pro
- **Tools**: Google Search, Code Execution, URL Context
- **Evaluation**: GAIA Level 1 benchmark (146 questions)

## 📊 GAIA Benchmark
GAIA tests fundamental AI capabilities including:
- Web browsing and information retrieval
- Multi-step reasoning
- Code execution
- Multimodal understanding

## 🔗 Links
- [GAIA Benchmark Paper](https://huggingface.co/gaia-benchmark)
- [Google Gemini Documentation](https://ai.google.dev/)