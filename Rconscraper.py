class RconClientManager:
    def __init__(self):
        self.clients_data = []
        self.companies_data = []

    def parse_rcon_packet(self, packet):
        data = {}
        fields = packet.split("  ")
        for field in fields:
            if "Client #" in field:
                data['client_id'] = int(field.split("#")[1].split()[0])
            elif "name:" in field:
                data['client_name'] = field.split(":")[1].strip()
            elif "status:" in field:
                data['client_status'] = field.split(":")[1].strip()
            elif "company:" in field:
                data['client_company_id'] = int(field.split(":")[1].strip())
        return data

    def parse_company_packet(self, packet):
        data = {}
        fields = packet.split("  ")
        for field in fields:
            if "Company Name:" in field:
                data['company_name'] = field.split(":")[1].strip()
            elif "Year Founded:" in field:
                data['year_founded'] = int(field.split(":")[1].strip())
            elif "Money:" in field:
                data['money'] = int(field.split(":")[1].strip())
            elif "Loan:" in field:
                data['loan'] = int(field.split(":")[1].strip())
            elif "Value:" in field:
                data['value'] = int(field.split(":")[1].strip())
            elif "#:" in field:
                data['company_id'] = int(field.split("#:")[1].split("(")[0].strip())
        return data

    def add_packet(self, packet):
        if packet.startswith("RconPacket"):
            if "Client #" in packet:
                client_data = self.parse_rcon_packet(packet)
                self.clients_data.append(client_data)
            elif "#:" in packet:
                company_data = self.parse_company_packet(packet)
                self.companies_data.append(company_data)

    def get_client_info_by_id(self, client_id):
        for client_data in self.clients_data:
            if client_data['client_id'] == client_id:
                return client_data
        return None

    def get_client_info(self, client_id, info_key):
        for client_data in self.clients_data:
            if client_data['client_id'] == client_id:
                return client_data.get(info_key, None)
        return None

    def get_company_info_by_id(self, company_id):
        for company_data in self.companies_data:
            if company_data['company_id'] == company_id:
                return company_data
        return None

    def get_company_info(self, company_id, info_key):
        for company_data in self.companies_data:
            if company_data['company_id'] == company_id:
                return company_data.get(info_key, None)
        return None

'''
# Example status packets and company packets
packets = [
    "RconPacket(8, Client #1  name: 'John Doe'  status: 'active'  frame-lag: 1  company: 1  IP: 192.168.1.207)",
    "RconPacket(8, Client #2  name: 'rose #1'  status: 'active'  frame-lag: 1  company: 2  IP: 192.168.1.206)",
    "RconPacket(8, Client #3  name: 'Alice'  status: 'inactive'  frame-lag: 1  company: 1  IP: 192.168.1.208)",
    "RconPacket(8, Client #4  name: 'Bob'  status: 'active'  frame-lag: 1  company: 2  IP: 192.168.1.209)",
    "RconPacket(8, #:1(Orange) Company Name: 'rose #1 Transport'  Year Founded: 1960  Money: 88308  Loan: 100000  Value: 1  (T:0, R:0, P:0, S:0) unprotected)",
    "RconPacket(8, #:2(Pink) Company Name: 'Unnamed'  Year Founded: 1960  Money: 90033  Loan: 100000  Value: 1  (T:0, R:0, P:0, S:0) unprotected)"
]

# Create an instance of the RconClientManager class
manager = RconClientManager()

# Add packets to the manager
for packet in packets:
    manager.add_packet(packet)

# Example: Get client info by ID
client_id_to_get = 3
client_info = manager.get_client_info_by_id(client_id_to_get)
if client_info:
    print("Client ID:", client_info['client_id'])
    print("Client Name:", client_info['client_name'])
    print("Client Status:", client_info['client_status'])
    print("Client Company ID:", client_info['client_company_id'])
else:
    print("Client not found.")

# Example: Get company info by ID
company_id_to_get = 1
company_info = manager.get_company_info_by_id(company_id_to_get)
if company_info:
    print("\nCompany ID:", company_info['company_id'])
    print("Company Name:", company_info['company_name'])
    print("Year Founded:", company_info['year_founded'])
    print("Money:", company_info['money'])
    print("Loan:", company_info['loan'])
    print("Value:", company_info['value'])
else:
    print("\nCompany not found.")
'''