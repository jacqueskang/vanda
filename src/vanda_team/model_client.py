"""Model client initialization."""

import os

from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.openai import OpenAIChatClient
from azure.identity.aio import DefaultAzureCredential

from vanda_team import config as _config  # Loads .env


async def get_model_client():
    """Initialize the model client based on configuration."""
    model_endpoint = os.getenv("MODEL_ENDPOINT", "https://models.github.ai/inference/").strip()
    model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini").strip()
    github_token = os.getenv("GITHUB_TOKEN", "").strip()

    if "models.github.ai" in model_endpoint or model_endpoint.startswith("https://models"):
        if not github_token:
            raise ValueError(
                "GitHub token not found. Please:\n"
                "1. Create a token at: https://github.com/settings/tokens\n"
                "2. Set GITHUB_TOKEN in .env file\n"
                "3. Re-run this script"
            )

        client = OpenAIChatClient(
            base_url=model_endpoint,
            model_id=model_name,
            api_key=github_token,
        )
        return client

    credential = DefaultAzureCredential()
    endpoint = model_endpoint
    deployment = model_name

    if not endpoint or endpoint.startswith("https://models"):
        raise ValueError(
            "Azure Foundry endpoint not configured. Please:\n"
            "1. Set up an Azure AI Foundry project\n"
            "2. Update MODEL_ENDPOINT in .env\n"
            "3. Update MODEL_NAME in .env"
        )

    client = AzureOpenAIChatClient(
        endpoint=endpoint,
        deployment_name=deployment,
        ad_token_provider=credential,
    )

    return client


__all__ = ["get_model_client"]
