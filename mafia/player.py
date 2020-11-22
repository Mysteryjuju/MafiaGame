import asyncio
import discord
from mafia.misc.utils import Misc, Colors
from mafia.house import House
from mafia.roles.mafia.mafioso import Mafioso


class Player:
    """
    Player class
    """
    ALLOWED_DEATH_NOTE_ROLES = [Mafioso]

    def __init__(self, ctx):
        """
        Initializer
        """
        self._author = ctx.author
        self._player_channel = None
        self._nickname = None
        self._role = None
        self._house = None
        self._last_will = None
        self._death_note = None
        self._alive = True
        self._vote_id = None
        self._trial_vote = None

        self._loop = asyncio.get_event_loop()

    async def init(self, ctx):
        private_category = discord.utils.get(ctx.guild.categories, name=Misc.CATEGORY_CHANNEL_MAFIA)
        player_channel_name = 'private_{}'.format(self._author.name).lower().replace(" ", "-")
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.message.author: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_text_channel(player_channel_name, category=private_category, overwrites=overwrites)
        self._player_channel = discord.utils.get(ctx.guild.channels, name=player_channel_name)

        await self._player_channel.send("Bienvenue de la partie {}. "
                                        "En attente des autres joueurs...".format(self._author.name))

    def send_message_to_player(self, message):
        asyncio.run_coroutine_threadsafe(self._player_channel.send(message), self._loop)

    def send_message_embed(self, title=discord.Embed.Empty,
                           description=discord.Embed.Empty,
                           color=Colors.DEFAULT):
        embed = discord.Embed(title=title,
                              description=description,
                              colour=color)
        asyncio.run_coroutine_threadsafe(self._player_channel.send(embed=embed), self._loop)

    def get_id(self):
        return self._author.id

    def set_nickname(self, nickname: str):
        """
        Configure a custom nickname for the game
        :param nickname: custom nickname
        """
        self._nickname = nickname

    def get_nickname(self) -> str:
        if self._nickname is None:
            return None
        return "**{}**".format(self._nickname)

    def get_private_channel(self):
        return self._player_channel

    def set_role(self, role):
        self._role = role()
        self._role.print_role(self.send_message_embed)

    def get_role(self):
        return self._role

    def set_house(self, house_id):
        self._house = House(house_id)

    def get_house(self) -> House:
        return self._house

    def set_last_will(self, last_will: str):
        self._last_will = last_will

    def get_last_will(self) -> str:
        return self._last_will

    def set_death_note(self, death_note: str):
        if self._role in self.ALLOWED_DEATH_NOTE_ROLES:
            self._death_note = death_note
        else:
            self.send_message_to_player("*## Vous ne pouvez pas configurer de death note.*")

    def get_death_note(self) -> str:
        return self._death_note

    def is_player_alive(self) -> bool:
        return self._alive

    def set_dead(self):
        self._alive = False

    def set_vote_id(self, vote_id: int):
        self._vote_id = vote_id

    def get_vote_id(self) -> int:
        return self._vote_id

    def set_trial_vote(self, vote):
        if vote in [Misc.TRIAL_GUILTY, Misc.TRIAL_INNOCENT]:
            self._trial_vote = vote
        else:
            self._trial_vote = None

    def get_trial_vote(self):
        return self._trial_vote
