import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = "servers.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_server(data, guild_id):
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {"prefix": "!", "commands": {}}
    return data[gid]

def get_prefix(bot, message):
    if not message.guild:
        return "!"
    data = load_data()
    return get_server(data, message.guild.id).get("prefix", "!")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Zalogowano jako {bot.user} (Serwery: {len(bot.guilds)})")

@bot.tree.command(name="addcmd", description="Dodaj własną komendę (maks. 5 na serwer)")
@app_commands.checks.has_permissions(manage_guild=True)
async def addcmd(interaction: discord.Interaction, trigger: str, response: str):
    data = load_data()
    server = get_server(data, interaction.guild_id)
    trigger = trigger.lower().strip()

    if trigger not in server["commands"] and len(server["commands"]) >= 5:
        await interaction.response.send_message(
            "❌ Osiągnięto limit! Możesz mieć maksymalnie **5 własnych komend**. Użyj najpierw `/removecmd`.",
            ephemeral=True
        )
        return

    server["commands"][trigger] = response
    save_data(data)
    prefix = server["prefix"]
    await interaction.response.send_message(
        f"✅ Zapisano! Wpisanie `{prefix}{trigger}` wyśle odpowiedź:\n> {response}"
    )

@bot.tree.command(name="removecmd", description="Usuń jedną ze swoich własnych komend")
@app_commands.checks.has_permissions(manage_guild=True)
async def removecmd(interaction: discord.Interaction, trigger: str):
    data = load_data()
    server = get_server(data, interaction.guild_id)
    trigger = trigger.lower().strip()

    if trigger not in server["commands"]:
        await interaction.response.send_message(f"❌ Komenda `{trigger}` nie istnieje.", ephemeral=True)
        return

    del server["commands"][trigger]
    save_data(data)
    await interaction.response.send_message(f"🗑️ Usunięto `{trigger}` (wykorzystano {len(server['commands'])}/5 slotów).")

@bot.tree.command(name="listcmds", description="Pokaż wszystkie własne komendy na tym serwerze")
async def listcmds(interaction: discord.Interaction):
    data = load_data()
    server = get_server(data, interaction.guild_id)
    cmds = server["commands"]
    prefix = server["prefix"]

    if not cmds:
        await interaction.response.send_message("Brak własnych komend! Użyj `/addcmd`, żeby stworzyć pierwszą.")
        return

    lines = [f"• `{prefix}{name}` → {reply}" for name, reply in cmds.items()]
    await interaction.response.send_message(
        f"**Własne komendy ({len(cmds)}/5):**\n" + "\n".join(lines)
    )

@bot.tree.command(name="setprefix", description="Zmień znak komendy (domyślnie: !)")
@app_commands.checks.has_permissions(manage_guild=True)
async def setprefix(interaction: discord.Interaction, new_prefix: str):
    if len(new_prefix) > 3:
        await interaction.response.send_message("❌ Prefix może mieć maksymalnie 3 znaki.", ephemeral=True)
        return
    data = load_data()
    server = get_server(data, interaction.guild_id)
    server["prefix"] = new_prefix
    save_data(data)
    await interaction.response.send_message(f"✅ Zmieniono prefix na `{new_prefix}`")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    data = load_data()
    server = get_server(data, message.guild.id)
    prefix = server["prefix"]

    if message.content.startswith(prefix):
        typed = message.content[len(prefix):].strip().lower()
        if typed in server["commands"]:
            await message.channel.send(server["commands"][typed])

    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
