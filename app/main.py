"""FastAPI application demonstrating ADK Gemini Live API Toolkit with WebSocket."""

import asyncio
import base64
import json
import logging
import warnings
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.image_state import image_holder
from app.tools.firestore_utils import get_build_timeline

# Load environment variables from .env file BEFORE importing agent
# load_dotenv(Path(__file__).parent / ".env")
load_dotenv()  # No params to fetch from app start dir

# Import agent after loading environment variables
# pylint: disable=wrong-import-position
from app.agent import agent  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress Pydantic serialization warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Application name constant
APP_NAME = "BuildBuddy"

# ========================================
# Phase 1: Application Initialization (once at startup)
# ========================================

app = FastAPI()

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Define your session service
session_service = InMemorySessionService()

# Define your runner
runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)


# ========================================
# HTTP Endpoints
# ========================================


@app.get("/")
async def root():
    """Serve the index.html page."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")


# ========================================
# Report Endpoint
# ========================================
@app.get("/report")
async def get_report():
    """Return all build timeline entries from Firestore, ordered by timestamp."""
    timeline = get_build_timeline()
    return {"timeline": timeline, "total_entries": len(timeline)}


@app.get("/report/page")
async def report_page():
    """Serve the report HTML page. It's the same link all the time but works well for the hackathon especially if human reviewer wants to always be updated with progress"""
    return FileResponse(Path(__file__).parent / "static" / "report.html")


# ========================================
# WebSocket Endpoint
# ========================================


@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    proactivity: bool = False,
    affective_dialog: bool = False,
) -> None:
    """WebSocket endpoint for bidirectional streaming with ADK.

    Args:
        websocket: The WebSocket connection
        user_id: User identifier
        session_id: Session identifier
        proactivity: Enable proactive audio (native audio models only), reactive mode
        affective_dialog: Enable affective dialog (native audio models only), detects emotional state
    """
    logger.debug(
        f"WebSocket connection request: user_id={user_id}, session_id={session_id}, "
        f"proactivity={proactivity}, affective_dialog={affective_dialog}"
    )
    await websocket.accept()
    logger.debug("WebSocket connection accepted")

    # ========================================
    # Phase 2: Session Initialization (once per streaming session)
    # ========================================

    # Automatically determine response modality based on model architecture
    # Native audio models (containing "native-audio" in name)
    # ONLY support AUDIO response modality.
    # Half-cascade models support both TEXT and AUDIO,
    # we default to TEXT for better performance.
    # Also keeping TEXT for fallback and for users to type their part list
    model_name = agent.model
    is_native_audio = "native-audio" in model_name.lower()

    if is_native_audio:
        # Native audio models require AUDIO response modality
        # with audio transcription
        response_modalities = ["AUDIO"]

        # Build RunConfig with optional proactivity and affective dialog
        # These features are only supported on native audio models
        run_config = RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=response_modalities,
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            session_resumption=types.SessionResumptionConfig(),
            proactivity=(
                types.ProactivityConfig(proactive_audio=True) if proactivity else None
            ),
            enable_affective_dialog=affective_dialog if affective_dialog else None,
        )
        logger.debug(
            f"Native audio model detected: {model_name}, "
            f"using AUDIO response modality, "
            f"proactivity={proactivity}, affective_dialog={affective_dialog}"
        )
    else:
        # Half-cascade models support TEXT response modality
        # for faster performance
        response_modalities = ["TEXT"]
        run_config = RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=response_modalities,
            input_audio_transcription=None,
            output_audio_transcription=None,
            session_resumption=types.SessionResumptionConfig(),
        )
        logger.debug(
            f"Half-cascade model detected: {model_name}, using TEXT response modality"
        )
        # Warn if user tried to enable native-audio-only features
        if proactivity or affective_dialog:
            logger.warning(
                f"Proactivity and affective dialog are only supported on native "
                f"audio models. Current model: {model_name}. "
                f"These settings will be ignored."
            )
    logger.debug(f"RunConfig created: {run_config}")

    # Get or create session (handles both new sessions and reconnections)
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if not session:
        await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    live_request_queue = LiveRequestQueue()

    # ========================================
    # Phase 3: Active Session (concurrent bidirectional communication)
    # ========================================

    latest_image_blob = None  # Tracks the latest frame instead of ongoing feed
    frame_sent_this_turn = False  # Flag to track if latest frame was sent with VAD
    is_tool_active = False

    frames_allowed = asyncio.Event()  # Ensures we block
    frames_allowed.set()

    # Background task worker for image sending
    async def frame_injection_worker():
        nonlocal latest_image_blob, is_tool_active
        last_sent_data = None  # need to identify by bytes, not by object
        while True:
            await frames_allowed.wait()
            await asyncio.sleep(1)

            # Possible that a tool call started after sleep
            if not frames_allowed.is_set():
                continue

            if (
                latest_image_blob is not None
                and latest_image_blob.data is not last_sent_data
            ):
                live_request_queue.send_realtime(latest_image_blob)
                last_sent_data = latest_image_blob.data
                logger.debug("Injected latest frame to Gemini")

    async def upstream_task() -> None:
        """Receives messages from WebSocket and sends to LiveRequestQueue."""
        logger.debug("upstream_task started")
        nonlocal latest_image_blob, frame_sent_this_turn, is_tool_active
        while True:
            # Receive message from WebSocket (text or binary)
            message = await websocket.receive()

            # Handle text frames first — always buffer images, even during tool calls
            if "text" in message:
                text_data = message["text"]
                logger.debug(f"Received text message: {text_data[:100]}...")

                json_message = json.loads(text_data)

                if json_message.get("type") == "image":
                    logger.debug("Received image data")
                    image_data = base64.b64decode(json_message["data"])
                    mime_type = json_message.get("mimeType", "image/jpeg")

                    # Track state in image holder to transport to the tool context layer
                    image_holder["b64"] = json_message[
                        "data"
                    ]  # Directly just pass the b64 rather than converting back and forth
                    image_holder["mime"] = mime_type

                    latest_image_blob = types.Blob(mime_type=mime_type, data=image_data)
                    logger.debug(
                        f"Buffered frame, {len(image_data)} bytes, type: {mime_type}"
                    )
                    continue

                if not frames_allowed.is_set():
                    # Drop image while tool is running
                    continue

                if json_message.get("type") == "text":
                    logger.debug(f"Sending text content: {json_message['text']}")
                    content = types.Content(
                        parts=[types.Part(text=json_message["text"])]
                    )
                    live_request_queue.send_content(content)
                continue

            # Gate audio behind is_tool_active
            if not frames_allowed.is_set():
                # Drop image while tool is running
                continue

            # Handle binary frames (audio data)
            if "bytes" in message:
                audio_data = message["bytes"]
                logger.debug(f"Received binary audio chunk: {len(audio_data)} bytes")

                audio_blob = types.Blob(
                    mime_type="audio/pcm;rate=16000", data=audio_data
                )
                live_request_queue.send_realtime(audio_blob)

    async def downstream_task() -> None:
        """Receives Events from run_live() and sends to WebSocket."""
        nonlocal frame_sent_this_turn, is_tool_active
        logger.debug("downstream_task started, calling runner.run_live()")
        logger.debug(
            f"Starting run_live with user_id={user_id}, session_id={session_id}"
        )
        async for event in runner.run_live(
            user_id=user_id,
            session_id=session_id,
            live_request_queue=live_request_queue,
            run_config=run_config,
        ):
            event_json = event.model_dump_json(exclude_none=True, by_alias=True)
            logger.debug(f"[SERVER] Event: {event_json}")
            await websocket.send_text(event_json)

            if event.get_function_calls():
                is_tool_active = True
                frames_allowed.clear()  # LOCK realtime input
                logger.debug("Tool call detected, pausing realtime input")

            # Blocking on image to prevent spamming the downstream server
            if getattr(event, "turn_complete", False) or getattr(
                event, "interrupted", False
            ):
                is_tool_active = False
                frame_sent_this_turn = False

                await asyncio.sleep(1.5)  # cooldown before accepting frames again
                frames_allowed.set()

                logger.debug("Turn complete, reset frame flag")

        logger.debug("run_live() generator completed")

    # Run both tasks concurrently
    # Exceptions from either task will propagate and cancel the other task
    try:
        logger.debug("Starting asyncio.gather for upstream and downstream tasks")
        await asyncio.gather(
            upstream_task(), downstream_task(), frame_injection_worker()
        )
        logger.debug("asyncio.gather completed normally")
    except WebSocketDisconnect:
        logger.debug("Client disconnected normally")
    except Exception as e:
        logger.error(f"Unexpected error in streaming tasks: {e}", exc_info=True)
    finally:
        # ========================================
        # Phase 4: Session Termination
        # ========================================

        # Always close the queue, even if exceptions occurred
        logger.debug("Closing live_request_queue")
        live_request_queue.close()
