from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
import json
import uuid

class GameProtocol(Protocol):
    factory = None  # type: GameFactory # type: ignore
    transport = None  # type: ITransport # type: ignore
    
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
        client_data = {'object': self, 'uuid': uid}
        self.factory.clients.append(client_data) # type: ignore

        #self.factory.clients.append(self) # type: ignore

        # client (uuid)

        print("Client connected:", self.transport.getPeer())
        
        print(f'Clients present: {len(self.factory.clients)}')
        for client in self.factory.clients:
            print(f'- {client}')
        
    def dataReceived(self, data):
        # Relay to all other clients
        for client in self.factory.clients:
            if client is not self:
                pass
            else:
                conv_data = self.bytes_to_json(data)
                if conv_data['entity'] == 'player':
                    pass
                    new_px = float(conv_data['px']) + 100
                    
                    packet = {
                        'entity': 'pixy',
                        'px': new_px, # Returns pixy a bit offset from the player
                        'py': conv_data['py'],
                        'altitude': conv_data['altitude'],
                    }

                    encoded = json.dumps(packet).encode('utf-8')
                    client.transport.write(encoded)
            
            

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


