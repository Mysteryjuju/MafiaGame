from mafia.roles.mafia.mafiarole import MafiaRole
from mafia.misc.utils import RoleCategory, InvestigationSheriff, InvestigationInvestigator


class Mafioso(MafiaRole):
    """
    Mafia role: Mafioso
    """

    def __init__(self):
        """
        Initializer
        """
        super().__init__()
        self.name = "Mafioso"
        self.categories = [RoleCategory.MAFIA_KILLING]
        self.summary = "Un modeste soldat à la solde de la mafia."
        self.abilities += ["Collaborez avec le Godfather pour tuer quelqu'un chaque nuit"]
        self.special_attributes += ["Le Godfather surcharge votre vote pour tuer lorsqu'il est en vie",
                                    "Vous devez voter pour tuer tant que la Mafia est en vie (commande '-target X')",
                                    "Un Mafioso aléatoire sera envoyé pour tuer la cible choisie par la Mafia"]

        self.investigation_sheriff = InvestigationSheriff.MAFIA
        self.investigation_investigator = [InvestigationInvestigator.MURDER,
                                           InvestigationInvestigator.TRESPASSING]
