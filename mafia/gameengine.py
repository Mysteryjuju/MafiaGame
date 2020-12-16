import discord
import random
import time
import names
import re
import math

import asyncio
from statemachine import StateMachine, State
from threading import Thread, Timer
from mafia.misc.utils import Alignment, Misc, Timers
from mafia.player import Player
from mafia.commands import Commands
from mafia.misc.role_util import get_role_class_from_string
from mafia.gamestate import GameState

# TODO: FOR DEBUG PURPOSES
from mafia.fakeplayer import FakePlayer


class MafiaEngine:

    def __init__(self, bot):
        """
        Initializer
        :param bot: discord Bot reference
        """
        self._bot = bot
        self._game_state = None
        self.players = []
        self.private_channels = []
        self._cmd_manager = Commands(self)

        self.mafia_players = []
        self.triad_players = []
        self.cultist_players = []
        self.mason_players = []

        self.player_trial = None
        self._player_skips = list()

    def reset_game(self):
        self._game_state = None
        self.players = []
        self.private_channels = []

    def get_game_state(self):
        if self._game_state is None:
            return None
        return self._game_state.current_state

    def send_message_everyone(self, message):
        for player in self.players:
            player.send_message_to_player(message)

    def set_player_nickname(self, message):
        for player in self.players:
            if message.author.id == player.get_id():
                # Check name content
                if re.match(r"^[a-zA-Z0-9 éèçàäëüïöâêûîôù'_-]+$", message.content):
                    if player.get_nickname() is None:
                        player.set_nickname(message.content[1:])
                        self.send_message_everyone("{} a rejoint la partie.".format(player.get_nickname()))
                    else:
                        old_nickname = player.get_nickname()
                        player.set_nickname(message.content[1:])
                        self.send_message_everyone("{} s'est renommé {}.".format(old_nickname, player.get_nickname()))
                else:
                    player.send_message_to_player("*ERROR* - Caractères invalides dans le pseudo.")

    def reset_votes(self):
        for player in self.players:
            player.set_vote(None)

    def compile_roles(self):
        # TODO: should be updated !
        from mafia.roles.town.citizen import Citizen
        from mafia.roles.mafia.mafioso import Mafioso
        roles = [Mafioso, Mafioso, Mafioso]
        roles += [Citizen for i in range(1, (len(self.players) + 1) - 3)]

        return roles

    def configure_players(self):
        # Generate list of house positions based on players count
        player_house_ids = [i for i in range(1, len(self.players) + 1)]
        # Randomize house positions order
        random.shuffle(player_house_ids)

        # Get list of roles based on configuration
        player_roles = self.compile_roles()

        # Configure players positions and roles
        for player in self.players:
            if player.get_nickname() is None:
                # Force a nickname
                player.set_nickname(nickname=names.get_full_name())
            player.set_house(player_house_ids.pop())
            player.set_role(player_roles.pop())

            # Update local variables
            if player.get_role().alignment == Alignment.MAFIA:
                self.mafia_players.append(player)

        # Sort players by position
        self.players = sorted(self.players, key=lambda k: k.get_house().get_id())

        time.sleep(2.0)
        full_town = ""
        for player in self.players:
            full_town += "{} - {}\n".format(player.get_house().get_id(), player.get_nickname())
        self.send_message_everyone("Composition des joueurs :")
        self.send_message_everyone(full_town)

    def player_send_message_to_players(self, message, players):
        sender = self.get_player_from_message(message)
        output = "{} - {}: {}".format(sender.get_house().get_id(), sender.get_nickname(), message.content)
        for player in players:
            player.send_message_to_player(output)

    def get_player_from_message(self, message) -> Player:
        for player in self.players:
            if message.author.id == player.get_id() and message.channel == player.get_private_channel():
                return player
            elif message.channel == player.get_private_channel() and type(player) is FakePlayer:
                return player
        raise Exception("Player not found for message {}. Should be {}.".format(message.content, message.author.name))

    def get_player_from_house_id(self, house_id) -> Player:
        for player in self.players:
            if player.get_house().get_id() == house_id:
                return player
        raise Exception("Player not found at house {}.".format(house_id))

    def check_day_skip(self, player: Player):
        # Add player to skippers
        if player not in self._player_skips:
            self._player_skips.append(player)
            self.send_message_everyone("*# {} souhaite passer la journée.*".format(player.get_nickname()))
        if len(self._player_skips) > math.ceil(self.get_nb_alive_players()/2):
            # Reset count and go to night now !
            self._player_skips = list()
            self._game_state.disable_next_state()
            self._game_state.night()

    def get_current_votes(self) -> dict:
        """
        Get a compilation of all current votes
        :return: dict containing player house IDs and their corresponding votes
        """
        current_votes = {}
        for item in self.players:
            player_vote = item.get_vote_id()
            if player_vote is not None:
                voted_player = self.get_player_from_house_id(player_vote)
                if voted_player.get_house().get_id() in current_votes:
                    current_votes[voted_player.get_house().get_id()] += 1
                else:
                    current_votes[voted_player.get_house().get_id()] = 1
        return current_votes

    def get_nb_alive_players(self) -> int:
        """
        Get the number of current alive players
        :return: number of current alive players
        """
        alive_players = 0
        for player in self.players:
            if player.is_player_alive():
                alive_players += 1
        return alive_players

    def check_votes_for_trial(self):
        """
        Check votes and go to trial if needed.
        """
        # Compute minimum votes to go to trial
        alive_players = self.get_nb_alive_players()
        votes_threshold = math.ceil(alive_players/2)
        # Check for each voted players if required votes are reached
        current_votes = self.get_current_votes()
        for house_id in current_votes:
            if current_votes[house_id] > votes_threshold:
                # Go to trial !
                self.player_trial = self.get_player_from_house_id(house_id)
                # Stop timer of night transition
                self._game_state.disable_next_state()
                # Go to trial !
                self._game_state.day_trial_launch()
                # Break the loop to stop check
                break

    def manage_day_common(self, message):
        player = self.get_player_from_message(message)
        # Manage commands
        if message.content.startswith('-'):
            self._cmd_manager.manage_command(message, player)
        else:
            self.player_send_message_to_players(message, self.players)

    def manage_day_trial_defense(self, message):
        player = self.get_player_from_message(message)
        # Manage commands
        if message.content.startswith('-'):
            self._cmd_manager.manage_command(message, player)
        else:
            if player == self.player_trial:
                self.player_send_message_to_players(message, self.players)

    def manage_day_trial_deliberation(self, message):
        player = self.get_player_from_message(message)
        # Manage commands
        if message.content.startswith('-'):
            self._cmd_manager.manage_command(message, player)
        else:
            self.player_send_message_to_players(message, self.players)

    def manage_night(self, message):
        player = self.get_player_from_message(message)
        # Manage commands
        if message.content.startswith('-'):
            self._cmd_manager.manage_command(message, player)
        else:
            if player in self.mafia_players:
                self.player_send_message_to_players(message, self.mafia_players)

    # ##################################################################################################################
    async def create_game(self, ctx):
        """
        Create a new game lobby
        :param ctx: context
        """
        print("MafiaEngine.start_game")
        if self._game_state is not None:
            await ctx.send("Impossible de lancer une nouvelle partie. Partie déjà en cours.")
        else:
            # Display message game start
            await ctx.send("Nouvelle partie de Mafia démarrée par {}. Pour rejoindre, tapez \"$join_game\""
                           .format(ctx.author.name))
            # Clean variables
            self.reset_game()

            # Initialize state machine
            self._game_state = GameState(self._bot, self)

            # Clean previous channels
            private_category = discord.utils.get(ctx.guild.categories, name=Misc.CATEGORY_CHANNEL_MAFIA)
            # Create the category if it doesn't exist
            if private_category is not None:
                for channel in private_category.channels:
                    await channel.delete()

    async def join_game(self, ctx):
        """
        Used by players to join a game
        :param ctx: context
        """
        # Send message state
        if self._game_state is None:
            await ctx.send("{} - pas de partie en cours, impossible de rejoindre.".format(ctx.author.name))
        elif self._game_state.current_state == GameState.state_wait_for_players:
            await ctx.send("{} a rejoint la partie !".format(ctx.author.name))

            # Create a private channel for this player
            private_category = discord.utils.get(ctx.guild.categories, name=Misc.CATEGORY_CHANNEL_MAFIA)
            # Create the category if it doesn't exist
            if private_category is None:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
                }
                await ctx.guild.create_category(Misc.CATEGORY_CHANNEL_MAFIA, overwrites=overwrites)

            # Manage new player
            new_player = Player(ctx)
            await new_player.init(ctx)
            self.players.append(new_player)
            self.private_channels.append(new_player.get_private_channel())

            ############################################################################################################
            # TODO: DEBUG
            if ctx.author.name == "Mystery":
                from mafia.fakeplayer import FakePlayer
                for i in range(1, 10):
                    new_player = FakePlayer(ctx)
                    await new_player.init(ctx)
                    self.players.append(new_player)
                    self.private_channels.append(new_player.get_private_channel())
            # TODO: DEBUG
            ############################################################################################################

        else:
            await ctx.send("{} - partie en cours, impossible de rejoindre.".format(ctx.author.name))

    async def start_game(self, ctx):
        """
        To launch a game when lobby is not full
        :param ctx: context
        """
        if self._game_state is None or self._game_state.current_state != GameState.state_wait_for_players:
            await ctx.send("{} - 'start_game': opération impossible.".format(ctx.author.name))
        else:
            await ctx.send("{} a démarré la partie. Bon jeu !".format(ctx.author.name))
            self._game_state.select_names()

    async def stop_game(self, ctx):
        """
        Used to stop a game manually
        :param ctx: context
        """
        if self._game_state is not None:
            self._game_state = None

            self.send_message_everyone("{} a mis fin à la partie en cours.".format(ctx.author.name))
            await ctx.send("{} a mis fin à la partie en cours.".format(ctx.author.name))
