## Getting Started

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- A Google API key with Gemini API access
- A Google Cloud project with Firestore and Cloud Storage enabled

### Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/0xKev/build-buddy.git
   cd build-buddy
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Fill in your `.env`:
   - `GOOGLE_API_KEY` - your Gemini API key
   - `PROJECT_ID` - your Google Cloud project ID
   - `GS_BUCKET_ID` - your Cloud Storage bucket name
   - `FIRESTORE_COLLECTION_ID` - your Firestore collection name

4. **Run locally (from project root)**
   ```bash
   make run
   ```
   The app will be available at `http://localhost:8000`

### Docker (alternative)
Run from the project root
```bash
make docker-build
make docker-run
```

### Testing the App

1. Open `http://localhost:8000` on your phone or in a mobile-sized browser window
2. **Tap the mic button** (bottom center) to enable audio, this is required before the AI can hear you
3. **Start talking** - say something like "I'm ready to start my build" and the AI will guide you through each step
4. **Try the camera** - tap the camera icon (top right) to open the live camera feed. Point it at a PC part and the AI will identify it
5. **Browse parts reference** - tap the wrench icon (top right) to see connector diagrams. Tap any card for detailed info
6. **Watch build progress** - as the AI guides you through steps, the progress bar at the top updates automatically
7. **View the build report** - tap the link icon (top right) to open the shareable build timeline at `/report/page`

**Note:** A microphone and camera are required for the full experience. Use Chrome or Edge for best Web Audio API support.

**Important:** This hackathon demo does not use session isolation. All build data is stored in a single Firestore collection and GCS bucket. For a clean experience, clear your Firestore collection and GCS bucket before each new build session.
