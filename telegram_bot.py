import requests

# 1. Va sur Telegram, cherche @BotFather
# 2. Tape /newbot, suis les instructions
# 3. Copie le token ici
BOT_TOKEN = "METS_TON_TOKEN_ICI"

# 4. Cherche @userinfobot sur Telegram
# 5. Tape /start, copie ton Chat ID ici
CHAT_ID = "METS_TON_CHAT_ID_ICI"

# Mémoriser les alarmes déjà envoyées
alarmes_envoyees = set()

MESSAGES_ALARMES = {
    "Klaxon":       "🚨 KLAXON — Niveau maximum relevage dépassé !",
    "P01_Defaut":   "🔴 ALM01 — Défaut pompe P01. Vérifier disjoncteur.",
    "P02_Defaut":   "🔴 ALM02 — Défaut pompe P02. Vérifier disjoncteur.",
    "Tamis_Defaut": "🔴 ALM04 — Défaut moteur tamis rotatif.",
    "Comp_Defaut":  "🔴 ALM06 — Défaut compresseur FPZ R-30.",
    "UV_Defaut":    "⚠️ ALM16 — Défaut lampe UV 40W. Vérifier/remplacer.",
    "FILSA_Max":    "⚠️ ALM17 — Niveau max FILSA. Fermer vanne épaississeur.",
}

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": f"🏭 STEP LafargeHolcim Agadir\n\n{message}",
            "parse_mode": "HTML"
        })
        print(f"📨 Telegram envoyé : {message}")
    except Exception as e:
        print(f"❌ Erreur Telegram : {e}")

def check_alarmes(state):
    # Klaxon actif
    if state.get("Klaxon") and "Klaxon" not in alarmes_envoyees:
        send_telegram(MESSAGES_ALARMES["Klaxon"])
        alarmes_envoyees.add("Klaxon")
    elif not state.get("Klaxon"):
        alarmes_envoyees.discard("Klaxon")
    
    # UV défaut
    if state.get("UV_Defaut") and "UV_Defaut" not in alarmes_envoyees:
        send_telegram(MESSAGES_ALARMES["UV_Defaut"])
        alarmes_envoyees.add("UV_Defaut")
    elif not state.get("UV_Defaut"):
        alarmes_envoyees.discard("UV_Defaut")