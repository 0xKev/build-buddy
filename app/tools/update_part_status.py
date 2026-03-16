from mimetypes import guess_type
import os
from typing import Literal, Optional
from google.cloud import storage
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from typing import Any
from app.image_state import get_latest_image
from app.tools.firestore_utils import (
    _build_snapshot,
    _update_firestore_record,
    _log_to_firestore,
)
import base64

# Create the client and bucket once and reuse
_storage_client = storage.Client(os.getenv("PROJECT_ID", "build-buddy-488918"))
_bucket_name = os.getenv("GS_BUCKET_ID", "gemini_hackathon_build_buddy_001")
_bucket = _storage_client.bucket(_bucket_name)


# Function Tool to update part status
def update_part_status(
    tool_context: ToolContext,
    part_id: str,
    status: Literal["NOT_STARTED", "IN_PROGRESS", "DONE", "BLOCKED"],
    notes: str = "",
) -> dict:
    """
    Update the installation status of a specific part in the current build.

    Use this when the user reports progress on a part, e.g. they've started
    installing it, finished it, or hit a problem. Do NOT use this to look up
    current progress. Use get_build_progress for that.

    Args:
        part_id: Identifier for the part (e.g. "cpu", "gpu", "psu", "ram").
        status: Current installation state of the part.
        notes: Optional context like issues encountered or tools needed.
    """
    build = tool_context.state.get("build_progress", {})

    build[part_id]["status"] = status
    build[part_id]["notes"] = notes

    # last_updated_part to track delta instead of full history
    tool_context.state["last_updated_part"] = part_id
    tool_context.state["build_progress"] = build

    # return summary
    done = [k for k, v in build.items() if v["status"] == "DONE"]
    remaining = [k for k, v in build.items() if v["status"] != "DONE"]

    return {
        "updated_part": part_id,
        "new_status": status,
        "part_notes": notes,
        "completed_tasks": done,
        "remaining_tasks": remaining,
    }


# https://google.github.io/adk-docs/callbacks/types-of-callbacks/#after-tool-callback
def after_tool_report_log(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, tool_response: dict
) -> Optional[dict]:

    if tool.name == "update_part_status":
        # no need to check for responses here from the tool call
        snapshot = _build_snapshot(tool, tool_context)
        doc_id = _log_to_firestore(snapshot)

        blob_url = _upload_blob_to_gcs(tool_context)
        if blob_url:
            # update firestore with blob_url
            _update_firestore_record(doc_id, blob_url)


def _upload_blob_to_gcs(tool_context: ToolContext) -> str:
    pending_blob: dict | None = tool_context.state.get("pending_blob", None)
    if pending_blob is None:
        return ""

    tool_context.state["pending_blob"] = (
        None  # clear out pending blob after uploading, no need to maintain
    )
    # otherwise upload the actual iamge blob to GCS
    # the part_id field is what ties the uploaded blob to the firestore record
    blob = _bucket.blob(pending_blob["filename"])

    # mime.guess_file_type is only py3.13
    # mime.guess_type() to support either images or text for testing
    image_bytes = base64.b64decode(pending_blob["data"])
    content_type, _ = guess_type(pending_blob["filename"])
    blob.upload_from_string(
        image_bytes, content_type=content_type or "application/octet-stream"
    )  # in case guess_file_type fails

    # note that can only make public if bucket rules aren't set to uniform or else can't modify individual blob settings
    # instead, i set entire bucket to public for hackathon, otherwise presigned urls with expirations
    # blob.make_public()

    # return url of uploaded blob
    # gs_url = f"gs://{_bucket_name}/{pending_blob['filename']}"

    # gs url can always be used to generate the actual direct download link as needed
    # return gs_url

    # for hackathon, just do public url instead with read access, making it easier for report generation later
    return blob.public_url


def before_tool_modifier(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
):
    if tool.name == "update_part_status":
        b64, mime_type = get_latest_image()
        # Using b64 since to prevent encoding/decoding back and forth, and only decode when need to show
        if b64:
            # Only attaching the latest to the tool context
            ext = mime_type.split("/")[-1].replace("jpeg", "jpg")
            part_id = args.get("part_id", "N/A")
            filename = f"{part_id}.{ext}" if part_id != "N/A" else "missing_part_id.jpg"

            tool_context.state["pending_blob"] = {
                "data": b64,
                "part_id": part_id,
                "filename": filename,
            }


if __name__ == "__main__":
    print("RUNNING...")

    class FakeToolContext:
        def __init__(self):
            self.state = {
                "pending_blob": {
                    "data": "this is a test",
                    "part_id": "cpu",
                    "filename": "test.txt",
                }
            }

    # Test blob upload works
    mock_tool_context = FakeToolContext()
    print("INIT FakeToolContext")
    gcs_url = _upload_blob_to_gcs(mock_tool_context)
    print(f"{gcs_url=}")
