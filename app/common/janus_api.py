import requests
import json
import socket
import time
import os

from datetime import datetime
import calendar
import uuid as uuid
import base64
import hashlib
import hmac
import random
import string


# FIXME prendere le Config globali
JANUS_SCHEMA = "http"
JANUS_HOST = os.getenv("JANUS_SERVICE_HOST") if os.getenv("JANUS_SERVICE_HOST") is not None else "192.168.1.24"
JANUS_PORT = os.getenv("JANUS_SERVICE_PORT") if os.getenv("JANUS_SERVICE_PORT") is not None else "8088"
api_secret = os.getenv("JANUS_API_SECRET") if os.getenv("JANUS_API_SECRET") is not None else "janusrocks"

__version__ = '0.1.0'

janus_url = JANUS_SCHEMA + '://' + JANUS_HOST + ':' + str(JANUS_PORT) + '/janus'

insttemplate = {
    "session_id": None,
    "handle_id": None,
    "ports": None,
    "hosts": None,
    "streamer": None,
}


def random_string(length):
    return ''.join(random.choice(string.ascii_letters) for m in range(0, length))


def get_free_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0))
    addr, port = tcp.getsockname()
    tcp.close()
    return port


def get_transaction_id():
    return str("streaming-" + random_string(12))


def get_janus_token(realm, data=[], timeout=24 * 60 * 60):
    d = datetime.utcnow()
    expiry = calendar.timegm(d.utctimetuple()) + timeout
    str_plugin = ','.join(str(x) for x in data)
    strdata = ','.join(str(x) for x in [str(expiry), realm, str_plugin])
    hashed = hmac.new(realm.encode(), strdata.encode("utf-8"), hashlib.sha1)
    hashed = base64.b64encode(hashed.digest()).decode()
    return ":".join(str(x) for x in [strdata, hashed])


def new_inst():
    return insttemplate.copy()


definstance = new_inst()


def mypost(url, json_v):
    return requests.request(
        "POST",
        url,
        data=json.dumps(json_v),
        headers={"Content-Type": "application/json"},
        verify=False
    )


def janus_cmd(cmd, cond=False, action=lambda x: x, endpoint=""):
    if cond:
        print("misplaced call!")
    else:
        r = mypost(janus_url + endpoint, cmd)
        if not r:
            print("error in communication!")
        else:
            j = r.json()
            # print(json.dumps(j, indent=4, separators=(',', ': ')))
            action(j)
            return j


def greet(token, transaction, session=None):
    session = session or definstance

    def helper(j):
        print(j)
        session["session_id"] = j["data"]["id"]

    janus_cmd({"janus": "create",
               "transaction": transaction,
               "token": token}, action=helper)


def keep_alive(token, transaction, delay=0, session=None):
    session = session or definstance
    janus_cmd({"janus": "keepalive",
               "transaction": transaction,
               "token": token
               }, not session["session_id"],
              endpoint="/" + str(session["session_id"]))
    if delay > 0:
        for i in range(0, delay):
            time.sleep(1)
            keep_alive()


def attach_plugin(token, transaction, plugin="janus.plugin.streaming", session=None):
    session = session or definstance

    def helper(j):
        session["handle_id"] = j["data"]["id"]

    janus_cmd({"janus": "attach",
               "plugin": plugin,
               "token": token,
               "transaction": transaction},
              not session["session_id"],
              helper,
              endpoint="/" + str(session["session_id"]))


def create_session(token, transaction, plugin=None):
    greet(token, transaction)
    attach_plugin(token, transaction, plugin)



def list_feeds(token, transaction, id=None, session=None):
    session = session or definstance
    body = not id and {"request": "list"} or {"request": "list", "id": id}
    janus_cmd({"janus": "message",
               "transaction": transaction,
               "token": token,
               "body": body},
              not session["session_id"] or not session["handle_id"],
              endpoint="/" + str(session["session_id"]) + "/" + str(session["handle_id"]))


def create_feed(token, transaction, name_feed, id_feed, description, pin, audio_enabled=False, is_private=True, permanent=False,
                session=None):
    session = session or definstance

    response = False

    def helper(j):
        session["ports"] = []
        session["hosts"] = []

    while not response:

        random_vport = random.randint(10000, 10200)
        random_aport = random.randint(10000, 10200)
        print("CREATE FEED => random_vport : ", random_vport)
        print("CREATE FEED => random_aport : ", random_aport)
        print("CREATE FEED => id_feed : ", id_feed)

        result = janus_cmd({"janus": "message",
                            "transaction": transaction,
                            "token": token,
                            "body": {
                                "request": "create",
                                "type": "rtp",
                                "id": id_feed,
                                "name": str(name_feed),
                                "description": description,
                                "is_private": is_private,
                                "audio": audio_enabled,
                                "audioport": random_aport,
                                "audiortpmap": "OPUS/48000/2",
                                "audiopt": 111,
                                "video": True,
                                "data": False,
                                #"pin": str(pin),
                                "permanent": permanent,
                                "videoport": int(random_vport),
                                "videopt": 96,
                                "videortpmap": "H264/90000",
                                "videofmtp": "profile-level-id=42e028;packetization-mode=1"
                            }
                        }, not session["session_id"] or not session["handle_id"], helper,
                    endpoint="/" + str(session["session_id"]) + "/" + str(session["handle_id"]))
        print(result)
        if result['plugindata']['data']['streaming'] == "created":

            """
            PROTOTIPO JSON DI CREAZIONE FEED
            {
            'janus': 'success', 
            'session_id': 6725499797744819, 
            'transaction': 'tester.py', 
            'sender': 6671143667533536, 
            'plugindata': 
                        {'plugin': 'janus.plugin.streaming', 
                        'data': 
                                {'streaming': 'created', 
                                'created': '17f39c26-bbf0-11e8-b0c2-b8aeed9f2252', 
                                'permanent': False, 
                                'stream': 
                                        {'id': 1234, 
                                        'description': 'Prova creazione', 
                                        'type': 'live', 
                                        'is_private': True, 
                                        'video_port': 5999
                                        }
                                }
                        }
            }
            """
            response = True

    return result


def destroy_feed(token, transaction, id_feed, session=None):
    session = session or definstance
    if session is None:
        create_session()

    result = janus_cmd({"janus": "message",
                        "transaction": transaction,
                        "token": token,
                        "body": {
                            "request": "destroy",
                            "id": id_feed,
                            "permanent": True
                        }}, not session["session_id"] or not session["handle_id"],
                       endpoint="/" + str(session["session_id"]) + "/" + str(session["handle_id"]))
    return result


def detach_plugin(token, transaction, plugin="janus.plugin.streaming", session=None):
    session = session or definstance
    janus_cmd({"janus": "detach",
               "plugin": plugin,
               "token": token,
               "transaction": transaction
               }, not session["session_id"] or not session["handle_id"],
              endpoint="/" + str(session["session_id"]) + "/" + str(session["handle_id"]))


def streaming_recording(token, transaction, streaming_id, plugin="janus.plugin.streaming", state="enable", session=None):
    '''

    :param token:
    :param transaction:
    :param streaming_id:
    :param plugin:
    :param state:
    :param session:
    :return:

    message template to start recording
    {
        "request" : "recording",
        "action" : "start",
        "id" : <unique ID of the mountpoint to manipulate; mandatory>,
        "audio" : "<enable audio recording, and use this base path/filename; optional>",
        "video" : "<enable video recording, and use this base path/filename; optional>",
        "data" : "<enable data recording, and use this base path/filename; optional>",
    }

    message template to stop recording
    {
        "request" : "recording",
        "action" : "stop",
        "id" : <unique ID of the mountpoint to manipulate; mandatory>,
        "audio" : <true|false; whether or not audio recording should be stopped>,
        "video" : <true|false; whether or not video recording should be stopped>,
        "data" : <true|false; whether or not datachannel recording should be stopped>
    }

    '''

    session = session or definstance
    action = "start" if state == "enable" else "stop"

    janus_cmd(
        {
            "janus" : "message",
            "transaction": transaction,
            "token": token,
            "body": {
                "request": "recording",
                "action": action,
                "id": streaming_id,
                "video": str(streaming_id) if state == 'enable' else True
            }
         }, not session["session_id"] or not session["handle_id"],
              endpoint="/" + str(session["session_id"]) + "/" + str(session["handle_id"]))


# GESTIONE PLUGIN VIDEOROOM
def list_videorooms(token, transaction, id=None, session=None):

    session = session or definstance
    body = not id and {"request": "list"} or {"request": "list", "id": id}
    result = janus_cmd({"janus": "message",
                        "transaction": transaction,
                        "token": token,
                        "body": body},
                       not session["session_id"] or not session["handle_id"],
                       endpoint="/" + str(session["session_id"]) + "/" + str(session["handle_id"]))
    n_videoroom_arr = []

    if len(result['plugindata']['data']['list']) > 0:
        for i in result['plugindata']['data']['list']:
            n_videoroom_arr.append(int(i['room']))
        print(max(n_videoroom_arr))
        return max(n_videoroom_arr)+1

    else:
        return 1


def create_videoroom(token, transaction, description, vr_name, is_private=True, permanent=False, session=None):
    session = session or definstance
    response = False
    random_pin = random.randint(100000, 9999999999)
    print("CREATE PIN => random_pin: ", random_pin)
    random_secret = random_string(20)
    print("CREATE SECRET => random_secret: ", random_secret)

    def helper(j):
        session["n_videoroom"] = []

    while not response:

        result = janus_cmd({"janus": "message",
                            "transaction": transaction,
                            "token": token,
                            "body": {
                                "request": "create",
                                "room": vr_name,
                                "max_publishers": 1,
                                "permanent": permanent,
                                "description": description,
                                "secret": random_secret,
                                "pin": str(random_pin),
                                "is_private": is_private,
                                "bitrate": 512000,
                                "audiolevel_ext": False,
                                "videoorient_ext": False,
                                "playoutdelay_ext": False,
                                "fir_freq": 10,
                                "record": True,
                                "rec_dir": "/tmp/",
                                "audiocodec": "opus,pcmu",
                                "videocodec": "vp8,vp9,h264"

        }
                            }, not session["session_id"] or not session["handle_id"], helper,
                           endpoint="/" + str(session["session_id"]) + "/" + str(session["handle_id"]))

        if result['plugindata']['data']['videoroom'] == "event":
            print("qualcosa non va")

        elif result['plugindata']['data']['videoroom'] == "created":
            print("apposto mbare")
            response = True

    return vr_name, random_pin, random_secret


def destroy_videoroom(token, transaction, vr_name, secret, permanent=True, session=None):
    session = session or definstance

    def helper(j):
        session["n_videoroom"] = []

    """
    {
        "request" : "destroy",
        "room" : <unique numeric ID of the room to destroy>,
        "secret" : "<room secret, mandatory if configured>",
        "permanent" : <true|false, whether the room should be also removed from the config file, default false>
    }
    """
    result = janus_cmd({"janus": "message",
                        "transaction": transaction,
                        "token": token,
                        "body": {
                            "request": "destroy",
                            "room": vr_name,
                            "permanent": permanent,
                            "secret": secret,
                            }
                        }, not session["session_id"] or not session["handle_id"], helper,
                       endpoint="/" + str(session["session_id"]) + "/" + str(session["handle_id"]))

    if result['plugindata']['data']['videoroom'] == "event":
        return "qualcosa non va"

    elif result['plugindata']['data']['videoroom'] == "created":
        return "apposto mbare"


if __name__ == "__main__":
    _token = get_janus_token('janus', ['janus.plugin.streaming'])
    _transaction = str("streaming-" + random_string(12))
    _name_feed = uuid.uuid1(node=None, clock_seq=None)
    _id_feed = random.getrandbits(32)
    _description_feed = "Prova creazione"
    _pin_feed = "0000"
    _is_private = True

    create_session(_token, _transaction, "janus.plugin.streaming")
    _id_feed = 791412856
    streaming_recording(_token, _transaction, _id_feed, state='enable')
    #result = create_feed(_token, _transaction, _name_feed, _id_feed, _description_feed, _pin_feed, _is_private)
    #print(json.dumps(result, indent=4, separators=(',', ': ')))
    #result = destroy_feed(_token, _transaction, _id_feed)
    #print(json.dumps(result, indent=4, separators=(',', ': ')))


