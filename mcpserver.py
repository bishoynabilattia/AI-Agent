from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings as embed
from ddgs import DDGS
import os
# from mcp.server import FastMCP
from dotenv import load_dotenv
load_dotenv()
from PIL import Image
import edge_tts as tts
import tempfile
import uuid


from langchain_core.tools import tool

# mcp=FastMCP()
# =========================================================================
# @mcp.tool(name="Web_search")
@tool
def search(query:str)->str:
    "use this tool when user asks you about information that not in RAG or recently published"
    if len(query)>300:
        return "too requests,finish srearch "
    with DDGS() as ddg:
        result= ddg.text(query,max_results=3,safesearch="on")
        lsit_result=[]
        for i in result:
            lsit_result.append(f"\n\n title:{i['title']},\n href:{i['href']},\n body:{i['body']}")

        return "\n".join(lsit_result)

# =================================setup RAG===================================

embed_fn=embed(model="models/gemini-embedding-2", api_key=os.getenv("google_API"),
    output_dimensionality=768)
name="final_stable_step"
vectorstore=Chroma(collection_name=name,embedding_function=embed_fn,
                       persist_directory=os.path.abspath(os.getenv("VECTOR_PATH"))
                        )
retriver=vectorstore.as_retriever(search_type="similarity",search_kwargs={"k":3})

# ======================================RAG_Tool==================================
# mcp.tool(name="RAG")
@tool
def dataset(query:str)->str:
    """Use this tool to answer *TEXT QUESTIONS* about the History of the Diocese of Samalut.
    Use it whenever the user asks about facts, events, people, dates, or general information.
    Do NOT use this tool if the user is asking to see or view an image or photo."""
    docs=retriver.invoke(query)
    if not docs:
        return "no docs are found!"
    list_doc=[]
    for i, doc in enumerate(docs):
        list_doc.append(f"{i+1}: {doc.page_content}")
    return "\n\n".join(list_doc)
# =======================================IMAGE_TOOL=================================
# mcp.tool(name="Image tool")
@tool
def img(query: str):
    """Use this tool ONLY when the user explicitly asks to see, show, view, or display an IMAGE or PHOTO
    related to the History of the Diocese of Samalut. Do NOT use this tool for general text questions."""
    doc = retriver.invoke(query)
    if not doc:  
        return "No image found for this query. Do not call this tool again for the same request."
    print("+++++++++++++++++++++++++++++++++++++")
    print("img tool has been called")
    print("+"*13)
    metadata = doc[0].metadata
    image_url = metadata.get('image_url')
    if not image_url:
        return "No image available for this topic. Do not call this tool again for the same request."
    # g = Image.open(image_url)
    # g.show()

    return {
        "type": "image",
        "format": "png",
        "data": image_url,
        "message": "The image has been successfully prepared for the user. Task complete."
    }
    
    # return "The image has been successfully opened and shown to the user. Task complete."
# =============================================================================

# mcp.tool(name="Voice TTS TOOL")
@tool
async def voice(last_answer: str):
    """Use this tool ONLY when the user explicitly requests to listen to or hear the last assistant response as AUDIO/VOICE (e.g., 'read your last answer', 'speak this out loud').
    Convert the assistant's previous text reply into speech. 
    Do NOT call this tool for standard text queries, image requests, or if there is no prior assistant response to convert."""
    try:
        text = last_answer
        voice_name = "ar-EG-ShakirNeural"
        com = tts.Communicate(text, voice_name, rate="+0%", volume="+16%")
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"tts_{uuid.uuid4().hex}.mp3")

        with open(file_path, "wb") as f:
            async for chunk in com.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
        return {
    "type": "audio",
    "format": "mp3",
    "data": file_path,
    "message": "Task completed print ('TTS called')"
}

    except Exception as e:
        print(f"حدث خطأ أثناء تحويل النص إلى صوت: {e}")
        raise



