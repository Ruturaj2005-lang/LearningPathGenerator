import streamlit as st
from utils import run_agent_sync

st.set_page_config(page_title="MCP POC", page_icon="🤖", layout="wide")
st.title("Model Context Protocol (MCP) - Learning Path Generator")

# Initialize session state
for key in ["current_step", "progress", "last_section", "is_generating"]:
    st.session_state.setdefault(key, "" if "step" in key else 0 if "progress" in key else False)

# Sidebar Inputs
st.sidebar.header("🔧 Configuration")
google_api_key = st.sidebar.text_input("Google API Key", type="password")

st.sidebar.subheader("Pipedream URLs")
youtube_url = st.sidebar.text_input("YouTube (Required)", placeholder="Enter Pipedream YouTube URL")
drive_url = st.sidebar.text_input("Google Drive", placeholder="Enter Pipedream Drive URL")
notion_url = st.sidebar.text_input("Notion", placeholder="Enter Pipedream Notion URL")

# Info Guide
st.info("""
**Quick Guide**  
1. Enter your Google API key and YouTube URL  
2. Optionally add Drive or Notion integration  
3. Enter a clear learning goal, for example:
    - "I want to learn python basics in 3 days"
    - "I want to learn data science basics in 10 days"
""")

# Goal Input
st.header("🎯 Define Your Goal")
user_goal = st.text_input("Learning Goal", help="e.g., Learn web dev in 7 days")

# Progress UI
progress_bar = st.empty()
progress_container = st.container()

def update_progress(msg: str):
    st.session_state.current_step = msg
    section_map = {
        "Setting up agent with tools": ("Setup", 0.1),
        "Added Google Drive integration": ("Integration", 0.2),
        "Added Notion integration": ("Integration", 0.2),
        "Creating AI agent": ("Setup", 0.3),
        "Generating your learning path": ("Generation", 0.5),
        "Learning path generation complete": ("Complete", 1.0)
    }

    section, prog = section_map.get(msg, (st.session_state.last_section or "Progress", st.session_state.progress))
    st.session_state.progress = prog
    st.session_state.last_section = section
    st.session_state.is_generating = (section != "Complete")

    progress_bar.progress(prog)
    with progress_container:
        prefix = "✓" if prog >= 0.5 else "→"
        if msg == "Learning path generation complete":
            st.success("All steps completed! 🎉")
        else:
            st.write(f"{prefix} {msg}")

# Trigger Learning Path Generation
if st.button("🚀 Generate Learning Path", type="primary", disabled=st.session_state.is_generating):
    if not google_api_key:
        st.error("Google API Key is required.")
    elif not youtube_url:
        st.error("YouTube Pipedream URL is required.")
    elif not user_goal:
        st.warning("Please enter your learning goal.")
    else:
        st.session_state.is_generating = True
        st.session_state.progress = 0
        st.session_state.current_step = ""
        st.session_state.last_section = ""

        try:
            result = run_agent_sync(
                google_api_key=google_api_key,
                youtube_pipedream_url=youtube_url,
                drive_pipedream_url=drive_url,
                notion_pipedream_url=notion_url,
                user_goal=user_goal,
                progress_callback=update_progress
            )

            st.header("📘 Your Learning Path")
            if result and "messages" in result:
                for msg in result["messages"]:
                    st.markdown(f" {msg.content}")
            else:
                st.error("No learning path generated. Try again.")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            st.session_state.is_generating = False
