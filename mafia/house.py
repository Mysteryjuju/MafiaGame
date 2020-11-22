

class House:
    """
    A house where people can live, sleep and go to night to perform some activities
    """
    def __init__(self, house_id: int):
        """
        Initializer
        :param house_id: id of the house
        """
        self._id = house_id

    def get_id(self) -> int:
        """
        Get house ID
        :return: house id
        """
        return self._id
