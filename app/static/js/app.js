/**
 * app.js — BuildBuddy: integrated ADK Gemini Live API + BuildBuddy UI
 *
 * Keeps: WebSocket, audio worklets, camera capture pipeline
 * Replaces: chat bubbles, event console, text input → orb UI, parts popup, progress stepper
 */

// ══════════════════════════════════════════════════════════════
// ── UI HELPERS ──
// ══════════════════════════════════════════════════════════════

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

// ── Build Steps ──
// IDs must match backend part_ids exactly
const BUILD_STEPS = [
    { id: "cpu", label: "Install CPU", sub: "AMD Ryzen 5 5600X" },
    { id: "cooler", label: "Mount CPU Cooler", sub: "Noctua NH-U12S" },
    { id: "motherboard", label: "Install Motherboard", sub: "Asus TUF X570-PLUS" },
    { id: "ram", label: "Seat RAM", sub: "G.Skill Ripjaws V 32GB" },
    { id: "storage", label: "Install Storage", sub: "Crucial T500 1TB NVMe" },
    { id: "gpu", label: "Install GPU", sub: "RTX 3060 Ti AORUS" },
    { id: "psu", label: "Install PSU", sub: "EVGA 750W Gold" },
    { id: "case", label: "Assemble Case", sub: "Corsair 4000D Airflow" },
    { id: "monitor", label: "Connect Monitor", sub: "LG 24GL600F 144Hz" },
];
const doneSet = new Set();
let currentStep = 0;

// ── Parts Reference Data ──
const PARTS = [
    {
        id: "atx24",
        icon: "\u{1F50C}",
        name: "24-Pin ATX",
        desc: "Main power",
        detail: "ATX 24-Pin Power Connector",
        sub: "Motherboard main power supply",
        tips: [
            {
                ico: "\u{1F4A1}",
                text: "The clip faces away from the board. Align the notch and push firmly until it clicks.",
            },
            {
                ico: "\u26A0\uFE0F",
                text: "This requires significant force \u2014 don't be afraid to press hard. A half-seated connector causes boot failures.",
            },
            {
                ico: "\u{1F50D}",
                text: "Located on the right edge of most ATX motherboards.",
            },
        ],
        svg: `<svg viewBox="0 0 320 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="60" y="30" width="200" height="140" rx="8" fill="#1a1a24" stroke="#3a3a50"/>
      <text x="160" y="22" text-anchor="middle" fill="#55556a" font-size="11" font-family="system-ui">24-PIN ATX CONNECTOR</text>
      ${Array.from({ length: 12 }, (_, i) => `<rect x="${80 + i * 15}" y="55" width="10" height="18" rx="2" fill="#00d4aa" opacity="0.6"/>`).join("")}
      ${Array.from({ length: 12 }, (_, i) => `<rect x="${80 + i * 15}" y="82" width="10" height="18" rx="2" fill="#00d4aa" opacity="0.4"/>`).join("")}
      <rect x="72" y="110" width="176" height="24" rx="4" fill="none" stroke="#00d4aa" opacity="0.3" stroke-dasharray="4 2"/>
      <text x="160" y="126" text-anchor="middle" fill="#00d4aa" opacity="0.5" font-size="10" font-family="system-ui">CLIP SIDE</text>
    </svg>`,
    },
    {
        id: "cpu8",
        icon: "\u26A1",
        name: "8-Pin CPU",
        desc: "CPU power",
        detail: "8-Pin CPU Power (EPS12V)",
        sub: "Dedicated CPU power delivery",
        tips: [
            {
                ico: "\u{1F4A1}",
                text: "Usually at the top-left of the motherboard. Route the cable behind the case before mounting the board.",
            },
            {
                ico: "\u26A0\uFE0F",
                text: "Do NOT confuse with the PCIe 8-pin \u2014 they look similar but are keyed differently.",
            },
            {
                ico: "\u{1F50D}",
                text: "Some boards have both a 4+4 and an extra 4-pin. You only need the main 4+4 for most builds.",
            },
        ],
        svg: `<svg viewBox="0 0 320 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="100" y="40" width="120" height="120" rx="8" fill="#1a1a24" stroke="#3a3a50"/>
      <text x="160" y="32" text-anchor="middle" fill="#55556a" font-size="11" font-family="system-ui">8-PIN EPS12V</text>
      ${Array.from({ length: 4 }, (_, i) => `<rect x="${118 + i * 22}" y="65" width="14" height="20" rx="2" fill="#ffaa33" opacity="0.6"/>`).join("")}
      ${Array.from({ length: 4 }, (_, i) => `<rect x="${118 + i * 22}" y="95" width="14" height="20" rx="2" fill="#ffaa33" opacity="0.4"/>`).join("")}
      <text x="160" y="140" text-anchor="middle" fill="#ffaa33" opacity="0.4" font-size="9" font-family="system-ui">CLIP</text>
    </svg>`,
    },
    {
        id: "pcie",
        icon: "\u{1F3AE}",
        name: "PCIe x16",
        desc: "GPU slot",
        detail: "PCIe x16 Slot",
        sub: "Primary graphics card slot",
        tips: [
            {
                ico: "\u{1F4A1}",
                text: "Pull the retention clip open BEFORE inserting the GPU. Align the gold contacts and press evenly.",
            },
            {
                ico: "\u26A0\uFE0F",
                text: "Support the GPU \u2014 don't let it hang by the slot alone. Consider a GPU support bracket.",
            },
            {
                ico: "\u{1F50D}",
                text: "Use the topmost x16 slot for best bandwidth (closest to CPU).",
            },
        ],
        svg: `<svg viewBox="0 0 320 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="30" y="80" width="240" height="40" rx="4" fill="#1a1a24" stroke="#3a3a50"/>
      <text x="150" y="72" text-anchor="middle" fill="#55556a" font-size="11" font-family="system-ui">PCIe x16 SLOT</text>
      <rect x="38" y="88" width="210" height="24" rx="2" fill="#00d4aa" opacity="0.15"/>
      <line x1="38" y1="100" x2="248" y2="100" stroke="#00d4aa" opacity="0.3" stroke-dasharray="2 2"/>
      <rect x="255" y="85" width="10" height="30" rx="2" fill="#ffaa33" opacity="0.5"/>
      <text x="275" y="104" fill="#ffaa33" font-size="8" font-family="system-ui">clip</text>
    </svg>`,
    },
    {
        id: "sata",
        icon: "\u{1F4BE}",
        name: "SATA",
        desc: "Storage data",
        detail: "SATA Data & Power",
        sub: "For SSDs and hard drives",
        tips: [
            {
                ico: "\u{1F4A1}",
                text: "SATA has an L-shaped connector \u2014 it only goes one way. Don't force it.",
            },
            {
                ico: "\u26A0\uFE0F",
                text: "You need BOTH a SATA data cable (to mobo) and SATA power cable (from PSU).",
            },
            {
                ico: "\u{1F50D}",
                text: "SATA ports are usually on the bottom-right of the motherboard.",
            },
        ],
        svg: `<svg viewBox="0 0 320 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <text x="90" y="30" fill="#55556a" font-size="11" font-family="system-ui">SATA DATA</text>
      <rect x="70" y="40" width="80" height="30" rx="4" fill="#1a1a24" stroke="#3a3a50"/>
      <rect x="78" y="48" width="50" height="14" rx="2" fill="#00d4aa" opacity="0.4"/>
      <rect x="128" y="48" width="14" height="14" rx="2" fill="#00d4aa" opacity="0.25"/>
      <text x="230" y="30" fill="#55556a" font-size="11" font-family="system-ui">SATA POWER</text>
      <rect x="190" y="40" width="100" height="30" rx="4" fill="#1a1a24" stroke="#3a3a50"/>
      <rect x="198" y="48" width="70" height="14" rx="2" fill="#ffaa33" opacity="0.4"/>
      <rect x="268" y="48" width="14" height="14" rx="2" fill="#ffaa33" opacity="0.25"/>
      <text x="160" y="120" text-anchor="middle" fill="#9090a8" font-size="10" font-family="system-ui">Both cables required per drive</text>
    </svg>`,
    },
    {
        id: "fpanel",
        icon: "\u{1F532}",
        name: "Front Panel",
        desc: "Case headers",
        detail: "Front Panel Headers",
        sub: "Power SW, Reset, LED+, LED-",
        tips: [
            {
                ico: "\u{1F4A1}",
                text: "Tiny cables from your case: POWER SW, RESET SW, HDD LED, POWER LED. Check your motherboard manual for the pin layout.",
            },
            {
                ico: "\u26A0\uFE0F",
                text: "Polarity matters for LEDs (+ and - sides). Power and Reset switches work either way.",
            },
            {
                ico: "\u{1F50D}",
                text: "Bottom-right corner of the motherboard. Use tweezers if your fingers are too big for the pins.",
            },
            {
                ico: "\u2728",
                text: "Some boards include a front-panel adapter block \u2014 plug cables into it off the board, then snap the whole block on.",
            },
        ],
        svg: `<svg viewBox="0 0 320 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <text x="160" y="22" text-anchor="middle" fill="#55556a" font-size="11" font-family="system-ui">FRONT PANEL HEADER (F_PANEL)</text>
      <rect x="80" y="35" width="160" height="80" rx="6" fill="#1a1a24" stroke="#3a3a50"/>
      ${[0, 1, 2, 3, 4]
                .map((r) =>
                    [0, 1]
                        .map(
                            (c) =>
                                `<circle cx="${105 + r * 30}" cy="${60 + c * 30}" r="5" fill="${r < 2 ? "#00d4aa" : r < 4 ? "#ffaa33" : "#ff4466"}" opacity="0.5"/>`
                        )
                        .join("")
                )
                .join("")}
      <text x="105" y="105" fill="#00d4aa" font-size="7" font-family="system-ui">PWR</text>
      <text x="135" y="105" fill="#00d4aa" font-size="7" font-family="system-ui">SW</text>
      <text x="165" y="105" fill="#ffaa33" font-size="7" font-family="system-ui">HDD</text>
      <text x="195" y="105" fill="#ffaa33" font-size="7" font-family="system-ui">RST</text>
      <text x="225" y="105" fill="#ff4466" font-size="7" font-family="system-ui">LED</text>
      <text x="160" y="150" text-anchor="middle" fill="#9090a8" font-size="9" font-family="system-ui">Check manual \u2014 layout varies per board</text>
    </svg>`,
    },
    {
        id: "m2",
        icon: "\u{1F4E6}",
        name: "M.2 NVMe",
        desc: "Fast storage",
        detail: "M.2 NVMe Slot",
        sub: "High-speed SSD slot on motherboard",
        tips: [
            {
                ico: "\u{1F4A1}",
                text: "Insert at a 30\u00B0 angle into the M-key slot, then press down and secure with the standoff screw.",
            },
            {
                ico: "\u26A0\uFE0F",
                text: "Remove the heatsink cover first if your board has one. Peel the thermal pad film!",
            },
            {
                ico: "\u{1F50D}",
                text: "Usually between the CPU and the first PCIe slot.",
            },
        ],
        svg: `<svg viewBox="0 0 320 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <text x="160" y="25" text-anchor="middle" fill="#55556a" font-size="11" font-family="system-ui">M.2 SLOT (M-KEY)</text>
      <rect x="60" y="80" width="200" height="24" rx="3" fill="#1a1a24" stroke="#3a3a50"/>
      <rect x="68" y="86" width="140" height="12" rx="2" fill="#00d4aa" opacity="0.2"/>
      <circle cx="240" cy="92" r="6" fill="none" stroke="#ffaa33" opacity="0.5" stroke-width="1.5"/>
      <text x="255" y="96" fill="#ffaa33" font-size="8" font-family="system-ui">screw</text>
      <path d="M90 70 Q90 50 120 50 L160 50" stroke="#55556a" stroke-dasharray="3 2"/>
      <text x="165" y="54" fill="#9090a8" font-size="8" font-family="system-ui">Insert at 30\u00B0 angle</text>
      <text x="160" y="140" text-anchor="middle" fill="#9090a8" font-size="9" font-family="system-ui">Push down flat, then secure screw</text>
    </svg>`,
    },
];

// ── UI State ──
let cameraOn = false;
let partsOpen = false;
let progressOpen = true;
let liveFeedInterval = null;

// ── Render functions ──
function renderSteps() {
    const list = $("#steps-list");
    const done = doneSet.size;
    const total = BUILD_STEPS.length;
    $("#prog-frac").textContent = done + " / " + total;
    $("#prog-fill").style.width = (done / total) * 100 + "%";

    list.innerHTML = BUILD_STEPS.map((s, i) => {
        const isDone = doneSet.has(s.id);
        const isCurr = i === currentStep && !isDone;
        const cls = isDone ? "done" : isCurr ? "now" : "";
        return (
            '<div class="step ' + cls + '">' +
            '<div class="step-dot">' + (isDone ? "\u2713" : "") + "</div>" +
            '<div class="step-info"><div class="step-text">' + s.label + "</div>" +
            (s.sub ? '<div class="step-sub">' + s.sub + "</div>" : "") +
            "</div></div>"
        );
    }).join("");
}

function renderParts() {
    const grid = $("#parts-grid");
    grid.innerHTML = PARTS.map(
        (p) =>
            '<div class="pcard" data-part="' +
            p.id +
            '">' +
            '<div class="pcard-ico">' +
            p.icon +
            "</div>" +
            '<div class="pcard-name">' +
            p.name +
            "</div>" +
            '<div class="pcard-sub">' +
            p.desc +
            "</div>" +
            "</div>"
    ).join("");

    grid.querySelectorAll(".pcard").forEach((c) => {
        c.addEventListener("click", function () {
            openDetail(this.dataset.part);
        });
    });
}

function openDetail(id) {
    const p = PARTS.find((x) => x.id === id);
    if (!p) return;
    $("#det-ico").textContent = p.icon;
    $("#det-title").textContent = p.detail;
    $("#det-sub").textContent = p.sub;
    $("#det-img").innerHTML = p.svg;
    $("#det-tips").innerHTML = p.tips
        .map(
            (t) =>
                '<div class="det-tip"><span class="det-tip-ico">' +
                t.ico +
                "</span><span>" +
                t.text +
                "</span></div>"
        )
        .join("");
    $("#detail-overlay").classList.add("open");
}

function closeDetail() {
    $("#detail-overlay").classList.remove("open");
}

function showPanel(name) {
    $$(".panel").forEach((p) => p.classList.remove("on"));
    $("#panel-" + name).classList.add("on");
}

function toggleParts() {
    partsOpen = !partsOpen;
    $("#parts-popup").classList.toggle("open", partsOpen);
    $("#btn-parts").classList.toggle("on", partsOpen);
}

// ── Speech / Orb state ──
function setSpeech(state) {
    const pill = $("#speech-pill");
    const label = $("#speech-label");
    const orb = $("#orb");
    const os = $("#orb-state");

    pill.classList.remove("active");
    orb.classList.remove("listening", "speaking");

    if (state === "listening") {
        pill.classList.add("active");
        label.textContent = "Listening\u2026";
        orb.classList.add("listening");
        os.textContent = "Listening";
    } else if (state === "speaking") {
        pill.classList.add("active");
        label.textContent = "AI Speaking\u2026";
        orb.classList.add("speaking");
        os.textContent = "Speaking";
    } else {
        label.textContent = "Tap to speak";
        os.textContent = "Ready";
    }
}

function setMsg(msg) {
    $("#ai-msg").textContent = msg;
}

function setUserTranscript(text) {
    const el = $("#user-transcript");
    if (text) {
        el.textContent = '\u201C' + text + '\u201D';
        el.classList.add("visible");
    } else {
        el.classList.remove("visible");
    }
}

// ── Image popup (for backend tool call images) ──
function showImagePopup(url, caption) {
    const img = $("#image-popup-img");
    const cap = $("#image-caption");
    img.src = url;
    if (caption) {
        cap.textContent = caption;
        cap.classList.add("visible");
    } else {
        cap.classList.remove("visible");
    }
    $("#image-overlay").classList.add("open");
}

function closeImagePopup() {
    $("#image-overlay").classList.remove("open");
    $("#image-popup-img").src = "";
}

// ── Connection status ──
function updateConnectionStatus(connected) {
    const dot = $("#connDot");
    const os = $("#orb-state");
    if (connected) {
        dot.classList.remove("disconnected");
        dot.title = "Connected";
    } else {
        dot.classList.add("disconnected");
        dot.title = "Disconnected";
        os.textContent = "Disconnected";
    }
}

// ── Build progress update (from update_part_status tool) ──
// Backend response shape:
// {
//   updated_part: "cpu",
//   new_status: "DONE" | "IN_PROGRESS" | "NOT_STARTED" | "BLOCKED",
//   part_notes: "...",
//   completed_tasks: ["cpu", "ram"],
//   remaining_tasks: ["cooler", "mobo", ...]
// }
function handlePartStatusUpdate(response) {
    const partId = response.updated_part;
    const status = response.new_status;

    if (!partId) {
        console.warn("update_part_status: no updated_part in response", response);
        return;
    }

    if (status === "DONE") {
        doneSet.add(partId);
    } else if (status === "NOT_STARTED") {
        // Undo / reset
        doneSet.delete(partId);
    } else if (status === "IN_PROGRESS") {
        // Don't mark done, but ensure it's the active step
        doneSet.delete(partId);
    } else if (status === "BLOCKED") {
        // Don't mark done; keep visible as current
        doneSet.delete(partId);
    }

    // If backend gives us the full completed list, trust it as source of truth
    if (response.completed_tasks && Array.isArray(response.completed_tasks)) {
        doneSet.clear();
        response.completed_tasks.forEach((id) => doneSet.add(id));
    }

    // Advance currentStep to the first non-done step
    currentStep = BUILD_STEPS.findIndex((s) => !doneSet.has(s.id));
    if (currentStep === -1) currentStep = BUILD_STEPS.length;

    renderSteps();

    // Check if build is complete
    if (doneSet.size === BUILD_STEPS.length) {
        setMsg("Build complete! Great job.");
    }
}

// ══════════════════════════════════════════════════════════════
// ── WEBSOCKET ──
// ══════════════════════════════════════════════════════════════

const userId = "demo-user";
const sessionId =
    "demo-session-" + Math.random().toString(36).substring(7);
let websocket = null;
let is_audio = false;
let isToolRunning = false;

function getWebSocketUrl() {
    const wsProtocol =
        window.location.protocol === "https:" ? "wss:" : "ws:";
    const baseUrl =
        wsProtocol + "//" + window.location.host + "/ws/" + userId + "/" + sessionId;
    // Hardcode proactivity + affective dialog on for demo, or adjust as needed
    const params = new URLSearchParams();
    // params.append("proactivity", "true");
    // params.append("affective_dialog", "true");
    const queryString = params.toString();
    return queryString ? baseUrl + "?" + queryString : baseUrl;
}

// ── Transcription state ──
let currentOutputText = "";
let isReceivingOutput = false;

function connectWebsocket() {
    const ws_url = getWebSocketUrl();
    websocket = new WebSocket(ws_url);

    websocket.onopen = function () {
        console.log("WebSocket connected.");
        updateConnectionStatus(true);
        setMsg("Connected! Tap the mic to start your build session.");
        $("#speech-label").textContent = "Tap to speak";
        $("#orb-state").textContent = "Ready";
    };

    websocket.onmessage = function (event) {
        const adkEvent = JSON.parse(event.data);
        console.log("[AGENT->CLIENT]", JSON.stringify(adkEvent, null, 2));

        // ── Turn complete ──
        if (adkEvent.turnComplete === true) {
            isToolRunning = false;
            isReceivingOutput = false;
            currentOutputText = "";
            setSpeech("idle");
            setUserTranscript(""); // clear user transcript
            return;
        }

        // ── Interrupted ──
        if (adkEvent.interrupted === true) {
            isToolRunning = false;
            isReceivingOutput = false;
            currentOutputText = "";
            if (audioPlayerNode) {
                audioPlayerNode.port.postMessage({ command: "endOfAudio" });
            }
            setSpeech("idle");
            return;
        }

        // ── Input transcription (what the user is saying) ──
        if (adkEvent.inputTranscription && adkEvent.inputTranscription.text) {
            const text = adkEvent.inputTranscription.text;
            setSpeech("listening");
            setUserTranscript(text);
        }

        // ── Output transcription (what the AI is saying) ──
        if (adkEvent.outputTranscription && adkEvent.outputTranscription.text) {
            const text = adkEvent.outputTranscription.text;
            const isFinished = adkEvent.outputTranscription.finished;

            setSpeech("speaking");

            if (isFinished) {
                // Final transcription — show complete text
                setMsg(text);
                currentOutputText = "";
            } else {
                // Partial — accumulate
                currentOutputText += text;
                setMsg(currentOutputText);
            }
            isReceivingOutput = true;
        }

        // ── Content parts (audio, text, tool calls/responses) ──
        if (adkEvent.content && adkEvent.content.parts) {
            const parts = adkEvent.content.parts;

            // Check for tool start
            const hasToolCall = parts.some((p) => p.functionCall);
            if (hasToolCall) {
                isToolRunning = true;
            }

            for (const part of parts) {
                // ── update_part_status tool response → update build progress ──
                if (
                    part.functionResponse &&
                    part.functionResponse.name === "update_part_status"
                ) {
                    const response = part.functionResponse.response;
                    if (response) {
                        handlePartStatusUpdate(response);
                    }
                    continue;
                }

                // ── get_connector_image tool response → show image popup ──
                if (
                    part.functionResponse &&
                    part.functionResponse.name === "get_connector_image"
                ) {
                    const response = part.functionResponse.response;
                    if (response && response.connector_url) {
                        showImagePopup(response.connector_url, "Connector Reference");
                    }
                    continue;
                }

                // ── show_user_part tool response → show image popup ──
                if (
                    part.functionResponse &&
                    part.functionResponse.name === "show_user_part"
                ) {
                    const response = part.functionResponse.response;
                    if (response && response.image_url) {
                        showImagePopup(response.image_url, "Part Reference");
                    }
                    continue;
                }

                // ── Audio playback ──
                if (part.inlineData) {
                    const mimeType = part.inlineData.mimeType;
                    const data = part.inlineData.data;
                    if (mimeType && mimeType.startsWith("audio/pcm") && audioPlayerNode) {
                        setSpeech("speaking");
                        audioPlayerNode.port.postMessage(base64ToArray(data));
                    }
                }

                // ── Text content (fallback if no output transcription) ──
                if (part.text && !part.thought) {
                    // Only show text in the UI if output transcription isn't handling it
                    if (!isReceivingOutput) {
                        setSpeech("speaking");
                        if (adkEvent.partial) {
                            currentOutputText += part.text;
                            setMsg(currentOutputText);
                        } else {
                            setMsg(part.text);
                            currentOutputText = "";
                        }
                    }
                }
            }
        }
    };

    websocket.onclose = function () {
        console.log("WebSocket closed.");
        updateConnectionStatus(false);
        setMsg("Connection lost. Reconnecting...");
        setSpeech("idle");
        setTimeout(function () {
            connectWebsocket();
        }, 5000);
    };

    websocket.onerror = function (e) {
        console.error("WebSocket error:", e);
        updateConnectionStatus(false);
    };
}

// ── Base64 → ArrayBuffer ──
function base64ToArray(base64) {
    let standardBase64 = base64.replace(/-/g, "+").replace(/_/g, "/");
    while (standardBase64.length % 4) {
        standardBase64 += "=";
    }
    const binaryString = window.atob(standardBase64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
}

// ══════════════════════════════════════════════════════════════
// ── CAMERA ──
// ══════════════════════════════════════════════════════════════

async function toggleCam() {
    if (cameraOn) {
        // Stop camera
        const feed = $("#cam-feed");
        if (feed.srcObject) {
            feed.srcObject.getTracks().forEach((t) => t.stop());
            feed.srcObject = null;
        }
        // Stop live feed interval
        if (liveFeedInterval) {
            clearInterval(liveFeedInterval);
            liveFeedInterval = null;
        }
        cameraOn = false;
        $("#btn-cam").classList.remove("on");
        showPanel("listen");
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: "environment",
                    width: { ideal: 1024 },
                    height: { ideal: 1024 },
                },
                audio: false,
            });
            $("#cam-feed").srcObject = stream;
            cameraOn = true;
            $("#btn-cam").classList.add("on");
            showPanel("cam");

            // Start sending frames every 1s (same as your original captureImageBtn flow)
            captureAndSendFrame(); // immediate first capture
            liveFeedInterval = setInterval(captureAndSendFrame, 1000);
        } catch (e) {
            console.error("Camera error:", e);
            setMsg("Camera access denied. Check browser permissions.");
        }
    }
}

function captureAndSendFrame() {
    const feed = $("#cam-feed");
    if (!feed.srcObject || isToolRunning) return;

    try {
        const canvas = document.createElement("canvas");
        canvas.width = feed.videoWidth;
        canvas.height = feed.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(feed, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(
            (blob) => {
                if (!blob) return;
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64data = reader.result.split(",")[1];
                    sendImage(base64data);
                };
                reader.readAsDataURL(blob);
            },
            "image/jpeg",
            0.85
        );
    } catch (e) {
        console.error("Frame capture error:", e);
    }
}

function sendImage(base64Image) {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(
            JSON.stringify({
                type: "image",
                data: base64Image,
                mimeType: "image/jpeg",
            })
        );
        console.log("[CLIENT->AGENT] Sent image frame");
    }
}

// ══════════════════════════════════════════════════════════════
// ── AUDIO ──
// ══════════════════════════════════════════════════════════════

let audioPlayerNode;
let audioPlayerContext;
let audioRecorderNode;
let audioRecorderContext;
let micStream;

import { startAudioPlayerWorklet } from "./audio-player.js";
import { startAudioRecorderWorklet } from "./audio-recorder.js";

function startAudio() {
    startAudioPlayerWorklet().then(([node, ctx]) => {
        audioPlayerNode = node;
        audioPlayerContext = ctx;
    });
    startAudioRecorderWorklet(audioRecorderHandler).then(
        ([node, ctx, stream]) => {
            audioRecorderNode = node;
            audioRecorderContext = ctx;
            micStream = stream;
        }
    );
}

function audioRecorderHandler(pcmData) {
    if (websocket && websocket.readyState === WebSocket.OPEN && is_audio) {
        websocket.send(pcmData);
    }
}

// ══════════════════════════════════════════════════════════════
// ── EVENT WIRING ──
// ══════════════════════════════════════════════════════════════

// Progress toggle
$("#prog-toggle").addEventListener("click", function () {
    progressOpen = !progressOpen;
    $("#progress").classList.toggle("shut", !progressOpen);
});

// Camera button
$("#btn-cam").addEventListener("click", function () {
    // Close parts popup when switching to camera
    if (partsOpen) {
        partsOpen = false;
        $("#parts-popup").classList.remove("open");
        $("#btn-parts").classList.remove("on");
    }
    toggleCam();
});

// Parts reference
$("#btn-parts").addEventListener("click", toggleParts);
$("#popup-close").addEventListener("click", toggleParts);

// Part detail modal
$("#det-close").addEventListener("click", closeDetail);
$("#detail-overlay").addEventListener("click", function (e) {
    if (e.target === e.currentTarget) closeDetail();
});

// Image overlay
$("#image-close").addEventListener("click", closeImagePopup);
$("#image-overlay").addEventListener("click", function (e) {
    if (e.target === e.currentTarget) closeImagePopup();
});

// Speech pill — starts audio on first tap, then acts as status indicator
let audioStarted = false;
$("#speech-pill").addEventListener("click", function () {
    if (!audioStarted) {
        audioStarted = true;
        startAudio();
        is_audio = true;
        setMsg("Audio enabled \u2014 start speaking to begin your build.");
        setSpeech("idle");
        console.log("Audio mode enabled");
    }
});

// Share button — opens report page in new tab
$("#btn-share").addEventListener("click", function () {
    window.open("/report/page", "_blank");
});

// ══════════════════════════════════════════════════════════════
// ── INIT ──
// ══════════════════════════════════════════════════════════════

renderSteps();
renderParts();
connectWebsocket();
