import discord
from mafia.misc.utils import Misc
from mafia.player import Player
import random


class FakePlayer(Player):
    """
    Fake Player class
    """

    async def init(self, ctx):
        private_category = discord.utils.get(ctx.guild.categories, name=Misc.CATEGORY_CHANNEL_MAFIA)
        player_channel_name = 'private_{}'.format(random.randint(100000, 999999)).lower().replace(" ", "-")
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.message.author: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_text_channel(player_channel_name, category=private_category, overwrites=overwrites)
        self._player_channel = discord.utils.get(ctx.guild.channels, name=player_channel_name)

        await self._player_channel.send("Bienvenue de la partie {}. "
                                        "En attente des autres joueurs...".format(self._author.name))
