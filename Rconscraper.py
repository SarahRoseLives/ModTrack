def parse_packets(packets):
    client_info = {}
    company_info = {}

    for packet in packets:
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

    return client_info, company_info

def get_client_info(client_id, client_info):
    return client_info.get(client_id, None)

def get_company_info(company_id, company_info):
    return company_info.get(company_id, None)

# Example packets
packets = [
    "RconPacket(8, #:1(Green) Company Name: 'rose #1 Transport'  Year Founded: 1960  Money: 84283  Loan: 100000  Value: 1  (T:0, R:0, P:0, S:0) unprotected)",
    "RconPacket(8, #:2(Pink) Company Name: 'Unnamed'  Year Founded: 1964  Money: 93291  Loan: 100000  Value: 1  (T:0, R:0, P:0, S:0) unprotected)",
    "RconPacket(8, Client #1  name: 'rose'  company: 255  IP: server)",
    "RconPacket(8, Client #3  name: 'rose #1'  company: 1  IP: 192.168.1.206)"
]

# Parse packets
client_info, company_info = parse_packets(packets)

# Test functions
client_id = 3
client_info_result = get_client_info(client_id, client_info)
print("Client Info for Client #{}:".format(client_id))
print(client_info_result)

company_id = 1
company_info_result = get_company_info(company_id, company_info)
print("\nCompany Info for Company #{}:".format(company_id))
print(company_info_result)
