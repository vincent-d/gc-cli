#!/usr/bin/env python3

import argparse
import sys
import requests
import tabulate
import json

class Mondo:
    # 0:  title
    INDEX_TITLE = 0
    # 1:  icon
    # 2:  type
    INDEX_TYPE = 2
    # 3:  containerType
    # 4:  containerPlayable
    # 5:  personType
    # 6:  albumType
    # 7:  imageType
    # 8:  audioType
    INDEX_AUDIOTYPE = 8
    # 9:  videoType
    # 10: epgType
    # 11: modifiable
    # 12: disabled
    # 13: flags
    # 14: path
    INDEX_PATH = 14
    # 15: value
    INDEX_VALUE = 15
    # 16: valueOperation()
    # 17: edit
    INDEX_EDIT = 17
    # 18: mediaData
    INDEX_MEDIADATA = 18
    # 19: query
    # 20: activate
    # 21: likeIt
    # 22: rowsOperation
    # 23: setRoles
    # 24: timestamp
    # 25: id
    # 26: valueUnit
    # 27: context
    # 28: description
    # 29: longDescription
    # 30: search
    # 31: valueBlob
    # 32: prePlay
    # 33: activity
    # 34: cancel
    # 35: accept
    # 36: risky
    # 37: preferred
    # 38: httpRequest
    # 39: encrypted
    # 40: encryptedValue
    # 41: rating
    # 42: fillParent
    # 43: autoCompletePath
    # 44: busyText
    # 45: sortKey
    # 46: renderAsButton
    # 47: doNotTrack
    # 48: persistentMetaData
    # 49: releaseDate
    # 50: audioType
    # 51: unknownSize
    ROLES = 'title,icon,type,containerType,containerPlayable,personType,albumType,imageType,audioType,videoType,' \
            'epgType,modifiable,disabled,flags,path,value,valueOperation(),edit,mediaData,query,' \
            'activate,likeIt,rowsOperation,setRoles,timestamp,id,valueUnit,context,description,longDescription,' \
            'search,valueBlob,prePlay,activity,cancel,accept,risky,preferred,httpRequest,encrypted,' \
            'encryptedValue,rating,fillParent,autoCompletePath,busyText,sortKey,renderAsButton,doNotTrack,persistentMetaData,releaseDate,' \
            'audioType,unknownSize'

    def __init__(self, hostname):
        self.hostname = 'http://' + hostname

    def get_data(self, path):
        params = { 'path': path, 'roles': self.ROLES }
        return requests.get(self.hostname + '/api/getData', params=params)

    def get_rows(self, path, from_= 0, to = 20):
        params = { 'path': path, 'roles': self.ROLES, 'from': from_, 'to': to }
        return requests.get(self.hostname + '/api/getRows', params=params)

    def set_data(self, path, value, role='activate'):
        params = { 'path': path, 'role': role, 'value': value }
        return requests.get(self.hostname + '/api/setData', params=params)

    def stop_playing(self):
        params = { 'control': 'stop' }
        resp = self.set_data('player:player/control', value=json.dumps(params))
        if (resp.status_code != 200):
            print("Error when stopping")
        else:
            print("Playing stopped")

    def get_current(self):
        current = self.get_data('player:player/data')
        if (current.status_code != 200):
            return None
        return current.json()

    def get_presets(self):
        presets = self.get_rows('/app:/presets')
        if (presets.status_code != 200):
            return None
        return presets.json()

    def print_current(self):
        current = self.get_current()
        if (current == None):
            print("Error while getting current")
        else:
            if ('mediaRoles' in current[self.INDEX_VALUE]):
                print("Currently playing: {}".format(current[self.INDEX_VALUE]['mediaRoles']['title']))
            else:
                print("Nothing is playing")

    def get_volume(self):
        volume = self.get_data('player:volume')
        if (volume.status_code != 200):
            return None
        else:
            volume = volume.json()
            return int(volume[self.INDEX_VALUE]['i32_']), int(volume[self.INDEX_EDIT]['max'])

    def print_volume(self):
        vol, max = self.get_volume()
        if (vol != None):
            print("Current volume: {}/{}".format(vol, max))
        else:
            print("Error when getting volume")

    def set_volume(self, val):
        vol, max = self.get_volume()
        if (vol == None):
            print("Error when setting volume")
            return
        if (val > max):
            val = max
        value = { 'type': 'i32_', 'i32_': val }
        self.set_data('player:volume', role='value', value=json.dumps(value))

    def print_presets(self):
        presets = self.get_presets()
        presets_array = []
        cnt = 1
        for p in presets['rows']:
            presets_array.append([cnt, p[0]])
            cnt += 1
        print(tabulate.tabulate(presets_array, headers=['#', 'Radio']))

    def set_presets(self, index):
        presets = self.get_presets()
        if (presets == None):
            print("Error getting presets")
            return None
        radio = presets['rows'][index - 1]
        name = radio[self.INDEX_TITLE]
        path = radio[self.INDEX_PATH]
        media_data = radio[self.INDEX_MEDIADATA]
        audio_type = radio[self.INDEX_AUDIOTYPE]
        container_type = radio[self.INDEX_TYPE]
        print('Playing preset #{}: {}'.format(index, name))
        params = {
                    'control': 'play',
                    'mediaRoles': {
                        'title': name,
                        'type': container_type,
                        'audioType': audio_type,
                        'modifiable': True,
                        'path': path,
                        'mediaData': media_data
                    }
                }
        resp = self.set_data('player:player/control', value=json.dumps(params))
        if (resp.status_code != 200):
            print("Error while setting preset #{}: {}", index, name)


def main(argv):
    parser = argparse.ArgumentParser(description='Control your radio')
    parser.add_argument('-a', '--address', help='hostname or IP address of the radio', required=True)
    parser.add_argument('-p', '--play', help='Preset to play', type=int, default=None)
    parser.add_argument('-l', '--list', help='List presets', action='store_true')
    parser.add_argument('-s', '--stop', help='Stop playing', action='store_true')
    parser.add_argument('-v', '--volume', help='Get or set volume level', nargs='?', const=-1, default=None, type=int)
    args = parser.parse_args(argv)

    mondo = Mondo(args.address)

    if (args.play != None):
        mondo.set_presets(args.play)
    elif (args.list == True):
        mondo.print_presets()
    elif (args.stop == True):
        mondo.stop_playing()
    else:
        mondo.print_current()

    if (args.volume != None):
        if (args.volume == -1):
            mondo.print_volume()
        else:
            mondo.set_volume(args.volume)

if __name__ == "__main__":
    main(sys.argv[1:])
