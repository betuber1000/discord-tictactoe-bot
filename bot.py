import os
import discord
from discord.ext import commands
from discord import app_commands, ui
from flask import Flask
import threading

# ----- Bot setup -----
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ----- Stats -----
stats = {}  # {user_id: {"wins":0,"losses":0,"played":0}}

# ----- Tic-Tac-Toe Button -----
class TicTacToeButton(ui.Button):
    def __init__(self, row, col):
        super().__init__(style=discord.ButtonStyle.secondary, label="⬜", row=row)
        self.row_pos = row
        self.col_pos = col

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if interaction.user.id != view.turn:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        # Set mark
        mark = "❌" if view.turn == view.player1.id else "⭕"
        self.label = mark
        self.disabled = True
        view.board[self.row_pos][self.col_pos] = mark

        # Check winner
        winner = view.check_winner()
        if winner:
            for child in view.children:
                child.disabled = True

            # Update stats for both players
            for player_id in [view.player1.id, view.player2.id]:
                stats[player_id] = stats.get(player_id, {"wins":0,"losses":0,"played":0})
                stats[player_id]["played"] += 1

            content = ""
            if winner == "Tie":
                content = "It's a tie!"
            else:
                winner_id = view.player1.id if winner == "❌" else view.player2.id
                loser_id = view.player2.id if winner == "❌" else view.player1.id
                stats[winner_id]["wins"] += 1
                stats[loser_id]["losses"] += 1
                content = f"<@{winner_id}> won!"

            await interaction.response.edit_message(content=content, view=view)
            return

        # Switch turn
        view.turn = view.player1.id if view.turn == view.player2.id else view.player2.id
        next_player = "<@{}>".format(view.turn)
        await interaction.response.edit_message(view=view, content=f"{next_player}'s turn {'❌' if view.turn == view.player1.id else '⭕'}")

# ----- Tic-Tac-Toe View -----
class TicTacToeView(ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=None)
        self.player1 = player1
        self.player2 = player2
        self.turn = player1.id
        self.board = [["" for _ in range(3)] for _ in range(3)]
        for r in range(3):
            for c in range(3):
                self.add_item(TicTacToeButton(row=r, col=c))

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

# ----- Slash command: /start-tictactoe -----
@bot.tree.command(name="start-tictactoe", description="Start a Tic-Tac-Toe game with another player")
@app_commands.describe(opponent="The player you want to challenge")
async def start(interaction: discord.Interaction, opponent: discord.Member):
    if opponent.bot:
        await interaction.response.send_message("You cannot play against bots!", ephemeral=True)
        return
    view = TicTacToeView(player1=interaction.user, player2=opponent)
    await interaction.response.send_message(
        f"Tic-Tac-Toe: {interaction.user.mention} vs {opponent.mention}\n{interaction.user.mention}'s turn ❌", 
        view=view
    )

# ----- Slash command: /stats -----
@bot.tree.command(name="stats", description="View your Tic-Tac-Toe stats")
async def user_stats(interaction: discord.Interaction):
    user = interaction.user
    data = stats.get(user.id, {"wins":0,"losses":0,"played":0})
    await interaction.response.send_message(
        f"{user.name}'s stats:\nWins: {data['wins']}\nLosses: {data['losses']}\nPlayed: {data['played']}"
    )

# ----- Ready event -----
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"Bot is online as {bot.user}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# ----- Start bot -----
bot.run(os.environ.get("DISCORD_TOKEN"))

# ----- Flask dummy server for Render -----
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()
