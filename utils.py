from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from prompt import user_goal_prompt
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional, Callable
import asyncio

cfg = RunnableConfig(recursion_limit=100)

def initialize_model(google_api_key: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key
    )

async def setup_agent_with_tools(
    google_api_key: str,
    youtube_pipedream_url: str,
    drive_pipedream_url: Optional[str] = None,
    notion_pipedream_url: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None
):
    try:
        if progress_callback:
            progress_callback("Setting up agent with tools")

        tools_config = {
            "youtube": {
                "url": youtube_pipedream_url,
                "transport": "streamable_http"
            }
        }

        if drive_pipedream_url:
            tools_config["drive"] = {
                "url": drive_pipedream_url,
                "transport": "streamable_http"
            }
            if progress_callback:
                progress_callback("Added Google Drive integration")

        if notion_pipedream_url:
            tools_config["notion"] = {
                "url": notion_pipedream_url,
                "transport": "streamable_http"
            }
            if progress_callback:
                progress_callback("Added Notion integration")

        mcp_client = MultiServerMCPClient(tools_config)
        tools = await mcp_client.get_tools()
        agent = create_react_agent(initialize_model(google_api_key), tools)

        if progress_callback:
            progress_callback("Creating AI agent")
        return agent
    except Exception as e:
        print(f"Error in setup_agent_with_tools: {str(e)}")
        raise

def run_agent_sync(
    google_api_key: str,
    youtube_pipedream_url: str,
    drive_pipedream_url: Optional[str] = None,
    notion_pipedream_url: Optional[str] = None,
    user_goal: str = "",
    progress_callback: Optional[Callable[[str], None]] = None
) -> dict:
    async def _run():
        agent = await setup_agent_with_tools(
            google_api_key=google_api_key,
            youtube_pipedream_url=youtube_pipedream_url,
            drive_pipedream_url=drive_pipedream_url,
            notion_pipedream_url=notion_pipedream_url,
            progress_callback=progress_callback
        )

        if progress_callback:
            progress_callback("Generating your learning path")

        # Notion-specific instruction
        learning_path_prompt = (
            f"User Goal: {user_goal}\n"
            f"{user_goal_prompt}\n"
            f"Now structure the output clearly and save the full learning plan into Notion. "
            f"Include sections, titles, and descriptions for each day."
        )

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=learning_path_prompt)]},
            config=cfg
        )

        if progress_callback:
            progress_callback("Learning path generation complete")
        return result

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
