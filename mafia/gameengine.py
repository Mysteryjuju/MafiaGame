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

    def check_votes_for_trial(self):
        """
        Check votes and go to trial if needed.
        """
        # Compute minimum votes to go to trial
        alive_players = 0
        for player in self.players:
            if player.is_player_alive():
                alive_players += 1
        votes_threshold = math.ceil(alive_players/2)
        # Check for each voted players if required votes are reached
        current_votes = self.get_current_votes()
        for house_id in current_votes:
            if current_votes[house_id] > votes_threshold:
                # Go to trial !
                self.player_trial = self.get_player_from_house_id(house_id)
                self._game_state.day_trial_launch()
                # Break the loop to stop check
                break

    # def _manage_generic_commands(self, message, player):
    #     # Manage "last will" command
    #     if message.content.startswith('-lw'):
    #         if len(message.content) > 4 and message.content.startswith("-lw "):
    #             # Configure a new last will
    #             player.set_last_will(message.content[4:])
    #         if player.get_last_will() is not None:
    #             # Display the player last will for information
    #             player.send_message_to_player("*## Votre dernière volonté : {}*".format(player.get_last_will()))
    #         else:
    #             player.send_message_to_player("*## Pas de dernière volonté configurée.*")
    #
    #     # Manage "death note" command
    #     elif message.content.startswith('-dn'):
    #         if len(message.content) > 4 and message.content.startswith("-dn "):
    #             # Configure a new death note
    #             player.set_death_note(message.content[4:])
    #         if player.get_death_note() is not None:
    #             # Display the player death note for information
    #             player.send_message_to_player("*## Votre death note : {}*".format(player.get_death_note()))
    #         else:
    #             player.send_message_to_player("*## Pas de death note configurée.*")
    #
    #     # Manage "votes" command
    #     elif message.content == '-votes':
    #         # Display a list of all votes
    #         current_votes = self._get_current_votes()
    #         if len(current_votes) == 0:
    #             player.send_message_to_player("*## Personne n'a voté.*")
    #         else:
    #             msg = "*## Votes en cours :*\n"
    #             for house_id in sorted(current_votes):
    #                 msg += "*## {} - **{}** : {} vote{}*\n".format(
    #                     house_id,
    #                     self.get_player_from_house_id(house_id).get_nickname(),
    #                     current_votes[house_id],
    #                     "s" if current_votes[house_id] > 1 else ""
    #                 )
    #             player.send_message_to_player(msg)
    #
    #     # Manage "vote" command
    #     elif message.content.startswith('-vote'):
    #         # The player want to vote, display all available votes
    #         votable_players = list()
    #         list_vote_players = ""
    #         for item in self.players:
    #             if item.is_player_alive() and item != player:
    #                 list_vote_players += "*## {} - {}*\n".format(item.get_house().get_id(), item.get_nickname())
    #                 votable_players.append(item)
    #
    #         if message.content.startswith('-vote ') and len(message.content) > 6:
    #             vote = message.content[6:]
    #             if vote.isdigit() and int(vote) in [i.get_house().get_id() for i in votable_players]:
    #                 # Vote OK
    #                 player.set_vote_id(int(vote))
    #                 msg = "```diff\n-> {} a voté contre {}.\n```" \
    #                     .format(player.get_nickname()[2:-2],
    #                             self.get_player_from_house_id(int(vote)).get_nickname()[2:-2])
    #                 self.send_message_everyone(msg)
    #             else:
    #                 # Wrong vote
    #                 output = "*## Vote impossible. Vous pouvez voter contre un joueur de cette liste (utilisez le numéro) :*\n" \
    #                          + list_vote_players
    #                 player.send_message_to_player(output)
    #         else:
    #             if player.get_vote_id() is None:
    #                 output = "*## Votez contre un joueur (utilisez le numéro) :*\n" + list_vote_players
    #                 player.send_message_to_player(output)
    #             else:
    #                 player.set_vote_id(None)
    #                 self.send_message_everyone("*{} a annulé son vote.*".format(player.get_nickname()))
    #         # Check if votes can launch a trial
    #         self._check_votes_for_trial()
    #
    #     # Manage "graveyard/cimetiere/cimetière" command
    #     elif message.content == "-graveyard" or message.content == "-cimetiere":
    #         # Display all dead players
    #         print("TO IMPLEMENT !")
    #
    #     # Manage "role" command
    #     elif message.content.startswith("-role"):
    #         if message.content == "-role":
    #             player.get_role().print_role(player.send_message_embed)
    #         elif message.content == "-roles":
    #             print("TODO: implement a feature to return possible roles in the game")
    #         else:
    #             output = re.findall(r"-role (.+)", message.content)
    #             if len(output) != 1:
    #                 player.send_message_to_player("*## Commande invalide de récupération de role.*")
    #             else:
    #                 # Get the role
    #                 role_class = get_role_class_from_string(output[0])
    #                 if role_class is not None:
    #                     role_class().print_role(player.send_message_embed)
    #                 else:
    #                     player.send_message_to_player("*## Role demandé inconnu.*")
    #
    #     # Manage "pm" command
    #     elif message.content.startswith("-pm"):
    #         output = re.findall(r"^-pm ([\d]+) (.+)$", message.content)
    #         if len(output) != 1:
    #             player.send_message_to_player("*## Commande de message privé invalide.*")
    #         else:
    #             target_id = int(output[0][0])
    #             private_msg = output[0][1]
    #             # Check if target player is not the author player
    #             if player.get_house().get_id() == target_id:
    #                 player.send_message_to_player("*## Vous ne pouvez pas vous envoyer à vous-même un message privé.*")
    #             else:
    #                 for item in self.players:
    #                     if item.get_house().get_id() in [target_id, player.get_house().get_id()]:
    #                         msg = "**## MESSAGE PRIVE ##** {} - **{}** : {}".format(player.get_house().get_id(),
    #                                                                                 player.get_nickname(),
    #                                                                                 private_msg)
    #                         item.send_message_to_player(msg)
    #                     else:
    #                         msg = "**{}** a envoyé un message privé à **{}**." \
    #                             .format(player.get_nickname(),
    #                                     self.get_player_from_house_id(target_id).get_nickname())
    #                         item.send_message_to_player(msg)

    def manage_day_discussion(self, message):
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
                self.player_send_message_to_players(message, self.mafia_players)

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
            await ctx.send("Nouvelle partie de Mafia démarrée par {}. Pour rejoindre, tappez \"$join_game\""
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

            ##############################################################################################################
            # TODO: DEBUG
            if ctx.author.name == "Mystery":
                from mafia.fakeplayer import FakePlayer
                for i in range(1, 10):
                    new_player = FakePlayer(ctx)
                    await new_player.init(ctx)
                    self.players.append(new_player)
                    self.private_channels.append(new_player.get_private_channel())
            # TODO: DEBUG
            ##############################################################################################################

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
