from __future__ import annotations

import getpass

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from Backend.config.secrets import ensure_config_secret_file

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


def configure_secrets() -> None:
    path = ensure_config_secret_file()
    api_key = getpass.getpass("Enter API key: ")
    base_url = input("Enter Base URL: ").strip()
    path.write_text(f'api_key = "{api_key}"\nbase_url = "{base_url}"\n', encoding="utf-8")
    print(f"Credentials saved to {path}")


if __name__ == "__main__":
    configure_secrets()
