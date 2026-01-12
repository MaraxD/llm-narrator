# LLM narrator
This project is an extension of Robo plush toy. I have added a llm-narrator acting as a museum guide, that describes my crocheted robot. This project uses a custom trained model with MediaPipe's real time object detection, and Jan Zuiderveld's llm actor. The narrator reacts based on robot's presence and emotions.

## Prerequisites

* [Python 3.10](https://www.python.org/downloads/) or newer (3.11 recommended as it's the version that this is tested on).
* [Deepgram](https://developers.deepgram.com/reference/deepgram-api-overview) and [Google API](https://ai.google.dev/gemini-api/docs/api-key) credentials with access to Flux STT, Aura-2 TTS, and Gemini 2.5 Flash.
* System audio devices accessible to PortAudio (used by Pipecat's local audio transport).
  * macOS: `brew install portaudio`
  * Ubuntu/Debian: `sudo apt install portaudio19-dev`
  * Windows: the bundled `sounddevice` wheel ships PortAudio automatically. However, Windows users need to install [ffmpeg](https://phoenixnap.com/kb/ffmpeg-windows) for audio playback.
* Clone/download [Interactive Robot](https://github.com/MaraxD/interactive-robot/tree/llm-narrator) and follow the instructions before starting (if you only want to speak with the llm-actor, skip this step and the model training one)

## MediaPipe custom model training & object detection 
For this idea i wanted to have my own custom data set in order for the robot to be detected by a camera. For this i took 130 pictures of my plush robot (some of them were mirrored), and labeled them using [Label Studio](https://labelstud.io/guide/install). I then exported everything as **Pascal VOC XML**.

You will then need to split some of the data. 80% of the data will be used for training, 10% for testing and the rest of 10% for validation. After the split, you will need to put the selected images under the folder `model_training/robo_plush/train` and the rest under `model_training/robo_plush/validate`. The idea of validation is to show the model new data that has not been in the training phase in order to see how well the model recognizes the object(s).

After the model has been generated (`robo_plush.tflite`), you can start testing the real time object detection by running `model_training/robo_recognition`.

## LLM actor (Jan Zuiderveld)
This project packages a thin Python CLI around [Pipecat](https://docs.pipecat.ai/) to deliver a real-time audio loop using Deepgram Flux speech-to-text, Gemini 2.5 Flash streaming text generation, and Deepgram Aura-2 text-to-speech. External automation hooks are exposed via append-only files under `runtime/`.

## Features

* Deepgram Flux STT → Gemini 2.5 Flash → Deepgram Aura-2 TTS pipeline, fully streaming.
* File-based automation using append-only `runtime/inbox.txt`, `runtime/actions.txt`, and `runtime/params_inbox.ndjson`.
* Turn-level transcript and event logging per session.
* Runtime parameter application between turns (LLM, STT, TTS, history operations).

## Quickstart

Projects provide self-contained recipes that wrap the core audio loop, refresh runtime state, and launch any helper daemons you need alongside the agent. The repository ships with an **Exclusive Door** experience that demonstrates how to run the full pipeline with custom automation.

Follow these steps to run the door project end-to-end:

1. **Set up the environment**

   ```bash
   git clone https://github.com/janzuiderveld/llm-actor
   cd llm_actor
   python -m venv .venv # make sure to use python3.10+ (use python -V to check)
   # if you get "command not found: python" type python3 instead of python
   
   source .venv/bin/activate # for Mac or Linux
   
   .venv\Scripts\activate # for Windows
   
   python -m pip install --upgrade pip 
   pip install -e .
   ```

   Reactivate the virtual environment with `source .venv/bin/activate` (Mac/Linux) or `.venv\Scripts\activate` (Windows) whenever you open a new terminal for this project.

2. **Add credentials and defaults**

   (Mac)
   ```bash
   cp .env.example .env
   ```
   
   (Windows)
   ```bash
   copy .env.example .env
   ```

   Open `.env` in your editor and fill in `GOOGLE_API_KEY`, `DEEPGRAM_API_KEY`, and any optional defaults (LLM, STT, voice) you want to preload. Save the file before continuing.

4. **Launch the example project**

   ```bash
   python EXAMPLE_PROJECT/boot.py
   ```

   The boot script resets `runtime/`, seeds the persona, and starts the main audio loop together with the helper daemons. Stop everything with `Ctrl+C` when you are done.

When the project is running, a terminal window running `inbox_writer.py` prompts you to press Enter to simulate “someone approaches the door.” The action watcher listens for `<UNLOCK>` / `<LOCK>` directives given by the persona and keeps the persona aligned with the door state.

### Project Files

- `EXAMPLE_PROJECT/boot.py`: Coordinates startup, clears prior transcripts, seeds the locked persona, and spins up the helper processes. Adjust the `locked_config` and `unlocked_config` blocks to experiment with different prompts or voices.
- `EXAMPLE_PROJECT/action_watcher.py`: Monitors `runtime/actions.txt` for `<UNLOCK>` / `<LOCK>` cues, keeps `runtime/inbox.txt` tidy, and flips between the locked and unlocked personalities.
- `EXAMPLE_PROJECT/inbox_writer.py`: Provides a simple keyboard loop that appends “someone approaches the door” to `runtime/inbox.txt`, triggering a new turn whenever a visitor arrives.
- `runtime/actions.txt`: Append-only instruction log produced by the agent. External automations (such as the watcher) listen here for directives like `<UNLOCK>`.
- `runtime/inbox.txt`: Entry point for out-of-band events and user speech. The watcher uses it to queue prompts that walk the agent through the door state transitions.
- `runtime/params_inbox.ndjson`: Applies configuration tweaks between turns. The watcher writes persona swaps into this file when the door locks or unlocks.
- `runtime/conversations/<timestamp>/`: Holds transcripts and event logs for each session. Use it to inspect how the persona responded while you iterate on prompts.
- `EXAMPLE_PROJECT/assets/*.mp3`: The short door-open and door-close cues that play alongside persona changes. Swap them with your own audio to customize the ambience.


## Runtime Automation Reference

**`runtime/inbox.txt`**
- `P: <text>` — push a full user turn immediately.
- `A: <text>` — buffer supplemental text; multiple lines are joined with newlines and appended to the next user entry.

**`runtime/actions.txt`**
- Append-only log emitted by the agent (everything between <...> is added to this file. for example `<LOCK>` > `LOCK\n`). External services should tail this file and react to directives as they appear.

**`runtime/params_inbox.ndjson`**
- Processed between turns to adjust runtime behavior. Append any of the following operations one JSON object per line:

```bash
{"op":"history.reset"}
{"op":"history.append","role":"user","content":"Remember my name is Kai."}
{"op":"llm.set","model":"gemini-2.5-flash","temperature":0.6,"max_tokens":1024}
{"op":"llm.system","text":"You are a concise assistant."}
{"op":"stt.flux","eager_eot_threshold":0.5,"eot_threshold":0.85,"eot_timeout_ms":1500}
{"op":"tts.set","voice":"aura-2-thalia-en","encoding":"linear16","sample_rate":24000}
```

## Acoustic Echo Cancellation

- Install [Krisp](https://krisp.ai/download/) for system-level acoustic echo cancellation. This makes sure persona output does not leak into the microphone input.
- Set **Krisp Microphone** and **Krisp Speaker** as your input/output devices in `boot.py` or use the auto flag in the audio config.
NOTE: It is possible that sound output is crackling when using Krisp. If this happens, for now continue with headphones. Will do a universal fix in future update.

## Testing

The test harness expects valid API keys in your environment. Once configured, run:

```bash
pytest -q
```

Tests perform the following real API checks:

1. `tests/test_api_readiness.py`
   * Streams a short utterance through Deepgram Flux STT and validates a transcript.
   * Requests a 1-second sample from Deepgram Aura-2 TTS.
   * Streams a small prompt through Gemini 2.5 Flash and verifies tokens arrive.
2. `tests/test_full_pipeline.py`
   * Synthesizes test audio via Deepgram TTS and feeds it into the Pipecat pipeline.
   * Logs turn-level latency markers including TTFRAP (time to first response audio packet).

If credentials are missing the tests skip with a clear message.

## Troubleshooting

* **Audio devices missing**: Ensure PortAudio is installed (see prerequisites) and run `python -m sounddevice` inside your virtualenv to confirm the runtime can enumerate devices.
* **429 / rate limits**: The tests and pipeline perform real API calls; adjust usage or upgrade account tiers if needed.
* **High latency**: Tune Flux EOT thresholds via `runtime/params_inbox.ndjson` to improve responsiveness.
* **SSL CERTIFICATE_VERIFY_FAILED**: (error on Mac) try running `/Applications/Python\ 3.x/Install\ Certificates.command` and replace the version number with your current one

## License

MIT
