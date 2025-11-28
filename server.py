from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.protocols.basic import Int32StringReceiver
import json
import uuid

class GameProtocol(Int32StringReceiver):
    factory = None  # type: GameFactory # type: ignore
    transport = None  # type: ITransport # type: ignore
    
    def __init__(self):
        self.handshaked:bool = False
    
    def bytes_to_json(self, data: bytes) -> dict:
        '''
        Converts bytes received from the client into a JSON object (dict).
        Raises ValueError if the data is not valid JSON.
        '''
        try:
            text = data.decode("utf-8")     # bytes → string
            return json.loads(text)         # string → dict
        except Exception as e:
            print("JSON decode error:", e)
            return {'': ''}

    def connectionMade(self):
        uid = uuid.uuid4()
        client_data = {'object': self, 'uuid': uid, 'player_name': ''}
        self.factory.clients.append(client_data) # type: ignore

        #self.factory.clients.append(self) # type: ignore

        # client (uuid)

        print("Client connected:", self.transport.getPeer())
        
        print(f'Clients present: {len(self.factory.clients)}')
        for client in self.factory.clients:
            print(f'- {client}')
        
    def stringReceived(self, data):
        print(f'Received -- {data}')
        conv_data = self.bytes_to_json(data)

        # Handshake procedure
        if (not self.handshaked):
            if conv_data['packet_type'] == 'handshake':
                for client in self.factory.clients:
                    if client['object'] == self:
                        client['player_name'] = conv_data['player_name']
                        # Send handshake confirmation message to client
                        handshake_packet = {'packet_type': 'handshake', 'handshake_status': 'complete'}
                        encoded = json.dumps(handshake_packet).encode('utf-8')
                        self.sendString(encoded)
                        self.handshaked = True


        
        for client in self.factory.clients:
            if client['object'] != self: # Send back player data as if it were pixy's
                conv_data = self.bytes_to_json(data)
                if conv_data['packet_type'] == 'game' and conv_data['entity'] == 'player':
                    new_px = float(conv_data['px']) + 100
                    
                    packet = {
                        'packet_type': 'game',
                        'entity': 'pixy',
                        'px': new_px, # Returns pixy a bit offset from the player
                        'py': conv_data['py'],
                        'altitude': conv_data['altitude'],
                    }

                    encoded = json.dumps(packet).encode('utf-8')
                    client['object'].sendString(encoded)
            
            

    def connectionLost(self, reason):
        print("Client disconnected:", reason)
        #self.factory.clients.remove(self) # type: ignore

        for client in self.factory.clients:
            if client['object'] == self:
                self.factory.clients.remove(client)



        print(f'Clients remaining: {len(self.factory.clients)}')
        for client in self.factory.clients:
            print(f'- {client}')

class GameFactory(Factory):
    protocol = GameProtocol
    clients = []
    client_increment = 0

factory = GameFactory()
reactor.listenTCP(1234, factory) # type: ignore
print("Server running on port 1234")
reactor.run() # type: ignore


