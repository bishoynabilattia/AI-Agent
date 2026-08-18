from typing import TypedDict,Annotated,Sequence
from langgraph.graph import StateGraph,START,END
from langchain_core.messages import BaseMessage,HumanMessage,SystemMessage, AIMessage,ToolMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
import os
import json
from dotenv import load_dotenv
load_dotenv()
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
# ========================================================================
from langchain_google_genai import GoogleGenerativeAIEmbeddings as embed
embed_fn=embed(model="models/gemini-embedding-2", api_key=os.getenv("GOOGLE_API"),
    output_dimensionality=768)
checkpointer = InMemorySaver()
store = InMemoryStore()





from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI as gemy


# ========================TOOLS=====================================

from mcpserver import img,voice, dataset,search
# import arabic_reshaper
from bidi.algorithm import get_display

from langsmith import traceable

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY") 
os.environ["LANGCHAIN_PROJECT"] = "Church-History-RAG"


def reshape(text):
    if isinstance(text,list):
        ec=[]
        for i in text:
            if isinstance(i,dict) and "text" in i:
                ec.append(i['text'])
            elif isinstance(i,str):
                ec.append(i)
        text="\n".join(ec)
    elif isinstance(text,dict):
        text=text.get("text",str(text))
    res = str(text)
    finaltext = res
    return finaltext


google=gemy(model="gemini-3.1-flash-lite",temperature=0.1, api_key=os.getenv("GOOGLE_API"))
groq=ChatGroq(model="openai/gpt-oss-120b",temperature=0,api_key=os.getenv("groq_API"))
prompt_V1=prompt_V1 = """أنت مساعد ذكي متخصص ومباشر تجيب باللغة العربية.

قواعد الاستجابة الصارمة (Conciseness Rules):
1. أجب عن سؤال المستخدم مباشرة وبأقل عدد ممكن من الكلمات دون تمهيد أو مقدمات.
2. يمنع تماماً استخدام الجمل الترحيبية الختامية مثل: "هل هناك شيء آخر..." أو "أتمنى لك يوماً سعيداً".
3. يمنع الإشارة إلى سياق المحادثة كعبارات: "كما ذكرت سابقاً" أو "بناءً على تعريفك لنفسك".
4. لا تستخدم الإيموجي نهائياً في الإجابات.
5. لا تقم باستدعاء أي أداة في حالة التحيات أو الأسئلة العادية.
6. قلل عدد الكلمات الناتجة وقصر من الاجابة 
"""
prompt=SystemMessage(content=prompt_V1)
class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage],add_messages]



tools=[img,voice,dataset,search]
g=google.bind_tools(tools=tools)
gr=groq.bind_tools(tools=tools)
@traceable(name="chat")
def gemy_llm_fn(state:AgentState)->AgentState:
    message=list(state["messages"]) + [prompt]
    re=g.invoke(message)
    # s=AIMessage(content=re.content)
    return {"messages":re}

def groq_llm_fn(state:AgentState)->AgentState:
    message=list(state["messages"]) + [prompt]
    re=gr.invoke(message)
    # s=AIMessage(content=re.content)
    return {"messages":re}

def route (state:AgentState):
    result= state["messages"][-1]
    if hasattr(result,'tool_calls')and len(result.tool_calls)>0:
        return True
    elif not hasattr(result,'tool_calls'):
         return False
    return False
    

graph=StateGraph(AgentState)
graph.add_node("llm",gemy_llm_fn)
tool_node=ToolNode(tools=tools)
graph.add_node("tool",tool_node)
graph.add_edge(START,"llm")
graph.add_conditional_edges("llm",route,
                            {True:"tool",
                            False:END}
                            )
graph.add_edge("tool","llm")
app=graph.compile(checkpointer=checkpointer,store=store)

import ast

async def run_ai(userin):
    config = {"configurable": {"thread_id": "session_1"}}
    user_input = userin
    if user_input.lower() in ["finishe", "quite", "q"]:
        return json.dumps({"text": f"USER: {user_input}", "media": []})

    user = HumanMessage(content=user_input)
    result = await app.ainvoke({'messages': [user]}, config=config)

    messages = result["messages"]
    final_content = messages[-1].content
    if isinstance(final_content, list):
        final_content = "\n".join(
            i.get("text", "") if isinstance(i, dict) else str(i)
            for i in final_content
        )

    media = []
    for m in messages:
        if isinstance(m, ToolMessage):
            content = m.content
            parsed = None
            if isinstance(content, dict):
                parsed = content
            elif isinstance(content, str):
                try:
                    parsed = ast.literal_eval(content) 
                except Exception:
                    parsed = None
            if isinstance(parsed, dict) and parsed.get("type") in ("image", "audio"):
                media.append({
                    "type": parsed["type"],
                    "format": parsed.get("format", "png" if parsed["type"] == "image" else "mp3"),
                    "data": parsed.get("data")
                })

    return json.dumps({"text": final_content, "media": media})























