"""
AKOBot.py
"""

import spacy

from Database.DatabaseConnector import DBConnection


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
        return self.nlp(input_text)


def get_all_stations():
    query = "SELECT * FROM main.Stations"
    db_connection = DBConnection('AKODatabase.db')
    result = db_connection.send_query(query).fetchall()
    if result:
        stations = []
        for res in result:
            stations.append(res[0])
            stations.append(res[1])
        return stations
    else:
        return "error_error_error"


if __name__ == '__main__':
    pass
