import re
from pathlib import Path


def _extract_css_classes(html: str) -> list[str]:
    # Find all class="..." and class='...'
    class_regex = re.compile(r'class\s*=\s*["\']([^"\']+)["\']')
    classes = set()
    for match in class_regex.finditer(html):
        for cls in match.group(1).split():
            classes.add(cls)
    return sorted(classes)


def main() -> None:
    """Entrypoint."""
    search_path = Path("src/lantern/resources/templates")
    output_path = Path("./css-audit.txt")
    classes = []

    for html_file in search_path.rglob("*.html.j2"):
        with html_file.open("r", encoding="utf-8") as f:
            content = f.read()
        classes.extend(_extract_css_classes(content))

    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(sorted(set(classes))))
    print(f"Classes written to {output_path.resolve()}")


if __name__ == "__main__":
    main()
