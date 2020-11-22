import discord
import random
import time
import names
import re
import math

import asyncio
from statemachine import StateMachine, State
from threading import Thread
from mafia.misc.utils import Misc, Timers

# TODO: FOR DEBUG PURPOSES
from mafia.fakeplayer import FakePlayer


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

    # Game steps
    # Players join
    # Players configure custom names
    # Dispatch roles
    # Roulement des jours:
    ## Day 1, only speaking
    ## Night 1, tchats for some players, prepare actions
    ## Day 2, speaking
    ## Night 2, ...
    """

    # Game states
    state_wait_for_players = State('WaitForPlayers', initial=True)
    state_players_nicknames = State('PlayersNicknames')
    state_configure_players = State('ConfigurePlayers')
    state_day_discussion = State('DayDiscussion')
    state_day_trial_launch = State('DayTrialLaunch')
    state_day_trial_defense = State('DayTrialDefense')
    state_day_trial_deliberation = State('DayTrialDeliberation')
    state_day_trial_verdict = State('DayTrialVerdict')
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
    day_trial_launch = state_day_discussion.to(state_day_trial_launch)
    day_trial_defense = state_day_trial_launch.to(state_day_trial_defense)
    day_trial_deliberation = state_day_trial_defense.to(state_day_trial_deliberation)
    day_trial_verdict = state_day_trial_deliberation.to(state_day_trial_verdict)

    # TODO: un état transitoire court à ajouter pour ajouter de la tempo ?
    # end_of_day =

    night = state_night.from_(state_day_discussion)
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

        self._next_state = DelayedOperation(Timers.TIME_DAY_CHAT,
                                            self.night,
                                            "Discussion",
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
        msg = "***{}**, vous êtes jugé pour conspiration contre la ville. Quelle est votre défense ?* - {} secondes"\
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
        msg = "*La ville doit maintenant déterminer le sort de **{}**. '-innocent' pour innocent, '-guilty' pour coupable.* - {} secondes"\
            .format(self._mafia_engine.player_trial.get_nickname(), Timers.TIME_DAY_TRIAL_DELIBERATION)
        self._mafia_engine.send_message_everyone(msg)

        self._next_state = DelayedOperation(Timers.TIME_DAY_TRIAL_DELIBERATION,
                                            self.day_trial_verdict)
        self._next_state.start()

    def on_day_trial_verdict(self):
        """
        Called when state_day_trial_verdict state is set
        """
        print("TRIAL VERDICT TODO !!!")

    def _on_night_operations(self):
        """
        Function to run the end of the day and the night
        """
        self._mafia_engine.send_message_everyone("*Fin de la journée...*")
        self._mafia_engine.send_message_everyone(Misc.STATES_STRING_SEPARATOR)
        self._mafia_engine.send_message_everyone("**NUIT {}** - {} secondes"
                                                 .format(self._current_day, Timers.TIME_NIGHT))
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
