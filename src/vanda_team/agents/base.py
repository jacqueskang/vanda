"""Base team agent class with shared properties and methods."""

from agent_framework import ChatAgent, Executor


class BaseTeamAgent(Executor):
    """Base agent with shared metadata."""

    key: str = ""
    name: str = ""
    gender: str = ""
    role_title: str = ""
    avatar_url: str = ""
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
