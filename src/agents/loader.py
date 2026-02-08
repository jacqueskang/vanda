"""Agent loader for loading agents from YAML configuration files."""

from pathlib import Path
from typing import Dict, Any, Type
import yaml  # type: ignore

from .base import BaseAgent


class AgentLoader:
    """Loads agents from YAML configuration files."""

    CONFIG_DIR = Path(__file__).parent / "config"

    @classmethod
    async def load_all(cls) -> Dict[str, BaseAgent]:
        """Load all agents from YAML files in config directory.

        Returns:
            Dict[str, BaseAgent]: Dictionary mapping agent keys to agent instances.

        Raises:
            ValueError: If no YAML files found in config directory.
        """
        agents = {}

        # Get all YAML files in config directory
        yaml_files = sorted(cls.CONFIG_DIR.glob("*.yaml"))

        if not yaml_files:
            raise ValueError(f"No agent configuration files found in {cls.CONFIG_DIR}")

        for yaml_file in yaml_files:
            config = cls._load_yaml(yaml_file)
            if config:
                agent_key = config.get("key")
                # Check if there's a custom agent class for this key
                if agent_key is not None:
                    agent_class = cls._get_agent_class(agent_key)
                    agent = await agent_class.create(config)
                if agent_key:
                    agents[agent_key] = agent

        return agents

    @classmethod
    def load_agent(cls, agent_key: str) -> Dict[str, Any]:
        """Load a single agent configuration from YAML file.

        Args:
            agent_key: The agent key (filename without .yaml extension).

        Returns:
            Dict[str, Any]: Agent configuration dictionary.

        Raises:
            FileNotFoundError: If config file not found for agent.
        """
        yaml_file = cls.CONFIG_DIR / f"{agent_key}.yaml"

        if not yaml_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found for agent '{agent_key}' at {yaml_file}"
            )

        config = cls._load_yaml(yaml_file)
        if not config:
            raise ValueError(f"Failed to load configuration from {yaml_file}")

        return config

    @staticmethod
    def _get_agent_class(agent_key: str) -> Type[BaseAgent]:
        """Get the agent class for a given agent key.

        Checks if there's a custom agent class in the agents module,
        otherwise returns BaseAgent.

        Args:
            agent_key: The agent key.

        Returns:
            Type[BaseAgent]: The agent class to use.
        """
        # Import here to avoid circular imports
        from . import router

        # Map of agent keys to custom classes
        custom_classes = {
            "router": router.RouterAgent,
        }

        return custom_classes.get(agent_key, BaseAgent)

    @staticmethod
    def _load_yaml(yaml_file: Path) -> Dict[str, Any]:
        """Load and parse a YAML file.

        Args:
            yaml_file: Path to YAML file.

        Returns:
            Dict[str, Any]: Parsed YAML content.
        """
        try:
            with open(yaml_file, "r") as f:
                content = yaml.safe_load(f)
                return content if isinstance(content, dict) else {}
        except Exception as e:
            print(f"Error loading YAML file {yaml_file}: {e}")
            return {}
