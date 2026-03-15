from typing import Literal, Optional
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from mcp import Tool
from typing import Any
from datetime import datetime, timezone
from google.cloud import firestore      # might have to move this down?
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("path/to/service_account_key.json")
firebase_admin.initialize_app(cred)

db = firestore.Client()

def _build_snapshot(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
):
    return {
        "tool_name": tool.name,
        "timestamp": datetime.now(timezone.utc),
        "args": args,
        "response": tool_response,
        "build_progress": tool_context.state.get("build_progress", {}),
        "gcs_url": "PENDING",
    }

def _update_firestore_record(doc_id: str, fields: dict):
    # the main thing we'll only be updating is just "gcs_url"
    upload_url = fields.get("gcs_url")
    if upload_url:
        # update the firestore record
        """
        #url to exisiting database
        cred = credentials.Certificate('path/to/serviceAccount.json')

        app = firebase_admin.initialize_app(cred)

        db = firestore.client()
        """
        ...


def _log_to_firestore(snapshot: dict[str, str]) -> str:
    ...
    # store to firestore
    # return firestore id for this record