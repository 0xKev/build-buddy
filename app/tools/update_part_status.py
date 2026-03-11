from typing import Literal, Optional
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from mcp import Tool
from typing import Any


# TODO: hook to context with pre and post hooks
# also create another tool for "get_build_progress"
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
    # TODO: later i want to make it so we take a snapshot of history so we can generate a report
    # currently, this overwrites status history
    build[part_id]["status"] = status
    build[part_id]["notes"] = notes
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
# TODO: send reports to firebase/cloud
# need to add the blob to toolcontext
def after_tool_report_log(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, tool_response: dict
) -> Optional[dict]:
    # Add a hook to take a snapshot and log time, and status
    snapshot = _build_snapshot(tool, args, tool_context, tool_response)
    doc_id = _log_to_firestore(snapshot)

    blob_url = _upload_blob_to_gcs(tool_context)
    if blob_url:
        # update firestore with blob_url
        _update_firestore_record(doc_id, {"gcs_url": blob_url})


# Snapshot for firestore
def _build_snapshot(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
):
    return {
        "tool_name": tool.name,
        "timestamp": ...,  #
        "args": args,
        "response": tool_response,
        "build_progress": tool_context.get("build_progress", {}),
        "gcs_url": "PENDING",
    }


def _update_firestore_record(doc_id: str, fields: dict):
    # the main thing we'll only be updating is just "gcs_url"
    upload_url = fields.get("gcs_url")
    if upload_url:
        # update the firestore record
        ...


def _log_to_firestore(snapshot: dict[str, str]) -> str:
    ...
    # store to firestore
    # return firestore id for this record


def _upload_blob_to_gcs(tool_context: ToolContext) -> str:
    pending_blob: dict = tool_context.state.pop("pending_blob", None)
    # if exists, it'll be a dictionary
    # {
    #     "data": blob, # bytes
    #     "part_id": "cpu", # str
    #     "filename": "cpu_verification.jpg", # str
    # }
    if pending_blob is None:
        return ""

    # otherwise upload the actual iamge blob to GCS
    # the part_id field is what ties the uploaded blob to the firestore record

    # return url of uploaded blob
