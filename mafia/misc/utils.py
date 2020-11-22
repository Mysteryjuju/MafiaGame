
class Misc:

    STATES_STRING_SEPARATOR = "----------------------------------------"
    CATEGORY_CHANNEL_MAFIA = "Mafia Private Channels"
    TRIAL_INNOCENT = "Innocent"
    TRIAL_GUILTY = "Guilty"


class Timers:
    TIMER_SELECT_NICKNAME = 1
    #TIMER_SELECT_NICKNAME = 30
    TIMER_DISPATCH_ROLES = 5
    #TIME_DAY_CHAT = 45
    TIME_DAY_CHAT = 4500
    #TIME_DAY_TRIAL_DEFENSE = 30
    TIME_DAY_TRIAL_DEFENSE = 60
    #TIME_DAY_TRIAL_DELIBERATION = 30
    TIME_DAY_TRIAL_DELIBERATION = 60
    #TIME_NIGHT = 30
    TIME_NIGHT = 3000


class Colors:
    DEFAULT = 0
    AQUA = 1752220
    GREEN = 3066993
    BLUE = 3447003
    PURPLE = 10181046
    GOLD = 15844367
    ORANGE = 15105570
    RED = 15158332
    GREY = 9807270
    DARKER_GREY = 8359053
    NAVY = 3426654
    DARK_AQUA = 1146986
    DARK_GREEN = 2067276
    DARK_BLUE = 2123412
    DARK_PURPLE = 7419530
    DARK_GOLD = 12745742
    DARK_ORANGE = 11027200
    DARK_RED = 10038562
    DARK_GREY = 9936031
    LIGHT_GREY = 12370112
    DARK_NAVY = 2899536
    LUMINOUS_VIVID_PINK = 16580705
    DARK_VIVID_PINK = 12320855
    TOWN_COLOR = 3066993
    MAFIA_COLOR = 15158332


class Alignment:
    TOWN = "Town"
    MAFIA = "Mafia"
    TRIAD = "Triad"
    NEUTRAL = "Neutral"


class RoleCategory:
    TOWN_INVESTIGATIVE = "Town Investigative"
    TOWN_PROTECTIVE = "Town Protective"
    TOWN_GOVERNMENT = "Town Government"
    TOWN_KILLING = "Town Killing"
    TOWN_POWER = "Town Power"
    MAFIA_DECEPTION = "Mafia Deception"
    MAFIA_KILLING = "Mafia Killing"
    MAFIA_SUPPORT = "Mafia Support"
    TRIAD_DECEPTION = "Triad Deception"
    TRIAD_KILLING = "Triad Killing"
    TRIAD_SUPPORT = "Triad Support"
    NEUTRAL_BENIGN = "Neutral Benign"
    NEUTRAL_EVIL = "Neutral Evil"
    NEUTRAL_KILLING = "Neutral Killing"


class InvestigationSheriff:
    NOT_SUSPICIOUS = "Non suspect"
    MAFIA = "Mafia"
    TRIAD = "Triad"
    ARSONIST = "Arsonist"
    CULTIST = "Cultist"
    MASS_MURDERER = "Mass Murderer"


class InvestigationInvestigator:
    TRESPASSING = "Intrusion"
    KIDNAPPING = "Enlèvement"
    NO_CRIME = "Pas de crime"
    CORRUPTION = "Corruption"
    IDENTITY_THEFT = "Vol d'identité"
    SOLICITING = "Sollicitation"
    MURDER = "Meurtre"
    DISTURBING_PEACE = "Trouble de l'ordre public"
    CONSPIRACY = "Conspiration"
    DESTRUCTION_OF_PROPERTY = "Destruction de biens"
    ARSON = "Arsonist"
