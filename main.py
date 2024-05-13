import discord
from discord.ext import commands
from pyopenttdadmin import Admin, AdminUpdateType, openttdpacket
import threading
import asyncio
import re
import configparser

# Read config from file
def load_config():
    config = configparser.ConfigParser()
    config.read("config.txt")
    return config

# Load configuration
config = load_config()

# Define our Config Definitions

# [ModTrack] Config
BOT_NAME = config.get(section='ModTrack', option='BOT_NAME')
BOT_DESCRIPTION = config.get(section='ModTrack', option='BOT_DESCRIPTION')
BOT_PREFIX = config.get(section='ModTrack', option='BOT_PREFIX')
LOG_CONSOLE_TO_DISCORD = config.get(section='ModTrack', option='LOG_CONSOLE_TO_DISCORD')


# [OpenTTDAdmin] Config
SERVER = config.get(section='OpenTTDAdmin', option='SERVER')
PORT = int(config.get(section='OpenTTDAdmin', option='PORT'))
PASSWORD = config.get(section='OpenTTDAdmin', option='PASSWORD')

# [Discord] Config
TOKEN = config.get(section='Discord', option='TOKEN')
BOT_ID_ON_DISCORD = int(config.get(section='Discord', option='BOT_ID_ON_DISCORD'))
DISCORD_ADMIN_ROLE_ID = int(config.get(section='Discord', option='DISCORD_ADMIN_ROLE_ID'))

# Channel declarations
CHANNEL_ADMIN_REQUEST = int(config.get(section='Discord', option='CHANNEL_ADMIN_REQUEST'))
CHANNEL_CHAT_MESSAGES = int(config.get(section='Discord', option='CHANNEL_CHAT_MESSAGES'))
CHANNEL_BOT_COMMANDS = int(config.get(section='Discord', option='CHANNEL_BOT_COMMANDS'))
CHANNEL_LOG_MESSAGES = int(config.get(section='Discord', option='CHANNEL_LOG_MESSAGES'))


# Function to get prefix
def get_prefix(bot, message):
    prefixes = [BOT_PREFIX]
    if not message.guild:
        return '?'
    return commands.when_mentioned_or(*prefixes)(bot, message)

# Discord bot setup
Intents = discord.Intents.default()
Intents.message_content = True
bot = commands.Bot(command_prefix=get_prefix, description=BOT_DESCRIPTION, intents=Intents)



# Function to send message to Discord channel
async def send_to_discord_channel(channel_id, message):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)
    else:
        print(f"Channel with ID {channel_id} not found.")

# Function to send message to OpenTTD admin port
def send_to_openttd_admin(message, send_type):
    try:
        with Admin(ip=SERVER, port=PORT, name=f"{BOT_NAME} Sender", password=PASSWORD) as admin:
            if send_type == 'global':
                admin.send_global(message)
            if send_type == 'rcon':
                admin.send_rcon(message)
    except Exception as e:
        print(f"An error occurred while sending message to OpenTTD admin port: {e}")

# Listener Thread, This is the main loop where we'll monitor for packets comming from OpenTTD
def openTTD_listener_thread():
    try:
        with Admin(ip=SERVER, port=PORT, name=f"{BOT_NAME} Listener", password=PASSWORD) as admin:
            admin.send_subscribe(AdminUpdateType.CHAT)
            admin.send_subscribe(AdminUpdateType.CONSOLE)
            admin.send_subscribe(AdminUpdateType.CLIENT_INFO)
            #admin.send_subscribe(AdminUpdateType.COMPANY_INFO)
            #admin.send_subscribe(AdminUpdateType.COMPANY_ECONOMY)
            #admin.send_subscribe(AdminUpdateType.COMPANY_STATS)
            while True:
                packets = admin.recv()
                for packet in packets:

                    # Capture Chat Packets from OpenTTD
                    if isinstance(packet, openttdpacket.ChatPacket):

                        # If BOT_PREFIX is start of string it's a command
                        if packet.message.startswith(BOT_PREFIX):
                            # Report/admin command, sends user report over to bot.py for processing on discord.
                            packet.message = packet.message.replace(BOT_PREFIX, '') # remove the command symbol

                            if packet.message.startswith(('report', 'admin')):
                                # Define the regex pattern to remove command from message
                                pattern = r'^(?:!help|!admin)\s*'
                                message = re.sub(pattern, '', packet.message)
                                asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=CHANNEL_ADMIN_REQUEST, message=f"<@&{DISCORD_ADMIN_ROLE_ID}> ID: {packet.id} Message: {message}", ), bot.loop)
                        else:
                            # Send chat message to discord
                            asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=CHANNEL_CHAT_MESSAGES, message=packet.message, ), bot.loop)


                        # Capture console packets
                    if isinstance(packet, openttdpacket.ConsolePacket):
                        if LOG_CONSOLE_TO_DISCORD == 'enabled':
                            asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=CHANNEL_LOG_MESSAGES, message=packet.message, ), bot.loop)

                        # Print Stuff
                    if isinstance(packet, openttdpacket.ClientInfoPacket):
                        print(f'Client Info Packet:  {packet}')

                    if isinstance(packet, openttdpacket.RconPacket):
                        print(f'Rcon Packet: {packet}')
                        asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=CHANNEL_BOT_COMMANDS, message=packet.message, ), bot.loop)



    except Exception as e:
        print(f"An error occurred in openTTD_listener: {e}")

# Define cog and command
class OpenTTDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Example command just to test in discord
    @commands.command(name='ping', hidden=False)
    async def ping(self, ctx):
        # Only run command if it's in the channel we want.
        if ctx.channel.id == CHANNEL_BOT_COMMANDS:
            await ctx.send('Yes, I\'m Alive...')

    @commands.command(name='rcon', hidden=False)
    async def rcon(self, ctx, message):
        # Only run command in the channel we want
        if ctx.channel.id == CHANNEL_BOT_COMMANDS:
            # Sends an rcon command, any rcon recieved will be sent to the designated channel in the OpenTTD recieve loop
            send_to_openttd_admin(message=message, send_type='rcon')

# Load cog
@bot.event
async def on_ready():
    await bot.add_cog(OpenTTDCog(bot))
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    message = 'Bot Connected'
    channel = bot.get_channel(CHANNEL_LOG_MESSAGES)
    await channel.send(message)
    print(f'Successfully logged in and booted...!')

# Discord Events, Allows us to do things like capture messages from a channel to send to OpenTTD
# IE, Chat
@bot.event
async def on_message(message):
    # IF the channel of the message matches our channel ID, we'll continue.
    if message.channel.id == CHANNEL_CHAT_MESSAGES:
        # We don't want to echo what our bot says, let's ensure we ignore messages posted by ourselves
        if BOT_ID_ON_DISCORD != message.author.id:
            send_to_openttd_admin(message=f"[Discord] {message.author}: {message.content}", send_type='global')

    await bot.process_commands(message)


# Start OpenTTD admin listener thread
openTTD_thread = threading.Thread(target=openTTD_listener_thread)
openTTD_thread.daemon = True
openTTD_thread.start()

# Start Discord bot
bot.run(TOKEN, reconnect=True)
