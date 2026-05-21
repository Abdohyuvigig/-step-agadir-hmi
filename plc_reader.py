import openpyxl
import os

XLSX_PATH = "plc_data.xlsx"

NAME_MAP = {
    "Q_Pompe01_Run":           "P01_Run",
    "Q_Pompe02_Run":           "P02_Run",
    "Q_Voyant_P01_Marche":     "Voyant_P01_Marche",
    "Q_Voyant_P02_Marche":     "Voyant_P02_Marche",
    "Q_Voyant_P01_Defaut":     "Voyant_P01_Defaut",
    "Q_Voyant_P02_Defaut":     "Voyant_P02_Defaut",
    "Q_Tamis_MoteurRun":       "Tamis_Run",
    "Q_Tamis_EV_Nettoyage":    "Tamis_EV",
    "Q_Compresseur_Run":       "Compresseur",
    "Q_Pompe03_Run":           "P03_Run",
    "Q_Pompe04_Run":           "P04_Run",
    "Q_Pompe05_Run":           "P05_Run",
    "Q_Pompe06_Run":           "P06_Run",
    "Q_Pompe07_Run":           "P07_Run",
    "Q_Pompe08_Run":           "P08_Run",
    "Q_UV_Run":                "UV_Run",
    "Q_DosPreChlor_Run":       "DosPreChlor",
    "Q_DosPostChlor_Run":      "DosPostChlor",
    "Q_Klaxon":                "Klaxon",
    "Q_Voyant_Alarme_General": "Voyant_Alarme",
    "Q_Voyant_Marche_General": "Voyant_Marche_General",
    "Q_VanneNO_Ouvrir":        "Vanne_NO",
    "Q_VanneNF_Ouvrir":        "Vanne_NF",
    "Q_VanneEpais_Ouvrir":     "Vanne_Epais",
}

def read_all():
    result = {}
    try:
        if not os.path.exists(XLSX_PATH):
            print("❌ plc_data.xlsx introuvable")
            return {}

        wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=1, values_only=True):
            if not row[0]:
                continue
            # Nettoyer le nom : enlever guillemets
            raw_name = str(row[0]).strip().replace('"', '').replace("'", "")
            raw_val  = str(row[4]).strip() if row[4] is not None else "FALSE"

            if raw_name in NAME_MAP:
                result[NAME_MAP[raw_name]] = (raw_val.upper() == "TRUE")

        print(f"✅ Lu {len(result)} variables")

    except Exception as e:
        print(f"❌ Erreur lecture: {e}")

    return result