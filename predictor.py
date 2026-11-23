import tensorflow as tf
import keras


MODEL_FILE = "models/predictor.keras"


class Predictor:

    def __init__(self):
        self.load_model()


    # ========================================================
    # LOAD MODEL
    # ========================================================

    def load_model(self):

        self.model = keras.models.load_model(
            MODEL_FILE
        )

        vectorizer = self.model.get_layer(
            "text_vectorization"
        )

        self.vocabulary = vectorizer.get_vocabulary()

        self.id_to_word = {
            i: word
            for i, word in enumerate(self.vocabulary)
        }


    # ========================================================
    # RELOAD MODEL
    # ========================================================

    def reload(self):

        self.load_model()


    # ========================================================
    # PREDICT NEXT WORDS
    # ========================================================

    def predict(self, text, amount=3):

        if not text.strip():

            return []


        # ----------------------------------------------------
        # Convert text to TensorFlow string tensor
        # ----------------------------------------------------

        input_text = tf.constant(
            [text],
            dtype=tf.string
        )


        # ----------------------------------------------------
        # Run model
        # ----------------------------------------------------

        predictions = self.model.predict(
            input_text,
            verbose=0
        )[0]


        # ----------------------------------------------------
        # Get highest probabilities
        # ----------------------------------------------------

        indices = predictions.argsort()[::-1]


        # ----------------------------------------------------
        # Convert IDs → words
        # ----------------------------------------------------

        results = []

        for index in indices:

            index = int(index)


            if index == 0:
                continue


            word = self.id_to_word.get(index)


            if not word:
                continue


            if word == "[UNK]":
                continue


            if word not in results:

                results.append(word)


            if len(results) >= amount:

                break


        return results