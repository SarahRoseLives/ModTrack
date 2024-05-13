import discord
from discord.ext import commands
from pyopenttdadmin import Admin, AdminUpdateType, openttdpacket
import threading
import asyncio
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



# [OpenTTDAdmin] Config
SERVER = config.get(section='OpenTTDAdmin', option='SERVER')
PORT = int(config.get(section='OpenTTDAdmin', option='PORT'))
PASSWORD = config.get(section='OpenTTDAdmin', option='PASSWORD')

# [Discord] Config
discordtoken = config.get(section='Discord', option='token')
bot_id_on_discord = int(config.get(section='Discord', option='bot_id_on_discord'))
discord_admin_role_id = int(config.get(section='Discord', option='discord_admin_role_id'))

# Channel declarations
channel_admin_request = int(config.get(section='Discord', option='channel_admin_request'))
channel_chat_messages = int(config.get(section='Discord', option='channel_chat_messsages'))
channel_bot_commands = int(config.get(section='Discord', option='channel_bot_commands'))
channel_log_messages = int(config.get(section='Discord', option='channel_log_messages'))


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
def send_to_openttd_admin(message):
    try:
        with Admin(ip=SERVER, port=PORT, name=f"{BOT_NAME} Sender", password=PASSWORD) as admin:
            admin.send_global(message)
    except Exception as e:
        print(f"An error occurred while sending message to OpenTTD admin port: {e}")

# Listener Thread, This is the main loop where we'll monitor for packets comming from OpenTTD
def openTTD_listener_thread():
    try:
        with Admin(ip=SERVER, port=PORT, name=f"{BOT_NAME} Listener", password=PASSWORD) as admin:
            admin.send_subscribe(AdminUpdateType.CHAT)
            while True:
                packets = admin.recv()
                for packet in packets:
                    if isinstance(packet, openttdpacket.ChatPacket):
                        print(f'ID: {packet.id} Message: {packet.message}')
                        asyncio.run_coroutine_threadsafe(send_to_discord_channel(channel_id=channel_chat_messages, message=packet.message, ), bot.loop)
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
        if ctx.channel.id == channel_bot_commands:
            await ctx.send('Yes, I\'m Alive...')

# Load cog
@bot.event
async def on_ready():
    await bot.add_cog(OpenTTDCog(bot))
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    message = 'Bot Connected'
    channel = bot.get_channel(channel_log_messages)
    await channel.send(message)
    print(f'Successfully logged in and booted...!')

# Discord Events, Allows us to do things like capture messages from a channel to send to OpenTTD
# IE, Chat
@bot.event
async def on_message(message):
    # IF the channel of the message matches our channel ID, we'll continue.
    if message.channel.id == channel_chat_messages:
        # We don't want to echo what our bot says, let's ensure we ignore messages posted by ourselves
        if bot_id_on_discord != message.author.id:
            send_to_openttd_admin(f"[Discord] {message.author}: {message.content}")

    await bot.process_commands(message)


# Start OpenTTD admin listener thread
openTTD_thread = threading.Thread(target=openTTD_listener_thread)
openTTD_thread.daemon = True
openTTD_thread.start()

# Start Discord bot
bot.run(discordtoken, reconnect=True)
