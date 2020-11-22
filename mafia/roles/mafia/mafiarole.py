from mafia.roles.baserole import BaseRole
from mafia.misc.utils import Alignment, Colors


class MafiaRole(BaseRole):
    """
    Mafia role base
    """

    def __init__(self):
        """
        Initializer
        """
        super().__init__()
        self.alignment = Alignment.MAFIA
        self.color = Colors.MAFIA_COLOR
        self.goal = "Tuer tous les membres de la ville et tous vos opposants."

        self.special_attributes = ["Suggérez une cible à éliminer avec la commande \"-target X\"",
                                   "Vous pouvez parler à la Mafia durant la nuit"]
