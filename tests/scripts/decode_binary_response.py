import base64
from pathlib import Path


def decode_file(base64_str: str, output_path: Path) -> None:
    """Save base64-encoded binary file to disk."""
    data = base64.b64decode(base64_str)
    with output_path.open(mode="wb") as f:
        f.write(data)


def main():
    """Entrypoint."""
    base64_str = ""
    output_path = Path("decoded.tar.gz")
    decode_file(base64_str, output_path)
    print(f"Decoded file saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
