import os
import discord
from discord.ext import commands
from discord import app_commands, ui
from flask import Flask
import threading

# ---------------- BOT SETUP ----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

stats = {}

# ---------------- TICTACTOE BUTTON ----------------
class TicTacToeButton(ui.Button):
    def __init__(self, row, col):
        super().__init__(style=discord.ButtonStyle.secondary, label=" ", row=row)
        self.row_pos = row
        self.col_pos = col

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view

        if interaction.user.id != view.turn:
            await interaction.response.send_message("Not your turn.", ephemeral=True)
            return

        mark = "❌" if view.turn == view.player1.id else "⭕"
        self.label = mark
        self.disabled = True
        view.board[self.row_pos][self.col_pos] = mark

        winner = view.check_winner()

        if winner:
            for child in view.children:
                child.disabled = True

            for pid in [view.player1.id, view.player2.id]:
                stats[pid] = stats.get(pid, {"wins": 0, "losses": 0, "played": 0})
                stats[pid]["played"] += 1

            if winner == "Tie":
                msg = "It's a tie!"
            else:
                win_id = view.player1.id if winner == "❌" else view.player2.id
                lose_id = view.player2.id if winner == "❌" else view.player1.id
                stats[win_id]["wins"] += 1
                stats[lose_id]["losses"] += 1
                msg = f"<@{win_id}> won! 🎉"

            await interaction.response.edit_message(content=msg, view=view)
            return

        view.turn = view.player1.id if view.turn == view.player2.id else view.player2.id
        symbol = "❌" if view.turn == view.player1.id else "⭕"

        await interaction.response.edit_message(
            content=f"<@{view.turn}>'s turn {symbol}",
            view=view
        )


# ---------------- VIEW ----------------
class TicTacToeView(ui.View):
    def __init__(self, p1, p2):
        super().__init__(timeout=None)
        self.player1 = p1
        self.player2 = p2
        self.turn = p1.id
        self.board = [["" for _ in range(3)] for _ in range(3)]

        for r in range(3):
            for c in range(3):
                self.add_item(TicTacToeButton(r, c))

    def check_winner(self):
        b = self.board
        lines = [
            [b[0][0], b[0][1], b[0][2]],
            [b[1][0], b[1][1], b[1][2]],
            [b[2][0], b[2][1], b[2][2]],
            [b[0][0], b[1][0], b[2][0]],
            [b[0][1], b[1][1], b[2][1]],
            [b[0][2], b[1][2], b[2][2]],
            [b[0][0], b[1][1], b[2][2]],
            [b[0][2], b[1][1], b[2][0]],
        ]

        for line in lines:
            if line[0] == line[1] == line[2] != "":
                return line[0]

        if all(all(cell != "" for cell in row) for row in b):
            return "Tie"

        return None


# ---------------- SLASH COMMANDS ----------------
@bot.tree.command(name="start-tictactoe", description="Play TicTacToe")
@app_commands.describe(opponent="Who do you want to play against?")
async def start(interaction: discord.Interaction, opponent: discord.Member):
    if opponent.bot:
        await interaction.response.send_message("You can't play vs bots.", ephemeral=True)
        return

    view = TicTacToeView(interaction.user, opponent)

    await interaction.response.send_message(
        f"{interaction.user.mention} vs {opponent.mention}\n"
        f"{interaction.user.mention}'s turn ❌",
        view=view
    )


@bot.tree.command(name="stats", description="See your stats")
async def stats_cmd(interaction: discord.Interaction):
    data = stats.get(interaction.user.id, {"wins": 0, "losses": 0, "played": 0})

    await interaction.response.send_message(
        f"Wins: {data['wins']}\nLosses: {data['losses']}\nPlayed: {data['played']}"
    )


# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    print("Slash commands synced")


# ---------------- FLASK (FOR RENDER FREE) ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"


def run_web():
    app.run(host="0.0.0.0", port=8080)


threading.Thread(target=run_web).start()

# 🔥 BOT IN MAIN THREAD (IMPORTANT)
bot.run(os.environ["DISCORD_TOKEN"])
