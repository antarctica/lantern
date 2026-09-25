from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, cast

from importlib_resources import as_file as resources_as_file
from importlib_resources import files as resources_files

from lantern.models.checks import Check, CheckType
from lantern.models.site import ExportMeta, SiteContent, SiteEntry, SiteRedirect
from lantern.outputs.base import OutputSite

if TYPE_CHECKING:
    import logging


class SiteResourcesOutput(OutputSite):
    """
    Static site resources output.

    For resources used across the static site (CSS, JS, fonts, etc.).
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta) -> None:
        super().__init__(logger=logger, meta=meta, name="Site Resources", check_type=CheckType.SITE_RESOURCES)
        self._css_src_ref = "lantern.resources.css"
        self._fonts_src_ref = "lantern.resources.fonts"
        self._img_src_ref = "lantern.resources.img"
        self._txt_src_ref = "lantern.resources.txt"
        self._js_src_ref = "lantern.resources.js"
        self._js_dyn_src_ref = "lantern.resources.templates._assets.js"
        self._json_src_ref = "lantern.resources.json"
        self._base_path = Path("static")

        self._css_base_path = self._base_path / "css"
        self._font_base_path = self._base_path / "fonts"
        self._img_base_path = self._base_path / "img"
        self._txt_base_path = self._base_path / "txt"
        self._js_base_path = self._base_path / "js"
        self._json_base_path = self._base_path / "json"
        self._root_base_path = Path()

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        return {"build_key": self._meta.build_key}

    @staticmethod
    def _package_contents(
        package_ref: str,
        base_path: Path,
        entries: list[SiteEntry],
        binary: bool = False,
    ) -> list[SiteContent]:
        """
        Load the contents of package resources described by entries.

        Where `package_ref` is a module reference to a directory within a given package (e.g. 'lantern.resources.css').
        """
        items = []
        mode = "rb" if binary else "r"
        with resources_as_file(resources_files(package_ref)) as resources_path:
            for entry in entries:
                relative_path = (
                    entry.path.relative_to(base_path) if entry.path.is_relative_to(base_path) else entry.path
                )
                with (resources_path / relative_path).open(mode=mode) as f:
                    content = f.read()
                items.append(SiteContent(content=content, **vars(entry)))
        return items

    @staticmethod
    def _package_entries(
        package_ref: str, base_path: Path, media_type: str, glob: str, object_meta: dict[str, str]
    ) -> list[SiteEntry]:
        """Enumerate package resources without opening any files."""
        with resources_as_file(resources_files(package_ref)) as resources_path:
            return [
                SiteEntry(
                    path=base_path / path.relative_to(resources_path), media_type=media_type, object_meta=object_meta
                )
                for path in resources_path.glob(glob)
            ]

    @cached_property
    def _css_entries(self) -> list[SiteEntry]:
        """Descriptions for site styles."""
        return self._package_entries(
            package_ref=self._css_src_ref,
            base_path=self._css_base_path,
            media_type="text/css",
            glob="**/*.css",
            object_meta=self._object_meta,
        )

    @property
    def _css_content(self) -> list[SiteContent]:
        """
        Output content for site styles.

        Updated styles need generating from `resources/templates/_assets/css/main.css.j2` using the `css` dev task.
        """
        return self._package_contents(
            package_ref=self._css_src_ref,
            base_path=self._css_base_path,
            entries=self._css_entries,
        )

    @cached_property
    def _font_entries(self) -> list[SiteEntry]:
        """Descriptions for site fonts."""
        return self._package_entries(
            package_ref=self._fonts_src_ref,
            base_path=self._font_base_path,
            media_type="font/ttf",
            glob="**/*.ttf",
            object_meta=self._object_meta,
        )

    @property
    def _font_content(self) -> list[SiteContent]:
        """Output content for site fonts."""
        return self._package_contents(
            package_ref=self._fonts_src_ref,
            base_path=self._font_base_path,
            entries=self._font_entries,
            binary=True,
        )

    @cached_property
    def _img_entries(self) -> list[SiteEntry]:
        """Descriptions for site images, including favicon."""
        return [
            *self._package_entries(
                package_ref=self._img_src_ref,
                base_path=self._img_base_path,
                media_type="image/png",
                glob="**/*.png",
                object_meta=self._object_meta,
            ),
            *self._package_entries(
                package_ref=self._img_src_ref,
                base_path=self._img_base_path,
                media_type="image/x-icon",
                glob="**/favicon.ico",
                object_meta=self._object_meta,
            ),
            *self._package_entries(
                package_ref=self._img_src_ref,
                base_path=self._root_base_path,
                media_type="image/x-icon",
                glob="**/favicon.ico",
                object_meta=self._object_meta,
            ),
            *self._package_entries(
                package_ref=self._img_src_ref,
                base_path=self._img_base_path,
                media_type="image/svg+xml",
                glob="**/*.svg",
                object_meta=self._object_meta,
            ),
        ]

    @property
    def _img_content(self) -> list[SiteContent]:
        """Output content for site images, including favicon."""
        return self._package_contents(
            package_ref=self._img_src_ref,
            base_path=self._img_base_path,
            entries=self._img_entries,
            binary=True,
        )

    @cached_property
    def _txt_static_entries(self) -> list[SiteEntry]:
        """Descriptions for text files under static/txt."""
        return self._package_entries(
            package_ref=self._txt_src_ref,
            base_path=self._txt_base_path,
            media_type="text/plain",
            object_meta=self._object_meta,
            glob="**/*.txt",
        )

    @cached_property
    def _txt_root_entries(self) -> list[SiteEntry]:
        """Descriptions for robots.txt files published at the site root."""
        return self._package_entries(
            package_ref=self._txt_src_ref,
            base_path=self._root_base_path,
            media_type="text/plain",
            object_meta=self._object_meta,
            glob="**/robots.txt",
        )

    @cached_property
    def _txt_entries(self) -> list[SiteEntry]:
        """Descriptions for text resources and the security.txt redirect."""
        return [
            *self._txt_static_entries,
            *self._txt_root_entries,
            SiteEntry(
                path=Path(".well-known") / "security.txt",
                media_type="text/html",
                redirect=self._meta.base_url + f"/{self._txt_base_path}/security.txt",
            ),
        ]

    @property
    def _txt_content(self) -> list[SiteContent]:
        """
        Output content for text based resources, including a basic health/availability indicator.

        This results in the `robots.txt` file being copied twice (to `/static/txt/robots.txt` and `/robots.txt`). This
        is inefficient/inelegeant but simplistic.
        """
        redirect = self._txt_entries[-1]
        return [
            *self._package_contents(
                package_ref=self._txt_src_ref,
                base_path=self._txt_base_path,
                entries=self._txt_static_entries,
            ),
            *self._package_contents(
                package_ref=self._txt_src_ref,
                base_path=self._root_base_path,
                entries=self._txt_root_entries,
                binary=True,
            ),
            SiteRedirect(path=redirect.path, target=cast("str", redirect.redirect), object_meta=redirect.object_meta),
        ]

    @cached_property
    def _js_dynamic_entries(self) -> list[SiteEntry]:
        """Descriptions for templated site scripts without rendering templates."""
        with resources_as_file(resources_files(self._js_dyn_src_ref)) as resources_path:
            return [
                SiteEntry(
                    path=self._js_base_path / path.relative_to(resources_path).stem,
                    media_type="application/javascript",
                    object_meta=self._object_meta,
                )
                for path in resources_path.glob("**/*.js.j2")
            ]

    def _js_dynamic_content(self) -> list[SiteContent]:
        """Output content for templated site scripts."""
        content = []
        with resources_as_file(resources_files(self._js_dyn_src_ref)) as resources_path:
            for source_path, entry in zip(resources_path.glob("**/*.js.j2"), self._js_dynamic_entries, strict=True):
                relative_source_path = source_path.relative_to(resources_path)
                template_path = f"_assets/js/{relative_source_path.as_posix()}"

                rnd = self._jinja.get_template(str(template_path)).render(data=self._meta.site_metadata)
                rnd = "\n".join([line.rstrip() for line in rnd.splitlines() if line.strip() != ""])  # trim blank lines
                content.append(SiteContent(content=rnd, **vars(entry)))
        return content

    @cached_property
    def _js_static_entries(self) -> list[SiteEntry]:
        """Descriptions for packaged scripts."""
        return self._package_entries(
            package_ref=self._js_src_ref,
            base_path=self._js_base_path,
            media_type="application/javascript",
            object_meta=self._object_meta,
            glob="**/*.js",
        )

    @cached_property
    def _js_entries(self) -> list[SiteEntry]:
        """Descriptions for static and dynamic site scripts."""
        return [*self._js_static_entries, *self._js_dynamic_entries]

    @property
    def _js_content(self) -> list[SiteContent]:
        """Output content for static and dynamic site scripts."""
        return [
            *self._package_contents(
                package_ref=self._js_src_ref,
                base_path=self._js_base_path,
                entries=self._js_static_entries,
            ),
            *self._js_dynamic_content(),
        ]

    @cached_property
    def _json_entries(self) -> list[SiteEntry]:
        """Descriptions for web manifests."""
        return self._package_entries(
            package_ref=self._json_src_ref,
            base_path=self._json_base_path,
            media_type="application/manifest+json",
            object_meta=self._object_meta,
            glob="**/manifest.webmanifest",
        )

    @property
    def _json_content(self) -> list[SiteContent]:
        return self._package_contents(
            package_ref=self._json_src_ref,
            base_path=self._json_base_path,
            entries=self._json_entries,
        )

    @cached_property
    def entries(self) -> list[SiteEntry]:
        """Descriptions for all site resources without loading their content."""
        return [
            *self._css_entries,
            *self._font_entries,
            *self._img_entries,
            *self._txt_entries,
            *self._js_entries,
            *self._json_entries,
        ]

    @cached_property
    def content(self) -> list[SiteContent]:
        """Output content for all site resources."""
        return [
            *self._css_content,
            *self._font_content,
            *self._img_content,
            *self._txt_content,
            *self._js_content,
            *self._json_content,
        ]

    @property
    def checks(self) -> list[Check]:
        """Output checks."""
        _patterns = ("favicon.ico", "robots.txt", "**/css/main.css", "**/txt/heartbeat.txt")
        subset = [o for o in self.entries if any(o.path.match(p) for p in _patterns)]
        return [
            Check.from_site_entry(content=c, check_type=CheckType.SITE_RESOURCES, base_url=self._meta.base_url)
            for c in subset
        ]

    @property
    def invalidation_keys(self) -> list[str]:
        """Keys to invalidate."""
        return [f"/{self._base_path}/*"]
