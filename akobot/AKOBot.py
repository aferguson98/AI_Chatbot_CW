"""
AKOBot.py
"""

import spacy


class NLPEngine:
    def __init__(self):
        """
        A basic NLP Engine that takes can process input text
        """
        self.nlp = spacy.load("en_core_web_sm")

    def process(self, input_text):
        """
        Takes in user input and uses SpaCy to process it

        Parameters
        ----------
        input_text: str
            The string the user has passed into the chatbot that needs to be
            processed

        Returns
        -------
        list
            A list of tokens
        """
        print("I AM IN THE AKOBOT FILE")
        return self.nlp(input_text)


if __name__ == '__main__':
    pass
