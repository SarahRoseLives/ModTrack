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

# Regular expressions
client_regex = re.compile(r"Client #(\d+)  name: '(.+?)'  company: (\d+)  IP: (\d+\.\d+\.\d+\.\d+)")
company_regex = re.compile(
    r"#:(\d+)\((\w+)\) Company Name: '(.+?)'  Year Founded: (\d+)  Money: (\d+)  Loan: (\d+)  Value: (\d+)")




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

# Grab data from our user / client details dict

def send_client_details_rcon():
    admin.send_rcon('companies')
    admin.send_rcon('clients')

global client_info
global company_info
client_info = {}
company_info = {}

def get_client_info(client_id, client_info):
    return client_info.get(client_id, None)

def get_company_info(company_id, company_info):
    return company_info.get(company_id, None)



# Defines the code which handles communication with the OpenTTD Admin port
# Within the loop of this function is where we'll send data back to bot.py
def admin_connection(admin):
    # Subscribe to receive chat updates
    admin.send_subscribe(AdminUpdateType.CHAT)

    # Let's make sure our dict of client details is updated
    send_client_details_rcon()

    # Our Socket for sending data to the bot.py discord application
    txsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Keep the connection open and print incoming chat messages
    while True:
        # Receive packets from the server
        packets = admin.recv()
        for packet in packets:

            # Collect a number of rcon packets to make a dict of active clients id, name, comapny name, company id, money, loan
            if isinstance(packet, openttdpacket.RconPacket):
                packet = str(packet)
                if "Client #" in packet:
                    # Extract client information
                    client_id_start = packet.index("Client #") + len("Client #")
                    client_id_end = packet.index("name:")
                    client_id = int(packet[client_id_start:client_id_end].strip())
                    name_start = packet.index("name: '") + len("name: '")
                    name_end = packet.index("'", name_start)
                    name = packet[name_start:name_end]
                    company_start = packet.index("company: ") + len("company: ")
                    company_end = packet.index(" IP:")
                    company_id = int(packet[company_start:company_end].strip())
                    ip_start = packet.index("IP: ") + len("IP: ")
                    ip = packet[ip_start:].strip()
                    client_info[client_id] = {"name": name, "company_id": company_id, "IP": ip}
                else:
                    # Extract company information
                    company_id_start = packet.index("#:") + len("#:")
                    company_id_end = packet.index("(", company_id_start)
                    company_id = int(packet[company_id_start:company_id_end].strip())
                    name_start = packet.index("Company Name: '") + len("Company Name: '")
                    name_end = packet.index("'", name_start)
                    name = packet[name_start:name_end]
                    year_founded_start = packet.index("Year Founded: ") + len("Year Founded: ")
                    year_founded_end = packet.index(" ", year_founded_start)
                    year_founded = int(packet[year_founded_start:year_founded_end])
                    money_start = packet.index("Money: ") + len("Money: ")
                    money_end = packet.index(" ", money_start)
                    money = int(packet[money_start:money_end])
                    loan_start = packet.index("Loan: ") + len("Loan: ")
                    loan_end = packet.index(" ", loan_start)
                    loan = int(packet[loan_start:loan_end])
                    value_start = packet.index("Value: ") + len("Value: ")
                    value_end = packet.index(" ", value_start)
                    value = int(packet[value_start:value_end])
                    company_info[company_id] = {
                        "name": name,
                        "year_founded": year_founded,
                        "money": money,
                        "loan": loan,
                        "value": value
                    }
            #print(f'Client Dict: {client_info}')
            #print(f'Company Dict: {company_info}')

            #return client_info, company_info


            # Read CHATPACKET from Admin port
            if isinstance(packet, openttdpacket.ChatPacket):
                # Print chat message details
                # Omit users entering commands
                if not packet.message.startswith('!'):

                    # A chat message that has no text is likely a company change packet informing us that a client has joined a compnany.
                    # Company messages are not really working right, the dict isn't up to date, likely because it's looking at the wrong time.
                    if packet.message == '':


                        # Grab the client and company information from dict
                        client_name = get_client_info(packet.id, client_info)['name']
                        client_company_id = get_client_info(packet.id, client_info)['company_id']
                        client_company_name = get_company_info(client_company_id, company_info)['name']
                        print(client_info)
                        print(company_info)
                        print(packet.id)
                        print(client_company_id)
                        print(client_company_name)


                        # Send a packet to the discord bot that the user has joined a company
                        txsock.sendto(bytes(f"LOG_PACKET{client_name} has joined company {client_company_id}".encode('utf-8')), (UDPHOST, TXPORT))

                    # If it's not a company change packet, treat as a common chat packet.
                    else:
                        client_name = get_client_info(packet.id, client_info)['name']

                        # Send Normal Chat Message
                        txsock.sendto(bytes(f"CHAT_PACKET{client_name} (ID: {packet.id}) {packet.message}".encode('utf-8')), (UDPHOST, TXPORT))


                # These are bot commands from OpenTTD players coming from the admin port.
                if packet.message.startswith('!'):
                    # Report/admin command, sends user report over to bot.py for processing on discord.
                    if packet.message == 'report' or 'admin':
                        # Define the regex pattern to remove command from message
                        pattern = r'^(?:!help|!admin)\s*'
                        message = re.sub(pattern, '', packet.message)
                        txsock.sendto(bytes(f"REPORT_PACKET{packet.id} {message}".encode('utf-8')), (UDPHOST, TXPORT))
                        admin.send_private(id=packet.id, message="A Discord Admin as been alerted and should be with you shortly!")



        # Add a short sleep to avoid busy-waiting
        time.sleep(0.1)

# Instantiate the Admin class and establish connection to the server
with Admin(ip=UDPHOST, port=3977, name="ModRail Bot", password="toor") as admin:
    admin.send_rcon('companies')
    admin.send_rcon('clients')
    # Create and start the UDP receiver thread
    rx_thread = threading.Thread(target=udp_rx, args=(admin,))
    rx_thread.start()

    # Call the admin connection function directly
    admin_connection(admin)
