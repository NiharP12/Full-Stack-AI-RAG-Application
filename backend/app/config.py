"""
Application configuration module.
Loads settings from environment variables and .env file using Pydantic BaseSettings.
"""

import os
from pathlib import Path
from typing import List

from pydantic import BaseSettings, Field


# Resolve the project root (two levels up from this file: backend/app/config.py -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Central configuration loaded from environment variables / .env file."""

    # ----- LLM Provider -----
    llm_provider: str = Field("ollama", env="LLM_PROVIDER", description="LLM backend: 'openai' or 'ollama'")

    # OpenAI
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-3.5-turbo", env="OPENAI_MODEL")

    # Ollama
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field("llama3", env="OLLAMA_MODEL")

    # ----- Embeddings -----
    embedding_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL",
    )

    # ----- Vector Store -----
    vector_store_path: str = Field("./vectorstore", env="VECTOR_STORE_PATH")
    vector_store_type: str = Field("faiss", env="VECTOR_STORE_TYPE")

    # ----- Document Processing -----
    chunk_size: int = Field(1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    allowed_extensions: str = Field(
        ".pdf,.txt,.docx,.doc,.csv,.xlsx",
        env="ALLOWED_EXTENSIONS",
    )

    # ----- Retrieval -----
    top_k_results: int = Field(5, env="TOP_K_RESULTS")
    similarity_threshold: float = Field(0.3, env="SIMILARITY_THRESHOLD")

    # ----- Server -----
    backend_host: str = Field("0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(8000, env="BACKEND_PORT")
    frontend_url: str = Field("http://localhost:4200", env="FRONTEND_URL")

    # ----- Logging -----
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("./logs/app.log", env="LOG_FILE")

    # ----- Upload -----
    upload_dir: str = Field("./uploads", env="UPLOAD_DIR")

    # ----- Chat History -----
    chat_history_dir: str = Field("./chat_history", env="CHAT_HISTORY_DIR")
    max_conversation_memory: int = Field(10, env="MAX_CONVERSATION_MEMORY")

    class Config:
        env_file = str(_PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False

    # ----- Computed helpers -----

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Return allowed extensions as a list."""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Max upload size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        for dir_path in [self.upload_dir, self.vector_store_path, self.chat_history_dir, os.path.dirname(self.log_file)]:
            os.makedirs(dir_path, exist_ok=True)


# Singleton settings instance
settings = Settings()
