import re
from pathlib import Path


def _extract_css_classes(html: str) -> list[str]:
    # Find all class="..." and class='...'
    class_regex = re.compile(r'class\s*=\s*["\']([^"\']+)["\']')
    exclude = ["%}", "{%", "%}", "{{", "}}", "{%", "%}{{", "if", "endif"]
    classes = set()
    for match in class_regex.finditer(html):
        for cls in match.group(1).split():
            if cls not in exclude:
                cls = cls.replace("%}", "").replace("{%", "").replace("}}", "")
                classes.add(cls)
    return sorted(classes)


def _get_template_classes(search_path: Path) -> list[str]:
    classes = []
    for html_file in search_path.rglob("*.html.j2"):
        with html_file.open("r", encoding="utf-8") as f:
            content = f.read()
        classes.extend(_extract_css_classes(content))
    classes.append("!! DOES NOT INCLUDE CLASSES USED IN MACROS !!")
    return classes


def main() -> None:
    """Entrypoint."""
    search_path = Path("src/lantern/resources/templates")
    output_path = Path("./css-audit.txt")

    classes = _get_template_classes(search_path)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(sorted(set(classes))))
    print(f"Classes written to {output_path.resolve()}")


if __name__ == "__main__":
    main()
