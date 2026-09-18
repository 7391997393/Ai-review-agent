from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    openai_api_key: str
    openai_model: str
    openai_base_url: str | None
    github_token: str
    github_owner: str
    github_repo: str

    @classmethod
    def from_env(cls) -> "Settings":
        # Gemini exposes an OpenAI-compatible API, so we keep the existing
        # ChatOpenAI integration while allowing a Gemini-specific key name.
        required = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENAI_API_KEY"),
            "OPENAI_MODEL": os.getenv("OPENAI_MODEL"),
            "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv(
                "GITHUB_PERSONAL_ACCESS_TOKEN"
            ),
        }

        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                f"Missing environment variables: {', '.join(missing)}"
            )

        return cls(
            openai_api_key=required["GEMINI_API_KEY"],
            openai_model=required["OPENAI_MODEL"],
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            github_token=required["GITHUB_PERSONAL_ACCESS_TOKEN"],
            github_owner=os.getenv("GITHUB_OWNER", ""),
            github_repo=os.getenv("GITHUB_REPO", ""),
        )
