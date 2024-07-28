import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='?', intents=intents)

# Canale per i log
log_channel_id = id_log # sostituisci con l'ID del canale dei log

# File di log
log_file = "ticket_logs.txt"

# Funzione per loggare i messaggi
def log_message(message):
    with open(log_file, "a") as f:
        f.write(f"{datetime.datetime.now()} - {message}\n")

async def send_log_message(message):
    channel = bot.get_channel(log_channel_id)
    if channel:
        await channel.send(message)
    log_message(message)

@bot.event
async def on_ready():
    print(f'Bot è pronto. Connesso come {bot.user}')
    # Sincronizza i comandi di applicazione (slash commands)
    await bot.tree.sync()

# View per i pulsanti del ticket
class TicketView(discord.ui.View):
    def __init__(self, member: discord.Member, *, timeout=180):
        super().__init__(timeout=timeout)
        self.member = member

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)

    @discord.ui.button(label="Reclama", style=discord.ButtonStyle.primary, custom_id="reclama")
    async def claim_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Esecuzione del comando /reclama...", ephemeral=True)
        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        await reclama(ctx)

    @discord.ui.button(label="Chiudi", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Esecuzione del comando /close...", ephemeral=True)
        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        await close(ctx)

# Comando per reclamare il ticket
@bot.command()
async def reclama(ctx):
    await reclama_command(ctx)

@bot.tree.command(name="reclama", description="Reclama un ticket")
async def reclama_command(interaction: discord.Interaction):
    ticket_channel = interaction.channel
    claimed_by = interaction.user
    admin_role = discord.utils.get(interaction.guild.roles, name="1258130322143449138")

    if admin_role not in claimed_by.roles:
        await interaction.response.send_message("Solo un amministratore può reclamare il ticket.", ephemeral=True)
        return

    await ticket_channel.set_permissions(claimed_by, read_messages=True, send_messages=True)
    await interaction.response.send_message(f'Ticket reclamato da {claimed_by.mention}')
    await ticket_channel.send(f'Ticket reclamato da {claimed_by.mention}')
    await send_log_message(f'Ticket {ticket_channel.name} reclamato da {claimed_by.name}')

# Comando per aprire un ticket
@bot.command()
async def ticket(ctx):
    await ticket_command(ctx)

@bot.tree.command(name="ticket", description="Crea un ticket")
async def ticket_command(interaction: discord.Interaction):
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="Tickets")

    if not category:
        category = await guild.create_category("Tickets")

    ticket_channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category)

    await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False)
    await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

    view = TicketView(interaction.user)
    message = await ticket_channel.send(f"Benvenuto {interaction.user.mention} nel ticket! Aspetta uno staffer che le risponderà il prima possibile. I tempi di attesa possono durare 3/4 ore. @everyone", view=view)
    view.message = message

    await send_log_message(f'Ticket creato: {ticket_channel.name} da {interaction.user.name}')

    await interaction.response.send_message(f'Ticket creato: {ticket_channel.mention}', ephemeral=True)

# Comando per chiudere il ticket e inviare la trascrizione
@bot.command()
async def close(ctx, delay: int = 3):
    await close_command(ctx, delay)

@bot.tree.command(name="close", description="Chiudi un ticket")
@app_commands.describe(delay="Tempo in secondi prima della chiusura del ticket")
async def close_command(interaction: discord.Interaction, delay: int = 3):
    if "ticket-" in interaction.channel.name:
        if delay > 3:
            await interaction.response.send_message(f'Questo ticket sarà chiuso tra {delay} secondi.')
            await asyncio.sleep(delay)
        await interaction.response.send_message(f'Ticket {interaction.channel.name} sarà chiuso.')
        await send_log_message(f'Ticket {interaction.channel.name} chiuso da {interaction.user.name}')
        await interaction.channel.delete()
    else:
        await interaction.response.send_message('Questo comando può essere usato solo in un canale ticket.', ephemeral=True)

# Comando chi_sono
@bot.command()
async def chi_sono(ctx):
    await chi_sono_command(ctx)

@bot.tree.command(name="chi_sono", description="Informazioni sul bot")
async def chi_sono_command(interaction: discord.Interaction):
    await interaction.response.send_message("Bot creato da Pietr YT", ephemeral=True)


# Comando per rinominare il ticket
@bot.command()
async def rinomina(ctx, *, nuovo_nome: str):
    await rinomina_command(ctx, nuovo_nome)

@bot.tree.command(name="rinomina", description="Rinomina un ticket")
@app_commands.describe(nuovo_nome="Il nuovo nome per il ticket")
async def rinomina_command(interaction: discord.Interaction, nuovo_nome: str):
    ticket_channel = interaction.channel
    if "ticket-" in ticket_channel.name:
        old_name = ticket_channel.name
        await ticket_channel.edit(name=nuovo_nome)
        await interaction.response.send_message(f'Ticket rinominato da {old_name} a {nuovo_nome}')
        await send_log_message(f'Ticket rinominato da {old_name} a {nuovo_nome} da {interaction.user.name}')
    else:
        await interaction.response.send_message('Questo comando può essere usato solo in un canale ticket.', ephemeral=True)

bot.run('token')
