import paho.mqtt.client as mqtt
import mongoengine
from app.models import device, organization
import json
from config import config

# TODO env variable
conf = config["development"]

mqtt_sub_topic = "/+/devices-status"

mongoengine.connect(
    db=conf.MONGODB_SETTINGS['db'],
    host=conf.MONGODB_SETTINGS['host'],
    port=conf.MONGODB_SETTINGS['port']
)


def on_mqtt_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(mqtt_sub_topic)


def on_mqtt_message(client, userdata, msg):

    payload = json.loads(msg.payload.decode("utf-8"))

    print(msg.topic + " " + str(payload))

    org = msg.topic.split("/")[1]
    serial = payload['serial']
    status = payload['state']

    org_obj = organization.Organization.objects(domain=org).first()

    dev_obj = device.Device.objects(
        name=serial,
        organization=org_obj
    ).first()

    dev_obj.status = status
    dev_obj.save()


if __name__ == '__main__':

    # MQTT configuration
    client_mqtt = mqtt.Client()

    client_mqtt.username_pw_set(
        username=conf.MQTT_BROKER_SETTINGS['username'],
        password=conf.MQTT_BROKER_SETTINGS['password']
    )

    client_mqtt.on_connect = on_mqtt_connect
    client_mqtt.on_message = on_mqtt_message
    client_mqtt.connect(
        conf.MQTT_BROKER_SETTINGS['hostname'],
        conf.MQTT_BROKER_SETTINGS['port'],
        60
    )

    client_mqtt.loop_forever()



