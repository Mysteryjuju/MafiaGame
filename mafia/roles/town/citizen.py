from mafia.roles.town.townrole import TownRole
from mafia.misc.utils import RoleCategory, InvestigationSheriff, InvestigationInvestigator


class Citizen(TownRole):
    """
    Town role: Citizen
    """

    def __init__(self):
        """
        Initializer
        """
        super().__init__()
        self.name = "Citizen"
        self.categories = [RoleCategory.TOWN_GOVERNMENT]
        self.summary = "Une personne normale qui croit en la vérité et la justice."
        self.abilities = ["Possibilité d'utiliser un gilet pare-balles pendant la nuit pour s'immuniser contre la mort"]
        self.special_attributes = ["Vous pouvez utiliser le gilet pare-balles une fois uniquement",
                                   "Dans le cas d'un duel à égalité entre la Mafia et la Ville, si vous êtes en vie, la Ville gagnera"]

        self.investigation_sheriff = InvestigationSheriff.NOT_SUSPICIOUS
        self.investigation_investigator = [InvestigationInvestigator.NO_CRIME]
