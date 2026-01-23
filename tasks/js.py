from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from lantern.config import Config


def regenerate_scripts(base_path: Path) -> None:
    """Regenerate app Tailwind CSS styles."""
    templates_path = base_path / "templates"
    output_base = base_path / "js"
    _jinja = Environment(loader=FileSystemLoader(str(templates_path)), autoescape=select_autoescape())
    config = Config()
    data = {"sentry_dsn": config.SENTRY_DSN}

    for source_path in templates_path.glob("_assets/js/*.js.j2"):
        relative_source_path = source_path.relative_to(templates_path)
        output_path = output_base / relative_source_path.stem

        rendered = _jinja.get_template(str(relative_source_path)).render(data=data)
        rendered = "\n".join(  # trim any blank lines
            [line.rstrip() for line in rendered.splitlines() if line.strip() != ""]
        )
        with output_path.open("w") as f:
            f.write(rendered)
            f.write("\n")  # append trailing new line


def main() -> None:
    """Entrypoint."""
    base_path = Path("src/lantern/resources")
    regenerate_scripts(base_path)
    print("Updated site scripts. Re-run build to apply.")


if __name__ == "__main__":
    main()
