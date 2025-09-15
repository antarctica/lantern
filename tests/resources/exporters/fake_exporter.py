from lantern.exporters.base import Exporter, ResourceExporter, ResourcesExporter


class FakeExporter(Exporter):
    """Fake exporter for testing."""

    @property
    def name(self) -> str:
        """Exporter name."""
        return "fake"

    def export(self) -> None:
        """Export."""
        pass

    def publish(self) -> None:
        """Publish."""
        pass


class FakeResourcesExporter(ResourcesExporter):
    """Fake exporter for testing."""

    @property
    def name(self) -> str:
        """Exporter name."""
        return "fake"

    def export(self) -> None:
        """Export."""
        pass

    def publish(self) -> None:
        """Publish."""
        pass


class FakeResourceExporter(ResourceExporter):
    """Fake exporter for testing."""

    @property
    def name(self) -> str:
        """Exporter name."""
        return "fake"

    def dumps(self) -> str:
        """Dump."""
        return "x"
