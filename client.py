from twisted.internet import reactor, protocol, task
import json
import time

import game_latch as gl

CLIENT_ID = -1
TICK_RATE = 60  # ticks per second
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

        # decode data:
        conv_data = bytes_to_json(data)
        update_fields = [('px', 'pos_east_west'), ('py' ,'pos_north_south'), ('altitude', 'altitude')]
        if conv_data['entity'] == 'pixy':
            for field in update_fields:
                pixy_entity = LATCH.pixy_entity
                value = conv_data[field[0]]
                LATCH.set_aircaft_data_float(value=value,
                                             aircraft=pixy_entity,
                                             field=field[1])



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


def bytes_to_json(data: bytes) -> dict:
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
    

if __name__ == '__main__':
    reactor.connectTCP(SERVER_HOST, SERVER_PORT, GameClientFactory())
    reactor.run()
