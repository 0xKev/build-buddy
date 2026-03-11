from google.adk.tools.tool_context import ToolContext


def get_build_progress(tool_context: ToolContext) -> dict:
    """
    Retrieve the current build progress for all tracked parts.

    Use this when the user asks what's been done, what's left, or wants
    an overall status check. Returns a dict keyed by part_id.

    Returns an empty dict if no parts have been tracked yet.
    """
    build = tool_context.state.get("build_progress", {})
    return build
