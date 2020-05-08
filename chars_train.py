import pickle
import time
import matplotlib.pyplot as plt
import tqdm
from absl import app, flags, logging
from absl.flags import FLAGS
import cv2
import numpy as np
import tensorflow as tf
import os

from chars_model import CModel
from yolov3_tf2.utils import freeze_all
from tensorflow.keras.callbacks import (
    ReduceLROnPlateau,
    EarlyStopping,
    ModelCheckpoint,
    TensorBoard
)
import yolov3_tf2.dataset_chars as dataset
import tensorflow.keras as keras
from tensorflow.keras.layers import Flatten, Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Sequential

from yolov3_tf2.dataset_chars import transform_images

DATA_SIZE=13163
VAL_SIZE=int(DATA_SIZE*0.20)


flags.DEFINE_string('ckpt_name', 'chars_checkpoints/resnet101v2_train_{epoch}.tf', 'checkpoint name')
flags.DEFINE_string('tb_log_dir', 'chars_logs/chars/resnet101v2', 'tensorboard log dir')
flags.DEFINE_integer('size', 32, 'size of each character should be resize to')
flags.DEFINE_integer('epochs', 100, 'epoch num')
flags.DEFINE_integer('batch_size', 32, 'size of each batch')
flags.DEFINE_string('dataset_path', './data/chars_data.tfrecord', 'path to output dataset file')
flags.DEFINE_string('classes_path', './data/chars_data.names', 'path to output class file')

def main(_argv):
    cv2.imread()
    all_dataset = dataset.load_tfrecord_dataset(FLAGS.dataset_path, size=FLAGS.size)
    all_dataset = all_dataset.map(lambda x, y: (dataset.transform_images(x, FLAGS.size), y))
    all_dataset = all_dataset.shuffle(buffer_size=1024)
    val_dataset, train_dataset = all_dataset.take(VAL_SIZE), all_dataset.skip(VAL_SIZE)
    train_dataset = train_dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE).batch(FLAGS.batch_size)
    val_dataset = val_dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE).batch(FLAGS.batch_size)

    class_map = {name: idx for idx, name in enumerate(open(FLAGS.classes_path).read().splitlines())}
    class_num = len(class_map)
    model = CModel(FLAGS.size, class_num, 'imagenet')

    model.compile(loss=tf.keras.losses.SparseCategoricalCrossentropy(),
                  optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
                  metrics=['accuracy'])
    model.summary()

    callbacks = [
        ReduceLROnPlateau(monitor='val_loss', verbose=1),
        EarlyStopping(monitor='val_loss', patience=20, verbose=1),
        ModelCheckpoint(FLAGS.ckpt_name, verbose=1, monitor='val_accuracy',
                        save_best_only=True, save_weights_only=True, mode='max'),
        TensorBoard(log_dir=FLAGS.tb_log_dir)
    ]

    history = model.fit(train_dataset,
                        epochs=FLAGS.epochs,
                        callbacks=callbacks,
                        validation_data=val_dataset)

if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass
