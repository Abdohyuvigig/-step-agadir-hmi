from flask import Flask, render_template
from flask_socketio import SocketIO
from plc_reader import read_all
from telegram_bot import check_alarmes
import paho.mqtt.client as mqtt
import threading, time, json, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)
sio = SocketIO(app, cors_allowed_origins="*")

# ── CONFIG HIVEMQ ──────────────────────────────────
MQTT_HOST   = "277a9bc1ee1e48f88ff42c82bdecb4c5.s1.eu.hivemq.cloud"
MQTT_PORT   = 8883
MQTT_USER   = "step_agadir"
MQTT_PASS   = "Step2025"
TOPIC_STATE = "step/agadir/state"
TOPIC_CMD   = "step/agadir/cmd/#"

XLSX_PATH = os.path.join(os.path.dirname(__file__), "plc_data.xlsx")

# ── MQTT ───────────────────────────────────────────
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.username_pw_set(MQTT_USER, MQTT_PASS)
mqttc.tls_set()

def on_connect(client, userdata, flags, rc, props):
    print("✅ HiveMQ connecté")
    client.subscribe(TOPIC_CMD)

def on_message(client, userdata, msg):
    sio.emit("cmd", {"topic": msg.topic, "value": msg.payload.decode()})

mqttc.on_connect = on_connect
mqttc.on_message = on_message

def mqtt_connect():
    try:
        mqttc.connect(MQTT_HOST, MQTT_PORT)
        mqttc.loop_start()
        print("✅ HiveMQ démarré")
    except Exception as e:
        print(f"❌ HiveMQ erreur: {e}")

# ── LECTURE ET ENVOI ────────────────────────────────
def send_state():
    try:
        state = read_all()
        if state:
            sio.emit("update", state)
            mqttc.publish(TOPIC_STATE, json.dumps(state))
            check_alarmes(state)
            print(f"✅ Données envoyées: {len(state)} variables")
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")

# ── WATCHDOG — surveille le fichier Excel ───────────
class ExcelHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_sent = 0

    def on_modified(self, event):
        # Déclenche quand plc_data.xlsx est modifié
        if 'plc_data' in event.src_path and event.src_path.endswith('.xlsx'):
            now = time.time()
            # Anti-rebond : pas plus d'une lecture par seconde
            if now - self.last_sent > 1:
                self.last_sent = now
                print(f"📂 Excel modifié détecté — lecture automatique!")
                time.sleep(0.5)  # attendre fin écriture
                send_state()

    def on_created(self, event):
        # Déclenche aussi si le fichier est recréé (Save As)
        if 'plc_data' in event.src_path and event.src_path.endswith('.xlsx'):
            print(f"📂 Nouveau fichier Excel détecté!")
            time.sleep(0.5)
            send_state()

def start_watchdog():
    watch_dir = os.path.dirname(XLSX_PATH)
    handler = ExcelHandler()
    observer = Observer()
    observer.schedule(handler, watch_dir, recursive=False)
    observer.start()
    print(f"👁️ Surveillance automatique: {watch_dir}")
    print(f"   → Dès que tu exportes plc_data.xlsx, le dashboard se met à jour !")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# ── BOUCLE BACKUP toutes les 10s ───────────────────
def backup_loop():
    while True:
        time.sleep(10)
        send_state()

# ── ROUTES ─────────────────────────────────────────
@app.route("/")
def index():
    return render_template("STEP_HMI_v3.html")

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    mqtt_connect()

    # Watchdog dans un thread
    t1 = threading.Thread(target=start_watchdog, daemon=True)
    t1.start()

    # Backup loop dans un thread
    t2 = threading.Thread(target=backup_loop, daemon=True)
    t2.start()

    # Lecture initiale au démarrage
    time.sleep(1)
    send_state()

    print("🌐 Dashboard local: http://localhost:5000")
    sio.run(app, host="0.0.0.0", port=5000)
