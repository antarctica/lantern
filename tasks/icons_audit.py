from pathlib import Path

from tasks.css_audit import _get_template_classes


def _get_icon_classes(search_path: Path) -> list[str]:
    icon_classes = []
    classes = _get_template_classes(search_path)
    excluded = ["fa-fw", "fa-2x"]

    for cls in classes:
        if cls.startswith("fa-") and cls not in excluded:
            icon_classes.append(cls)

    icon_classes.append("!! DOES NOT INCLUDE ICONS USED IN MACROS !!")
    return icon_classes


def main() -> None:
    """Entrypoint."""
    search_path = Path("src/lantern/resources/templates")
    output_path = Path("./icons-audit.txt")

    classes = _get_icon_classes(search_path)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(sorted(set(classes))))
    print(f"Icon classes written to {output_path.resolve()}")


if __name__ == "__main__":
    main()
