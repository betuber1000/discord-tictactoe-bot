import os
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
import threading

# ----- Bot setup -----
intents = discord.Intents.default()
intents.message_content = True  # Zorg dat dit aan staat in Developer Portal
bot = commands.Bot(command_prefix="/", intents=intents)

# ---- Tic-Tac-Toe data -----
games = {}  # {channel_id: game_state}
stats = {}  # {user_id: {"wins":0,"losses":0,"played":0}}

# ---- Tic-Tac-Toe logica -----
def check_winner(board):
    for line in [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]:
        a,b,c = line
        if board[a] == board[b] == board[c] and board[a] != "⬜":
            return board[a]
    if "⬜" not in board:
        return "Tie"
    return None

def render_board(board):
    return "".join(board[:3]) + "\n" + "".join(board[3:6]) + "\n" + "".join(board[6:9])

# ----- Slash command: /start-tictactoe -----
@bot.tree.command(name="start-tictactoe", description="Start een spelletje Tic-Tac-Toe")
async def start(interaction: discord.Interaction):
    board = ["⬜"]*9
    games[interaction.channel_id] = {"board": board, "turn": interaction.user.id}
    await interaction.response.send_message(f"Tic-Tac-Toe gestart!\n{render_board(board)}")

# ----- Slash command: /stats -----
@bot.tree.command(name="stats", description="Bekijk je Tic-Tac-Toe stats")
async def user_stats(interaction: discord.Interaction):
    user = interaction.user
    data = stats.get(user.id, {"wins":0,"losses":0,"played":0})
    await interaction.response.send_message(
        f"{user.name} stats:\nGewonnen: {data['wins']}\nVerloren: {data['losses']}\nGespeeld: {data['played']}"
    )

# ----- Ready event -----
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"Bot is online als {bot.user}")
    except Exception as e:
        print(f"Fout bij sync: {e}")

# ----- Start bot -----
bot.run(os.environ.get("DISCORD_TOKEN"))

# ----- Flask dummy server voor Render -----
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

# Start Flask in aparte thread
threading.Thread(target=run).start()
