import discord
import random
import time
import names
import re
import math

import asyncio
from statemachine import StateMachine, State
from threading import Thread
from mafia.misc.utils import Misc, Timers, Alignment


class DelayedOperation(Thread):
    TIME_MESSAGE_BEFORE_END = 10
    MSG_TEMPLATE = "*{}: {} secondes restantes...*"

    def __init__(self, timer, operation, title: str = None, send_message_fnc=None):
        """
        Initializer
        :param timer: a duration before operation, in seconds
        :param operation: a function to execute after the timer
        :param title: string displayed as timer name
        :param send_message_fnc: function used to send a message to everyone
        """
        super().__init__()
        self._timer = timer
        self._operation = operation
        self._title = title
        self._send_message_fnc = send_message_fnc

        self._disabled = False

    def run(self):
        """
        Run thread
        """
        if self._title is not None and \
                self._send_message_fnc is not None and \
                self._timer < self.TIME_MESSAGE_BEFORE_END:
            self._send_message_fnc(self.MSG_TEMPLATE.format(self._title, int(self._timer)))
        init_time = time.time()
        while time.time() - init_time < self._timer and not self._disabled:
            time.sleep(1.0)
            if self._title is not None and self._send_message_fnc is not None:
                if int(self._timer - round(time.time() - init_time)) == self.TIME_MESSAGE_BEFORE_END:
                    self._send_message_fnc(self.MSG_TEMPLATE.format(self._title,
                                                                    int(self._timer - round(time.time() - init_time))))
        if not self._disabled:
            # Execute operation
            self._operation()

    def disable(self):
        """
        Disable task
        """
        self._disabled = True


class GameState(StateMachine):
    """
    Game engine to handler games session
    """

    # Game states
    state_wait_for_players = State('WaitForPlayers', initial=True)
    state_players_nicknames = State('PlayersNicknames')
    state_configure_players = State('ConfigurePlayers')
    state_day_discussion = State('DayDiscussion')
    state_day_vote = State('DayDiscussion')
    state_day_trial_launch = State('DayTrialLaunch')
    state_day_trial_defense = State('DayTrialDefense')
    state_day_trial_deliberation = State('DayTrialDeliberation')
    state_day_trial_verdict = State('DayTrialVerdict')
    state_day_trial_last_words = State('DayTrialLastWords')
    state_day_trial_kill = State('DayTrialKill')
    state_day_end = State('DayEnd')
    state_night = State("Night")
    state_night_sequence = State("NightSequence")

    # Transitions between states
    reset = state_wait_for_players.from_(state_wait_for_players,
                                         state_players_nicknames,
                                         state_configure_players,
                                         state_day_discussion,
                                         state_night)
    select_names = state_wait_for_players.to(state_players_nicknames)
    configure_players = state_players_nicknames.to(state_configure_players)
    day_discussion = state_day_discussion.from_(state_configure_players, state_night_sequence)
    day_vote = state_day_vote.from_(state_day_discussion, state_day_trial_verdict)
    day_trial_launch = state_day_vote.to(state_day_trial_launch)
    day_trial_defense = state_day_trial_launch.to(state_day_trial_defense)
    day_trial_deliberation = state_day_trial_defense.to(state_day_trial_deliberation)
    day_trial_verdict = state_day_trial_deliberation.to(state_day_trial_verdict)
    day_trial_last_words = state_day_trial_verdict.to(state_day_trial_last_words)
    day_trial_kill = state_day_trial_last_words.to(state_day_trial_kill)
    day_end = state_day_end.from_(state_day_discussion, state_day_vote, state_day_trial_kill)

    night = state_night.from_(state_day_end)
    night_sequence = state_night.to(state_night_sequence)

    def __init__(self, bot, mafia_engine):
        super().__init__()
        self._bot = bot
        self._mafia_engine = mafia_engine
        self._loop = asyncio.get_event_loop()
        self._current_day = 0
        self._next_state = None

    def _send_message(self, message):
        channel = self._bot.get_channel(775453457708482622)
        asyncio.run_coroutine_threadsafe(channel.send(message), self._loop)

    def disable_next_state(self):
        """
        Used to disable configured next state
        """
        if self._next_state is not None:
            self._next_state.disable()

    def on_reset(self):
        """
        Called when state_reset state is set
        """
        print("Reset !")

    def on_select_names(self):
        """
        Called when state_select_names state is set
        """
        print("on_select_names")
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        self._mafia_engine.send_message_everyone("Lancement de la partie. "
                                                 "Configurez un pseudo personnalisé avec la commande '-VOTRE_PSEUDO'.")
        self._next_state = DelayedOperation(Timers.TIMER_SELECT_NICKNAME,
                                            self.configure_players,
                                            "Choix des pseudos",
                                            self._mafia_engine.send_message_everyone)
        self._next_state.start()

    def _on_configure_players_operations(self):
        """
        Function to configure players with precise timing. Include sleeps, must be threaded !
        """
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        time.sleep(2.0)
        self._mafia_engine.send_message_everyone("Répartition des rôles. Vous êtes...")
        time.sleep(2.0)
        self._mafia_engine.configure_players()
        time.sleep(3.0)
        # Go to first day !
        next_state = DelayedOperation(3.0, self.day_discussion)
        next_state.start()

    def on_configure_players(self):
        """
        Called when state_configure_players state is set
        """
        print("on_configure_players")
        operation = Thread(target=self._on_configure_players_operations)
        operation.start()

    def on_day_discussion(self):
        """
        Called when state_day_discussion state is set
        """
        print("on_day_discussion")
        # Increase day counter
        self._current_day += 1
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        self._mafia_engine.send_message_everyone("**JOUR {}** - Discussion - {} secondes"
                                                 .format(self._current_day, Timers.TIME_DAY_CHAT))

        if self._current_day == 1:
            next_state = self.day_end
        else:
            next_state = self.day_vote
        self._next_state = DelayedOperation(Timers.TIME_DAY_CHAT,
                                            next_state,
                                            "Discussion",
                                            self._mafia_engine.send_message_everyone)
        self._next_state.start()

    def on_day_vote(self):
        """
        Called when state_day_vote state is set
        """
        print("on_day_vote")
        self._mafia_engine.send_message_everyone("*Vous pouvez désormais voter pour démarrer un procès (utilisez '-vote X' pour voter contre quelqu'un).*")
        self._next_state = DelayedOperation(Timers.TIME_DAY_VOTE,
                                            self.day_end,
                                            "Vote",
                                            self._mafia_engine.send_message_everyone)
        self._next_state.start()

    def _on_day_trial_launch_operations(self):
        """
        Function to run the trial beginning
        """
        self._mafia_engine.send_message_everyone("*La ville a décidé d'envoyer {} au procès.*"
                                                 .format(self._mafia_engine.player_trial.get_nickname()))
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        time.sleep(3.0)
        self._mafia_engine.send_message_everyone("**Procès de **{}"
                                                 .format(self._mafia_engine.player_trial.get_nickname()))
        # Launch trial defense
        self.day_trial_defense()

    def on_day_trial_launch(self):
        """
        Called when state_day_trial_launch state is set
        """
        print("on_day_trial_launch")
        operation = Thread(target=self._on_day_trial_launch_operations)
        operation.start()

    def on_day_trial_defense(self):
        """
        Called when state_day_trial_defense state is set
        """
        time.sleep(1.0)
        msg = "*{}, vous êtes jugé pour conspiration contre la ville. Quelle est votre défense ?* - {} secondes"\
            .format(self._mafia_engine.player_trial.get_nickname(), Timers.TIME_DAY_TRIAL_DEFENSE)
        self._mafia_engine.send_message_everyone(msg)

        # Wait and go to trial deliberation
        self._next_state = DelayedOperation(Timers.TIME_DAY_TRIAL_DEFENSE,
                                            self.day_trial_deliberation)
        self._next_state.start()

    def on_day_trial_deliberation(self):
        """
        Called when state_day_trial_deliberation state is set
        """
        msg = "*La ville doit maintenant déterminer le sort de {}. '-innocent' pour innocent, '-guilty' pour coupable, '-cancel' pour annuler.* - {} secondes"\
            .format(self._mafia_engine.player_trial.get_nickname(), Timers.TIME_DAY_TRIAL_DELIBERATION)
        self._mafia_engine.send_message_everyone(msg)

        self._next_state = DelayedOperation(Timers.TIME_DAY_TRIAL_DELIBERATION,
                                            self.day_trial_verdict)
        self._next_state.start()

    def _on_day_trial_verdict_operations(self):
        """
        Function to run the trial verdict
        """
        self._mafia_engine.send_message_everyone("*Fin des délibérations*")
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        time.sleep(2.0)
        self._mafia_engine.send_message_everyone("*Le procès est terminé. Les votes vont être comptés.*")
        time.sleep(2.0)

        # Compute the verdict
        guilty = 0
        innocent = 0
        verdict_msg = ""
        for player in self._mafia_engine.players:
            player_vote = player.get_trial_vote()
            if player_vote == Misc.TRIAL_GUILTY:
                guilty += 1
                verdict_msg += "*[{} a voté **Coupable**]*\n".format(player.get_nickname())
            elif player_vote == Misc.TRIAL_INNOCENT:
                innocent += 1
                verdict_msg += "*[{} a voté **Innocent**]*\n".format(player.get_nickname())
            else:
                verdict_msg += "*[{} s'est abstenu]*\n".format(player.get_nickname())

        if guilty > innocent:
            # Execute the player
            verdict_msg = "*La ville a décidé de lyncher {} par un vote de {} coupable(s) contre {} innocent(s).*\n"\
                .format(self._mafia_engine.player_trial.get_nickname(), guilty, innocent) + verdict_msg
            self._mafia_engine.send_message_everyone(verdict_msg)
            # Kill the player !
            self.day_trial_last_words()
        else:
            # Player saved by the town
            verdict_msg = "*La ville a décidé de sauver {} par un vote de {} coupable(s) contre {} innocent(s).*\n"\
                .format(self._mafia_engine.player_trial.get_nickname(), guilty, innocent) + verdict_msg
            self._mafia_engine.send_message_everyone(verdict_msg)
            self._mafia_engine.player_trial = None
            time.sleep(2.0)
            # Return to day_vote
            self.day_vote()

    def on_day_trial_verdict(self):
        """
        Called when state_day_trial_verdict state is set
        """
        print("on_day_trial_verdict")
        operation = Thread(target=self._on_day_trial_verdict_operations)
        operation.start()

    def on_day_trial_last_words(self):
        """
        Called when state_trial_last_words state is set
        """
        print("on_day_trial_last_words")
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        self._mafia_engine.send_message_everyone("*Un dernier mot ?*")
        self._next_state = DelayedOperation(Timers.TIME_DAY_TRIAL_LAST_WORDS, self.day_trial_kill)
        self._next_state.start()

    def _on_day_trial_kill_operation(self):
        """
        Function to run the trial verdict
        """
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        self._mafia_engine.send_message_everyone("*Exécution de {}...*".format(self._mafia_engine.player_trial.get_nickname()))
        time.sleep(2.0)
        self._mafia_engine.player_trial.set_dead()
        self._mafia_engine.send_message_everyone("*{} est mort.*".format(self._mafia_engine.player_trial.get_nickname()))
        time.sleep(2.0)
        msg = "*{} était **{}**.*".format(self._mafia_engine.player_trial.get_nickname(),
                                          self._mafia_engine.player_trial.get_role().name)
        self._mafia_engine.send_message_everyone(msg)
        time.sleep(1.0)
        self._mafia_engine.send_message_everyone("*## Derniers mots*\n{}".format(self._mafia_engine.player_trial.get_last_will()))
        time.sleep(2.0)
        self._mafia_engine.player_trial = None
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        self.day_end()

    def on_day_trial_kill(self):
        """
        Called when state_day_trial_kill state is set
        """
        print("on_day_trial_kill")
        operation = Thread(target=self._on_day_trial_kill_operation)
        operation.start()

    def _on_day_end_operations(self):
        """
        Function to run the end of the day
        """
        self._mafia_engine.send_message_everyone("*Fin de la journée, revoyons-nous demain.*")
        self._next_state = DelayedOperation(Timers.TIME_DAY_END, self.night)
        self._next_state.start()

    def on_day_end(self):
        """
        Called when state_day_end state is set
        """
        print("on_day_end")
        operation = Thread(target=self._on_day_end_operations)
        operation.start()

    def _on_night_operations(self):
        """
        Function to run the night
        """
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        self._mafia_engine.send_message_everyone("**NUIT {}** - {} secondes"
                                                 .format(self._current_day, Timers.TIME_NIGHT))
        for player in self._mafia_engine.players:
            if player.get_role().alignment == Alignment.MAFIA:
                # Display he can speak to the mafia
                player.send_message_to_player("*Vous pouvez discuter avec les autres membres de la Mafia.*")

        # Wait and go to night resolution !
        self._next_state = DelayedOperation(Timers.TIME_NIGHT,
                                            self.night_sequence,
                                            "Nuit",
                                            self._mafia_engine.send_message_everyone)
        self._next_state.start()

    def on_night(self):
        """
        Called when state_night state is set
        """
        print("on_night")
        operation = Thread(target=self._on_night_operations)
        operation.start()

    def _on_night_sequence_operations(self):
        """
        Function to run the night sequence operations
        """
        self._mafia_engine.send_message_everyone("*Fin de la nuit...*")
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        self._mafia_engine.send_message_everyone("**Que s'est-il passé pendant la nuit ?**")

        # TODO...
        self._next_state = DelayedOperation(3.0, self.day_discussion)
        self._next_state.start()

    def on_night_sequence(self):
        """
        Called when state_night_sequence state is set
        """
        print("on_night_sequence")
        operation = Thread(target=self._on_night_sequence_operations)
        operation.start()

    def get_current_day(self) -> int:
        """
        Get the current day ID
        :return: current day number
        """
        return self._current_day
