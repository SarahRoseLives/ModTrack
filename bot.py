import discord
from discord import ChannelType
from discord.ext import commands
import configparser
import socket
import asyncio
import re

# UDP Socket Configuration
# bot.py and admin.py listen and send on reversed ports as we're using one-way UDP communication
UDPHOST = '127.0.0.1'  # Listen on all available interfaces
TXPORT = 12346        # The port on which to send data
RXPORT = 12345        # The port on which to get data

def load_config():
    config = configparser.ConfigParser()
    config.read("config.txt")
    return config

# Load configuration
config = load_config()

# [Discord] Config
discordtoken = config.get(section='Discord', option='token')
bot_id_on_discord = int(config.get(section='Discord', option='bot_id_on_discord'))
discord_admin_role_id = int(config.get(section='Discord', option='discord_admin_role_id'))
# Channel declarations
channel_admin_request = int(config.get(section='Discord', option='channel_admin_request'))
channel_chat_messages = int(config.get(section='Discord', option='channel_chat_messsages'))
channel_bot_commands = int(config.get(section='Discord', option='channel_bot_commands'))


# Setup Discord bot
Intents = discord.Intents.default()
Intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=Intents) # prefix is the bot command

# UDP Receiver listens for data from admin.py (OpenTTD Admin Port Connection)
async def udp_rx():
    # Create a UDP socket
    rxsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    rxsock.bind((UDPHOST, RXPORT))
    print("Receiver is listening...")

    loop = asyncio.get_event_loop()

    try:
        while True:
            # Receive data
            data, addr = await loop.sock_recvfrom(rxsock, 1024)  # Buffer size is 1024 bytes
            print("Received:", data.decode())
            # Process received data here
            # For example, you can send a message to Discord based on the received data

            #await channel.send(f"Received UDP data: {data.decode()}")
            print(f'DEBUG: {data.decode()}')

            # Identify Rcon Packet and print it to the channel
            if data.decode().startswith('RCON_PACKET'):
                channel = bot.get_channel(channel_bot_commands)
                await channel.send(data.decode().replace('RCON_PACKET', ''))

            # Identify Chat Packet and print it to the channel
            if data.decode().startswith('CHAT_PACKET'):
                channel = bot.get_channel(channel_chat_messages)
                await channel.send(data.decode().replace('CHAT_PACKET', ''))

            # Identify Report Packet and print it to the channel
            if data.decode().startswith('REPORT_PACKET'):
                channel = bot.get_channel(channel_admin_request)
                thread = await channel.create_thread(name="example", type=ChannelType.public_thread)
                await thread.send(data.decode().replace('REPORT_PACKET', f'<@&{discord_admin_role_id}>'))




            #if "!admin" in data.decode():
            #    txsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #    message = "Please enter your report in your next message"
            #    txsock.sendto(bytes(message.encode('utf-8')), (UDPHOST, TXPORT))
            #    print(f'Sent: {message}')
            #    await channel.send('A user has requested an admin')


    finally:
        rxsock.close()

# Function acts like a command decorator to check if the command was sent from the allowed channel
# @bot.command(name='command_name')
# @commands.check(is_channel_bot_commands)
async def is_channel_bot_commands(ctx):
    return ctx.channel.id == channel_bot_commands

txsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Starts the Async task for the UDP Receiver
@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    # Start the UDP receiver in a separate task
    asyncio.create_task(udp_rx())


@bot.event
async def on_message(message):
    # Just send all channel_chat_messages to admin port as a chat packet
    if message.channel.id == channel_chat_messages:
        # Ensure we don't echo our own bot back
        if bot_id_on_discord != message.author.id: # If bot id is not the same as message id then we continue
            txsock.sendto(bytes(str(f"CHAT_PACKET {message.author}: {message.content}").encode('utf-8')), (UDPHOST, TXPORT))
    # Continue with regular bot commands now
    await bot.process_commands(message)

# rcon Bot command sends data to the UDP receiver running on admin.py
@bot.command(name="rcon")
@commands.check(is_channel_bot_commands)
async def rcon(ctx, message):

    txsock.sendto(bytes(str(f'rcon {message}').encode('utf-8')), (UDPHOST, TXPORT))
    #await ctx.send("You executed the slash command!")

bot.run(discordtoken)
