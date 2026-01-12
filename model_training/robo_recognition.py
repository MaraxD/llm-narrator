import argparse
import sys
import time
import os

import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from model_training.utils import visualize
from projects import append_action, append_inbox_line, set_system_prompt

from EXAMPLE_PROJECT.boot import (
    NARRATOR_PROMPT_NOT_DETECTED as DEFAULT_LOCKED_PROMPT,
    NARRATOR_PROMPT_DETECTED as DEFAULT_UNLOCKED_PROMPT,
)
from projects.utils import append_detection

detection_threshold = 10
detection_counter = {"count": 0}

robot = {"detected": False}

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


def run(model: str, camera_id: int, width: int, height: int) -> None:
    """Continuously run inference on images acquired from the camera.

    Args:
      model: Name of the TFLite object detection model.
      camera_id: The camera id to be passed to OpenCV.
      width: The width of the frame captured from the camera.
      height: The height of the frame captured from the camera.
    """

    # Variables to calculate FPS
    counter, fps = 0, 0
    start_time = time.time()

    # Start capturing video input from the camera
    cap = cv2.VideoCapture(camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # Visualization parameters
    row_size = 20  # pixels
    left_margin = 24  # pixels
    text_color = (0, 0, 255)  # red
    font_size = 1
    font_thickness = 1
    fps_avg_frame_count = 10

    detection_result_list = []

    def visualize_callback(
        result: vision.ObjectDetectorResult,
        output_image: mp.Image,
        timestamp_ms: int,
    ):
        result.timestamp_ms = timestamp_ms
        # only append when something was detected and the probability is relatively high
        if result.detections and result.detections[0].categories[0].score > 0.71:
            detection_counter["count"] += 1
        else:
            detection_counter["count"] = 0

        detection_result_list.append(result)

        if detection_counter["count"] >= detection_threshold and not robot["detected"]:
            robot["detected"] = True
            append_detection(text="DETECTED")
            set_system_prompt(unlocked_prompt)
            append_inbox_line(
                text="P: [The plush robot toy has appeared in the frame.]"
            )

    # Initialize the object detection model
    base_options = python.BaseOptions(model_asset_path=model)
    options = vision.ObjectDetectorOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        score_threshold=0.5,
        result_callback=visualize_callback,
    )
    detector = vision.ObjectDetector.create_from_options(options)

    # Continuously capture images from the camera and run inference
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            sys.exit(
                "ERROR: Unable to read from webcam. Please verify your webcam settings."
            )

        counter += 1
        image = cv2.flip(image, 1)

        # Convert the image from BGR to RGB as required by the TFLite model.
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # Run object detection using the model.
        detector.detect_async(mp_image, counter)
        current_frame = mp_image.numpy_view()
        current_frame = cv2.cvtColor(current_frame, cv2.COLOR_RGB2BGR)

        # Calculate the FPS
        if counter % fps_avg_frame_count == 0:
            end_time = time.time()
            fps = fps_avg_frame_count / (end_time - start_time)
            start_time = time.time()

        # Show the FPS
        fps_text = "FPS = {:.1f}".format(fps)
        text_location = (left_margin, row_size)
        cv2.putText(
            current_frame,
            fps_text,
            text_location,
            cv2.FONT_HERSHEY_PLAIN,
            font_size,
            text_color,
            font_thickness,
        )

        if detection_result_list:
            # print(detection_result_list)
            vis_image = visualize(current_frame, detection_result_list[0])
            cv2.imshow("object_detector", vis_image)
            detection_result_list.clear()
        else:
            cv2.imshow("object_detector", current_frame)

        # Stop the program if the ESC key is pressed.
        if cv2.waitKey(1) == 27:
            break

    detector.close()
    cap.release()
    cv2.destroyAllWindows()


def main():
    print(os.getcwd())
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--model",
        help="Path of the object detection model.",
        required=False,
        default="model_training/exported_model/robo_plush.tflite",
    )
    parser.add_argument(
        "--cameraId", help="Id of camera.", required=False, type=int, default=0
    )
    parser.add_argument(
        "--frameWidth",
        help="Width of frame to capture from camera.",
        required=False,
        type=int,
        default=1280,
    )

    parser.add_argument(
        "--frameHeight",
        help="Height of frame to capture from camera.",
        required=False,
        type=int,
        default=720,
    )
    args = parser.parse_args()

    append_detection(text="NOT DETECTED")
    append_inbox_line(text="P: [The plush robot toy has not appeared in the frame.]")

    run(args.model, int(args.cameraId), args.frameWidth, args.frameHeight)


if __name__ == "__main__":
    main()
