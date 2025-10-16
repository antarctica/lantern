import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import TypeVar

import cattrs

TAdministration = TypeVar("TAdministration", bound="Administration")


@dataclass
class Permission:
    """
    Access permission.

    Represents a group with access to a resource within a given directory, optionally for a given time.

    Freetext comments can optionally be added for any additional context (e.g. why a non-obvious group has access).

    The expiry property is not currently used or enforced. It exists to record any known expiry for use in the future.

    Note: Comments are ignored in equality comparisons.

    Schema definition: permission [1]

    [1] https://gist.github.com/felnne/307bfa81672fbac2cd9cd7dd632a410c/83fa75e3c35ded8a105fb4c9abd1122d118aefef#file-schema-json-L25
    """

    directory: str
    group: str
    expiry: datetime = field(default_factory=lambda: datetime.max.replace(tzinfo=UTC))
    comments: str | None = None

    def __eq__(self, other: object) -> bool:
        """Equality comparison ignoring comments."""
        if not isinstance(other, type(self)):
            raise TypeError() from None
        self_dict = asdict(self)
        other_dict = asdict(other)
        self_dict.pop("comments", None)
        other_dict.pop("comments", None)
        return self_dict == other_dict


@dataclass(kw_only=True)
class Administration:
    """
    Representation of non-public, non-standard, metadata for internal administrative use.

    This class is a complete mapping of the BAS MAGIC Administrative Metadata v1 configuration schema [1] to Python
    dataclasses. See docs/data-model.md#item-administrative-metadata for more information.

    This class supports conversion to/from plain types and JSON strings. It does not perform value signing/encryption.

    Schema definition: administration [2]

    [1] https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/magic-admin-v1.json
    [2] https://gist.github.com/felnne/307bfa81672fbac2cd9cd7dd632a410c/83fa75e3c35ded8a105fb4c9abd1122d118aefef#file-schema-json-L99
    """

    _schema: str = (
        "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/magic-admin-v1.json"
    )

    id: str
    gitlab_issues: list[str] = field(default_factory=list)
    access_permissions: list[Permission] = field(default_factory=list)

    @classmethod
    def structure(cls: type[TAdministration], value: dict) -> "Administration":
        """
        Parse AdministrativeMetadata class from plain types.

        Returns a new class instance with parsed data. Intended to be used as a cattrs structure hook.
        E.g. `converter.register_structure_hook(AdministrativeMetadata, lambda d, t: AdministrativeMetadata.structure(d))`
        """
        if value["$schema"] != Administration._schema:
            msg = "Unsupported JSON Schema in data."
            raise ValueError(msg) from None

        converter = cattrs.Converter()
        converter.register_structure_hook(datetime, lambda d, t: datetime.fromisoformat(d))
        return converter.structure(value, cls)

    def unstructure(self) -> dict:
        """
        Convert AdministrativeMetadata class into plain types.

        Intended to be used as a cattrs unstructure hook.
        E.g. `converter.register_unstructure_hook(AdministrativeMetadata, lambda d: d.unstructure())`
        """
        converter = cattrs.Converter()
        converter.register_unstructure_hook(datetime, lambda d: d.isoformat())
        value = converter.unstructure(self)

        # remove internal keys (ensuring order)
        value.pop("_schema", None)

        return value

    @classmethod
    def loads_json(cls: type[TAdministration], value: str) -> "Administration":
        """Parse AdministrativeMetadata class from a JSON encoded string."""
        return Administration.structure(json.loads(value))

    def dumps_json(self) -> str:
        """Convert AdministrativeMetadata class into a JSON encoded string."""
        return json.dumps({"$schema": self._schema, **self.unstructure()}, indent=2, ensure_ascii=False)
