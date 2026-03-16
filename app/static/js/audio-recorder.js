/**
 * Audio Recorder Worklet
 */

const SEND_INTERVAL_MS = 50; // Flush every 50ms, to prevent overloading api

let micStream;

export async function startAudioRecorderWorklet(audioRecorderHandler) {
    // Create an AudioContext
    const audioRecorderContext = new AudioContext({ sampleRate: 16000 });
    console.log("AudioContext sample rate:", audioRecorderContext.sampleRate);

    // Load the AudioWorklet module
    const workletURL = new URL("./pcm-recorder-processor.js", import.meta.url);
    await audioRecorderContext.audioWorklet.addModule(workletURL);

    // Request access to the microphone
    micStream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1 },
    });
    const source = audioRecorderContext.createMediaStreamSource(micStream);

    // Create an AudioWorkletNode that uses the PCMProcessor
    const audioRecorderNode = new AudioWorkletNode(
        audioRecorderContext,
        "pcm-recorder-processor"
    );

    // Connect the microphone source to the worklet.
    source.connect(audioRecorderNode);

    // Buffer the audio sending
    let pcmBuffer = [];
    let pcmBufferBytes = 0;

    // Flush as a single merged buffer
    function flushBuffer() {
        if (pcmBufferBytes === 0) {
            return;
        }
        // TODO:
        // Merge and reset 

        const merged = new Uint8Array(pcmBufferBytes);
        let offset = 0;
        for (const chunk of pcmBuffer) {
            merged.set(new Uint8Array(chunk), offset);
            offset += chunk.byteLength;
        }

        // reset 
        pcmBuffer = [];
        pcmBufferBytes = 0;

        audioRecorderHandler(merged.buffer)
    }

    // flush on fixed interval, prevent flooding
    const flushTimer = setInterval(flushBuffer, SEND_INTERVAL_MS)

    audioRecorderNode.port.onmessage = (event) => {
        // Convert to 16-bit PCM
        const pcmData = convertFloat32ToPCM(event.data);

        // Accumulate, don't send yet
        pcmBuffer.push(pcmData);
        pcmBufferBytes += pcmData.byteLength;
    };

    // Attach cleanup so callers can cancel 
    audioRecorderNode._flushTimer = flushTimer;

    return [audioRecorderNode, audioRecorderContext, micStream];
}

/**
 * Stop the microphone.
 */
export function stopMicrophone(micStream) {
    micStream.getTracks().forEach((track) => track.stop());
    console.log("stopMicrophone(): Microphone stopped.");
}

// Convert Float32 samples to 16-bit PCM.
function convertFloat32ToPCM(inputData) {
    // Create an Int16Array of the same length.
    const pcm16 = new Int16Array(inputData.length);
    for (let i = 0; i < inputData.length; i++) {
        // Multiply by 0x7fff (32767) to scale the float value to 16-bit PCM range.
        pcm16[i] = inputData[i] * 0x7fff;
    }
    // Return the underlying ArrayBuffer.
    return pcm16.buffer;
}
