import os
import tensorflow as tf
assert tf.__version__.startswith('2')

from mediapipe_model_maker import object_detector

train_dataset_path = "./robo_plush/train"
validation_dataset_path = "./robo_plush/validate"

train_data = object_detector.Dataset.from_pascal_voc_folder(
    './robo_plush/train',
    cache_dir="/tmp/od_data/train",
)

print("train data size: ", train_data.size)

val_data = object_detector.Dataset.from_pascal_voc_folder(
    './robo_plush/validate',
    cache_dir="/tmp/od_data/validation")

print("validation data size: ", val_data.size)


hparams = object_detector.HParams(batch_size=5, learning_rate=0.3, epochs=50, export_dir='exported_model')
options = object_detector.ObjectDetectorOptions(
    supported_model=object_detector.SupportedModels.MOBILENET_V2,
    hparams=hparams
)
model = object_detector.ObjectDetector.create(
    train_data=train_data,
    validation_data=val_data,
    options=options)

loss, coco_metrics = model.evaluate(val_data, batch_size=4)
print(f"Validation loss: {loss}")
print(f"Validation coco metrics: {coco_metrics}")

model.export_model('robo_plush.tflite')
