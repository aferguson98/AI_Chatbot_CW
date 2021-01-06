"""

"""


class StationNoMatchError(Exception):
    def __init__(self, alternatives,
                 message="No exact station match found"):
        self.alternatives = alternatives
        self.message = message


class StationNotFoundError(Exception):
    pass


class UnknownPriorityException(Exception):
    def __init__(self, priority):
        message = "Priority {} is not a valid priority value."
        self.message = message.format(priority)
