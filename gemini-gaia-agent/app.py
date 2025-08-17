import os
import gradio as gr
import requests
import pandas as pd
from google import genai
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Part,
    ThinkingConfig,
    Tool,
    ToolCodeExecution,
    UrlContext,
)

# Constants
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

# --- Gemini Agent Definition ---
class GeminiAgent:
    def __init__(self, api_key=None):
        """Initialize the Gemini Agent with API key."""
        print("Initializing GeminiAgent...")
        
        # Get API key from environment or parameter
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not provided. Set GOOGLE_API_KEY environment variable or pass it to the constructor.")
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.5-pro"  # Using Flash for better speed/cost ratio
        
        # Configure tools for the agent
        self.google_search_tool = Tool(google_search=GoogleSearch())
        self.code_execution_tool = Tool(code_execution=ToolCodeExecution())
        self.url_context_tool = Tool(url_context=UrlContext)
        
        # System prompt for GAIA-style questions
        self.system_instruction = """You are an expert problem-solving agent designed to answer questions accurately.
        
        IMPORTANT INSTRUCTIONS:
        1. Read the question carefully and identify what specific information is being asked for.
        2. If the question requires current information, use Google Search.
        3. If the question involves code or calculations, use code execution.
        4. If the question references URLs or files, use URL context to read them.
        5. Your final answer should be ONLY the direct answer to the question - no explanations, no "The answer is...", just the answer itself.
        6. For numerical answers, provide just the number (e.g., "42" not "42 people").
        7. For yes/no questions, answer only "yes" or "no".
        8. For multiple choice, provide only the letter or the exact option text.
        9. Be extremely precise - the answer must match exactly what is expected.
        
        Examples of good final answers:
        - "42"
        - "Paris"
        - "yes"
        - "2024-03-15"
        - "$1,234.56"
        
        Remember: Output ONLY the final answer, nothing else."""
        
        print(f"GeminiAgent initialized with model: {self.model_id}")
    
    def process_files(self, task_id: str, api_url: str) -> str:
        """Download and process files associated with a task."""
        files_context = ""
        files_url = f"{api_url}/files/{task_id}"
        
        try:
            print(f"Checking for files at: {files_url}")
            response = requests.get(files_url, timeout=10)
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    # If JSON, it might be a list of files or file metadata
                    try:
                        files_data = response.json()
                        if isinstance(files_data, list):
                            files_context = f"\n\nAssociated files for this task: {files_data}"
                        else:
                            files_context = f"\n\nFile data: {files_data}"
                    except:
                        # If not valid JSON, treat as raw content
                        files_context = f"\n\nFile content:\n{response.text[:5000]}"  # Limit to 5000 chars
                elif 'text' in content_type:
                    # Text file
                    files_context = f"\n\nFile content:\n{response.text[:5000]}"
                else:
                    # Binary file
                    files_context = f"\n\n[Binary file of type {content_type} - {len(response.content)} bytes]"
                
                print(f"Files found for task {task_id}: {len(response.content)} bytes")
            elif response.status_code == 404:
                print(f"No files found for task {task_id}")
            else:
                print(f"Unexpected status {response.status_code} when fetching files")
                
        except Exception as e:
            print(f"Error fetching files for task {task_id}: {e}")
        
        return files_context
    
    def __call__(self, question: str, task_id: str = None, api_url: str = None) -> str:
        """Process a question and return an answer using Gemini."""
        print(f"Processing question: {question[:100]}...")
        
        # Check for files if task_id and api_url are provided
        enhanced_question = question
        if task_id and api_url:
            files_context = self.process_files(task_id, api_url)
            if files_context:
                enhanced_question = question + files_context
        
        try:
            # Use dynamic thinking (no budget limit) for maximum reasoning capability
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=enhanced_question,
                config=GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=[
                        self.google_search_tool, 
                        self.code_execution_tool,
                        self.url_context_tool  # Added URL context for reading web pages/files
                    ],
                    temperature=0.2,  # Low temperature for consistency
                    thinking_config=ThinkingConfig(
                        # No thinking_budget specified - let model decide dynamically
                        include_thoughts=False  # We don't need to see the thoughts in production
                    )
                ),
            )
            
            answer = response.text.strip()
            
            # Clean up the answer - remove any explanatory text
            # Look for patterns like "The answer is:" or similar
            if "answer is" in answer.lower():
                # Extract just the answer part
                parts = answer.lower().split("answer is")
                if len(parts) > 1:
                    answer = parts[-1].strip().strip(":.").strip()
            
            # Remove quotes if present (unless they're part of the answer)
            if answer.startswith('"') and answer.endswith('"'):
                answer = answer[1:-1]
            if answer.startswith("'") and answer.endswith("'"):
                answer = answer[1:-1]
            
            # Additional cleanup for common patterns
            answer = answer.replace("The answer is ", "")
            answer = answer.replace("Answer: ", "")
            answer = answer.replace("ANSWER: ", "")
            
            print(f"Generated answer: {answer}")
            return answer
            
        except Exception as e:
            print(f"Error processing question: {e}")
            # Fallback to a simpler approach without tools
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=f"Answer this question with ONLY the direct answer, no explanation: {enhanced_question}",
                    config=GenerateContentConfig(
                        temperature=0.2,
                    ),
                )
                return response.text.strip()
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                return "Error: Unable to process question"


def run_and_submit_all(profile: gr.OAuthProfile | None):
    """
    Fetches all questions, runs the GeminiAgent on them, submits all answers,
    and displays the results.
    """
    # Determine HF Space Runtime URL and Repo URL
    space_id = os.getenv("SPACE_ID")
    
    if profile:
        username = f"{profile.username}"
        print(f"User logged in: {username}")
    else:
        print("User not logged in.")
        return "Please Login to Hugging Face with the button.", None
    
    api_url = DEFAULT_API_URL
    questions_url = f"{api_url}/questions"
    submit_url = f"{api_url}/submit"
    
    # 1. Instantiate Agent
    try:
        # Get API key from environment or Gradio secrets
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Error: Google API key not found. Please set GOOGLE_API_KEY in your Space secrets.", None
        
        agent = GeminiAgent(api_key=api_key)
    except Exception as e:
        print(f"Error instantiating agent: {e}")
        return f"Error initializing agent: {e}", None
    
    agent_code = f"https://huggingface.co/spaces/{space_id}/tree/main"
    print(f"Agent code URL: {agent_code}")
    
    # 2. Fetch Questions
    print(f"Fetching questions from: {questions_url}")
    try:
        response = requests.get(questions_url, timeout=15)
        response.raise_for_status()
        questions_data = response.json()
        if not questions_data:
            print("Fetched questions list is empty.")
            return "Fetched questions list is empty or invalid format.", None
        print(f"Fetched {len(questions_data)} questions.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching questions: {e}")
        return f"Error fetching questions: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred fetching questions: {e}")
        return f"An unexpected error occurred fetching questions: {e}", None
    
    # 3. Run your Agent
    results_log = []
    answers_payload = []
    print(f"Running agent on {len(questions_data)} questions...")
    
    for idx, item in enumerate(questions_data, 1):
        task_id = item.get("task_id")
        question_text = item.get("question")
        
        if not task_id or question_text is None:
            print(f"Skipping item with missing task_id or question: {item}")
            continue
        
        print(f"\n[{idx}/{len(questions_data)}] Processing task {task_id}")
        print(f"Question preview: {question_text[:150]}...")
        
        try:
            # Pass task_id and api_url to agent for file handling
            submitted_answer = agent(question_text, task_id=task_id, api_url=api_url)
            answers_payload.append({"task_id": task_id, "submitted_answer": submitted_answer})
            results_log.append({
                "Task ID": task_id, 
                "Question": question_text[:100] + "..." if len(question_text) > 100 else question_text,
                "Submitted Answer": submitted_answer
            })
            print(f"✓ Answer: {submitted_answer}")
        except Exception as e:
            print(f"✗ Error running agent on task {task_id}: {e}")
            error_msg = f"AGENT ERROR: {str(e)[:50]}"
            results_log.append({
                "Task ID": task_id, 
                "Question": question_text[:100] + "..." if len(question_text) > 100 else question_text,
                "Submitted Answer": error_msg
            })
    
    if not answers_payload:
        print("Agent did not produce any answers to submit.")
        return "Agent did not produce any answers to submit.", pd.DataFrame(results_log)
    
    # 4. Prepare Submission 
    submission_data = {
        "username": username.strip(), 
        "agent_code": agent_code, 
        "answers": answers_payload
    }
    status_update = f"Agent finished. Submitting {len(answers_payload)} answers for user '{username}'..."
    print(status_update)
    
    # 5. Submit
    print(f"Submitting {len(answers_payload)} answers to: {submit_url}")
    try:
        response = requests.post(submit_url, json=submission_data, timeout=60)
        response.raise_for_status()
        result_data = response.json()
        final_status = (
            f"Submission Successful!\n"
            f"User: {result_data.get('username')}\n"
            f"Overall Score: {result_data.get('score', 'N/A')}% "
            f"({result_data.get('correct_count', '?')}/{result_data.get('total_attempted', '?')} correct)\n"
            f"Message: {result_data.get('message', 'No message received.')}"
        )
        print("Submission successful.")
        results_df = pd.DataFrame(results_log)
        return final_status, results_df
    except requests.exceptions.HTTPError as e:
        error_detail = f"Server responded with status {e.response.status_code}."
        try:
            error_json = e.response.json()
            error_detail += f" Detail: {error_json.get('detail', e.response.text)}"
        except:
            error_detail += f" Response: {e.response.text[:500]}"
        status_message = f"Submission Failed: {error_detail}"
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df
    except Exception as e:
        status_message = f"An unexpected error occurred during submission: {e}"
        print(status_message)
        results_df = pd.DataFrame(results_log)
        return status_message, results_df


# --- Build Gradio Interface using Blocks ---
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 Gemini-Powered Agent for GAIA Benchmark")
    gr.Markdown(
        """
        **Instructions:**
        
        1. **Set up your Google API Key**: Add `GOOGLE_API_KEY` to your Space's secrets/environment variables
        2. **Log in** to your Hugging Face account using the button below
        3. **Click 'Run Evaluation & Submit All Answers'** to test your agent on all questions
        
        This agent uses Google's Gemini 2.5 Pro model with:
        - 🔍 Google Search for current information
        - 💻 Code execution for calculations
        - 🌐 URL context for reading web pages and files
        - 🧠 Dynamic reasoning (unlimited thinking capability)
        
        ---
        """
    )
    
    gr.LoginButton()
    
    run_button = gr.Button("🚀 Run Evaluation & Submit All Answers", variant="primary")
    
    status_output = gr.Textbox(
        label="📊 Run Status / Submission Result", 
        lines=5, 
        interactive=False
    )
    results_table = gr.DataFrame(
        label="📋 Questions and Agent Answers", 
        wrap=True
    )
    
    run_button.click(
        fn=run_and_submit_all,
        outputs=[status_output, results_table]
    )

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 GEMINI AGENT FOR GAIA BENCHMARK")
    print("="*60)
    
    # Check for required environment variables
    space_host = os.getenv("SPACE_HOST")
    space_id = os.getenv("SPACE_ID")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if space_host:
        print(f"✅ SPACE_HOST found: {space_host}")
        print(f"   Runtime URL: https://{space_host}.hf.space")
    else:
        print("ℹ️  SPACE_HOST not found (running locally?)")
    
    if space_id:
        print(f"✅ SPACE_ID found: {space_id}")
        print(f"   Repo URL: https://huggingface.co/spaces/{space_id}")
    else:
        print("ℹ️  SPACE_ID not found (running locally?)")
    
    if google_api_key:
        print(f"✅ GOOGLE_API_KEY found: {google_api_key[:10]}...")
    else:
        print("⚠️  GOOGLE_API_KEY not found - Please set it in your environment!")
    
    print("="*60 + "\n")
    print("Launching Gradio Interface...")
    demo.launch(debug=True, share=False)