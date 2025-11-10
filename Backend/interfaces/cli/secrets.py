from __future__ import annotations

import getpass

from Backend.config.secrets import ensure_user_secret_file


def configure_secrets() -> None:
    path = ensure_user_secret_file()
    api_key = getpass.getpass("Enter API key: ")
    base_url = input("Enter Base URL: ").strip()
    path.write_text(f'api_key = "{api_key}"\nbase_url = "{base_url}"\n', encoding="utf-8")
    print(f"Credentials saved to {path}")


if __name__ == "__main__":
    configure_secrets()
