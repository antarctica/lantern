import cattrs
import pytest

from lantern.lib.metadata_library.models.record.elements.common import Contact, ContactIdentity
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Distribution,
    Distributions,
    Format,
    OnlineResource,
    Size,
    TransferOption,
)
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, OnlineResourceFunctionCode
from lantern.lib.metadata_library.models.record.utils.clean import clean_dict, clean_list


class TestFormat:
    """Test Format element."""

    @pytest.mark.parametrize("value", [None, "x"])
    def test_init(self, value: str | None):
        """Can create a Format element from directly assigned properties."""
        expected = "x"
        format_ = Format(format=expected, href=value)

        assert format_.format == expected
        assert format_.href == value


class TestSize:
    """Test Size element."""

    def test_init(self):
        """Can create a Size element from directly assigned properties."""
        expected_str = "x"
        expected_float = 1.0
        size = Size(unit=expected_str, magnitude=expected_float)

        assert size.unit == expected_str
        assert size.magnitude == expected_float


class TestTransferOption:
    """Test TransferOption element."""

    @pytest.mark.parametrize(
        "values",
        [
            {"online_resource": OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)},
            {
                "online_resource": OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD),
                "size": Size(unit="x", magnitude=1.0),
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create a TransferOption element from directly assigned properties."""
        transfer_opt = TransferOption(**values)

        assert isinstance(transfer_opt.online_resource, OnlineResource)

        if "size" in values:
            assert isinstance(transfer_opt.size, Size)
        else:
            assert transfer_opt.size is None


class TestDistribution:
    """Test Distribution element."""

    @pytest.mark.parametrize(
        "values",
        [
            {
                "distributor": Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                "transfer_option": TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            },
            {
                "distributor": Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                "transfer_option": TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
                "format": Format(format="x", href="x"),
            },
        ],
    )
    def test_init(self, values: dict):
        """Can create a Distribution element from directly assigned properties."""
        distribution = Distribution(**values)

        assert isinstance(distribution.transfer_option, TransferOption)

        if "format" in values:
            assert isinstance(distribution.format, Format)
        else:
            assert distribution.format is None

    def test_invalid_distributor_role(self):
        """Can't create a Distribution without a Contact with the distributor role."""
        with pytest.raises(ValueError, match=r"Distributor contact must include the 'distributor' role."):
            Distribution(
                distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.AUTHOR}),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            )

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a Distribution instance into plain types."""
        expected_enum = ContactRoleCode.DISTRIBUTOR
        value = Distribution(
            format=Format(format="x", href="x"),
            distributor=Contact(organisation=ContactIdentity(name="x"), role={expected_enum}),
            transfer_option=TransferOption(
                online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
            ),
        )
        expected = {
            "distributor": {"organisation": {"name": "x"}, "role": [expected_enum.value]},
            "format": {"format": "x", "href": "x"},
            "transfer_option": {
                "online_resource": {"href": "x", "function": OnlineResourceFunctionCode.DOWNLOAD.value}
            },
        }

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Distribution, lambda d: d.unstructure())
        result = clean_dict(converter.unstructure(value))

        assert result == expected


class TestDistributions:
    """Test Distribution options container."""

    test_distribution = Distribution(
        distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
        transfer_option=TransferOption(
            online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
        ),
    )

    def test_init(self):
        """Can create a Distribution options container from directly assigned properties."""
        expected = self.test_distribution
        distributions = Distributions([expected])

        assert len(distributions) == 1
        assert distributions[0] == expected

    @pytest.mark.parametrize(
        ("before", "after"),
        [
            (Distributions([]), Distributions([test_distribution])),
            (Distributions([test_distribution]), Distributions([test_distribution])),
        ],
    )
    def test_ensure(self, before: Distributions, after: Distributions):
        """Can append a distribution option as needed."""
        value = self.test_distribution

        before.ensure(value)
        assert before == after

    def test_structure(self):
        """Can create a Distribution options container by converting a list of plain types."""
        expected = Distributions(
            [
                Distribution(
                    distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                    ),
                )
            ]
        )
        result = Distributions.structure(
            [
                {
                    "distributor": {"organisation": {"name": "x"}, "role": ["distributor"]},
                    "transfer_option": {"online_resource": {"href": "x", "function": "download"}},
                }
            ]
        )

        assert type(result) is type(expected)
        assert result == expected

    def test_structure_cattrs(self):
        """Can use Cattrs to create a Distribution options instance from plain types."""
        value = [
            {
                "distributor": {"organisation": {"name": "x"}, "role": ["distributor"]},
                "transfer_option": {"online_resource": {"href": "x", "function": "download"}},
            }
        ]
        expected = Distributions(
            [
                Distribution(
                    distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                    ),
                )
            ]
        )

        converter = cattrs.Converter()
        converter.register_structure_hook(Distributions, lambda d, t: Distributions.structure(d))
        result = converter.structure(value, Distributions)

        assert result == expected

    def test_unstructure_cattrs(self):
        """Can use Cattrs to convert a Distribution options instance into plain types."""
        value = Distributions(
            [
                Distribution(
                    distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                    ),
                )
            ]
        )
        expected = [
            {
                "distributor": {"organisation": {"name": "x"}, "role": ["distributor"]},
                "transfer_option": {"online_resource": {"href": "x", "function": "download"}},
            }
        ]

        converter = cattrs.Converter()
        converter.register_unstructure_hook(Distributions, lambda d: d.unstructure())
        result = clean_list(converter.unstructure(value))

        assert result == expected
