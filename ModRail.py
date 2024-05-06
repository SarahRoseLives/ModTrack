import time
import re
import configparser
import os
import datetime

from src.main import Admin
from src.enums import PacketType, Actions, ChatDestTypes, AdminUpdateType
from src.packet import ChatPacket, RconPacket, RconEndPacket

# Name of bot
botname = "[ModRail]"

# Dictionary to store counts of true messages for each ID
id_counts = {}

# Dictionary to store count of kick and ban votes
kick_votes = {}
ban_votes = {}

# Load config and set variables
def load_config():
    config = configparser.ConfigParser()
    config.read("config.cfg")
    return config

# Load configuration
config = load_config()

wordlists = dict(config.items("Wordlists"))
port = config.get("ModRail", "port")
ip = config.get("ModRail", "server")
adminpass = config.get("ModRail", "adminpass")
welcome_message = config.get("ModRail", "welcome")
prefix = config.get("ModRail", "prefix")
logstate = config.get("ModRail", "logging")

# Warning messages
warning1 = config.get("Warnings", "warning1")
warning2 = config.get("Warnings", "warning2")
votedwarning = config.get("Warnings", "votedwarning")

# Votes

votestokick = config.get("Votes", "votestokick")
votestoban = config.get("Votes", "votestoban")


# If enabled, log chat messages and bot actions to file
def action_log(admin, message, id):
    if logstate == "disabled":
        return

    if logstate == "enabled":
        log_filename = "log.txt"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        name = getclient_info(admin, identifier=id)['name']
        log_entry = f"{timestamp} - {id}:{name}: {message}\n"
        print(log_entry)

        # Check if log file exists
        if not os.path.exists(log_filename):
            with open(log_filename, "w") as logfile:
                logfile.write(log_entry)
        else:
            with open(log_filename, "a") as logfile:
                logfile.write(log_entry)



def check_message_in_wordlists(message, id, wordlists):
    try:
        for wordlist_name, enabled in wordlists.items():
            if enabled.lower() == 'enabled':
                wordlist_path = f"wordlists/{wordlist_name}.txt"
                with open(wordlist_path, "r") as file:
                    wordlist = file.read().splitlines()
                    for word in wordlist:
                        pattern = r'\b{}\b'.format(re.escape(word))  # \b is a word boundary
                        if re.fullmatch(pattern, message, re.IGNORECASE):
                            # Increment count for the ID
                            id_counts[id] = id_counts.get(id, 0) + 1
                            # Check if count reaches 1
                            if id_counts[id] == 1:
                                admin.send_private(id=id, message=f'{botname} {warning1}')
                            # Check if count reaches 2
                            if id_counts[id] == 2:
                                admin.send_private(id=id, message=f'{botname} {warning2}')
                            # Check if count reaches 3
                            if id_counts[id] == 3:
                                print(f"Kicking user id {id} for wordlist violations")
                                admin.send_rcon('kick ' + str(id))
                            return True
        return False
    except FileNotFoundError:
        print("Error: wordlist file not found.")
        return False

# Takes the admin session and a client id and returns the clients name company and ip
def getclient_info(admin, identifier):
    # Defines a dictionary of active clients on the server.
    client_info = {}

    # Send rcon command to get client list
    admin.send_rcon('clients')

    # Loop over rcon packets until we find one that matches our client id and return client info
    while True:
        packets = admin.recv()
        for packet in packets:
            if isinstance(packet, RconPacket):
                match = re.search(r"Client #(\d+)  name: '(.+)'  company: (\d+)  IP: (.+)", str(packet))
                if match:
                    client_id = match.group(1)
                    client_name = match.group(2)
                    client_company = match.group(3)
                    client_ip = match.group(4)

                    # Check if the identifier matches any client information
                    if str(identifier) == client_id or identifier == client_name or identifier == client_company or identifier == client_ip:
                        return {'id': client_id, 'name': client_name, 'company': client_company, 'ip': client_ip}


    return None  # Return None if no matching client is found

# Dissect recieved commands and execute them
def check_commands(admin, message, id):
    command = re.sub('^!', '', message)
    if command.startswith('vote'):
        kickorban = command.split()[1]
        offending_username = ' '.join(command.split()[2:]).lower()
        offending_id = getclient_info(admin, offending_username)['id']

        if kickorban == 'kick':
            votes = kick_votes
        elif kickorban == 'ban':
            votes = ban_votes
        else:
            # Handle invalid vote type
            return

        if offending_username in votes:
            if id not in votes[offending_username]['voters']:
                votes[offending_username]['voters'].append(id)
            else:
                admin.send_private(id=id, message=votedwarning)
                action_log(admin, message=votedwarning, id=id)
                return
        else:
            votes[offending_username] = {'voters': [id], 'offending_id': offending_id, 'count': 0}

        if len(votes[offending_username]['voters']) >= int(votestokick) and kickorban == 'kick':
            admin.send_rcon(f'kick {votes[offending_username]["offending_id"]}')
            admin.send_global(f'{offending_username} has been vote kicked!')
            action_log(f'{offending_username} has been vote kicked!')
            del votes[offending_username]
        elif len(votes[offending_username]['voters']) >= int(votestoban) and kickorban == 'ban':
            admin.send_rcon(f'ban {votes[offending_username]["offending_id"]}')
            admin.send_global(f'{offending_username} has been vote banned!')
            action_log(f'{offending_username} has been vote banned!')
            del votes[offending_username]


# Create an instance of the Admin class and connect to the server
with Admin(ip, int(port), "ModRail 0.1", adminpass) as admin:
    admin.send_global(welcome_message)
    action_log(admin, message=welcome_message, id=str(255))
    # Subscribe to chat messages
    admin.send_subscribe(AdminUpdateType.CHAT)

    #print(getclient_info(admin, '12')['name'])


    # Keep the connection open and print out any chat messages
    while True:
        packets = admin.recv()
        for packet in packets:
            if isinstance(packet, ChatPacket) and packet.desttype == ChatDestTypes.BROADCAST:
                print(f"{packet.message} (sent by {packet.id})")
                action_log(admin, message=packet.message, id=packet.id)
                check_message_in_wordlists(message=packet.message, id=packet.id, wordlists=wordlists)
                if packet.message.startswith(prefix):
                    check_commands(admin, packet.message, packet.id)

            if isinstance(packet, RconPacket):
                #print(packet)
                pass
                if isinstance(packet, RconEndPacket):
                    #print(packet)
                    pass

        # Sleep for a short time before checking for new packets
        time.sleep(0.1)
