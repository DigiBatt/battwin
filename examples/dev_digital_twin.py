from __future__ import annotations

import logging
from pathlib import Path

from echoed import DigitalTwin
from echoed.data import BdfDependencyError, load_bdf

try:
    from gleaned import FileSource, WMIDataSource
except ImportError:  # pragma: no cover - optional dependency for examples
    FileSource = None
    WMIDataSource = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parents[1]
data_dir = project_root / "assets" / "data"

data_sources = []
if WMIDataSource is not None:
    data_sources.append(WMIDataSource(refresh_interval=1))
if FileSource is not None:
    for ext in ("parquet", "csv", "json"):
        data_sources.append(FileSource(file_path=str(data_dir / f"battery_data.{ext}"), file_type=ext))
else:
    logger.warning("gleaned is not installed; skipping live data sources.")

# Create a digital twin
my_twin = DigitalTwin(metamodel=None, data_sources=data_sources)

logger.info("Digital twin initialized: %s", my_twin)

if data_sources:
    data = my_twin.get_live_status()
    logger.info("Live data snapshot: %s", data)

bdf_path = data_dir / "battery_data.bdf"
if bdf_path.exists():
    try:
        dataset = load_bdf(bdf_path)
        logger.info("Loaded BDF metadata keys: %s", sorted(dataset.metadata.keys()))
    except BdfDependencyError as exc:
        logger.warning("BDF support unavailable: %s", exc)

