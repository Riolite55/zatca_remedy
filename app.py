import streamlit as st
import os
import asyncio
import sys
import threading
import queue
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Remedy AI Support Agent", page_icon="🎫")
st.title("🎫 Remedy AI Support Agent")

# Check for API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    st.warning("⚠️ Please set your GEMINI_API_KEY in the .env file.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pydantic_messages" not in st.session_state:
    st.session_state.pydantic_messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def run_agent_in_thread(prompt: str, pydantic_messages: list) -> tuple[str, list]:
    """Runs the asyncio event loop in a dedicated background thread to avoid Streamlit event loop clashes."""
    q = queue.Queue()
    
    async def _ask_agent_wrapper():
        async with MCPServerStdio(sys.executable, args=["remedy_mcp.py"]) as server:
            agent = Agent(
                'gemini-2.5-flash',
                system_prompt=(
                    "You are a Support Manager AI working with a local BMC Remedy system. "
                    "You must use your tools to fetch incidents. "
                    "Always look up tickets using your tools before answering, filter the raw JSON data effectively, "
                    "and provide concise, helpful summaries based on the user's request."
                ),
                toolsets=[server]
            )
            result = await agent.run(prompt, message_history=pydantic_messages)
            return result.output, result.all_messages()

    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            output, new_messages = loop.run_until_complete(_ask_agent_wrapper())
            q.put(("success", (output, new_messages)))
        except Exception as e:
            q.put(("error", e))
        finally:
            loop.close()
            
    thread = threading.Thread(target=_worker)
    thread.start()
    thread.join()
    
    status, result = q.get()
    if status == "error":
        raise result
    return result

if prompt := st.chat_input("Ask about Remedy tickets..."):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking & querying Remedy..."):
            try:
                # Execute in an isolated thread passing the message history safely
                response, updated_messages = run_agent_in_thread(prompt, st.session_state.pydantic_messages)
                st.session_state.pydantic_messages = updated_messages
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error communicating with Agent or Remedy: {e}")
