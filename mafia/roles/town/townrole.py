from mafia.roles.baserole import BaseRole
from mafia.misc.utils import Alignment, Colors


class TownRole(BaseRole):
    """
    Town role base
    """

    def __init__(self):
        """
        Initializer
        """
        super().__init__()
        self.alignment = Alignment.TOWN
        self.color = Colors.TOWN_COLOR
        self.goal = "Lyncher tous les criminels et les scélérats."
