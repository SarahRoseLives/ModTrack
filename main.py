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

# Layout Dicts To Facilitate Running Information
serverdetails_dict = {}

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

def process_welcome_packet(packet):
    global serverdetails_dict  # Declare that we're going to modify the global variable

    # Create a new dictionary to store packet data with specific keys
    packet_data = {
        'server_name': packet.server_name,
        'version': packet.version,
        'map_name': packet.map_name,
        'seed': packet.seed,
        'mapwidth': packet.mapwidth,
        'mapheight': packet.mapheight,
        'startdate': packet.startdate,
        'landscape': packet.landscape
    }

    # Add the packet data to the serverdetails_dict
    for key, value in packet_data.items():
        if key not in serverdetails_dict:
            serverdetails_dict[key] = [value]
        else:
            serverdetails_dict[key].append(value)

    asyncio.run_coroutine_threadsafe(
        send_to_discord_channel(
            channel_id=CHANNEL_LOG_MESSAGES,
            message=packet.server_name
        ),
        bot.loop
    )
    
def process_chat_packet(packet):
    if packet.message.startswith(BOT_PREFIX):
        # Report/admin command, sends user report over to bot.py for processing on discord.
        packet.message = packet.message.replace(BOT_PREFIX, '')  # remove the command symbol

        if packet.message.startswith(('report', 'admin')):
            # Define the regex pattern to remove command from message
            pattern = r'^(?:!help|!admin)\s*'
            message = re.sub(pattern, '', packet.message)
            asyncio.run_coroutine_threadsafe(
                send_to_discord_channel(channel_id=CHANNEL_ADMIN_REQUEST,
                                        message=f"<@&{DISCORD_ADMIN_ROLE_ID}> ID: {packet.id} Message: {message}"),
                bot.loop)
    else:
        # Send chat message to discord
        asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=CHANNEL_CHAT_MESSAGES,
                                                                message=packet.message),
                                         bot.loop)

def process_console_packet(packet):
    if LOG_CONSOLE_TO_DISCORD == 'enabled':
        asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=CHANNEL_LOG_MESSAGES,
                                                                message=packet.message),
                                         bot.loop)

def process_rcon_packet(packet):
    print(f'Rcon Packet: {packet}')
    asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=CHANNEL_BOT_COMMANDS,
                                                            message=packet.message),
                                     bot.loop)

def openTTD_listener_thread():
    try:
        with Admin(ip=SERVER, port=PORT, name=f"{BOT_NAME} Listener", password=PASSWORD) as admin:
            admin.send_subscribe(AdminUpdateType.CHAT)
            admin.send_subscribe(AdminUpdateType.CONSOLE)
            admin.send_subscribe(AdminUpdateType.CLIENT_INFO)

            while True:
                packets = admin.recv()
                for packet in packets:
                    # Capture Welcome Packets from OpenTTD
                    if isinstance(packet, openttdpacket.WelcomePacket):
                        process_welcome_packet(packet)
                    # Capture Chat Packets from OpenTTD
                    if isinstance(packet, openttdpacket.ChatPacket):
                        process_chat_packet(packet)

                    # Capture console packets
                    elif isinstance(packet, openttdpacket.ConsolePacket):
                        process_console_packet(packet)

                    # Capture Rcon packets
                    elif isinstance(packet, openttdpacket.RconPacket):
                        process_rcon_packet(packet)

                    # Add more packet processing functions for other packet types if needed

    except Exception as e:
        # Handle exceptions gracefully
        print(f"An error occurred: {e}")


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

    server_name = serverdetails_dict['server_name'][0]
    server_version = serverdetails_dict['version'][0]
    message = f"{BOT_NAME} With Command Prefix {BOT_PREFIX} has connected to {server_name} version {server_version}"
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
