from typing import Literal, Optional
from annotated_types import doc
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from typing import Any
from datetime import datetime, timezone
from google.cloud import firestore
import os

FIRESTORE_COLLECTION_ID = os.getenv("FIRESTORE_COLLECTION_ID", "bb-report-data")
PROJECT_ID = os.getenv("PROJECT_ID", "build-buddy-488918")

_db = firestore.Client(PROJECT_ID)


# capture just the delta instead of full history
def _build_snapshot(
    tool: BaseTool,
    tool_context: ToolContext,
):
    build = tool_context.state.get("build_progress", {})
    last_updated = tool_context.state.get("last_updated_part")

    # removing args and tool_resonse from params because build_progess has sufficient info for reports
    return {
        "tool_name": tool.name,
        "timestamp": datetime.now(timezone.utc),
        "part_id": last_updated,
        "part_data": build.get(last_updated, {}),
        "gcs_url": "PENDING",
    }


def _update_firestore_record(doc_id: str, gcs_url: str):
    # the main thing we'll only be updating is just "gcs_url"
    doc_ref = _db.collection(FIRESTORE_COLLECTION_ID).document(doc_id)
    doc_ref.update({"gcs_url": gcs_url})


def _log_to_firestore(snapshot: dict[str, str]) -> str:
    # store to firestore
    # return firestore id for this record
    _, doc_ref = _db.collection(FIRESTORE_COLLECTION_ID).add(snapshot)
    return doc_ref.id  # return the doc id, not the reference


if __name__ == "__main__":

    class FakeTool:
        def __init__(self):
            self.name = "fake_tool_call"

    class FakeToolContext:
        def __init__(self):
            self.state = {
                "build_progress": {
                    "cpu": {
                        "name": "AMD Ryzen 5 5600X 3.7 GHz 6-Core Processor",
                        "category": "CPU",
                        "status": "NOT_STARTED",
                        "notes": "",
                    },
                    "cooler": {
                        "name": "Noctua NH-U12S 55 CFM CPU Cooler",
                        "category": "CPU Cooler",
                        "status": "NOT_STARTED",
                        "notes": "",
                    },
                    "motherboard": {
                        "name": "Asus TUF GAMING X570-PLUS (WI-FI) ATX AM4 Motherboard",
                        "category": "Motherboard",
                        "status": "NOT_STARTED",
                        "notes": "",
                    },
                    "ram": {
                        "name": "G.Skill Ripjaws V 32 GB (2 x 16 GB) DDR4-3200 CL16 Memory",
                        "category": "Memory",
                        "status": "NOT_STARTED",
                        "notes": "",
                    },
                    "storage": {
                        "name": "Crucial T500 1 TB M.2-2280 PCIe 4.0 X4 NVME Solid State Drive",
                        "category": "Storage",
                        "status": "NOT_STARTED",
                        "notes": "",
                    },
                    "gpu": {
                        "name": "Gigabyte AORUS ELITE GeForce RTX 3060 Ti 8 GB Video Card",
                        "category": "Video Card",
                        "status": "NOT_STARTED",
                        "notes": "",
                    },
                    "case": {
                        "name": "Corsair 4000D Airflow ATX Mid Tower Case",
                        "category": "Case",
                        "status": "NOT_STARTED",
                        "notes": "",
                    },
                    "psu": {
                        "name": "EVGA SuperNOVA 750 GA 750 W 80+ Gold Certified Fully Modular ATX Power Supply",
                        "category": "Power Supply",
                        "status": "NOT_STARTED",
                        "notes": "",
                    },
                    "monitor": {
                        "name": 'LG 24GL600F-B 23.6" 1920 x 1080 144 Hz Monitor',
                        "category": "Monitor",
                        "status": "NOT_STARTED",
                        "notes": "",
                    },
                }
            }

    mock_tool = FakeTool()
    mock_tool_context = FakeToolContext()
    mock_gcs_url = "testing-gcs-url.com/abc"

    mock_tool_context.state["last_updated_part"] = "cpu"

    snapshot = _build_snapshot(mock_tool, mock_tool_context)
    doc_id = _log_to_firestore(snapshot)
    print(f"{doc_id=}")
    _update_firestore_record(doc_id, mock_gcs_url)
