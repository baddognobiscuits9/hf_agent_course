# Alfred AI Assistant

A multi-tool AI assistant powered by Google Gemini and LangGraph that can search the web, check weather, query HuggingFace models, and retrieve guest information.

## Features

- 🔍 **Web Search**: Search the internet using DuckDuckGo
- 🌤️ **Weather Information**: Get real-time weather data for any location
- 🤗 **HuggingFace Stats**: Query download statistics for HuggingFace models
- 👥 **Guest Information**: Retrieve information about gala guests from a dataset

## Setup

### 1. Clone the repository and install dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Set up your API key

1. Get a Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a `.env` file in the project root:

```bash
cp .env.example .env
```

3. Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Project Structure

```
.
├── app.py          # Main agent application
├── retriever.py    # Guest information retrieval tool
├── tools.py        # Weather, search, and HuggingFace tools
├── .env           # Your API keys (create this)
├── requirements.txt # Python dependencies
└── README.md      # This file
```

## Usage

Run the main agent:

```bash
python app.py
```

You'll see a menu with three options:

1. **Run test queries**: Execute predefined example queries
2. **Enter your own query**: Type custom questions
3. **Exit**: Close the application

### Example Queries

- "Tell me about guest Lady Ada Lovelace"
- "What's the weather in Tokyo?"
- "Who is the current President of France?"
- "What's Meta's most downloaded model on HuggingFace?"
- "Find information about guest Einstein and what's the weather in Princeton?"

### Using as a Module

You can also import and use Alfred in your own code:

```python
from app import alfred
from langchain_core.messages import HumanMessage

# Create a query
messages = [HumanMessage(content="What's the weather in London?")]

# Get response
response = alfred.invoke({"messages": messages})
print(response['messages'][-1].content)
```

## Available Tools

1. **guest_info_retriever**: Searches through a dataset of gala guests
2. **DuckDuckGoSearchRun**: Performs web searches
3. **get_weather_info**: Fetches current weather using Open-Meteo API
4. **get_hub_stats**: Retrieves HuggingFace model download statistics

## Customization

### Changing the Gemini Model

In `app.py`, you can change the model by modifying:

```python
chat = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",  # Options: "gemini-1.5-pro", "gemini-1.5-flash", etc.
    google_api_key=GEMINI_API_KEY,
    temperature=0  # Adjust for more/less creative responses
)
```

### Adding New Tools

1. Create a new function in `tools.py`
2. Wrap it with `Tool` from langchain
3. Import and add it to the tools list in `app.py`

## Troubleshooting

### API Key Issues

If you get "GEMINI_API_KEY not found" error:

1. **Check .env file location**: Make sure `.env` is in the same directory as `app.py`
   ```bash
   ls -la .env  # Should show your .env file
   ```

2. **Check .env file format**: Ensure your `.env` file has the correct format (no spaces around =)
   ```
   GEMINI_API_KEY=your_actual_key_here
   ```

3. **Try alternative environment variable names**: The app also accepts:
   - `GOOGLE_API_KEY`
   - `GOOGLE_GEMINI_API_KEY`

4. **Set environment variable directly** (temporary):
   ```bash
   export GEMINI_API_KEY='your_api_key_here'
   python app.py
   ```

5. **Debug mode**: The app will print diagnostic info:
   - Whether .env was loaded
   - Current directory
   - Whether .env exists
   - Whether the API key was found

### Other Issues

- **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **Rate limits**: If you hit API rate limits, add delays between queries or upgrade your API plan
- **Tool errors**: Some tools may fail due to external API issues (weather, search) - try again later

## License

This project is for educational purposes. Please respect the terms of service for all APIs used.