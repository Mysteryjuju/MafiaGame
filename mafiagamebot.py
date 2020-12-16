from discord.ext import commands
from mafia.gameengine import MafiaEngine, GameState

bot = commands.Bot(command_prefix='$')
bot.mafia_engine = MafiaEngine(bot)


@bot.event
async def on_ready():
    print('Connected to server as {0.user}'.format(bot))


@bot.event
async def on_message(message):
    # Don't manage bot messages
    if message.author == bot.user:
        return

    # Manage messages depending on game state
    if message.channel in bot.mafia_engine.private_channels:
        # Delete message
        await message.delete()

        # Manage message depending on game state
        game_state = bot.mafia_engine.get_game_state()
        if game_state == GameState.state_players_nicknames:
            # Start game, only accept custom nicknames
            if message.content.startswith('-') and len(message.content) > 1:
                bot.mafia_engine.set_player_nickname(message)
        elif game_state in [GameState.state_day_discussion,
                            GameState.state_day_vote,
                            GameState.state_day_trial_deliberation]:
            bot.mafia_engine.manage_day_common(message)
        elif game_state in [GameState.state_day_trial_defense,
                            GameState.state_day_trial_last_words]:
            bot.mafia_engine.manage_day_trial_defense(message)
        elif game_state == GameState.state_night:
            bot.mafia_engine.manage_night(message)

    # To process commands sent to bot
    await bot.process_commands(message)


########################################################################################################################
# BOT commands to manage games
########################################################################################################################
@bot.command()
async def create_game(ctx):
    # Delete message
    await ctx.message.delete()
    # Start a new game !
    await bot.mafia_engine.create_game(ctx)


@bot.command()
async def join_game(ctx):
    # Delete message
    await ctx.message.delete()
    # Join a new game
    await bot.mafia_engine.join_game(ctx)


@bot.command()
async def start_game(ctx):
    # Delete message
    await ctx.message.delete()
    # Start the game
    await bot.mafia_engine.start_game(ctx)


@bot.command()
async def stop_game(ctx):
    # Delete message
    await ctx.message.delete()
    # Stop the game !
    await bot.mafia_engine.stop_game(ctx)


# FOR DEBUG !
@bot.command()
async def debug_game_state(ctx):
    # Delete message
    await ctx.message.delete()
    # Stop the game !
    await ctx.message.channel.send("Current state: {}".format(bot.mafia_engine.get_game_state()))

my_string = """
Ma super belle description
Qui envoie du poney !
Et qui déchire sa race sur plusieurs lignes !"""

@bot.command()
async def test(ctx):
    message = await ctx.send("hello")
    #await asyncio.sleep(1)
    await message.edit(content="newcontent")

with open('bot.token', 'r') as bot_token_file:
    bot_token = bot_token_file.read()
bot.run(bot_token)
