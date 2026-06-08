import snap7
from snap7 import util
import struct

# ── CONFIG ─────────────────────────────────────────
PLC_IP   = "172.16.17.68"
PLC_RACK = 0
PLC_SLOT = 1  # S7-1500

# DB Numbers — confirmés depuis TIA Portal
DB_SORTIES     = 9   # DB_Sorties [DB9]
DB_ANALOGIQUES = 1   # DB_Analogiques [DB1]

# Mapping DB_Sorties — (byte, bit)
Q_MAP = {
    "P01_Run":               (0, 0),
    "P02_Run":               (0, 1),
    "Voyant_P01_Marche":     (0, 2),
    "Voyant_P02_Marche":     (0, 3),
    "Voyant_P01_Defaut":     (0, 4),
    "Voyant_P02_Defaut":     (0, 5),
    "Tamis_Run":             (0, 6),
    "Tamis_EV":              (0, 7),
    "Voyant_Tamis_Marche":   (1, 0),
    "Voyant_Tamis_Defaut":   (1, 1),
    "Voyant_Tamis_Securite": (1, 2),
    "Compresseur":           (1, 3),
    "P03_Run":               (1, 4),
    "P04_Run":               (1, 5),
    "Voyant_Comp_Marche":    (1, 6),
    "Voyant_Comp_Defaut":    (1, 7),
    "P05_Run":               (2, 2),
    "P06_Run":               (2, 5),
    "P07_Run":               (2, 6),
    "P08_Run":               (2, 7),
    "Vanne_NO":              (3, 0),
    "Vanne_NF":              (3, 1),
    "DosPreChlor":           (3, 2),
    "DosPostChlor":          (3, 3),
    "UV_Run":                (3, 4),
    "Klaxon":                (4, 4),
    "Voyant_Alarme":         (4, 5),
    "Voyant_Marche_General": (4, 6),
}

plc = snap7.client.Client()
connected = False

def connect():
    global connected
    try:
        plc.connect(PLC_IP, PLC_RACK, PLC_SLOT)
        connected = True
        print(f"✅ snap7 connecté: {PLC_IP}")
    except Exception as e:
        connected = False
        print(f"❌ snap7 erreur connexion: {e}")

def read_all():
    global connected
    if not connected:
        connect()
    if not connected:
        return {}

    result = {}
    try:
        # Lire DB_Sorties [DB9] — 5 bytes
        data = plc.db_read(DB_SORTIES, 0, 5)
        for name, (byte, bit) in Q_MAP.items():
            result[name] = util.get_bool(data, byte, bit)

        # Lire DB_Analogiques [DB1] — REDOX + Débit
        try:
            data_a = plc.db_read(DB_ANALOGIQUES, 0, 4)
            redox_raw = struct.unpack('>h', bytes(data_a[0:2]))[0]
            debit_raw = struct.unpack('>h', bytes(data_a[2:4]))[0]
            result["REDOX_mV"]  = round(-2000 + (redox_raw / 27648) * 4000, 1)
            result["Debit_m3h"] = round(0.25  + (debit_raw / 27648) * 2.25,  3)
        except Exception as e:
            result["REDOX_mV"]  = 0.0
            result["Debit_m3h"] = 0.0

        print(f"✅ Lu {len(result)} variables snap7 temps réel")

    except Exception as e:
        print(f"❌ Erreur lecture snap7: {e}")
        connected = False

    return result
