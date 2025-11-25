''' This module is responsible for latching onto the game memory
and manipulate its data '''

import pymem as pm


class Aircraft:
    def __init__(self, struct_start_add, objstring_add):
        self.struct_start_add = struct_start_add

        self.data = {
            'struct_start': self.struct_start_add,
            'pos_east_west': self.struct_start_add + 0x260,
            'altitude': self.struct_start_add + 0x264,
            'pos_north_south': self.struct_start_add + 0x268,
            'unk1': self.struct_start_add + 0x26C,
            'unk2': self.struct_start_add + 0x270,
            'yaw': self.struct_start_add + 0x274,
            'roll': self.struct_start_add + 0x278,
            'unk3': self.struct_start_add + 0x27C,
            'obj_string': objstring_add
        }
    
    def get_address(self, query):
        out = self.data[query]
        return out


class GameLatch():
    def __init__(self, process_name):
        self.PM_SESSION = pm.Pymem(process_name)
        self.detect()
        
        self.player_entity:Aircraft
        self.pixy_entity:Aircraft

    def find_earlier_address(self, add_compare, list_compare):
        '''Finds in a 'list_compare' the address the biggest number before 'add_compare' '''
        for i in range(len(list_compare)): # type: ignore
            if list_compare[i] > add_compare: # type: ignore
                if i == 0:
                    return list_compare[i] # type: ignore
                else:
                    return list_compare[i-1] # type: ignore

    def detect(self):
        ''' Runs a routine to detect the location of useful flags'''

        # Search pattern flags
        spawnable_objstring_pattern = b'\x4C\x42'
        player_objstring_pattern = b'\x4C\x42player'
        pixy_objstring_pattern = b'\x4C\x42pixy'
        plane_struct_begin_pattern = b'\xF0\xB2\x3C\x00'

        # List of objects addresses
        all_spawnables_add = self.PM_SESSION.pattern_scan_all(spawnable_objstring_pattern, return_multiple=True)
        all_spawnables_add = self.PM_SESSION.pattern_scan_all(spawnable_objstring_pattern, return_multiple=True)
        all_plane_struct_begins_add = self.PM_SESSION.pattern_scan_all(plane_struct_begin_pattern, return_multiple=True)

        
        # Search for player struct start
        player_airc = None
        player_objstring_add = self.PM_SESSION.pattern_scan_all(player_objstring_pattern)
        player_structstart_add = self.find_earlier_address(player_objstring_add, all_plane_struct_begins_add)
        player_airc = Aircraft(player_structstart_add, player_objstring_add)
        #player_altitude = self.PM_SESSION.read_float(player_airc.get_address('altitude'))
        #print(f'Player struct: {hex(player_structstart_add)} | altitude: {player_altitude}') # type: ignore
        self.player_entity = player_airc # Assign to member variable
        
        
        # Only proceed with Pixy's data if he is present in the map
        # TODO: Do the same to PJ later
        pixy_airc = None
        pixy_objstring_add = self.PM_SESSION.pattern_scan_all(pixy_objstring_pattern)
        if pixy_objstring_add != None:
            pixy_structstart_add = self.find_earlier_address(pixy_objstring_add, all_plane_struct_begins_add)
            pixy_airc = Aircraft(pixy_structstart_add, player_objstring_add)
            #pixy_altitude = self.PM_SESSION.read_float(pixy_airc.get_address('altitude'))
            #print(f'Pixy struct: {hex(pixy_structstart_add)} | altitude: {pixy_altitude}') # type: ignore
            self.pixy_entity = pixy_airc # Assign to member variable        
        

    def get_aircaft_data(self, aircraft:Aircraft, field:str):
        if aircraft != None:
            address = aircraft.get_address(field)
            return self.PM_SESSION.read_float(address)
        else:
            return None
    def get_player_data(self, field:str):
        return self.get_aircaft_data(self.player_entity, field)
    
    def set_aircaft_data_float(self, value, aircraft:Aircraft, field:str):
        if aircraft == None:
            return None
        
        address = aircraft.get_address(field)
        self.PM_SESSION.write_float(value=value,address=address)
    pass



if __name__ == '__main__':
    GAME_PROCESS_NAME = "pcsx2.exe"
    latch = GameLatch(process_name=GAME_PROCESS_NAME)
    
    print(f'Player Altitude: {latch.get_player_data('altitude')}')
    

