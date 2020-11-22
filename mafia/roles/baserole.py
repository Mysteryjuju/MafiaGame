

class BaseRole:
    """
    Base role
    """

    def __init__(self):
        """
        Initializer
        """
        super().__init__()
        self.name = None
        self.alignment = None
        self.color = None
        self.categories = []
        self.summary = None
        self.abilities = []
        self.special_attributes = []
        self.goal = None
        self.investigation_sheriff = None
        self.investigation_investigator = None
        self.unique_role = False

    def _get_description(self) -> str:
        """
        Get a full role description
        :return: a string containing the full role description, ready to be printed/displayed
        """
        categories = ", ".join([category.split()[1] for category in self.categories])
        description = "**Alignement** : {} ({})".format(self.alignment, categories)
        description += "\n**En bref** : {}\n".format(self.summary)
        description += "\n**Capacités** :\n{}".format("".join("- {}\n".format(i) for i in self.abilities))
        description += "\n**Attributs spéciaux** :\n{}".format("".join("- {}\n".format(i) for i in self.special_attributes))
        description += "\n**Objectif** : {}".format(self.goal)

        return description

    def print_role(self, send_message_embed):
        """
        Used to print a role complete description
        :param send_message_embed: function to send an embed message
        """
        send_message_embed(title=self.name,
                           description=self._get_description(),
                           color=self.color)
