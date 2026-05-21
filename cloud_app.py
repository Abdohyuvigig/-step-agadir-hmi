rom flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json, os
 
app = Flask(__name__)
sio = SocketIO(app, cors_allowed_origins="*")
 
# ── CONFIG HIVEMQ ──────────────────────────────────
MQTT_HOST   = "277a9bc1ee1e48f88ff42c82bdecb4c5.s1.eu.hivemq.cloud"
MQTT_PORT   = 8883
MQTT_USER   = "step_agadir"
MQTT_PASS   = "Step2025"
TOPIC_STATE = "step/agadir/state"
TOPIC_CMD   = "step/agadir/cmd"
 
last_state = {}
 
# ── MQTT CLIENT ────────────────────────────────────
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.username_pw_set(MQTT_USER, MQTT_PASS)
mqttc.tls_set()
 
def on_connect(client, userdata, flags, rc, props):
    client.subscribe(TOPIC_STATE)
    print("✅ Cloud HiveMQ connecté")
 
def on_message(client, userdata, msg):
    global last_state
    try:
        last_state = json.loads(msg.payload.decode())
        sio.emit("update", last_state)
    except Exception as e:
        print(f"❌ Erreur message: {e}")
 
mqttc.on_connect = on_connect
mqttc.on_message = on_message
 
try:
    mqttc.connect(MQTT_HOST, MQTT_PORT)
    mqttc.loop_start()
    print("✅ MQTT démarré")
except Exception as e:
    print(f"❌ MQTT erreur: {e}")
 
# ── ROUTES ─────────────────────────────────────────
@app.route("/")
def index():
    return render_template("STEP_HMI_v3.html")
 
@app.route("/health")
def health():
    return {"status": "ok", "equipements": len(last_state)}
 
# ── COMMANDES DEPUIS DASHBOARD → PLC ───────────────
@sio.on("send_cmd")
def send_cmd(data):
    try:
        topic = f"{TOPIC_CMD}/{data['cmd']}"
        mqttc.publish(topic, str(data['value']))
        print(f"📤 Commande: {topic} = {data['value']}")
    except Exception as e:
        print(f"❌ Erreur commande: {e}")
 
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    sio.run(app, host="0.0.0.0", port=port)