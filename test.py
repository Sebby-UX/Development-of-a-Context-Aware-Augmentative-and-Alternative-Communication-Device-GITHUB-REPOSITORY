import os
import json
import keras
from keras import layers

VOCAB_FOLDER = "./"
MODEL_DIR = "models"
MODEL_FILE = os.path.join(MODEL_DIR, "predictor.keras")

SEQUENCE_LENGTH = 3
MAX_VOCAB_SIZE = 10000


def get_words_from_json():

    words = []

    if not os.path.exists(VOCAB_FOLDER):
        print("Vocabulary folder not found.")
        return words

    for filename in os.listdir(VOCAB_FOLDER):

        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(VOCAB_FOLDER, filename)

        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)

        for item in data:

            if "text" in item:
                words.append(item["text"])

    # Remove duplicates
    words = list(dict.fromkeys(words))

    return words


# --------------------------------------------------
# LOAD VOCABULARY
# --------------------------------------------------

words = get_words_from_json()

print("Vocabulary words:", len(words))

if not words:
    raise ValueError("No vocabulary words found.")


# --------------------------------------------------
# TEXT VECTORIZATION
# --------------------------------------------------

vectorizer = layers.TextVectorization(
    max_tokens=MAX_VOCAB_SIZE,
    standardize="lower_and_strip_punctuation",
    split="whitespace",
    output_mode="int",
    output_sequence_length=SEQUENCE_LENGTH,
    name="text_vectorization"
)

vectorizer.set_vocabulary(words)

vocabulary = vectorizer.get_vocabulary()

vocab_size = len(vocabulary)

print("Model vocabulary size:", vocab_size)


# --------------------------------------------------
# MODEL
# --------------------------------------------------

inputs = keras.Input(
    shape=(),
    dtype="string",
    name="text_input"
)

x = vectorizer(inputs)

x = layers.Embedding(
    input_dim=vocab_size,
    output_dim=128,
    name="embedding"
)(x)

x = layers.LSTM(
    128,
    name="lstm"
)(x)

outputs = layers.Dense(
    vocab_size,
    activation="softmax",
    name="next_word"
)(x)


model = keras.Model(
    inputs=inputs,
    outputs=outputs
)


# --------------------------------------------------
# COMPILE
# --------------------------------------------------

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy"
)


# --------------------------------------------------
# SAVE
# --------------------------------------------------

os.makedirs(MODEL_DIR, exist_ok=True)

model.save(MODEL_FILE)

print()
print("Blank model created!")
print("Saved to:")
print(MODEL_FILE)