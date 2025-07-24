## Overview

Source code adapted from **Hugging Face Agent Course notebooks**. 

Modified to use local Ollama models and Gemini models instead of original cloud services to avoid quota limitations.

## Setup

**For Ollama:**
```bash
ollama pull <model-name>
ollama serve
```

**For Gemini:**
```bash
export GEMINI_API_KEY="your-api-key"
```

## Credits

Based on [Hugging Face Agent Course](https://huggingface.co/agents-course/notebooks) notebooks.