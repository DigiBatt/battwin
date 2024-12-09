import pandas as pd
import os
from gleaned import DataHarvester, FileSource, WMIDataSource


class DigitalTwin:
    """
    DigitalTwin class for representing and managing a digital twin of a battery.

    Attributes:
        metamodel (object): The metamodel instance representing the battery.
        data_sources (list): A list of data sources associated with the digital twin.
        harvester (DataHarvester): A harvester instance for managing data collection.
    """

    def __init__(self, metamodel, data_sources=None):
        """
        Initialize the DigitalTwin.

        :param metamodel: The metamodel representing the battery.
        :param data_sources: A list of data sources (optional).
        """
        self.metamodel = metamodel
        self.harvester = DataHarvester()
        self.data_sources = data_sources or []

        # Register all provided data sources
        for source in self.data_sources:
            self.harvester.register_source(source)

    def harvest_static_data(self, source_name):
        """
        Harvest static data from a registered source.

        :param source_name: Name of the source to harvest data from.
        :return: DataFrame containing the harvested data.
        """
        print(f"Harvesting static data from source: {source_name}")
        return self.harvester.harvest_static(source_name)

    def harvest_live_data(self, source_name, duration, serialize_path=None):
        """
        Harvest live data from a source for a specific duration.

        :param source_name: Name of the source to harvest data from.
        :param duration: Duration (in seconds) for live data harvesting.
        :param serialize_path: Path to serialize the collected data (optional).
        """
        print(f"Starting live data harvesting from source: {source_name}")
        self.harvester.harvest_live_by_interval(source_name, duration, serialize_path)

    def get_live_status(self, source_name=None):
        """
        Get a snapshot of the current live status from a source.

        :param source_name: Name of the source to get status from. If not provided,
                            it defaults to the first registered live source.
        :return: Dictionary with the live status values.
        """
        if not source_name:
            # Find the first live source if no source_name is provided
            live_sources = [source for source in self.harvester.sources if source.refresh_interval > 0]
            if live_sources:
                source_name = live_sources[0].metadata()["source"]
                print(f"No source_name provided. Defaulting to live source: {source_name}")
            else:
                raise ValueError("No live sources registered, and no source_name provided.")

        print(f"Getting live status from source: {source_name}")
        return self.harvester.get_live_status(source_name)


    def register_new_source(self, source):
        """
        Register a new data source.

        :param source: The data source to register.
        """
        print(f"Registering new data source: {source.metadata()['source']}")
        self.data_sources.append(source)
        self.harvester.register_source(source)

    def describe(self):
        """
        Print a summary of the Digital Twin.

        :return: None
        """
        print("=== Digital Twin Summary ===")
        print(f"Metamodel: {self.metamodel}")
        print("Registered Data Sources:")
        for source in self.data_sources:
            print(f"  - {source.metadata()['source']}")

    def serialize_metamodel(self, file_path):
        """
        Serialize the metamodel to a file.

        :param file_path: Path to save the serialized metamodel.
        """
        print(f"Serializing metamodel to: {file_path}")
        with open(file_path, "w") as f:
            f.write(str(self.metamodel))
        print("Metamodel serialized successfully.")
