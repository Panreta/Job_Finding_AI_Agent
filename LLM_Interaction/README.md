This is the code to deploy the LLM for job searching. Also with the power of RAG and vector database, the searching will be much more precise.

Start from agent.py, you can input the words you want to send to LLM, and the prompt will be generated from both input from prompt and history to be the form like:

History is retrieved from "conversation_history = load_conversation_history()".
The response will get into 
```json
  prompt = f"""
    You are a job search assistant agent. You can use tools to help the user.

    Available tools:
    {tools_description}

    To use a tool, respond with: [TOOL: tool_name] {{"arg1": "value1", "arg2": "value2"}}

    Conversation history:
    {history_text}

    User: {user_input}
    Agent:
    """
```
This is the prompt we are goona send to LLM by: response = ask_llama(prompt).
(Randomness)

Then use "[TOOL:" to match tool_name, tool_args, just the function's name and the arg of the
function into one string to form followup_prompt and put it into LLM again to get the response.




To quit: Type "quit" in the comsolo.








---

# 1. Deploy a LLM local: Ollama


https://www.runoob.com/ollama/ollama-tutorial.html

Final function: I can use shell to start a chat with LLM without wifi


ollama run llama3.2 "What are the key skills for a software engineer?"




# 2. Files Preparation

### llm.py: input: prompt into the llama; output response from the llama

OS principle: Each program runs in its own **isolated memory space**:
┌──────────────────────────────────────────┐
│         Your Computer's RAM              │
├──────────────────────────────────────────┤
│  Chrome: 500MB     │  (isolated)                                                │
│  VS Code: 300MB    │  (isolated)                                                │
│  Ollama: 2GB          │   STAYS HERE!                                           │
│  agent.py: 50MB    │  Can start/stop                                          │
└──────────────────────────────────────────┘

**1. LLM models aren't simple files you can "read"**

The llama3.2 model file is **2GB of binary data** - it's not like opening a text file. To use it, you need to:

- Load 2GB into RAM
- Initialize neural network layers
- Run complex mathematical operations (matrix multiplications)
- Manage GPU/CPU efficiently

**2. This is VERY resource intensive**

If your Python script loaded the model directly:


````python
# Every time you run agent.py:
- Load 2GB model into memory (30 seconds)
- Initialize everything
- Process one question
- Shut down and unload
- Next question? Load 2GB again! (30 seconds)
```

This would be **incredibly slow** - reloading 2GB every time!

````




What we are doing here:
Start Ollama ONCE (ollama serve):

┌─────────────────────────────────────┐
│  Ollama Server Process              │
│  - Loads 2GB model into RAM (once)  │
│  - Keeps running in background      │
│  - Listens on port 11434            │
│  - Waits for requests...            │
└─────────────────────────────────────┘
         ↑
         │ HTTP Request (tiny, <1KB)
         │
┌─────────────────────────────────────┐
│  Your Python Script (agent.py)      │
│  - Sends question via HTTP          │  ← Instant
│  - Gets answer back                 │  ← 2 seconds
│  - Script can exit                  │
│  - Model STAYS LOADED in server!    │  ← Key point!
└─────────────────────────────────────┘

Run agent.py again?
Model is STILL loaded in Ollama server!
No need to reload 2GB

---
def ask_llama(prompt, stream=False):

```python

 json={

                "model": MODEL,

                "prompt": prompt,

                "stream": stream

            },
     
```


```python
  timeout=120 #  "If Ollama doesn't respond within 120 seconds (2 minutes), stop waiting and raise an error."
```

```python
if response.status_code == 200: # When you make an HTTP request, the server responds with a status code
```
  result = response.json()
    { "model": "llama3.2", "response": " The key skills are: Python, problem-solving... ", "done": true } 

# tools.py: 

Defined the tools and 4 useful funcs here:

```python
TOOLS = {

    "search_jobs": {

        "description": "Search for jobs by keywords and location",

        "function": lambda kwargs: search_jobs(**kwargs)

    },

    "read_resume": {

        "description": "Read the user's resume from file",

        "function": lambda kwargs: read_resume()

    },

    "save_application": {

        "description": "Save a job application with cover letter",

        "function": lambda kwargs: save_application(**kwargs)

    },

    "list_applications": {

        "description": "List all saved job applications",

        "function": lambda kwargs: list_applications()

    }

}
```

One by one illustration about these funcs:
### Search-jobs

More like building a placehold function here, waiting to be fixed later.
```python
"search_jobs": {

        "description": "Search for jobs by keywords and location",

        "function": lambda kwargs: search_jobs(**kwargs)

    },
```

```python
kwargs = {"keywords": "python", "location": "Seattle"}

search_jobs(**kwargs)
# This is EXACTLY the same as:
search_jobs(keywords="python", location="Seattle")
```


```python
def search_jobs(keywords="", location=""):

    """Search for jobs (mock data for now)"""

    # TODO: Integrate with real job APIs (Indeed, LinkedIn, etc.)

    mock_jobs = [

        {

            "title": "Software Engineer",

            "company": "TechCorp",

            "location": location or "Seattle",

            "description": "Looking for Python developer with AI experience",

            "url": "https://example.com/job1"

        },

        {

            "title": "Backend Developer",

            "company": "StartupXYZ",

            "location": location or "Remote",

            "description": "Node.js and database experience required",

            "url": "https://example.com/job2"

        }

    ]

    return json.dumps(mock_jobs, indent=2)
```

### read_resume

Read the resume in pdf form and generate in text in python

### save_application

```python
    filename = filename.replace(" ", "_").replace("/", "-")
```

If the path is

"data/applications/Amazon AWS Software Engineer/Backend 20260201.txt"
                    ↑     ↑                   ↑
                  space space              slash (causes path confusion!)
we wanna form a path, that's why we need this line.


### list_applications

Generate all the applied job based on the list in application folder

## memory.py

Generate a json file to record 

history.append({

        "timestamp": datetime.now().isoformat(),

        "user": user_message,

        "agent": agent_response

    })
Also, if you don't like the file, it also has a clear function to clean it out/


### agent.py: 

This is the main part of the LLM, and the data stream is described below:


Input the word, and the file will choose a model and parameter for you then use ask_llama to response.

For 1st response is in .json, so we can send back to make .json to be paragraph.
Then save the question into the memory.(Be careful about the history)

	Use quit to stop this func


### build_prompt
Brainwash the LLM to let it be a job agent. Based on user_input, history to generate a prompt
Use the last 5 history :

```python
    history_text = "\n".join([f"User: {h['user']}\nAgent: {h['agent']}" for h in history[-5:]])
```


In llm.py, use prompt here to generate response.

```python
    json={

                "model": MODEL,

                "prompt": prompt,

                "stream": stream

            },
```

```python
        if "[TOOL:" in response:
```

The code checks if the LLM's response contains the text `[TOOL:` anywhere in it.

### parse_tool_call

extract the method and arg out, like

```text
Let me read your resume. [TOOL: read_resume] {}
```
output read_resume, {}

put into execute_tool in tools.py.

ask llm like "read_resume()" in chatting.

Function wanna realize:
* Search for jobs by keywords and location?
* Review or create a resume?
* Save an application or cover letter?
* View all saved applications?

---

# 3. Use Chromadb to store the vectorized data

This code is querying the ChromaDB vector database to find jobs that are semantically similar to the input query.
### search_jobs_by_similarity

```python
 results = jobs_collection.query(

        query_texts=[query],

        n_results=n_results

    )
```

- **`query_texts=[query]`** - The search query (e.g., "python machine learning"). ChromaDB converts this text into a vector embedding and compares it against all stored job embeddings.
- **`n_results=n_results`** - How many of the most similar jobs to return (default is 5 in your function).


The ChromaDB requires all-MiniLM-L6-v2, and if you don't have it, ChromaDB will help you to download automatically.



**ChromaDB's all-MiniLM-L6-v2:**

- **Purpose**: Only converts text → vector embeddings for similarity search
- **Size**: 79MB (tiny!)
- **Use**: Understanding semantic similarity between job descriptions
Think it as a modified BERT, 

[[What the .bin Files Store]]
