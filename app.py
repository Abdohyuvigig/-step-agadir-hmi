from flask import Flask, render_template
from flask_socketio import SocketIO
from plc_reader import read_all
from telegram_bot import check_alarmes
import paho.mqtt.client as mqtt
import threading, time, json
 
app = Flask(__name__)
sio = SocketIO(app, cors_allowed_origins="*")
 
# ── CONFIG HIVEMQ ──────────────────────────────────
MQTT_HOST   = "277a9bc1ee1e48f88ff42c82bdecb4c5.s1.eu.hivemq.cloud"
MQTT_PORT   = 8883
MQTT_USER   = "step_agadir"
MQTT_PASS   = "Step2025"
TOPIC_STATE = "step/agadir/state"
TOPIC_CMD   = "step/agadir/cmd/#"
 
# ── MQTT CLIENT ────────────────────────────────────
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.username_pw_set(MQTT_USER, MQTT_PASS)
mqttc.tls_set()
 
def on_connect(client, userdata, flags, rc, props):
    print("✅ HiveMQ connecté")
    client.subscribe(TOPIC_CMD)
 
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"📥 Commande reçue: {topic} = {payload}")
    sio.emit("cmd", {"topic": topic, "value": payload})
 
def on_disconnect(client, userdata, flags, rc, props):
    print("⚠️ HiveMQ déconnecté — reconnexion...")
 
mqttc.on_connect    = on_connect
mqttc.on_message    = on_message
mqttc.on_disconnect = on_disconnect
 
def mqtt_connect():
    try:
        mqttc.connect(MQTT_HOST, MQTT_PORT)
        mqttc.loop_start()
        print("✅ HiveMQ démarré")
    except Exception as e:
        print(f"❌ HiveMQ erreur: {e}")
 
# ── BOUCLE LECTURE PLC ─────────────────────────────
def plc_loop():
    while True:
        try:
            state = read_all()
            if state:
                sio.emit("update", state)
                mqttc.publish(TOPIC_STATE, json.dumps(state))
                check_alarmes(state)
        except Exception as e:
            print(f"❌ Erreur boucle: {e}")
        time.sleep(2)
 
@app.route("/")
def index():
    return render_template("STEP_HMI_v3.html")
 
if __name__ == "__main__":
    mqtt_connect()
    t = threading.Thread(target=plc_loop, daemon=True)
    t.start()
    print("🌐 Dashboard local: http://localhost:5000")
    sio.run(app, host="0.0.0.0", port=5000)