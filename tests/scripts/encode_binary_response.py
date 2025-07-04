import base64
from pathlib import Path


def encode_file(input_path: Path) -> str:
    """Encode file from disk as base64."""
    with open(input_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def main():
    """Entrypoint."""
    input_path = Path("x-main-abc123.tar.gz")
    base64_str = encode_file(input_path)
    print(f"Encoded file: '{base64_str}'")


if __name__ == "__main__":
    main()
