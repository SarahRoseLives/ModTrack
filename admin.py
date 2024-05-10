import socket
import threading
import time
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
        if 'rcon' in data.decode():
            rcon_command = data.decode().replace("rcon ", "")
            admin.send_rcon(rcon_command)
            print(rcon_command)

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
                print(f'ID: {packet.id} Message: {packet}')
                txsock.sendto(bytes(str(packet).encode('utf-8')), (UDPHOST, TXPORT))

            # Read RCONPACKET from Admin port
            if isinstance(packet, openttdpacket.RconPacket):
                txsock.sendto(bytes(f"RCON_PACKET{packet.response}".encode('utf-8')), (UDPHOST, TXPORT))

        # Add a short sleep to avoid busy-waiting
        time.sleep(0.1)

# Instantiate the Admin class and establish connection to the server
with Admin(ip=UDPHOST, port=3977, name="pyOpenTTDAdmin", password="toor") as admin:
    # Create and start the UDP receiver thread
    rx_thread = threading.Thread(target=udp_rx, args=(admin,))
    rx_thread.start()

    # Call the admin connection function directly
    admin_connection(admin)
