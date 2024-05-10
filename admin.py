import socket
import threading
import time
import re
from pyopenttdadmin import Admin, AdminUpdateType, openttdpacket

# UDP Socket Configuration
# bot.py and admin.py listen and send on reversed ports as we're using one-way UDP communication
UDPHOST = '127.0.0.1'  # The receiver's IP address
RXPORT = 12346      # The port on which to receive data
TXPORT = 12345      # The port on which to send data

# UDP Receiver gets messages from bot.py, which are likely to be commands for us to execute.
def udp_rx(admin):
    # Create a UDP socket
    rxsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    rxsock.bind((UDPHOST, RXPORT))
    print("Receiver is listening...")

    while True:
        # Receive data
        data, addr = rxsock.recvfrom(1024)  # Buffer size is 1024 bytes
        print("Received data:", data)  # Print received data

        # Discord user did !rcon command, we'll grab the command data and send it over to the OpenTTD Admin port.
        # We use .replace to remove the command and leave us with jus the data we're sending to rcon on the admin port.
        if 'rcon' in data.decode():
            rcon_command = data.decode().replace("rcon ", "")
            admin.send_rcon(rcon_command)
            print(rcon_command)

        # Chat from Discord being sent to our Admin port.
        if 'CHAT_PACKET' in data.decode():
            chat_packet = data.decode().replace("CHAT_PACKET ", "")
            admin.send_global(f"[Discord] {chat_packet}")
            print(chat_packet)



# Defines the code which handles communication with the OpenTTD Admin port
# Within the loop of this function is where we'll send data back to bot.py
def admin_connection(admin):
    # Subscribe to receive chat updates
    admin.send_subscribe(AdminUpdateType.CHAT)

    # Our Socket for sending data to the bot.py discord application
    txsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Keep the connection open and print incoming chat messages
    while True:
        # Receive packets from the server
        packets = admin.recv()
        for packet in packets:

            # Read CHATPACKET from Admin port
            if isinstance(packet, openttdpacket.ChatPacket):
                # Print chat message details
                # Omit users entering commands
                if not packet.message.startswith('!'):
                    print(f'ID: {packet.id} Message: {packet}')
                    txsock.sendto(bytes(f"CHAT_PACKET{packet.id} {packet.message}".encode('utf-8')), (UDPHOST, TXPORT))

                # These are bot commands from OpenTTD players coming from the admin port.
                if packet.message.startswith('!'):
                    # Report/admin command, sends user report over to bot.py for processing on discord.
                    if packet.message == 'report' or 'admin':
                        # Define the regex pattern to remove command from message
                        pattern = r'^(?:!help|!admin)\s*'
                        message = re.sub(pattern, '', packet.message)
                        txsock.sendto(bytes(f"REPORT_PACKET{packet.id} {message}".encode('utf-8')), (UDPHOST, TXPORT))
                        admin.send_private(id=packet.id, message="A Disord Admin as been alerted and should be with you shortly!")

            # Read RCONPACKET from Admin port to discord
            if isinstance(packet, openttdpacket.RconPacket):
                #txsock.sendto(bytes(f"RCON_PACKET{packet.response}".encode('utf-8')), (UDPHOST, TXPORT))
                #coming back to abstract, we don't need direct access to rcon when we can make custom commands and leave rcon for internal
                pass

            # Collect a number of rcon packets to make a dict of active clients id, name, comapny name, company id, money, loan
            if isinstance(packet, openttdpacket.RconPacket):
                print(packet)


        # Add a short sleep to avoid busy-waiting
        time.sleep(0.1)

# Instantiate the Admin class and establish connection to the server
with Admin(ip=UDPHOST, port=3977, name="ModRail Bot", password="toor") as admin:
    # Create and start the UDP receiver thread
    rx_thread = threading.Thread(target=udp_rx, args=(admin,))
    rx_thread.start()

    # Call the admin connection function directly
    admin_connection(admin)
