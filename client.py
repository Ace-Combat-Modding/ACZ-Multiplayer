from twisted.internet import reactor, protocol, task
import json
import time

import game_latch as gl

CLIENT_NAME = 'Alpha'
TICK_RATE = 5  # ticks per second
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 1234

GAME_PROCESS_NAME = "pcsx2.exe"
LATCH = gl.GameLatch(process_name=GAME_PROCESS_NAME)

class GameClient(protocol.Protocol):
    def connectionMade(self):
        print("Connected to server.")

        # Start the game loop
        self.loop = task.LoopingCall(self.game_tick)
        self.loop.start(1.0 / TICK_RATE)

        # Example initial message
        #self.transport.write(b"HELLO_SERVER")
        #print("sending: HELLO_SERVER")


    def dataReceived(self, data):
        ''' Receive data from server. Called automatically by Twisted. '''
        print("Server:", data)

    def connectionLost(self, reason):
        print("Connection lost:", reason)
        if self.loop.running:
            self.loop.stop()

    def game_tick(self):
        '''
        This runs at your TICK_RATE.
        Poll your game state here and send packets if needed.
        '''

        player_data = LATCH.get_player_data('altitude')

        #print(f'Player Altitude: {}')

        # Example: send a JSON state packet
        packet = {
            'entity': 'player',
            'px': LATCH.get_player_data('pos_east_west'),
            'py': LATCH.get_player_data('pos_north_south'),
            'altitude': LATCH.get_player_data('altitude'),
        }

        encoded = json.dumps(packet).encode('utf-8')
        self.transport.write(encoded)


class GameClientFactory(protocol.ClientFactory):
    protocol = GameClient

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed:', reason)
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print('Connection lost:', reason)
        reactor.stop()


if __name__ == '__main__':
    reactor.connectTCP(SERVER_HOST, SERVER_PORT, GameClientFactory())
    reactor.run()
