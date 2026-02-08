import discord
from discord.ext import commands
from discord import app_commands
import os
import json

# Intents voor de bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

STATS_FILE = "stats.json"

# Helper functies voor stats
def load_stats():
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def update_stats(user_id, result):
    stats = load_stats()
    user_id = str(user_id)
    if user_id not in stats:
        stats[user_id] = {"gewonnen":0, "verloren":0, "gespeeld":0}
    stats[user_id]["gespeeld"] += 1
    if result == "win":
        stats[user_id]["gewonnen"] += 1
    elif result == "loss":
        stats[user_id]["verloren"] += 1
    save_stats(stats)

# Tic-Tac-Toe bord en logica
class TicTacToe(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=None)
        self.board = [" "] * 9
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.symbols = {player1: "❌", player2: "⭕"}
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        for i in range(9):
            row = i // 3
            btn = discord.ui.Button(
                label=self.board[i] if self.board[i] != " " else "⬜️",
                style=discord.ButtonStyle.secondary,
                row=row,
                disabled=self.board[i] != " "
            )
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.current_player:
                await interaction.response.send_message("Niet jouw beurt!", ephemeral=True)
                return

            self.board[index] = self.symbols[self.current_player]

            winner = self.check_winner()
            if winner:
                self.update_buttons()
                await interaction.response.edit_message(content=f"{self.current_player.mention} wint! 🎉", view=self)
                # Stats bijwerken
                loser = self.player1 if self.current_player == self.player2 else self.player2
                update_stats(self.current_player.id, "win")
                update_stats(loser.id, "loss")
                self.stop()
                return
            elif " " not in self.board:
                self.update_buttons()
                await interaction.response.edit_message(content="Gelijkspel! 🤝", view=self)
                # Stats bijwerken
                update_stats(self.player1.id, "draw")
                update_stats(self.player2.id, "draw")
                self.stop()
                return

            # Wissel speler
            self.current_player = self.player1 if self.current_player == self.player2 else self.player2
            self.update_buttons()
            await interaction.response.edit_message(content=f"Beurt van {self.current_player.mention}", view=self)
        return callback

    def check_winner(self):
        combos = [
            [0,1,2],[3,4,5],[6,7,8],
            [0,3,6],[1,4,7],[2,5,8],
            [0,4,8],[2,4,6]
        ]
        for combo in combos:
            a,b,c = combo
            if self.board[a] == self.board[b] == self.board[c] != " ":
                return True
        return False

# /start-tictactoe
@bot.tree.command(name="start-tictactoe", description="Start een potje Tic-Tac-Toe")
@app_commands.describe(opponent="Kies een tegenstander")
async def start_tictactoe(interaction: discord.Interaction, opponent: discord.Member):
    if opponent.bot:
        await interaction.response.send_message("Je kunt niet tegen een bot spelen.", ephemeral=True)
        return
    view = TicTacToe(interaction.user, opponent)
    await interaction.response.send_message(f"Tic-Tac-Toe gestart! Beurt van {interaction.user.mention}", view=view)

# /stats
@bot.tree.command(name="stats", description="Bekijk je Tic-Tac-Toe statistieken")
async def stats(interaction: discord.Interaction):
    stats = load_stats()
    user_id = str(interaction.user.id)
    if user_id not in stats:
        await interaction.response.send_message("Je hebt nog geen spellen gespeeld! 🎮")
        return
    s = stats[user_id]
    await interaction.response.send_message(
        f"{interaction.user.mention} Stats:\n"
        f"Gespeeld: {s['gespeeld']}\n"
        f"Gewonnen: {s['gewonnen']}\n"
        f"Verloren: {s['verloren']}"
    )

# Bot klaar
@bot.event
async def on_ready():
    print(f"Bot is online als {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Commands gesynct: {len(synced)}")
    except Exception as e:
        print(f"Fout bij sync: {e}")

bot.run(os.environ.get("DISCORD_TOKEN"))

from flask import Flask
import threading

# Maak Flask app
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

# Functie die Flask start op poort 8080
def run():
    app.run(host="0.0.0.0", port=8080)

# Start Flask in een aparte thread
threading.Thread(target=run).start()
