from twisted.internet import reactor, protocol, task
from twisted.protocols.basic import Int32StringReceiver
import json
import time

import game_latch as gl

#CLIENT_NAME = 'UNNAMED'
TICK_RATE = 120  # ticks per second
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 1234

GAME_PROCESS_NAME = "pcsx2.exe"
LATCH = gl.GameLatch(process_name=GAME_PROCESS_NAME)

class GameClient(Int32StringReceiver):
    factory = None  # type: GameClientFactory # type: ignore
    transport = None  # type: ITransport # type: ignore

    def __init__(self):
        self.handshaked:bool = False
        self.session_id = ''

    def connectionMade(self):
        print("Connecting to server...")

        # Start the join loop
        self.join_loop = task.LoopingCall(self.server_join_setup)
        self.join_loop.start(1.0)

        
        
        

        # Example initial message
        #self.transport.write(b"HELLO_SERVER")
        #print("sending: HELLO_SERVER")


    def server_join_setup(self):
        ''' This loop waits and deals with initial connection to the server.
        It hands game logic to 'game_tick()' afterwards '''
        
        print('Attempting to handshake!')

        handshake_packet = {
            'packet_type': 'handshake',
            'player_name': self.factory.player_name
        }

        encoded = json.dumps(handshake_packet).encode('utf-8')
        self.sendString(encoded)
        


        ################
        # Exit condition
        if self.handshaked:
            print('Handshake done!')
            print("Connected to server!")
            # Start the game loop
            self.loop = task.LoopingCall(self.game_tick)
            self.loop.start(1.0 / TICK_RATE)
            self.join_loop.stop() # Stop this loop


    def game_tick(self):
        '''
        This runs at your TICK_RATE.
        Poll your game state here and send packets if needed.
        '''
        print('game tick')

        player_data = LATCH.get_player_data('altitude')

        #print(f'Player Altitude: {}')

        # Example: send a JSON state packet
        packet = {
            'packet_type': 'game',
            'entity': 'player',
            'px': LATCH.get_player_data('pos_east_west'),
            'py': LATCH.get_player_data('pos_north_south'),
            'altitude': LATCH.get_player_data('altitude'),
        }

        encoded = json.dumps(packet).encode('utf-8')
        self.sendString(encoded)


    def stringReceived(self, data):
        ''' Receive data from server. Called automatically by Twisted. '''
        print(f'Received -- {data}')
        conv_data = bytes_to_json(data)
        
        # Handshake procedure
        if (not self.handshaked):
            if conv_data['packet_type'] == 'handshake':
                if conv_data['handshake_status'] == 'complete':
                    self.handshaked = True
                    print('Handshake Completed!')
                    
        else:
            # decode data:
            conv_data = bytes_to_json(data)
            update_fields = [('px', 'pos_east_west'), ('py' ,'pos_north_south'), ('altitude', 'altitude')]
            if conv_data['packet_type'] == 'game':
                if conv_data['entity'] == 'pixy':
                    for field in update_fields:
                        pixy_entity = LATCH.pixy_entity
                        value = conv_data[field[0]]
                        LATCH.set_aircaft_data_float(value=value,
                                                    aircraft=pixy_entity,
                                                    field=field[1])



    def connectionLost(self, reason):
        print("Connection lost:", reason)
        try:
            if self.loop.running:
                self.loop.stop()
        except:
            print('fuck! main loop error!')
        
        try:
            if self.join_loop.running:
                self.join_loop.stop()
        except:
            print('fuck! join loop error!')

    


class GameClientFactory(protocol.ClientFactory):
    protocol = GameClient
    
    
    join_loop_successful:bool = False
    def __init__(self):
        self.player_name = 'UNNAMED'
        
        

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed:', reason)
        reactor.stop() # type: ignore

    def clientConnectionLost(self, connector, reason):
        print('Connection lost:', reason)
        reactor.stop() # type: ignore


def bytes_to_json(data:bytes) -> dict:
    '''
    Converts bytes received from the client into a JSON object (dict).
    Raises ValueError if the data is not valid JSON.
    '''
    try:
        text = data.decode("utf-8")
        return json.loads(text)
    except Exception as e:
        print("JSON decode error:", e)
        return {'': ''}
    

if __name__ == '__main__':
    reactor.connectTCP(SERVER_HOST, SERVER_PORT, GameClientFactory()) # type: ignore
    reactor.run() # type: ignore
