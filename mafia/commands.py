import asyncio
import discord
import re
from mafia.house import House
from mafia.roles.mafia.mafioso import Mafioso
from mafia.misc.role_util import get_role_class_from_string
from mafia.gamestate import GameState
from mafia.misc.utils import Misc, Alignment


class Commands:
    """
    Commands manager class
    """
    # Generic commands
    CMD_LAST_WILL = "-lw"
    CMD_DEATH_NOTE = "-dn"
    CMD_GRAVEYARD = "-graveyard"
    CMD_CIMETIERE = "-cimetiere"
    CMD_ROLES = "-roles"
    CMD_ROLE = "-role"
    CMD_PLAYERS = "-players"
    CMD_MAFIA = "-mafia"
    # Commands used during day
    CMD_VOTES = "-votes"
    CMD_VOTE = "-vote"
    CMD_PRIVATE_MESSAGE = "-pm"
    CMD_SKIP = "-skip"
    # Commands used during trial
    CMD_INNOCENT = "-innocent"
    CMD_GUILTY = "-guilty"

    # Command with multiple behaviors
    CMD_CANCEL = "-cancel"

    CMDS_STATE_ANY = [
        CMD_ROLE,
        CMD_ROLES,
        CMD_GRAVEYARD,
        CMD_CIMETIERE,
        CMD_LAST_WILL,
        CMD_DEATH_NOTE,
        CMD_PLAYERS,
        CMD_MAFIA
    ]
    CMDS_STATE_DAY_DISCUSSION = [CMD_PRIVATE_MESSAGE, CMD_SKIP]
    CMDS_STATE_DAY_VOTE = [CMD_VOTE, CMD_VOTES, CMD_PRIVATE_MESSAGE, CMD_SKIP]
    CMDS_STATE_DAY_TRIAL_DELIBERATION = [CMD_INNOCENT, CMD_GUILTY, CMD_CANCEL]
    CMDS_STATE_NIGHT_DISCUSSION = []

    NO_CMDS_STATES = [
        GameState.state_wait_for_players,
        GameState.state_players_nicknames,
        GameState.state_night_sequence
    ]

    def __init__(self, mafia_engine):
        """
        Initializer
        """
        self._mafia_engine = mafia_engine
        self._cmds_managers = {
            self.CMD_LAST_WILL: self._manage_last_will,
            self.CMD_DEATH_NOTE: self._manage_death_note,
            self.CMD_VOTE: self._manage_vote,
            self.CMD_VOTES: self._manage_vote,
            self.CMD_ROLE: self._manage_role,
            self.CMD_ROLES: self._manage_role,
            self.CMD_GRAVEYARD: self._manage_graveyard,
            self.CMD_CIMETIERE: self._manage_graveyard,
            self.CMD_PRIVATE_MESSAGE: self._manage_private_message,
            self.CMD_SKIP: self._manage_skip,
            self.CMD_INNOCENT: self._manage_trial_vote,
            self.CMD_GUILTY: self._manage_trial_vote,
            self.CMD_CANCEL: self._manage_cancel,
            self.CMD_PLAYERS: self._manage_players,
            self.CMD_MAFIA: self._manage_mafia
        }

    def _manage_last_will(self, message, player):
        if len(message.content) > 4 and message.content.startswith("-lw "):
            # Configure a new last will
            player.set_last_will(message.content[4:])
        if player.get_last_will() is not None:
            # Display the player last will for information
            player.send_message_to_player("*## Votre dernière volonté : {}*".format(player.get_last_will()))
        else:
            player.send_message_to_player("*## Pas de dernière volonté configurée.*")

    def _manage_death_note(self, message, player):
        if len(message.content) > 4 and message.content.startswith("-dn "):
            # Configure a new death note
            player.set_death_note(message.content[4:])
        if player.get_death_note() is not None:
            # Display the player death note for information
            player.send_message_to_player("*## Votre death note : {}*".format(player.get_death_note()))
        else:
            player.send_message_to_player("*## Pas de death note configurée.*")

    def _manage_vote(self, message, player):
        if message.content == '-votes':
            # Display a list of all votes
            current_votes = self._mafia_engine.get_current_votes()
            if len(current_votes) == 0:
                player.send_message_to_player("*## Personne n'a voté.*")
            else:
                msg = "*## Votes en cours :*\n"
                for house_id in sorted(current_votes):
                    msg += "*## {} - **{}** : {} vote{}*\n".format(
                        house_id,
                        self._mafia_engine.get_player_from_house_id(house_id).get_nickname(),
                        current_votes[house_id],
                        "s" if current_votes[house_id] > 1 else ""
                    )
                player.send_message_to_player(msg)
        else:
            # The player want to vote, display all available votes
            votable_players = list()
            list_vote_players = ""
            for item in self._mafia_engine.players:
                if item.is_player_alive() and item != player:
                    list_vote_players += "*## {} - {}*\n".format(item.get_house().get_id(), item.get_nickname())
                    votable_players.append(item)

            if message.content.startswith('-vote ') and len(message.content) > 6:
                vote = message.content[6:]
                if vote.isdigit() and int(vote) in [i.get_house().get_id() for i in votable_players]:
                    # Vote OK
                    player.set_vote_id(int(vote))
                    msg = "```diff\n-> {} a voté contre {}.\n```" \
                        .format(player.get_nickname()[2:-2],
                                self._mafia_engine.get_player_from_house_id(int(vote)).get_nickname()[2:-2])
                    self._mafia_engine.send_message_everyone(msg)
                else:
                    # Wrong vote
                    output = "*## Vote impossible. Vous pouvez voter contre un joueur de cette liste (utilisez le numéro) :*\n" \
                             + list_vote_players
                    player.send_message_to_player(output)
            else:
                if player.get_vote_id() is None:
                    output = "*## Votez contre un joueur (utilisez le numéro) :*\n" + list_vote_players
                    player.send_message_to_player(output)
                else:
                    player.set_vote_id(None)
                    self._mafia_engine.send_message_everyone("*{} a annulé son vote.*".format(player.get_nickname()))
            # Check if votes can launch a trial
            self._mafia_engine.check_votes_for_trial()

    def _manage_role(self, message, player):
        if message.content == "-role":
            player.send_message_to_player("*# Votre rôle :*")
            player.get_role().print_role(player.send_message_embed)
        elif message.content == "-roles":
            print("TODO: implement a feature to return all possible roles in the game")
        else:
            output = re.findall(r"-role (.+)", message.content)
            if len(output) != 1:
                player.send_message_to_player("*## Commande invalide de récupération de rôle.*")
            else:
                # Get the role
                role_class = get_role_class_from_string(output[0])
                if role_class is not None:
                    player.send_message_to_player("*Description du rôle {} :*".format(output[0]))
                    role_class().print_role(player.send_message_embed)
                else:
                    player.send_message_to_player("*## Rôle demandé inconnu.*")

    def _manage_graveyard(self, message, player):
        print("TODO: Implement _manage_graveyard")

    def _manage_private_message(self, message, player):
        output = re.findall(r"^-pm ([\d]+) (.+)$", message.content)
        if len(output) != 1:
            player.send_message_to_player("*## Commande de message privé invalide.*")
        else:
            target_id = int(output[0][0])
            private_msg = output[0][1]
            # Check if target player is not the author player
            if player.get_house().get_id() == target_id:
                player.send_message_to_player("*## Vous ne pouvez pas vous envoyer à vous-même un message privé.*")
            else:
                for item in self._mafia_engine.players:
                    if item.get_house().get_id() in [target_id, player.get_house().get_id()]:
                        msg = "**## MESSAGE PRIVE ##** {} - **{}** : {}".format(player.get_house().get_id(),
                                                                                player.get_nickname(),
                                                                                private_msg)
                        item.send_message_to_player(msg)
                    else:
                        msg = "**{}** a envoyé un message privé à **{}**." \
                            .format(player.get_nickname(),
                                    self._mafia_engine.get_player_from_house_id(target_id).get_nickname())
                        item.send_message_to_player(msg)

    def _manage_skip(self, message, player):
        if message.content == self.CMD_SKIP:
            # Increase skip count
            self._mafia_engine.check_day_skip(player)

    def _manage_trial_vote(self, message, player):
        if player == self._mafia_engine.player_trial:
            player.send_message_to_player("*## Vous ne pouvez pas voter pour votre procès.*")
            return
        previous_vote = player.get_trial_vote()
        if message.content == self.CMD_INNOCENT:
            player.set_trial_vote(Misc.TRIAL_INNOCENT)
            player.send_message_to_player("*## Vous avez voté pour innocenter le joueur.*")
        elif message.content == self.CMD_GUILTY:
            player.set_trial_vote(Misc.TRIAL_GUILTY)
            player.send_message_to_player("*## Vous avez voté pour lyncher le joueur.*")
        else:
            # Invalid message content
            return

        # Send message to all players
        if previous_vote is None:
            self._mafia_engine.send_message_everyone("*{} a voté.*".format(player.get_nickname()))
        else:
            self._mafia_engine.send_message_everyone("*{} a changé d'avis pour son vote.*".format(player.get_nickname()))

    def _manage_cancel(self, message, player):
        if message.content == self.CMD_CANCEL:
            game_state = self._mafia_engine.get_game_state()
            if game_state == GameState.state_day_vote:
                player.reset_trial_vote()
                self._mafia_engine.send_message_everyone("*{} a annulé son vote.*".format(player.get_nickname()))

    def _manage_players(self, message, player):
        if message.content == self.CMD_PLAYERS:
            full_town = ""
            for item in self._mafia_engine.players:
                if item.is_player_alive():
                    full_town += "*{} - {}*\n".format(item.get_house().get_id(), item.get_nickname())
                else:
                    full_town += "*~~{} - {}~~ (Mort)*\n".format(item.get_house().get_id(), item.get_nickname())
            player.send_message_to_player("*Composition des joueurs :*")
            player.send_message_to_player(full_town)

    def _manage_mafia(self, message, player):
        if message.content == self.CMD_MAFIA and player.get_role().alignment == Alignment.MAFIA:
            mafia_players = ""
            for item in self._mafia_engine.players:
                if item.get_role().alignment == Alignment.MAFIA:
                    mafia_players += "*{} - {}*\n".format(item.get_house().get_id(), item.get_nickname())
            player.send_message_to_player("*Autres membres de la Mafia :*\n{}".format(mafia_players))

    def manage_command(self, message, player):
        game_state = self._mafia_engine.get_game_state()

        # Get commands list
        if game_state in self.NO_CMDS_STATES:
            # No command state, get out
            return

        # Get available commands base on game state
        available_cmds = self.CMDS_STATE_ANY
        if game_state == GameState.state_day_discussion:
            available_cmds += self.CMDS_STATE_DAY_DISCUSSION
        elif game_state == GameState.state_day_vote:
            available_cmds += self.CMDS_STATE_DAY_VOTE
        elif game_state == GameState.state_day_trial_deliberation:
            available_cmds += self.CMDS_STATE_DAY_TRIAL_DELIBERATION
        elif game_state == GameState.state_night:
            available_cmds += self.CMDS_STATE_NIGHT_DISCUSSION

        # Manage commands
        for cmd in available_cmds:
            if message.content.startswith(cmd):
                # Command found, execute it
                try:
                    self._cmds_managers[cmd](message, player)
                except Exception as exception:
                    print("Failed to execute '{}' with content '{}'. Error: {}".format(cmd, message.content, exception))
                # Exit the loop, we found the command and managed it
                break
