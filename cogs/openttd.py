import discord
import re

from discord.ext import commands, tasks

from pyopenttdadmin import Admin, AdminUpdateType, openttdpacket

# missing constants
# WEBHOOK_URL
# ADMIN_CHANNEL_ID
# DISCORD_ADMIN_ROLE_ID
# DISCORD_CHANNEL_ID

class OpenTTD(commands.Cog):
    def __init__(self, bot: commands.Bot, openttd: Admin):
        self.bot = bot
        self.openttd = openttd
        self.webhook = discord.Webhook.from_url(WEBHOOK_URL, client = bot)

        self.openttd.send_subscribe(AdminUpdateType.CHAT)
        self.openttd.send_subscribe(AdminUpdateType.CONSOLE)

        self.admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)

        self.users = {}

    @tasks.loop(seconds = 5)
    async def update(self):
        # get new packets
        packets = self.openttd.recv()

        for packet in packets:
            # do something with the packet
            if isinstance(packet, openttdpacket.ChatPacket):
                print(f"Chat message from {packet.id}: {packet.message}")
                await self.openttd_chat_packet(packet)
            
            if isinstance(packet, openttdpacket.ConsolePacket):
                print(f"Console message: {packet.message}")
                await self.openttd_console_packet(packet)
    
    async def openttd_chat_packet(self, packet: openttdpacket.ChatPacket):
        # These are bot commands from OpenTTD players coming from the admin port.
        if packet.message.startswith('!'):
            # Report/admin command, sends user report over to bot.py for processing on discord.
            if packet.message in ["report", "admin"]:
                # Define the regex pattern to remove command from message
                pattern = r'^(?:!help|!admin)\s*'
                message = re.sub(pattern, '', packet.message)
                thread = await self.admin_channel.create_thread(name = "example", type = discord.ChannelType.public_thread)
                await thread.send(f"<@&{DISCORD_ADMIN_ROLE_ID}> ID: {packet.id} Message: {packet.message}")
                self.openttd.send_private(id=packet.id, message="A Disord Admin as been alerted and should be with you shortly!")

                return

        # send message to channel
        # to create a webhook, go to the channel -> settings -> integrations -> webhooks | add webhook
        # webhooks allow you to send messages to a channel from a user with custom name and avatar
        # enhancement: use the color of the company to customize the avatar
        await self.webhook.send(packet.message, username = self.users.get(packet.id, "Unknown"))
    
    async def openttd_console_packet(self, packet: openttdpacket.ConsolePacket):
        if packet.origin == "net":
            print(packet.message)
            matched = re.fullmatch(r"\[server\] Client #(\d+) \([\d\.]+\) joined as (.+)", packet.message) # client id (ip) joined as name
            if matched is not None:
                print("player joined")
                # player joined
                self.users[int(matched.group(1))] = matched.group(2)
                await self.webhook.send(f"{matched.group(2)} joined the server.", username = "Server")
                
                return
            
            matched = re.fullmatch(r"\[server\] Client #(\d+) closed connection", packet.message) # client id closed connection
            if matched is not None:
                print("player left")
                # player left
                try:
                    name = self.users.pop(int(matched.group(1)))
                    await self.webhook.send(f"{name} left the server.", username = "Server")

                except KeyError:
                    print("player not found")
                
                return
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.update.start()
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # process commands
        if message.content.startswith(self.bot.command_prefix):
            return await self.bot.process_commands(message)
        
        # chat messages go to the server
        if message.channel.id == int(DISCORD_CHANNEL_ID):
            self.openttd.send_global(message.content)

    @commands.command()
    async def rcon(self, ctx, *, command: str):
        self.openttd.send_rcon(command)
