"""Centralized configuration for DevAgent using Pydantic Settings."""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Sandbox and workspace configuration
    sandbox_root: Path = Field(
        default=Path("./sandboxes"),
        description="Root directory under which all session sandboxes are created",
    )

    # Agent execution limits
    max_agent_iterations: int = Field(
        default=8,
        description="Global maximum turns allowed for the agent loop",
    )
    max_tool_calls: int = Field(
        default=20,
        description="Maximum total tool executions permitted per session",
    )
    max_verification_attempts: int = Field(
        default=5,
        description="Maximum test suite execution attempts permitted",
    )
    max_runtime_seconds: int = Field(
        default=300,
        description="Maximum wall-clock execution time for a session in seconds",
    )

    # Tool limits
    max_read_file_lines: int = Field(
        default=150,
        description="Maximum number of lines returned by read_file_lines",
    )
    max_directory_depth: int = Field(
        default=2,
        description="Maximum recursion depth for list_directory",
    )
    max_directory_entries: int = Field(
        default=200,
        description="Maximum entries returned in a directory listing",
    )
    max_search_matches: int = Field(
        default=15,
        description="Maximum match entries returned by search_code",
    )
    verification_timeout_seconds: int = Field(
        default=60,
        description="Subprocess timeout for verification commands in seconds",
    )
    max_verification_output_chars: int = Field(
        default=20000,
        description="Maximum characters preserved from verification stdout/stderr",
    )

    # LLM Provider configuration
    llm_provider: str = Field(
        default="mock",
        description="Active provider identifier: 'mock', 'gemini', 'openai', 'anthropic'",
    )
    llm_model: str = Field(
        default="mock-model",
        description="Underlying model name/ID for the provider",
    )
    gemini_api_key: str | None = Field(
        default=None,
        description="API key for Google Gemini provider",
    )
    openai_api_key: str | None = Field(
        default=None,
        description="API key for OpenAI-compatible provider",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="API key for Anthropic provider",
    )


def get_settings() -> Settings:
    """Factory function for settings dependency injection."""
    return Settings()
