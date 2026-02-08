import discord
from discord.ext import commands
import json
import random
import os

# ----- CONFIG -----
TOKEN = os.environ.get("DISCORD_TOKEN")  # Set your token in environment variables
INTENTS = discord.Intents.default()
INTENTS.message_content = True  # Needed for commands

bot = commands.Bot(command_prefix='!', intents=INTENTS)

STATS_FILE = "tictactoe_stats.json"

# Load stats
if os.path.exists(STATS_FILE):
    with open(STATS_FILE, "r") as f:
        stats = json.load(f)
else:
    stats = {}

# ----- HELPERS -----
def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def check_winner(board):
    # Rows, cols, diagonals
    lines = [
        board[0:3], board[3:6], board[6:9],        # Rows
        board[0:9:3], board[1:9:3], board[2:9:3],  # Cols
        board[0:9:4], board[2:7:2]                  # Diags
    ]
    for line in lines:
        if line[0] == line[1] == line[2] and line[0] != "⬜":
            return line[0]
    if "⬜" not in board:
        return "Tie"
    return None

def board_to_string(board):
    return "".join(board)

def ai_move(board):
    empty = [i for i, x in enumerate(board) if x == "⬜"]
    return random.choice(empty) if empty else None

# ----- COMMANDS -----
@bot.command(name="start")
async def start(ctx, opponent: discord.Member = None):
    board = ["⬜"] * 9
    player_symbols = {}
    player_symbols[ctx.author.id] = "❌"

    if opponent:
        player_symbols[opponent.id] = "⭕"
        await ctx.send(f"Tic Tac Toe started: {ctx.author.mention} vs {opponent.mention}")
    else:
        # Play vs AI
        player_symbols["AI"] = "⭕"
        await ctx.send(f"Tic Tac Toe started: {ctx.author.mention} vs AI")

    game_message = await ctx.send(
        embed=discord.Embed(
            title="Tic Tac Toe",
            description="".join(board[i] for i in range(9)),
            color=discord.Color.blue()
        )
    )

    # Save game state in message
    bot.games = getattr(bot, "games", {})
    bot.games[game_message.id] = {
        "board": board,
        "players": player_symbols,
        "turn": ctx.author.id
    }

@bot.command(name="move")
async def move(ctx, position: int):
    game = None
    for g in getattr(bot, "games", {}).values():
        if ctx.author.id in g["players"]:
            game = g
            break
    if not game:
        await ctx.send("You are not in a game!")
        return

    board = game["board"]
    turn = game["turn"]

    if ctx.author.id != turn:
        await ctx.send("It's not your turn!")
        return

    if board[position-1] != "⬜":
        await ctx.send("This spot is already taken!")
        return

    board[position-1] = game["players"][ctx.author.id]

    winner = check_winner(board)
    embed = discord.Embed(title="Tic Tac Toe", description="".join(board), color=discord.Color.green())
    await ctx.send(embed=embed)

    if winner:
        if winner == "Tie":
            await ctx.send("It's a tie!")
        elif winner == "❌":
            await ctx.send(f"{ctx.author.mention} wins!")
            stats[str(ctx.author.id)] = stats.get(str(ctx.author.id), 0) + 1
        elif winner == "⭕":
            await ctx.send("⭕ wins!")
        save_stats()
        del bot.games[next(iter(bot.games))]
        return

    # Switch turn
    if "AI" in game["players"]:
        ai_pos = ai_move(board)
        board[ai_pos] = "⭕"
        winner = check_winner(board)
        embed = discord.Embed(title="Tic Tac Toe", description="".join(board), color=discord.Color.red())
        await ctx.send(embed=embed)
        if winner:
            if winner == "Tie":
                await ctx.send("It's a tie!")
            else:
                await ctx.send("AI wins!")
            del bot.games[next(iter(bot.games))]
            return
    else:
        for player_id in game["players"]:
            if player_id != turn:
                game["turn"] = player_id
                break

@bot.command(name="leaderboard")
async def leaderboard(ctx):
    if not stats:
        await ctx.send("No stats yet!")
        return
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    description = ""
    for i, (user_id, wins) in enumerate(sorted_stats[:10], 1):
        user = await bot.fetch_user(int(user_id))
        description += f"{i}. {user.name} - {wins} wins\n"
    embed = discord.Embed(title="Tic Tac Toe Leaderboard", description=description, color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

# ----- RUN BOT -----
bot.run(TOKEN)
