from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence


logger = logging.getLogger(__name__)


class DataSource(Protocol):
    refresh_interval: int

    def metadata(self) -> Mapping[str, Any]:
        ...


class DataHarvesterProtocol(Protocol):
    sources: Sequence[DataSource]

    def register_source(self, source: DataSource) -> None:
        ...

    def harvest_static(self, source_name: str) -> Any:
        ...

    def harvest_live_by_interval(
        self,
        source_name: str,
        duration: int,
        serialize_path: str | Path | None = None,
    ) -> None:
        ...

    def get_live_status(self, source_name: str) -> Mapping[str, Any]:
        ...


class DigitalTwin:
    """
    DigitalTwin class for representing and managing a digital twin of a battery.

    Attributes:
        metamodel (object): The metamodel instance representing the battery.
        data_sources (list): A list of data sources associated with the digital twin.
        harvester (DataHarvester): A harvester instance for managing data collection.
    """

    def __init__(
        self,
        metamodel: object | None = None,
        data_sources: Iterable[DataSource] | None = None,
        harvester: DataHarvesterProtocol | None = None,
    ) -> None:
        """
        Initialize the DigitalTwin.

        :param metamodel: The metamodel representing the battery.
        :param data_sources: A list of data sources (optional).
        """
        self.metamodel = metamodel
        self.harvester = harvester or self._default_harvester()
        self.data_sources = list(data_sources or [])

        # Register all provided data sources
        for source in self.data_sources:
            self.harvester.register_source(source)

    def _default_harvester(self) -> DataHarvesterProtocol:
        try:
            from gleaned import DataHarvester  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "gleaned is required for live data harvesting. "
                "Install it or provide a custom harvester implementation."
            ) from exc
        return DataHarvester()

    def harvest_static_data(self, source_name: str) -> Any:
        """
        Harvest static data from a registered source.

        :param source_name: Name of the source to harvest data from.
        :return: DataFrame containing the harvested data.
        """
        logger.info("Harvesting static data from source: %s", source_name)
        return self.harvester.harvest_static(source_name)

    def harvest_live_data(
        self,
        source_name: str,
        duration: int,
        serialize_path: str | Path | None = None,
    ) -> None:
        """
        Harvest live data from a source for a specific duration.

        :param source_name: Name of the source to harvest data from.
        :param duration: Duration (in seconds) for live data harvesting.
        :param serialize_path: Path to serialize the collected data (optional).
        """
        logger.info("Starting live data harvesting from source: %s", source_name)
        self.harvester.harvest_live_by_interval(source_name, duration, serialize_path)

    def get_live_status(self, source_name: str | None = None) -> Mapping[str, Any]:
        """
        Get a snapshot of the current live status from a source.

        :param source_name: Name of the source to get status from. If not provided,
                            it defaults to the first registered live source.
        :return: Dictionary with the live status values.
        """
        if not source_name:
            # Find the first live source if no source_name is provided
            live_sources = [
                source for source in self.harvester.sources if source.refresh_interval > 0
            ]
            if live_sources:
                source_name = live_sources[0].metadata().get("source")
                if not source_name:
                    raise ValueError("Live source metadata is missing a 'source' identifier.")
                logger.info("No source_name provided. Defaulting to live source: %s", source_name)
            else:
                raise ValueError("No live sources registered, and no source_name provided.")

        logger.info("Getting live status from source: %s", source_name)
        return self.harvester.get_live_status(source_name)


    def register_new_source(self, source: DataSource) -> None:
        """
        Register a new data source.

        :param source: The data source to register.
        """
        logger.info("Registering new data source: %s", source.metadata().get("source", "unknown"))
        self.data_sources.append(source)
        self.harvester.register_source(source)

    def describe(self) -> str:
        """
        Print a summary of the Digital Twin.

        :return: Summary string
        """
        lines = [
            "=== Digital Twin Summary ===",
            f"Metamodel: {self.metamodel}",
            "Registered Data Sources:",
        ]
        for source in self.data_sources:
            lines.append(f"  - {source.metadata().get('source', 'unknown')}")
        summary = "\n".join(lines)
        logger.info(summary)
        return summary

    def serialize_metamodel(self, file_path: str | Path) -> None:
        """
        Serialize the metamodel to a file.

        :param file_path: Path to save the serialized metamodel.
        """
        if self.metamodel is None:
            raise ValueError("No metamodel available to serialize.")
        path = Path(file_path)
        logger.info("Serializing metamodel to: %s", path)
        path.write_text(str(self.metamodel), encoding="utf-8")
        logger.info("Metamodel serialized successfully.")
