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
user_details_dict = {}

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
def send_to_openttd_admin(message, send_type, client_id=None):
    try:
        with Admin(ip=SERVER, port=PORT, name=f"{BOT_NAME} Sender", password=PASSWORD) as admin:
            if send_type == 'global':
                admin.send_global(message)
            if send_type == 'rcon':
                admin.send_rcon(message)
            if send_type == 'private':
                if client_id is None:
                    raise ValueError("client_id is required for private messages.")
                admin.send_private(message, client_id)
    except Exception as e:
        print(f"An error occurred: {e}")
        # Handle the error appropriately

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

# Processes user details from console packets and creates a dict filled ith active players
def process_user_packet(packet):
    global user_details_dict


    join_pattern = r'\[server\] Client #(\d+) \(([\d\.]+)\) joined as ([\w\s#]+)'
    leave_pattern = r'\[server\] Client #(\d+) closed connection'
    name_change_pattern = r'\*\*\* ([\w\s#]+) has changed their name to ([\w\s#]+)'

    # Join Match
    join_match = re.search(join_pattern, packet.message)
    if join_match:
        client_id = join_match.group(1)
        client_ip = join_match.group(2)
        client_name = join_match.group(3)

        # Update user details dictionary with joined client
        user_details_dict[client_id] = {'client_ip': client_ip, 'client_name': client_name}

    # Leave Match
    leave_match = re.search(leave_pattern, packet.message)
    if leave_match:
        client_id = leave_match.group(1)

        # Remove client from user details dictionary if exists
        if client_id in user_details_dict:
            del user_details_dict[client_id]

    # Name Change Match
    name_change_match = re.search(name_change_pattern, packet.message)
    if name_change_match:
        old_name = name_change_match.group(1)
        new_name = name_change_match.group(2)


        #print("Name change detected - Old name:", old_name)
        #print("Name change detected - New name:", new_name)

        # Update user details dictionary with new name
        #print("Before update:", user_details_dict)
        for client_id, details in user_details_dict.items():
            #print("Checking client:", client_id, details['client_name'])
            if details['client_name'] == old_name:
                details['client_name'] = new_name
                break
        #print("After update:", user_details_dict)


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
                                                                message=f'{get_client_info(client_id=packet.id, key='client_name')} ({packet.id}) {packet.message}'),
                                         bot.loop)

def process_console_packet(packet):

    # If logging is enable post console messages to discord (rate limiting can happen so be careful with this)
    if LOG_CONSOLE_TO_DISCORD == 'enabled':
        asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=CHANNEL_LOG_MESSAGES,
                                                                message=packet.message),
                                         bot.loop)

def process_rcon_packet(packet):
    print(f'Rcon Packet: {packet}')
    asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=CHANNEL_BOT_COMMANDS,
                                                            message=packet.response),
                                     bot.loop)
# Retrieves data from the user client dict and allows us to grab users name id or ip
def get_client_info(client_id, key):
    global user_details_dict
    client_id_str = str(client_id)
    if client_id_str in user_details_dict:
        return user_details_dict[client_id_str].get(key)
    return None  # Return None if client ID is not found




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
                    # Capture Rcon Packets
                    if isinstance(packet, openttdpacket.RconPacket):
                        print(packet)
                        process_rcon_packet(packet)
                    # Capture console packets
                    elif isinstance(packet, openttdpacket.ConsolePacket):
                        process_user_packet(packet)
                        process_console_packet(packet)





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

    @commands.command(name='ping', hidden=False)
    async def ping(self, ctx):
        # Only run command if it's in the channel we want.
        if ctx.channel.id == CHANNEL_BOT_COMMANDS:
            server_name = serverdetails_dict['server_name'][0]

            await ctx.send('Yes, I\'m Alive...')

    @commands.command(name='rcon', hidden=False)
    async def rcon(self, ctx, message):
        # Only run command in the channel we want
        if ctx.channel.id == CHANNEL_BOT_COMMANDS:
            # Sends an rcon command, any rcon recieved will be sent to the designated channel in the OpenTTD recieve loop
            send_to_openttd_admin(message=message, send_type='rcon')


    @commands.command(name='clients', hidden=False)
    async def clients(self, ctx):
        # Only run command in the channel we want
        if ctx.channel.id == CHANNEL_BOT_COMMANDS:
            await ctx.send(user_details_dict)


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
