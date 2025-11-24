from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor

class GameProtocol(Protocol):

    def connectionMade(self):
        print("Client connected:", self.transport.getPeer())
        self.factory.clients.append(self)

    def dataReceived(self, data):
        # Relay to all other clients
        for client in self.factory.clients:
            if True:#client is not self:
                client.transport.write(data)

    def connectionLost(self, reason):
        print("Client disconnected:", reason)
        self.factory.clients.remove(self)

class GameFactory(Factory):
    protocol = GameProtocol
    clients = []

factory = GameFactory()
reactor.listenTCP(1234, factory)
print("Server running on port 1234")
reactor.run()
