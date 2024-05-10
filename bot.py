import discord
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
            channel = bot.get_channel(1238233747850133584)
            #await channel.send(f"Received UDP data: {data.decode()}")
            print(f'DEBUG: {data.decode()}')

            # Identify Rcon Packet and print it to the channel
            if data.decode().startswith('RCON_PACKET'):
                await channel.send(data.decode().replace('RCON_PACKET', ''))



            #if "!admin" in data.decode():
            #    txsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #    message = "Please enter your report in your next message"
            #    txsock.sendto(bytes(message.encode('utf-8')), (UDPHOST, TXPORT))
            #    print(f'Sent: {message}')
            #    await channel.send('A user has requested an admin')


    finally:
        rxsock.close()


# Starts the Async task for the UDP Receiver
@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    # Start the UDP receiver in a separate task
    asyncio.create_task(udp_rx())

# rcon Bot command sends data to the UDP receiver running on admin.py
@bot.command(name="rcon")
async def first_slash(ctx, message):
    txsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    txsock.sendto(bytes(str(f'rcon {message}').encode('utf-8')), (UDPHOST, TXPORT))
    #await ctx.send("You executed the slash command!")

bot.run(discordtoken)
