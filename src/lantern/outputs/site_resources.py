import logging
from pathlib import Path

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files

from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputSite


class SiteResourcesOutput(OutputSite):
    """
    Static site resources output.

    For resources used across the static site (CSS, JS, fonts, etc.).
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta) -> None:
        """Initialise."""
        super().__init__(logger=logger, meta=meta)
        self._css_src_ref = "lantern.resources.css"
        self._fonts_src_ref = "lantern.resources.fonts"
        self._img_src_ref = "lantern.resources.img"
        self._txt_src_ref = "lantern.resources.txt"
        self._js_src_ref = "lantern.resources.js"
        self._js_dyn_src_ref = "lantern.resources.templates._assets.js"
        self._json_src_ref = "lantern.resources.json"
        self._base_path = Path("static")

    @property
    def name(self) -> str:
        """Output name."""
        return "Site Resources"

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {"build_key": self._meta.build_key}

    @staticmethod
    def _package_contents(
        package_ref: str,
        base_path: Path,
        media_type: str,
        glob: str,
        object_meta: dict,
        binary: bool = False,
    ) -> list[SiteContent]:
        """
        Create site outputs for package resources.

        Where `package_ref` is a module reference to a directory within a given package (e.g. 'lantern.resources.css').
        """
        items = []
        mode = "rb" if binary else "r"
        with resources_as_file(resources_files(package_ref)) as resources_path:
            for path in resources_path.glob(glob):
                relative_path = path.relative_to(resources_path)
                with path.open(mode=mode) as f:
                    content = f.read()
                items.append(
                    SiteContent(
                        content=content, path=base_path / relative_path, media_type=media_type, object_meta=object_meta
                    )
                )
        return items

    @property
    def _css_outputs(self) -> list[SiteContent]:
        """
        Output content for site styles.

        Updated styles need generating from `resources/templates/_assets/css/main.css.j2` using the `css` dev task.
        """
        return self._package_contents(
            package_ref=self._css_src_ref,
            base_path=self._base_path / "css",
            media_type="text/css",
            glob="**/*.css",
            object_meta=self._object_meta,
        )

    @property
    def _font_outputs(self) -> list[SiteContent]:
        """Output content for site fonts."""
        return self._package_contents(
            package_ref=self._fonts_src_ref,
            base_path=self._base_path / "fonts",
            media_type="font/ttf",
            glob="**/*.ttf",
            object_meta=self._object_meta,
            binary=True,
        )

    @property
    def _img_outputs(self) -> list[SiteContent]:
        """Output content for site images, including favicon."""
        return [
            *self._package_contents(
                package_ref=self._img_src_ref,
                base_path=self._base_path / "img",
                media_type="image/png",
                glob="**/*.png",
                object_meta=self._object_meta,
                binary=True,
            ),
            *self._package_contents(
                package_ref=self._img_src_ref,
                base_path=Path(),
                media_type="image/x-icon",
                glob="**/favicon.ico",
                object_meta=self._object_meta,
                binary=True,
            ),
            *self._package_contents(
                package_ref=self._img_src_ref,
                base_path=self._base_path / "img",
                media_type="image/svg+xml",
                glob="**/*.svg",
                object_meta=self._object_meta,
                binary=True,
            ),
        ]

    @property
    def _txt_outputs(self) -> list[SiteContent]:
        """Output content for text based resources, including a basic health/availability indicator."""
        return [
            *self._package_contents(
                package_ref=self._txt_src_ref,
                base_path=self._base_path / "txt",
                media_type="text/plain",
                object_meta=self._object_meta,
                glob="**/*.txt",
            )
        ]

    def _js_dynamic(self, base_path: Path, media_type: str, object_meta: dict) -> list[SiteContent]:
        """Output content for templated site scripts."""
        content = []
        with resources_as_file(resources_files(self._js_dyn_src_ref)) as resources_path:
            for source_path in resources_path.glob("**/*.js.j2"):
                relative_source_path = source_path.relative_to(resources_path)
                template_path = f"_assets/js/{relative_source_path.as_posix()}"

                rnd = self._jinja.get_template(str(template_path)).render(data=self._meta.site_metadata)
                rnd = "\n".join([line.rstrip() for line in rnd.splitlines() if line.strip() != ""])  # trim blank lines
                content.append(
                    SiteContent(
                        content=rnd,
                        path=base_path / relative_source_path.stem,
                        media_type=media_type,
                        object_meta=object_meta,
                    )
                )
        return content

    @property
    def _js_outputs(self) -> list[SiteContent]:
        """Output content for static and dynamic site scripts."""
        base_path = self._base_path / "js"
        media_type = "application/javascript"
        object_meta = self._object_meta
        return [
            *self._package_contents(
                package_ref=self._js_src_ref,
                base_path=base_path,
                media_type=media_type,
                object_meta=object_meta,
                glob="**/*.js",
            ),
            *self._js_dynamic(base_path, media_type=media_type, object_meta=object_meta),
        ]

    @property
    def _json_outputs(self) -> list[SiteContent]:
        return self._package_contents(
            package_ref=self._json_src_ref,
            base_path=self._base_path / "json",
            media_type="application/manifest+json",
            object_meta=self._object_meta,
            glob="**/manifest.webmanifest",
        )

    @property
    def outputs(self) -> list[SiteContent]:
        """Output content for all site resources."""
        return [
            *self._css_outputs,
            *self._font_outputs,
            *self._img_outputs,
            *self._txt_outputs,
            *self._js_outputs,
            *self._json_outputs,
        ]
