# 🤖 RAG vs AI Agent — LangGraph + C# WinForms

A practical comparison between a **standard RAG pipeline** and an **AI Agent built with LangGraph**, implemented on the same dataset: the history of the **Diocese of Samalut**.

The goal of this project was not just to understand the theoretical difference between RAG and AI Agents, but to see how that difference appears in a real implementation.

---

## 🎯 Project Goal

What is the actual technical difference between a **standard RAG system** and an **AI Agent**?

Instead of comparing them theoretically, this project implements both systems using the same knowledge base and compares how they process user queries.

### The two approaches

**RAG**

```text
User Query
    ↓
Query Embedding
    ↓
Hybrid Retrieval
(BM25 + Vector Search)
    ↓
Retrieved Context
    ↓
LLM
    ↓
Response
```

**AI Agent**

```text
User Query
    ↓
    LLM
    ↓
Choose Tool
    ↓
Tool Execution
    ↓
Observe Result
    ↓
    LLM
    ↓
Continue or Finish
```

The key difference is **decision-making**.

RAG follows a predefined pipeline, while the Agent dynamically decides what actions are required to answer the user's question.

---

# 🧠 System 1 — Standard RAG

The first system implements a traditional Retrieval-Augmented Generation pipeline.

### Architecture

```text
User Query
     │
     ▼
Query Embedding
     │
     ▼
┌─────────────────────────────┐
│      Hybrid Retrieval       │
│                             │
│  BM25 ────────┐             │
│               ├─ Ensemble ──┤
│  Vector ──────┘             │
└─────────────────────────────┘
     │
     ▼
Retrieved Documents
     │
     ▼
     LLM
     │
     ▼
Final Answer
```

The retriever combines:

* **BM25** for keyword-based retrieval
* **Vector search** for semantic similarity
* **EnsembleRetriever** to combine both approaches

The retrieved documents are then passed to the LLM as context.

### Characteristics

* Fixed execution flow
* No tool selection
* No iterative reasoning
* No dynamic decision-making
* One retrieval step followed by generation

In other words:

> **Retrieve → Generate → Finish**

---

# 🤖 System 2 — AI Agent

The second system uses **LangGraph** to implement an Agent based on the **ReAct (Reason + Act)** pattern.

The Agent can dynamically decide which tool it needs depending on the user's question.

### Available Tools

The Agent can interact with:

| Tool                | Purpose                              |
| ------------------- | ------------------------------------ |
| 🔎 Internal Search  | Search the project's knowledge base  |
| 🌐 Web Search       | Retrieve information from the web    |
| 🖼️ Image Retrieval | Find relevant images                 |
| 🔊 Text-to-Speech   | Convert generated responses to audio |

### Agent Architecture

```text
                    ┌───────────────┐
                    │   User Query  │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │      LLM      │
                    │   Reasoning   │
                    └───────┬───────┘
                            │
                     Choose Action
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       ┌──────────────┐            ┌──────────────┐
       │     Tool     │            │    Finish    │
       │   Execution  │            │   Response   │
       └──────┬───────┘            └──────────────┘
              │
              ▼
        Observe Result
              │
              ▼
             LLM
              │
              └───────────────► Continue / Finish
```

The Agent repeatedly follows:

```text
Reason → Act → Observe → Reason → Act → ...
```

until it determines that it has enough information to produce a final answer.

---

# 🔄 RAG vs Agent

The main difference can be summarized as follows:

| Feature                | Standard RAG | AI Agent |
| ---------------------- | -----------: | -------: |
| Retrieval              |            ✅ |        ✅ |
| Vector Search          |            ✅ |        ✅ |
| Keyword Search         |            ✅ |        ✅ |
| Multiple Tools         |            ❌ |        ✅ |
| Dynamic Tool Selection |            ❌ |        ✅ |
| Iterative Reasoning    |            ❌ |        ✅ |
| Web Search             |            ❌ |        ✅ |
| Image Retrieval        |            ❌ |        ✅ |
| Text-to-Speech         |            ❌ |        ✅ |
| Dynamic Workflow       |            ❌ |        ✅ |
| Checkpointing          |            ❌ |        ✅ |
| Complexity             |          Low |   Higher |

The important distinction isn't simply:

> **RAG vs Agent**

It's:

> **Fixed workflow vs dynamically controlled workflow**

---

# 🕸️ Why LangGraph?

LangGraph was used to explicitly model the Agent's workflow as a graph.

The application contains different nodes for:

* LLM reasoning
* Tool execution
* State management
* Workflow transitions

The Agent can move between these nodes depending on the current state and the LLM's decision.

This makes the Agent workflow easier to control than implementing a manually managed reasoning loop.

---

# 💾 Checkpointing & Conversation Context

The Agent uses checkpointing to preserve conversation state.

This allows the system to maintain context across interactions instead of treating every request as an isolated query.

Conceptually:

```text
Conversation 1
      ↓
Agent State
      ↓
Checkpoint
      ↓
Conversation 2
      ↓
Updated Agent State
```

This becomes particularly useful when building conversational applications where previous interactions affect future decisions.

---

# 🖥️ C# WinForms + Python Integration

One of the most challenging parts of the project was not building the Agent itself.

It was integrating the Python-based AI systems into a **C# WinForms desktop application**.

The integration uses **Python.NET (pythonnet)** to allow the C# application to execute Python code directly.

### Architecture

```text
┌──────────────────────────────┐
│        C# WinForms           │
│                              │
│        User Interface        │
└──────────────┬───────────────┘
               │
               │ Python.NET
               ▼
┌──────────────────────────────┐
│          Python              │
│                              │
│  ┌────────────────────────┐  │
│  │       RAG System       │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │    LangGraph Agent     │  │
│  └────────────────────────┘  │
│                              │
└──────────────────────────────┘
```

---

# ⚙️ Engineering Challenges

Several issues appeared during the integration.

## 1. Python GIL

Calling Python from a C# background thread required careful management of Python's **Global Interpreter Lock (GIL)**.

The application needed to acquire and release the GIL correctly when executing Python code from C#.

---

## 2. Asyncio + Windows Threads

Another issue appeared around Python's default asyncio event loop on Windows.

The default **Proactor event loop** caused compatibility problems with the threading model being used by the application.

The solution was to switch to a **Selector event loop**.

Conceptually:

```python
import asyncio

asyncio.set_event_loop_policy(
    asyncio.WindowsSelectorEventLoopPolicy()
)
```

This allowed the asynchronous Agent workflow to operate more reliably inside the WinForms application.

---

# 🔌 Unified Response Format

Another important design decision was creating a common response format for both systems.

Instead of making the C# UI understand two completely different response structures, both the RAG pipeline and Agent return a unified JSON structure.

Conceptually:

```json
{
  "text": "Generated answer...",
  "images": [
    "image_url"
  ],
  "audio": "audio_file",
  "metadata": {
    "source": "agent",
    "processing_time": 2.8
  }
}
```

This means the UI layer doesn't need separate rendering logic for RAG and Agent responses.

```text
                 ┌───────────────┐
                 │      RAG      │
                 └───────┬───────┘
                         │
                         ▼
                  Unified JSON
                         ▲
                         │
                 ┌───────┴───────┐
                 │     Agent     │
                 └───────────────┘
                         │
                         ▼
                  C# UI Renderer
```

This significantly simplifies the integration between the AI layer and the desktop application.

---

# ⏱️ Performance

Response times were tracked using **LangSmith** across the different Agent tools.

The observed average response time was approximately:

> **2–3.5 seconds**

This includes workflows involving tools such as:

* Internal search
* Web search
* Image retrieval
* Text-to-speech

Performance naturally depends on which tools the Agent decides to use and how many iterations are required.

---

# 📊 What I Learned

The biggest lesson from the project was that building an Agent is not simply about connecting an LLM to multiple tools.

The more difficult problem is **controlling the decision-making process**.

An Agent needs to know:

* When should it search?
* Which search should it use?
* When should it use the web?
* When does it need an image?
* When should it generate audio?
* When does it have enough information?
* How can it avoid repeating the same action?

Adding more tools increases capabilities, but it also increases the number of possible paths through the system.

---

# 🆚 When Should You Use RAG vs an Agent?

A simple RAG pipeline is usually preferable when the workflow is predictable.

### Choose RAG when:

* You have a well-defined knowledge base
* Every query follows roughly the same workflow
* You primarily need document retrieval
* Low latency is important
* You want a simpler architecture
* You want easier debugging and maintenance

```text
Query
 ↓
Retrieve
 ↓
Generate
 ↓
Answer
```

### Consider an Agent when:

* Different questions require different tools
* The system needs web access
* Multiple actions may be required
* The workflow cannot be known in advance
* The system needs iterative reasoning
* The Agent needs to decide what to do next

```text
Query
 ↓
Reason
 ↓
Choose Tool
 ↓
Observe
 ↓
Reason
 ↓
Choose Tool
 ↓
Answer
```

The Agent's additional complexity is justified when the **workflow itself needs to be dynamic**.

---

# 🛠️ Tech Stack

### AI / LLM

* Python
* LangChain
* LangGraph
* RAG
* ReAct
* Hybrid Retrieval

### Search / Retrieval

* BM25
* Vector Search
* ChromaDB
* EnsembleRetriever

### Agent Observability

* LangSmith

### Application

* C#
* Windows Forms
* Python.NET / pythonnet

### Additional Capabilities

* Web Search
* Image Retrieval
* Text-to-Speech
* Async Python
* JSON-based communication

---

# 📁 High-Level Project Structure

A possible structure for the project is:

```text
project/
│
├── agent/
│   ├── graph.py
│   ├── state.py
│   └── tools/
│       ├── search.py
│       ├── web_search.py
│       ├── images.py
│       └── tts.py
│
├── rag/
│   ├── retriever.py
│   ├── embeddings.py
│   └── chain.py
│
├── data/
│   └── samalut_history/
│
├── integration/
│   └── python_bridge.py
│
├── winforms/
│   └── C# application
│
└── README.md
```

---

# 🚀 Key Takeaway

This project started with a simple question:

> **What actually makes an AI Agent different from RAG?**

After implementing both systems, the distinction became much clearer.

**RAG is primarily a retrieval pipeline.**

**An Agent is a decision-making system that can use retrieval and other tools as part of a dynamic workflow.**

The challenge isn't making an LLM call a tool.

The challenge is designing a system where the model can make **useful, controlled decisions about when and why to use that tool.**

---

# 🎥 Demo

A 3-minute technical walkthrough of the project is available here:

**[Add your demo video link here]**

---

# 🔮 Future Improvements

Some areas I'd like to explore next:

* Better Agent routing and tool selection
* More robust error handling
* Improved latency
* Streaming Agent responses
* More structured state management
* Better evaluation of RAG vs Agent quality
* Automated Agent evaluation with LangSmith
* More advanced memory strategies
* Improved tool-call observability
* Containerized deployment

---

# 🙏 Feedback

This is still an early step in my LangGraph journey.

If you've built RAG systems or production Agents before, I'd love to hear your thoughts:

**Where do you draw the line between a RAG pipeline and an Agent?**

And more importantly:

**When does the additional complexity of an Agent actually pay off?**

---

## 📌 Topics

`LangGraph` `LangChain` `RAG` `AI Agents` `ReAct` `Python` `C#` `Python.NET` `ChromaDB` `LangSmith` `WinForms` `BM25` `Vector Search` `Hybrid Search` `LLM`
