"""Base team agent class with shared properties and methods."""

from agent_framework import ChatAgent, Executor
from vanda_team.model_client import get_model_client


class BaseTeamAgent(Executor):
    """Base agent with shared metadata."""

    key: str = ""
    name: str = ""
    gender: str = ""
    role_title: str = ""
    avatar_url: str = ""
    model_name: str = ""
    tools: list = []
    personality: str = ""
    focus_areas: list[str] = []
    role_description: str = ""  # Override in subclasses for specific role instructions
    agent: ChatAgent

    def __init__(self, agent: ChatAgent, id: str):
        self.agent = agent
        super().__init__(id=id)

    @classmethod
    def metadata(cls) -> dict:
        return {
            "key": cls.key,
            "name": cls.name,
            "gender": cls.gender,
            "role": cls.role_title,
            "avatar_url": cls.avatar_url,
            "model_name": cls.model_name,
        }

    @classmethod
    def build_instructions(cls, mission: str, tools_info: str = "") -> str:
        """Build instructions dynamically from class properties."""
        focus_text = "\n".join(f"{i+1}. {area}" for i, area in enumerate(cls.focus_areas))
        
        instructions = f"{mission}\n\n"
        instructions += f"You are {cls.name}, {cls.role_description}\n\n"
        instructions += f"PERSONALITY: {cls.personality}\n\n"
        instructions += f"FOCUS AREAS:\n{focus_text}\n"
        
        if tools_info:
            instructions += f"\n{tools_info}\n"
        
        instructions += "\nKeep responses short and high-signal (3-6 bullets or 1-2 short paragraphs)."
        return instructions

    @classmethod
    def build_instructions_with_tools(cls, mission: str) -> str:
        """Build instructions with tools (for Strategy agent)."""
        focus_text = "\n".join(f"{i+1}. {area}" for i, area in enumerate(cls.focus_areas))
        
        tools_info = (
            "You have access to research tools:\n"
            "- strategy_web_search: Web search for market data\n"
            "- strategy_wikipedia_lookup: Background research\n"
            "- strategy_fetch_url: Fetch public sources\n"
            "\nUse these tools when you need real-world data."
        )
        
        instructions = f"{mission}\n\n"
        instructions += f"You are {cls.name}, {cls.role_description}\n\n"
        instructions += f"PERSONALITY: {cls.personality}\n\n"
        instructions += f"FOCUS AREAS:\n{focus_text}\n\n"
        instructions += tools_info
        instructions += "\n\nKeep responses short and high-signal (3-6 bullets or 1-2 short paragraphs)."
        return instructions

    @classmethod
    async def create_agent(
        cls,
        default_client: ChatAgent,
        mission: str,
        instruction_suffix: str = "",
        client_cache: dict | None = None,
    ) -> ChatAgent:
        """Create an agent instance with optional custom model."""
        if client_cache is None:
            client_cache = {}
        
        # Get the right client based on model_name
        model_name = cls.model_name.strip() if cls.model_name else ""
        if model_name and model_name not in client_cache:
            client_cache[model_name] = await get_model_client(model_name)
        
        client = client_cache.get(model_name, default_client) if model_name else default_client
        
        # Build instructions
        if cls.tools:
            instructions = cls.build_instructions_with_tools(mission)
        else:
            instructions = cls.build_instructions(mission)
        instructions += instruction_suffix
        
        # Create agent
        if cls.tools:
            return client.create_agent(
                name=f"{cls.__name__}",
                instructions=instructions,
                tools=cls.tools,
            )
        return client.create_agent(
            name=f"{cls.__name__}",
            instructions=instructions,
        )
