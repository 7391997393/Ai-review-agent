from dataclasses import dataclass
import os


def _clean_env(key: str) -> str | None:
    """Read an env var and return None if it is absent, blank, or a CI mask.

    GitHub Actions injects empty strings for undefined repository variables,
    and masked secrets appear as '***' (sometimes with trailing whitespace).
    Either value would be forwarded verbatim to the HTTP client and cause
    ``httpcore.LocalProtocolError: Illegal header value``.
    """
    value = os.getenv(key, "").strip()
    if not value or set(value) <= {"*"}:
        return None
    return value


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
        gemini_key = _clean_env("GEMINI_API_KEY")
        openai_key = _clean_env("OPENAI_API_KEY")

        using_gemini = bool(gemini_key and not openai_key)
        api_key = openai_key or gemini_key

        github_token = _clean_env("GITHUB_PERSONAL_ACCESS_TOKEN")
        github_owner = _clean_env("GITHUB_OWNER")
        github_repo = _clean_env("GITHUB_REPO")

        missing = []

        if not api_key:
            missing.append("GEMINI_API_KEY or OPENAI_API_KEY")

        if not github_token:
            missing.append("GITHUB_PERSONAL_ACCESS_TOKEN")

        if not github_owner:
            missing.append("GITHUB_OWNER")

        if not github_repo:
            missing.append("GITHUB_REPO")

        if missing:
            raise RuntimeError(
                "Missing environment variables: " + ", ".join(missing)
            )

        return cls(
            openai_api_key=api_key,
            openai_model=(
                _clean_env("OPENAI_MODEL")
                or ("gemini-2.5-flash" if using_gemini else "gpt-4o-mini")
            ),
            openai_base_url=(
                _clean_env("OPENAI_BASE_URL")
                or (
                    "https://generativelanguage.googleapis.com/v1beta/openai/"
                    if using_gemini
                    else None
                )
            ),
            github_token=github_token,
            github_owner=github_owner,
            github_repo=github_repo,
        )