import discord
from discord.ext import commands
import os
import json
import random

# ----- CONFIG -----
TOKEN = os.environ.get("DISCORD_TOKEN")
INTENTS = discord.Intents.default()
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

STATS_FILE = "tictactoe_stats.json"
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
    lines = [
        [0,1,2],[3,4,5],[6,7,8],      # Rows
        [0,3,6],[1,4,7],[2,5,8],      # Columns
        [0,4,8],[2,4,6]               # Diagonals
    ]
    for l in lines:
        if board[l[0]] == board[l[1]] == board[l[2]] and board[l[0]] != "⬜":
            return board[l[0]]
    if "⬜" not in board:
        return "Tie"
    return None

def ai_move(board):
    empty = [i for i, x in enumerate(board) if x == "⬜"]
    return random.choice(empty) if empty else None

# ----- BUTTONS -----
class TicTacToeButton(discord.ui.Button):
    def __init__(self, index, board, players, turn, message_id):
        super().__init__(style=discord.ButtonStyle.secondary, label="⬜", row=index//3)
        self.index = index
        self.board = board
        self.players = players
        self.turn = turn
        self.message_id = message_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.turn:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        if self.board[self.index] != "⬜":
            await interaction.response.send_message("This spot is already taken!", ephemeral=True)
            return

        self.board[self.index] = self.players[self.turn]
        self.label = self.board[self.index]
        winner = check_winner(self.board)
        view = self.view
        await interaction.response.edit_message(view=view)

        if winner:
            if winner == "Tie":
                content = "It's a tie!"
            else:
                winner_id = [k for k,v in self.players.items() if v==winner][0]
                if winner_id == "AI":
                    content = "AI wins!"
                else:
                    user = await bot.fetch_user(winner_id)
                    content = f"{user.mention} wins!"
                    stats[str(winner_id)] = stats.get(str(winner_id), 0) + 1
                    save_stats()
            for child in view.children:
                child.disabled = True
            await interaction.followup.send(content)
            await interaction.message.edit(view=view)

        # AI turn
        if "AI" in self.players and not winner:
            ai_index = ai_move(self.board)
            self.board[ai_index] = "⭕"
            view.children[ai_index].label = "⭕"
            winner_ai = check_winner(self.board)
            if winner_ai:
                if winner_ai == "Tie":
                    content = "It's a tie!"
                else:
                    content = "AI wins!"
                for child in view.children:
                    child.disabled = True
                await interaction.followup.send(content)
            await interaction.message.edit(view=view)
            self.turn = interaction.user.id
        else:
            # Switch turn
            ids = [k for k in self.players if k != self.turn]
            self.turn = ids[0]

class TicTacToeView(discord.ui.View):
    def __init__(self, board, players, turn, message_id):
        super().__init__(timeout=None)
        self.board = board
        self.players = players
        self.turn = turn
        self.message_id = message_id
        for i in range(9):
            self.add_item(TicTacToeButton(i, board, players, turn, message_id))

# ----- COMMANDS -----
@bot.command()
async def start(ctx, opponent: discord.Member = None):
    board = ["⬜"] * 9
    players = {ctx.author.id: "❌"}

    if opponent:
        players[opponent.id] = "⭕"
        await ctx.send(f"Tic Tac Toe started: {ctx.author.mention} vs {opponent.mention}")
    else:
        players["AI"] = "⭕"
        await ctx.send(f"Tic Tac Toe started: {ctx.author.mention} vs AI")

    view = TicTacToeView(board, players, ctx.author.id, None)
    await ctx.send("Tic Tac Toe", view=view)

@bot.command()
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
