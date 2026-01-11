"""Watch the shared action log and update the door's persona when it changes."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from projects.utils import (
    ACTIONS_FILE,
    INBOX_FILE,
    append_inbox_line,
    ensure_runtime_files,
    set_system_prompt,
    tail_line,
)
from .boot import (
    NARRATOR_PROMPT_NOT_DETECTED as DEFAULT_LOCKED_PROMPT,
    NARRATOR_PROMPT_DETECTED as DEFAULT_UNLOCKED_PROMPT,
    NARRATOR_FEELING as DEFAULT_FEELING_PROMPT,
    PROMPT_APPEND as PROMPT_APPEND,
)

from model_training.robo_recognition import robot as is_robot

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def main() -> None:
    # Ensure the shared files exist before we try to read from them.
    ensure_runtime_files()
    print("Starting action watcher...")
    with (
        ACTIONS_FILE.open("r", encoding="utf-8") as actions,
        INBOX_FILE.open("r", encoding="utf-8") as inbox,
    ):
        # Jump to the end so we only process new lines that arrive after startup.
        actions.seek(0, os.SEEK_END)
        inbox.seek(0, os.SEEK_END)

        # Track whether the door is currently locked so we know which persona to use.
        locked = True
        locked_prompt = (
            os.getenv("EXAMPLE_PROJECT_LOCKED_PROMPT")
            or os.getenv("LOCKED_PROMPT")
            or DEFAULT_LOCKED_PROMPT
        )
        unlocked_prompt = (
            os.getenv("EXAMPLE_PROJECT_UNLOCKED_PROMPT")
            or os.getenv("UNLOCKED_PROMPT")
            or DEFAULT_UNLOCKED_PROMPT
        )
        narrator_feeling = DEFAULT_FEELING_PROMPT

        print("starting loop")

        try:
            while True:
                action_line = tail_line(actions)
                if action_line and is_robot["detected"]:
                    if action_line == "NEUTRAL":
                        print("robot is neutral")
                        # Swap the assistant's persona and tell listeners what happened.
                        append_inbox_line(
                            "P: [The robot is neutral, the speech of the museum guide changed, see current system message]"
                        )
                        set_system_prompt(unlocked_prompt)
                        continue
                    # if action_line == "DETECTED":
                    #     print("robot appeared")
                    #     locked = False
                    #     # Swap the assistant's persona and tell listeners what happened.
                    #     set_system_prompt(unlocked_prompt)
                    #     append_inbox_line(
                    #         "A: [The robot appeared in the frame, the speech of the museum guide changed, see current system message]"
                    #     )
                    #     continue
                    # if action_line == "NOT DETECTED":
                    #     print("robot disappeared")
                    #     locked = True
                    #     # Restore the locked persona and log the change for the user.
                    #     set_system_prompt(locked_prompt)
                    #     append_inbox_line(
                    #         "A: [The robot has not appeared in the frame, the speech of the museum guide changed, see current system message]"
                    #     )
                    #     continue
                    if action_line == "EEPY":
                        print("robot is asleep")
                        EEPY_PROMPT = "The famous robo plush is now asleep, encourage everyone to speak in a quiet manner. You should also speak quietly from this point on, until the robot wakes up."
                        narrator_feeling += (
                            "\n\n" + EEPY_PROMPT + "\n\n" + PROMPT_APPEND
                        )
                        append_inbox_line(
                            "P: [The robot is asleep, the speech of the museum guide changed, see current system message]"
                        )
                        set_system_prompt(narrator_feeling)
                        continue
                    if action_line == "DISTRESS":
                        print("robot is in distress")
                        DISTRESS_PROMPT = "The famous robo plush is in distress!!! Tell people to not scare the robot, and to turn on the light if they turned them off. Have an annoyed voice throughout all this."
                        narrator_feeling += (
                            "\n\n" + DISTRESS_PROMPT + "\n\n" + PROMPT_APPEND
                        )
                        append_inbox_line(
                            "P: [The robot is in distress, the speech of the museum guide changed, see current system message]"
                        )
                        set_system_prompt(narrator_feeling)
                        continue
                    if action_line == "HURT":
                        print("robot is hurt")
                        HURT_PROMPT = "The famous robo plush is being shaken too agresively!!! Scold the person who did that. Have an annoyed and angry voice throughout all this."
                        narrator_feeling += (
                            "\n\n" + HURT_PROMPT + "\n\n" + PROMPT_APPEND
                        )
                        append_inbox_line(
                            "A: [The robot is hurt, the speech of the museum guide changed, see current system message]"
                        )
                        set_system_prompt(narrator_feeling)
                        continue

                time.sleep(0.2)
        except KeyboardInterrupt:
            print("Action watcher stopped by KeyboardInterrupt.")
        except Exception as e:
            print(f"Action watcher stopped by Exception: {e}")
            import traceback

            traceback.print_exc()
            time.sleep(10)


if __name__ == "__main__":
    main()
