import os
import sqlite3
import numpy as np
import tensorflow as tf
import keras
from keras import layers


DB_FILE = "chat.db"

MODEL_DIR = "models"
MODEL_FILE = os.path.join(MODEL_DIR, "predictor.keras")

SEQUENCE_LENGTH = 3
MAX_VOCAB_SIZE = 10000


# ==================================================
# GET MESSAGES FROM SQLITE
# ==================================================

def get_messages():

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT message
        FROM messages
        ORDER BY id ASC
    """)

    messages = [
        row[0]
        for row in cursor.fetchall()
    ]

    conn.close()

    return messages


# ==================================================
# CREATE TRAINING DATA
# ==================================================

def create_training_data(messages, vectorizer):

    """
    Creates:

        previous 3 words -> next word

    Example:

        I want to eat

        [I]              -> want
        [I, want]        -> to
        [I, want, to]    -> eat

    Sequences are padded on the LEFT.
    """

    inputs = []
    targets = []

    for message in messages:

        # Convert message into word IDs
        ids = vectorizer(
            tf.constant([message], dtype=tf.string)
        ).numpy()[0]

        # Remove padding
        ids = ids[ids != 0]

        if len(ids) < 2:
            continue

        # Create next-word samples
        for i in range(1, len(ids)):

            start = max(
                0,
                i - SEQUENCE_LENGTH
            )

            sequence = ids[start:i]

            # LEFT PAD to exactly 3 words
            if len(sequence) < SEQUENCE_LENGTH:

                sequence = np.pad(
                    sequence,
                    (
                        SEQUENCE_LENGTH - len(sequence),
                        0
                    ),
                    mode="constant"
                )

            # Safety: keep exactly 3
            sequence = sequence[-SEQUENCE_LENGTH:]

            inputs.append(sequence)

            targets.append(ids[i])

    return (
        np.array(inputs, dtype=np.int32),
        np.array(targets, dtype=np.int32)
    )


# ==================================================
# TRAIN MODEL
# ==================================================

def train_model():

    # --------------------------------------------------
    # Get messages
    # --------------------------------------------------

    messages = get_messages()

    if not messages:

        print("No messages found in database.")

        return

    print("Messages:", len(messages))


    # --------------------------------------------------
    # TextVectorization
    # --------------------------------------------------

    vectorizer = layers.TextVectorization(
        max_tokens=MAX_VOCAB_SIZE,
        standardize="lower_and_strip_punctuation",
        split="whitespace",
        output_mode="int",
        output_sequence_length=None,
        name="text_vectorization"
    )

    # Learn vocabulary from messages
    vectorizer.adapt(
        tf.constant(
            messages,
            dtype=tf.string
        )
    )

    vocabulary = vectorizer.get_vocabulary()

    vocab_size = len(vocabulary)

    print("Vocabulary size:", vocab_size)


    # --------------------------------------------------
    # Create training data
    # --------------------------------------------------

    X, y = create_training_data(
        messages,
        vectorizer
    )

    if len(X) == 0:

        print("Not enough data to train.")

        return

    print("Training samples:", len(X))


    # ==================================================
    # MODEL
    # ==================================================

    # Integer word IDs
    word_inputs = keras.Input(
        shape=(SEQUENCE_LENGTH,),
        dtype="int32",
        name="word_ids"
    )


    # --------------------------------------------------
    # Embedding
    # --------------------------------------------------

    x = layers.Embedding(
        input_dim=vocab_size,
        output_dim=128,
        name="embedding"
    )(word_inputs)


    # --------------------------------------------------
    # LSTM
    # --------------------------------------------------

    x = layers.LSTM(
        256,
        name="lstm"
    )(x)


    # --------------------------------------------------
    # Prediction
    # --------------------------------------------------

    outputs = layers.Dense(
        vocab_size,
        activation="softmax",
        name="prediction"
    )(x)


    # --------------------------------------------------
    # Training model
    # --------------------------------------------------

    lstm_model = keras.Model(
        inputs=word_inputs,
        outputs=outputs,
        name="word_predictor"
    )


    lstm_model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )


    # --------------------------------------------------
    # Show model
    # --------------------------------------------------

    lstm_model.summary()


    # ==================================================
    # TRAIN
    # ==================================================

    lstm_model.fit(
        X,
        y,
        epochs=20,
        batch_size=32,
        validation_split=0.1
    )


    # ==================================================
    # CREATE FINAL TEXT MODEL
    # ==================================================

    """
    Final model:

        Text
          ↓
        TextVectorization
          ↓
        last 3 words
          ↓
        Embedding
          ↓
        LSTM
          ↓
        Prediction
    """

    text_input = keras.Input(
        shape=(),
        dtype="string",
        name="text_input"
    )


    # --------------------------------------------------
    # Text → word IDs
    # --------------------------------------------------

    all_word_ids = vectorizer(
        text_input
    )


    # --------------------------------------------------
    # Take the last 3 words
    # --------------------------------------------------

    # TextVectorization produces a variable-length
    # sequence here. We handle the sequence in Python
    # during prediction/training instead of using
    # Lambda/ZeroPadding layers inside the saved model.
    #
    # For the final saved model, use exactly 3 tokens
    # by configuring the vectorizer accordingly.

    final_vectorizer = layers.TextVectorization(
        max_tokens=MAX_VOCAB_SIZE,
        standardize="lower_and_strip_punctuation",
        split="whitespace",
        output_mode="int",
        output_sequence_length=SEQUENCE_LENGTH,
        name="text_vectorization"
    )

    final_vectorizer.set_vocabulary(vocabulary)


    word_ids = final_vectorizer(
        text_input
    )


    # --------------------------------------------------
    # Connect to trained network
    # --------------------------------------------------

    predictions = lstm_model(
        word_ids
    )


    # --------------------------------------------------
    # Final model
    # --------------------------------------------------

    final_model = keras.Model(
        inputs=text_input,
        outputs=predictions,
        name="text_word_predictor"
    )


    # ==================================================
    # SAVE
    # ==================================================

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    final_model.save(
        MODEL_FILE
    )


    print()
    print("Training complete!")
    print()
    print("Saved model:")
    print(MODEL_FILE)
    print()
    print("Vocabulary is stored INSIDE the .keras file.")


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    train_model()