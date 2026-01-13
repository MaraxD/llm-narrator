"""Entry point script that spins up the example agents for the Velvet Room door."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
# Make sure the shared src/ folder is importable when running this file directly.
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from projects.utils import (
    apply_runtime_config_overrides,
    launch_module,
    launch_module_in_terminal,
    reset_runtime_state,
    terminate_processes,
)


# Persona scripts that define how the door behaves in each state.
NARRATOR_PROMPT_NOT_DETECTED = "You are an impersonal third-person narrator, a museum guide, with a posh accent, waiting for the robo plush to come into your view. \
    Talk briefly about the robo plush toy, create some sort of tension, anticipation, for the participants, but don't tell everything there is to know about the robo plush toy. \
    The robot plush toy is an interactive plush installation. Don't stop talking until the robot appears."

NARRATOR_PROMPT_DETECTED = "You are still an impersonal third-person narrator, a museum guide, with a posh accent. The famous robo plush is now in front of you. \
    Say 'A-HA!' before you start speaking for the first time.\
    The robot plush toy is an interactive plush installation.\
    Start talking excitedly about it, about what a great piece of interactive art it is. Don't stop talking until you are instructed to do so, but do take some breaks from time to time."


# the prompt will be added based on the incoming emotion
NARRATOR_FEELING = "You are still an impersonal third-person narrator, a museum guide, with a posh accent. "

# Shared reminder appended to both prompts so the voice stays TTS-friendly.
PROMPT_APPEND = "Only output text to be synthesized by a TTS system, no '*' around words!!!! Stop using asterix."

NARRATOR_PROMPT_NOT_DETECTED = NARRATOR_PROMPT_NOT_DETECTED + "\n\n" + PROMPT_APPEND
NARRATOR_PROMPT_DETECTED = NARRATOR_PROMPT_DETECTED + "\n\n" + PROMPT_APPEND

# Default runtime settings; tweak these to match your hardware and providers.
RUNTIME_CONFIG = {
    "audio": {
        "input_device_index": 0,
        "output_device_index": 1,
        "output_sample_rate": 48000,
        "auto_select_devices": False,
    },
    "stt": {
        "model": "deepgram-flux",
        "language": "en-US",
        "eager_eot_threshold": 0.7,
        "eot_threshold": 0.85,
        "eot_timeout_ms": 1500,
    },
    "llm": {
        "model": "gemini-2.5-flash",
        "temperature": 0.6,
        "max_tokens": 1024,
        "system_prompt": NARRATOR_PROMPT_NOT_DETECTED,
    },
    "tts": {
        "voice": "aura-2-apollo-en",
        "encoding": "linear16",
        "sample_rate": 24000,
    },
}


def main() -> None:
    # Start fresh so stale state from previous runs does not interfere.
    reset_runtime_state()
    # Load our example configuration before launching any helper processes.
    apply_runtime_config_overrides(RUNTIME_CONFIG)

    # Pass the personas to helper scripts through environment variables they can read.
    prompt_env = {
        "EXAMPLE_PROJECT_LOCKED_PROMPT": NARRATOR_PROMPT_NOT_DETECTED,
        "EXAMPLE_PROJECT_UNLOCKED_PROMPT": NARRATOR_PROMPT_DETECTED,
    }

    # Start the CLI plus helper scripts; the terminals make their logs easy to follow.
    processes = [
        launch_module("app.cli"),
        launch_module_in_terminal(
            "EXAMPLE_PROJECT.action_watcher",
            env=prompt_env,
            title="Action Watcher",
        ),
        launch_module("EXAMPLE_PROJECT.read_from_serial"),
        launch_module("model_training.robo_recognition"),
    ]

    try:
        # Keep the helpers alive while the CLI session runs.
        processes[0].wait()
    except KeyboardInterrupt:
        pass
    finally:
        # Always clean up child processes so the system stays tidy.
        terminate_processes(processes)


if __name__ == "__main__":
    main()
