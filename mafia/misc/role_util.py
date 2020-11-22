from mafia.roles.mafia.mafioso import Mafioso
from mafia.roles.town.citizen import Citizen


def get_role_class_from_string(role_string: str):
    """
    Get a role class from a string
    :param role_string: the role
    :return: the wanted role class, None if not exist
    """
    try:
        return eval(role_string.capitalize())
    except NameError:
        # Invalid class name
        return None
