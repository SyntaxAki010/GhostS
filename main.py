import asyncio
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
import discord.utils
from dotenv import load_dotenv
import json
import os
from datetime import datetime
import random
import sys

# Bot Setup

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True
bot = discord.Bot(command_prefix="!", intents=intents)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print(
        "Fehler: Der Bot-Token konnte nicht geladen werden. Überprüfe die .env-Datei."
    )
    exit()


with open("commands.json", "r") as f:

    categories = json.load(f)

with open("config.json", "r") as f:
    config = json.load(f)

category_permissions = {}

settings = {}
Data_File = "boost_settings.json"

settings_file = "settings.json"


def load_settings(guild_id):
    try:
        with open("settings.json", "r") as f:
            data = json.load(f)
        # Stelle sicher, dass die Struktur für den Guild existiert
        if str(guild_id) not in data:
            data[str(guild_id)] = {"custom_categories": []}
        return data[str(guild_id)]
    except FileNotFoundError:
        # Wenn die Datei nicht existiert, gib eine leere Struktur zurück
        return {"custom_categories": []}


# Funktion zum Speichern der Einstellungen in der JSON-Datei
def save_settings(guild_id, settings):
    try:
        # Lade die bestehenden Einstellungen
        with open("settings.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        # Falls die Datei nicht existiert, starte mit einer leeren Struktur
        data = {}

    # Aktualisiere die Einstellungen für den Guild
    data[str(guild_id)] = settings

    # Speichere die aktualisierten Einstellungen
    with open("settings.json", "w") as f:
        json.dump(data, f, indent=4)


def save_ticket_info(guild_id, ticket_info):
    settings = load_settings(guild_id)
    settings["tickets"] = settings.get("tickets", [])
    settings["tickets"].append(ticket_info)
    save_settings(guild_id, settings)


# Server boost
def load_data():
    try:
        with open(Data_File, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Funktion zum Speichern der Daten
def save_data(data):
    with open(Data_File, "w") as f:
        json.dump(data, f, indent=4)


boost_settings = load_data()

# Bot-Events


@bot.event
async def on_disconnect():
    print("Bot disconnected. Reconnecting in 120 seconds...")
    await asyncio.sleep(120)


# Booster
@bot.command()
@commands.has_permissions(administrator=True)
async def setboostchannel(ctx, channel: discord.TextChannel):
    """Setzt den Boost-Benachrichtigungskanal für diesen Server"""
    guild_id = str(ctx.guild.id)
    if guild_id not in boost_settings:
        boost_settings[guild_id] = {}
    boost_settings[guild_id]["channel_id"] = channel.id
    save_data(boost_settings)
    await ctx.send(f"✅ Der Boost-Kanal wurde auf {channel.mention} gesetzt!")


@bot.command()
@commands.has_permissions(administrator=True)
async def setboostrole(ctx, role: discord.Role):
    """Setzt die Booster-Rolle für diesen Server"""
    guild_id = str(ctx.guild.id)
    if guild_id not in boost_settings:
        boost_settings[guild_id] = {}
    boost_settings[guild_id]["role_id"] = role.id
    save_data(boost_settings)
    await ctx.send(f"✅ Die Booster-Rolle wurde auf `{role.name}` gesetzt!")


@bot.event
async def on_member_update(before, after):
    """Erkennt, wenn ein Benutzer boostet, und gibt ihm eine Rolle"""
    guild = after.guild
    guild_id = str(guild.id)

    if guild_id in boost_settings:
        role_id = boost_settings[guild_id].get("role_id")
        channel_id = boost_settings[guild_id].get("channel_id")

        booster_role = discord.utils.get(guild.roles, id=role_id) if role_id else None
        boost_channel = bot.get_channel(channel_id) if channel_id else None

        if before.premium_since is None and after.premium_since is not None:
            # Nutzer hat gerade geboostet
            if booster_role:
                await after.add_roles(booster_role)

            if boost_channel:
                await boost_channel.send(
                    f"🎉 {after.mention} hat den Server geboostet! Danke für deinen Support! 🚀"
                )


# Nur Booster


@bot.event
async def on_ready():
    for guild in bot.guilds:
        settings = load_settings(guild.id)

        # Synchronisiere benutzerdefinierte Kategorien
        for category_info in settings.get("custom_categories", []):
            category_name = category_info["name"]
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                # Erstelle die Kategorie, wenn sie nicht existiert
                category = await guild.create_category(name=category_name)
                print(f"Kategorie {category_name} wurde erstellt.")

        # Synchronisiere bestehende Tickets (optional)
        for ticket_info in settings.get("tickets", []):
            ticket_channel_id = ticket_info["channel_id"]
            ticket_channel = discord.utils.get(
                guild.text_channels, id=ticket_channel_id
            )
            if ticket_channel:
                print(f"Ticket-Channel {ticket_channel.name} existiert bereits.")
            else:
                print(
                    f"Ticket-Channel mit ID {ticket_channel_id} existiert nicht mehr."
                )

    print("------------------------------------")
    print(f"Bot Name: {bot.user.name}#{bot.user.discriminator}")
    print(f"Bot ID: {bot.user.id}")
    print("Discord Version: " + discord.__version__)
    print("------------------------------------")
    update_presence.start()


@tasks.loop(seconds=30)
async def update_presence():

    while True:

        await bot.change_presence(
            activity=discord.Game(
                name=f"Spielt mit {len(bot.users)} Mitgliedern | /help"
            )
        )
        await asyncio.sleep(10)
        await bot.change_presence(
            activity=discord.Streaming(
                name="Lee´s Stream", url="https://www.twitch.tv/leewhoever"
            )
        )
        await asyncio.sleep(10)
        await bot.change_presence(
            activity=discord.Game(
                name=f"Spielt mit {len(bot.commands)} Commands | /help"
            )
        )
        await asyncio.sleep(10)


@bot.event
async def send_welcome_message(member, config):
    guild_id = str(member.guild.id)
    if guild_id in config["guilds"] and config["guilds"][guild_id].get(
        "welcome_channel"
    ):
        channel_id = int(config["guilds"][guild_id]["welcome_channel"])
        channel = member.guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title="Willkommen!",
                description=f"Willkommen {member.mention} auf {member.guild.name}!",
                color=discord.Color.green(),
            )
            embed.set_thumbnail(url=member.avatar.url)
            await channel.send(embed=embed)


@bot.event
async def send_leave_message(member, config):
    guild_id = str(member.guild.id)
    if guild_id in config["guilds"] and config["guilds"][guild_id].get("leave_channel"):
        channel_id = int(config["guilds"][guild_id]["leave_channel"])
        channel = member.guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title="Auf Wiedersehen!",
                description=f"{member.mention} hat den Server verlassen.",
                color=discord.Color.red(),
            )
            embed.set_thumbnail(url=member.avatar.url)
            await channel.send(embed=embed)


# Slash-Commands


@bot.slash_command(description="Um Usern Rollen zu geben und wegzunehmen")
@commands.has_permissions(manage_roles=True)
async def roles(ctx, user: discord.Member, role: discord.Role):

    if role in user.roles:

        await user.remove_roles(role)

        embed = discord.Embed(
            title="**Rolle Entfernt**",
            description=f"Die Rolle {role} wurde dem User {user.mention} entfernt",
            colour=discord.Colour.dark_red(),
        )

    else:

        await user.add_roles(role)

        embed = discord.Embed(
            title="**Rolle verteilt**",
            description=f"Die Rolle {role} wurde dem User {user.mention} vergeben",
            colour=discord.Colour.random(),
        )

    embed.timestamp = datetime.utcnow()

    await ctx.send(embed=embed)


# Weitere Moderationsbefehle


@bot.slash_command(description="User stummschalten")
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, reason: str):

    guild = ctx.guild

    mute_role = discord.utils.get(guild.roles, name="Mute")

    if not mute_role:

        mute_role = await guild.create_role(name="Mute")

        for channel in guild.channels:

            await channel.set_permissions(
                mute_role, speak=False, send_messages=False, read_message_history=True
            )

    await member.add_roles(mute_role, reason=reason)

    embed = discord.Embed(
        title="Mute User",
        description=f'{member.mention} wurde für "{reason}" gemutet',
        color=discord.Colour.dark_red(),
    )

    await ctx.respond(embed=embed)


@bot.slash_command(description="User entmuten")
@commands.has_permissions(manage_messages=True)
async def unmute(ctx, member: discord.Member):

    mute_role = discord.utils.get(ctx.guild.roles, name="Mute")

    await member.remove_roles(mute_role)

    embed = discord.Embed(
        title="Entmutet User",
        description=f"{member.mention} wurde entmutet!",
        colour=discord.Colour.dark_red(),
    )

    await ctx.respond(embed=embed)


@bot.slash_command(description="Chat bereinigen")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, limit: int):

    await ctx.channel.purge(limit=limit)

    embed = discord.Embed(
        title="Chat Bereinigt",
        description=f"Chat wurde von {ctx.author.mention} gelöscht.",
        colour=discord.Colour.green(),
    )

    await ctx.respond(embed=embed)


@bot.slash_command(description="Den Channel locken!")
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = str):

    channel = channel or ctx.channel

    overwrite = channel.overwrites_for(ctx.guild.default_role)

    overwrite.send_messages = False

    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(
        title="Locked",
        description="Dieser Channel wurde nun gelocked!",
        colour=discord.Colour.random(),
    )

    await ctx.respond(embed=embed)


@bot.slash_command(description="Den Channel entsperren!")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None):

    channel = channel or ctx.channel

    overwrite = channel.overwrites_for(ctx.guild.default_role)

    overwrite.send_messages = True

    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(
        title="Entsperrt",
        description="Dieser Channel wurde nun gelocked!",
        colour=discord.Colour.dark_red(),
    )

    await ctx.respond(embed=embed)


@bot.command()
async def grund(ctx):

    embed = discord.Embed(
        title="Gründe", description="", colour=discord.Color.dark_red()
    )

    embed.add_field(name="Spam", value="Du hast den Channel vollgespammt", inline=False)

    embed.add_field(
        name="Rolle", value="du hast nach einer Rolle gegeiert", inline=False
    )

    await ctx.respond(embed=embed)


@bot.command(description="Um einen User zu Bannen")
@commands.has_permissions(kick_members=True)
async def kick(ctx, user: discord.Member, *, reason: str):

    await user.kick(reason=reason)

    embed = discord.Embed(
        title=f"Der User {user.mention} wurde mit dem {reason} gekickt!"
    )

    embed.set_author("SyntaxAki")

    await ctx.respond(embed=embed)


@bot.command(description="Um einen User zu bannen")
@commands.has_permissions(ban_members=True)
async def ban(ctx, user: discord.Member, *, reason: str):

    await user.ban(reason=reason)

    embed = discord.Embed(
        title=f"Der User {user} wurde mit dem {reason} gekickt!",
        description="",
        colour=discord.Color.dark_red(),
    )

    await ctx.respond(embed=embed)


@bot.command()
async def shutdown(ctx):
    """Befehl zum Beenden des Bots"""
    await ctx.send("⚠️ Der Bot wird heruntergefahren...")
    sys.exit(0)  # Beendet den Prozess sauber


@bot.command(description="Um einen User zu Entbannen")
@commands.has_permissions(ban_members=True, kick_members=True)
async def unban(ctx, *, member):

    banned_users = await ctx.guild.bans()

    member_name, member_discriminator = member.split("#")

    for ban_entry in banned_users:

        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):

            await ctx.guild.unban(user)

            e1 = discord.Embed(
                title="Entbannt",
                description=f"Der User {user.mention} wurde entbannt",
                color=discord.Color.dark_red(),
            )

            await ctx.respond(embed=e1)

            return


@unban.error
async def unban_error(ctx, error):

    if isinstance(error, commands.CheckFailure):

        await ctx.send("**You are not allowed to unban users.**")


@bot.command()
async def fight(ctx, opponent: discord.Member):

    fighters = [ctx.author, opponent]

    winner = random.choice(fighters)

    await ctx.send(f"{ctx.author.mention} Kämpft gegen {opponent.mention}!")

    if winner == ctx.author:

        await ctx.send(f"{winner.mention} is the winner!")

    else:

        await ctx.send(f"{winner.mention} emerges victorious!")


class HelpDropdown(discord.ui.Select):

    def __init__(self, ctx, user_roles):

        self.ctx = ctx

        self.user_roles = user_roles

        options = []

        for category, data in commands_data.items():

            # Check, ob der Benutzer die Berechtigung für die Kategorie hat

            if category in category_permissions:

                allowed_roles = category_permissions[category]

                if not any(role.id in allowed_roles for role in user_roles):

                    continue

            options.append(
                discord.SelectOption(label=category, description=data["description"])
            )

        if not options:

            options.append(
                discord.SelectOption(
                    label="Keine Kategorien verfügbar",
                    description="Du hast keine Berechtigungen für Befehle.",
                )
            )

        super().__init__(placeholder="Kategorie auswählen...", options=options)

    async def callback(self, interaction: discord.Interaction):

        category = self.values[0]

        if category not in commands_data:

            await interaction.response.send_message(
                "Kategorie nicht gefunden.", ephemeral=True
            )

            return

        # Zeige die Befehle der Kategorie

        commands_list = "\n".join(commands_data[category]["commands"])

        await interaction.response.send_message(
            f"**{category}**\n{commands_list}", ephemeral=True
        )


# View mit Dropdown


class HelpView(discord.ui.View):

    def __init__(self, ctx, user_roles):

        super().__init__()

        self.add_item(HelpDropdown(ctx, user_roles))


# Help Command


@bot.command()
async def help(ctx):

    user_roles = ctx.author.roles

    view = HelpView(ctx, user_roles)

    await ctx.send("Wähle eine Kategorie:", view=view)


# Command, um Rechte für eine Kategorie zu setzen


@bot.command()
@commands.has_permissions(administrator=True)
async def set_permission(ctx, category: str, role: discord.Role):

    if category not in commands_data:

        await ctx.send("Kategorie nicht gefunden.")

        return

    if category not in category_permissions:

        category_permissions[category] = []

    category_permissions[category].append(role.id)

    await ctx.send(f"Rolle {role.name} wurde für die Kategorie {category} hinzugefügt.")


# Command, um Rechte für eine Kategorie zu entfernen


@bot.command()
@commands.has_permissions(administrator=True)
async def remove_permission(ctx, category: str, role: discord.Role):

    if (
        category not in category_permissions
        or role.id not in category_permissions[category]
    ):

        await ctx.send("Die Rolle hat keine Berechtigung für diese Kategorie.")

        return

    category_permissions[category].remove(role.id)

    await ctx.send(f"Rolle {role.name} wurde aus der Kategorie {category} entfernt.")


# Fehlermeldung bei fehlenden Rechten


@help.error
@set_permission.error
@remove_permission.error
async def permission_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):

        await ctx.send("Du hast keine Berechtigung, diesen Befehl auszuführen.")

    else:

        raise error


class TicketSelect(discord.ui.Select):

    def __init__(self, categories):

        options = [
            discord.SelectOption(label=category, value=category)
            for category in categories
        ]

        super().__init__(
            placeholder="Wähle eine Kategorie für dein Ticket", options=options
        )

    async def callback(self, interaction: discord.Interaction):

        # Hole die gewählte Kategorie

        selected_category = self.values[0]

        guild = interaction.guild

        user = interaction.user

        # Kategorie im Server finden

        category_channel = discord.utils.get(guild.categories, name=selected_category)

        if not category_channel:

            await interaction.response.send_message(
                f"Die Kategorie `{selected_category}` existiert nicht auf dem Server.",
                ephemeral=True,
            )

            return

        # Prüfen, ob der Nutzer bereits ein Ticket hat

        existing_channel = discord.utils.get(
            category_channel.text_channels, name=f"ticket-{user.name}"
        )

        if existing_channel:

            await interaction.response.send_message(
                f"Du hast bereits ein Ticket: {existing_channel.mention}",
                ephemeral=True,
            )

            return

        # Berechtigungen für das Ticket festlegen

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        # Ticket-Kanal erstellen

        ticket_channel = await category_channel.create_text_channel(
            name=f"ticket-{user.name}", overwrites=overwrites
        )

        await ticket_channel.send(
            f"Hallo {user.mention}, ein Teammitglied wird dir bald helfen!"
        )

        await interaction.response.send_message(
            f"Dein Ticket wurde erstellt: {ticket_channel.mention}", ephemeral=True
        )


# View für das Dropdown-Menü


class TicketView(discord.ui.View):

    def __init__(self, categories):

        super().__init__()

        self.add_item(TicketSelect(categories))


# Close Ticket Button


class CloseTicketButton(View):

    def __init__(self):

        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket schließen", style=discord.ButtonStyle.red)
    async def close_ticket(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):

        ticket_channel = interaction.channel

        if ticket_channel.category and ticket_channel.category.name == "Tickets":

            # Rechte des Ticket-Channel entfernen

            overwrites = ticket_channel.overwrites

            for role in ticket_channel.guild.roles:

                if role.name != "@everyone":

                    await ticket_channel.set_permissions(
                        role, read_messages=False, send_messages=False
                    )

            user = interaction.user

            archive_category = discord.utils.get(
                interaction.guild.categories, id=settings.get("archive_category")
            )

            if not archive_category:

                await interaction.response.send_message(
                    "Das Archiv ist nicht eingerichtet!", ephemeral=True
                )

                return

            # Ticket in das Archiv verschieben und schließen

            await ticket_channel.edit(
                category=archive_category, name=f"archiv-{user.name}"
            )

            await ticket_channel.send(
                f"{user.mention}, dein Ticket wurde geschlossen und archiviert."
            )

            await interaction.response.send_message(
                "Das Ticket wurde erfolgreich geschlossen.", ephemeral=True
            )


@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    categories = ctx.guild.categories
    roles = ctx.guild.roles

    # Sicherstellen, dass Kategorien und Rollen vorhanden sind
    if not categories:
        await ctx.send(
            "Es gibt keine Kategorien auf diesem Server. Bitte erstelle eine Kategorie."
        )
        return

    if not roles:
        await ctx.send(
            "Es gibt keine Rollen auf diesem Server. Bitte erstelle eine Rolle."
        )
        return

    # Auswahl der Ticket-Kategorie
    ticket_select = discord.ui.Select(
        placeholder="Wähle eine Kategorie für Tickets",
        options=[
            discord.SelectOption(label=category.name, value=str(category.id))
            for category in categories
        ],
    )

    # Auswahl der Archiv-Kategorie
    archive_select = discord.ui.Select(
        placeholder="Wähle eine Archiv-Kategorie",
        options=[
            discord.SelectOption(label=category.name, value=str(category.id))
            for category in categories
        ],
    )

    # Auswahl der Support-Rolle
    role_select = discord.ui.Select(
        placeholder="Wähle eine Support-Rolle",
        options=[
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in roles
            if not role.is_bot_managed()
        ],
    )

    # Callback-Funktion für das Setup
    async def setup_callback(interaction: discord.Interaction):
        print(f"Interaktion empfangen: {interaction.user.name}")

        # Überprüfen, ob der Autor der Befehlsersteller ist
        if interaction.user != ctx.author:
            await interaction.response.send_message(
                "Nur der Admin kann diese Aktion ausführen.", ephemeral=True
            )
            return

        # Überprüfen, ob alle Optionen ausgewählt wurden
        if (
            not ticket_select.values
            or not archive_select.values
            or not role_select.values
        ):
            await interaction.response.send_message(
                "Du musst alle Optionen auswählen!", ephemeral=True
            )
            return

        # Die ausgewählten Kategorien und Rollen holen
        selected_ticket_category = discord.utils.get(
            ctx.guild.categories, id=int(ticket_select.values[0])
        )
        selected_archive_category = discord.utils.get(
            ctx.guild.categories, id=int(archive_select.values[0])
        )
        selected_role = discord.utils.get(
            ctx.guild.roles, id=int(role_select.values[0])
        )

        # Einstellungen speichern
        settings = {
            "ticket_category": selected_ticket_category.id,
            "archive_category": selected_archive_category.id,
            "support_role": selected_role.id,
        }

        # Einstellungen speichern
        save_settings(ctx.guild.id, settings)
        await interaction.response.send_message(
            "Die Einstellungen für das Ticketsystem wurden erfolgreich gespeichert!",
            ephemeral=True,
        )

    # View erstellen und die Items (Selects) hinzufügen
    view = discord.ui.View()
    view.add_item(ticket_select)
    view.add_item(archive_select)
    view.add_item(role_select)

    # Callback für die View setzen
    view.on_timeout = lambda: print(
        "View-Timer abgelaufen"
    )  # Debugging, falls der Timeout auftritt
    ticket_select.callback = setup_callback
    archive_select.callback = setup_callback
    role_select.callback = setup_callback

    # Nachricht mit View senden
    await ctx.send("Bitte wähle die benötigten Optionen aus:", view=view)


# Ticket-Befehl
# Befehl zum Erstellen eines Tickets
@bot.command()
async def ticket(ctx):
    settings = load_settings(ctx.guild.id)
    categories = settings.get("custom_categories", [])

    ticket_category_id = settings.get("ticket_category")
    support_role_id = settings.get("support_role")
    archive_category_id = settings.get("archive_category")
    custom_categories = settings.get("custom_categories", [])

    if not ticket_category_id or not support_role_id:
        await ctx.send(
            "Das Ticketsystem wurde noch nicht eingerichtet. Bitte führe zuerst `/setup` aus."
        )
        return

    ticket_category = discord.utils.get(ctx.guild.categories, id=ticket_category_id)
    support_role = discord.utils.get(ctx.guild.roles, id=support_role_id)
    archive_category = discord.utils.get(ctx.guild.categories, id=archive_category_id)

    if not ticket_category or not support_role:
        await ctx.send(
            "Die Standard-Ticket-Kategorie oder die Support-Rolle existiert nicht mehr."
        )
        return

    if not categories:
        await ctx.send("Es gibt keine verfügbaren Kategorien. Bitte füge eine hinzu.")
        return

    # Ticket Select erstellen
    ticket_select = discord.ui.Select(
        placeholder="Wähle eine Kategorie für dein Ticket",
        options=[
            discord.SelectOption(label=category["name"], value=category["name"])
            for category in categories
        ],
    )

    async def ticket_callback(interaction: discord.Interaction):
        selected_category_name = ticket_select.values[0]
        selected_category = discord.utils.get(
            ctx.guild.categories, name=selected_category_name
        )

        if selected_category:
            # Erstelle den Ticket-Channel in der ausgewählten Kategorie
            ticket_channel = await ctx.guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=ticket_category,
                overwrites={
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    ),
                    interaction.user: discord.PermissionOverwrite(read_messages=True),
                },
            )

            # Speichern der Ticket-Informationen
            ticket_info = {
                "channel_id": ticket_channel.id,
                "user_id": interaction.user.id,
                "category": selected_category_name,
            }
            save_ticket_info(ctx.guild.id, ticket_info)

            await ticket_channel.send(
                f"Hallo {interaction.user.mention}, dein Ticket wurde eröffnet!"
            )
            await interaction.response.send_message(
                f"Dein Ticket wurde im Channel {ticket_channel.mention} eröffnet.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Die ausgewählte Kategorie existiert nicht.", ephemeral=True
            )

    view = discord.ui.View()
    view.add_item(ticket_select)
    ticket_select.callback = ticket_callback

    await ctx.send(
        "Bitte wähle eine Kategorie aus, um dein Ticket zu eröffnen:", view=view
    )


@bot.command()
async def close_ticket(ctx):
    # Holen der gespeicherten Ticket- und Archiv-Kategorie aus den Einstellungen
    settings = load_settings(ctx.guild.id)
    ticket_category_id = settings.get("ticket_category")
    archive_category_id = settings.get("archive_category")

    if not ticket_category_id or not archive_category_id:
        await ctx.send(
            "Das Ticketsystem ist noch nicht eingerichtet. Bitte führe den Setup-Befehl aus."
        )
        return

    ticket_category = discord.utils.get(ctx.guild.categories, id=ticket_category_id)
    archive_category = discord.utils.get(ctx.guild.categories, id=archive_category_id)

    if not ticket_category or not archive_category:
        await ctx.send("Fehlende Kategorien. Bitte richte die Kategorien korrekt ein.")
        return

    # Sicherstellen, dass der Befehl nur im Ticket-Kanal ausgeführt wird
    if ctx.channel.category != ticket_category:
        await ctx.send(
            "Dieser Befehl kann nur in einem Ticket-Kanal ausgeführt werden."
        )
        return

    # Ticket umbenennen und in die Archiv-Kategorie verschieben
    new_name = f"geschlossen-{ctx.channel.name}"
    await ctx.channel.edit(name=new_name, category=archive_category)

    # Nachricht, dass das Ticket geschlossen wurde
    await ctx.send(f"Das Ticket wurde geschlossen und ins Archiv verschoben.")

    # Warten und Ticket nach 1 Minute löschen, falls noch im Archiv
    await asyncio.sleep(60)
    if (
        ctx.channel.category == archive_category
    ):  # Nur löschen, wenn der Kanal im Archiv ist
        try:
            await ctx.channel.delete(
                reason="Ticket wurde geschlossen und automatisch gelöscht."
            )
        except discord.NotFound:
            pass  # Kanal wurde möglicherweise manuell gelöscht
        except discord.Forbidden:
            print(
                f"Fehlende Berechtigungen, um den Kanal {ctx.channel.name} zu löschen."
            )


@bot.command()
@commands.has_permissions(administrator=True)
async def add_category(ctx, category_name: str):
    """Erstellt eine neue Kategorie und speichert sie in den Einstellungen des Guilds."""
    guild = ctx.guild

    # Überprüfen, ob die Kategorie bereits existiert
    existing_category = discord.utils.get(guild.categories, name=category_name)
    if existing_category:
        await ctx.send(f"Die Kategorie '{category_name}' existiert bereits.")
        return

    # Erstelle die neue Kategorie
    new_category = await guild.create_category(category_name)

    # Lade die Einstellungen für den Guild
    settings = load_settings(guild.id)

    # Füge die neue Kategorie hinzu
    custom_categories = settings.get("custom_categories", [])
    custom_categories.append({"id": new_category.id, "name": category_name})
    settings["custom_categories"] = custom_categories

    # Speichere die aktualisierten Einstellungen
    save_settings(guild.id, settings)

    await ctx.send(f"Die Kategorie '{category_name}' wurde erfolgreich hinzugefügt.")


@bot.command()
@commands.has_permissions(administrator=True)
async def remove_category(ctx, category_name: str):
    """Entfernt eine benutzerdefinierte Kategorie aus den Einstellungen"""

    guild_id = ctx.guild.id
    settings = load_settings(guild_id)

    # Überprüfen, ob "custom_categories" in den Einstellungen existiert
    if "custom_categories" not in settings:
        await ctx.send("Es gibt keine benutzerdefinierten Kategorien zum Entfernen.")
        return

    custom_categories = settings["custom_categories"]

    # Überprüfen, ob die Kategorie existiert
    category_to_remove = None
    for category in custom_categories:
        if category["name"].lower() == category_name.lower():
            category_to_remove = category
            break

    if not category_to_remove:
        await ctx.send(f"Die Kategorie '{category_name}' wurde nicht gefunden.")
        return

    # Entferne die Kategorie aus der Liste der benutzerdefinierten Kategorien
    custom_categories.remove(category_to_remove)

    # Speichern der geänderten Einstellungen
    settings["custom_categories"] = custom_categories
    save_settings(guild_id, settings)

    await ctx.send(f"Die Kategorie '{category_name}' wurde erfolgreich entfernt.")


@bot.command()
async def clean_categories(ctx):
    guild_id = ctx.guild.id
    settings = load_settings(guild_id)  # Lade die gespeicherten Einstellungen
    if "categories" in settings:
        categories = settings["categories"]

        # Holen der vorhandenen Kategorien im Server
        guild_categories = [category.name for category in ctx.guild.categories]

        # Filtere alle Kategorien, die nicht im Server existieren
        categories_to_remove = [
            category
            for category in categories
            if category["name"] not in guild_categories
        ]

        # Entferne die ungültigen Kategorien
        for category in categories_to_remove:
            categories.remove(category)

        # Speichere die aktualisierte Liste zurück in die JSON-Datei
        save_settings(guild_id, settings)

        if categories_to_remove:
            await ctx.send(
                f"Die folgenden Kategorien wurden entfernt: {', '.join([category['name'] for category in categories_to_remove])}"
            )
        else:
            await ctx.send("Es wurden keine ungültigen Kategorien gefunden.")
    else:
        await ctx.send("Es gibt keine gespeicherten Kategorien.")


@bot.command()
async def show_categories(ctx):
    settings = load_settings(ctx.guild.id)
    categories = settings.get("categories", [])
    await ctx.send(f"Verfügbare Kategorien: {', '.join(categories)}")


#################################################################################


bot.run(TOKEN)
