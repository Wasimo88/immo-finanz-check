import streamlit as st
import pandas as pd
import plotly.express as px
import json
from fpdf import FPDF

# --- KONFIGURATION ---
st.set_page_config(page_title="Immo-Finanz Master Pro", layout="wide")

# ==========================================
# 🧠 INTELLIGENTE LOGIK (CALLBACKS)
# ==========================================
# Diese Funktionen sorgen dafür, dass sich die Zahlen ÄNDERN, 
# wenn du oben die Personen oder qm änderst.

def update_lebenshaltung():
    """Berechnet Lebenshaltung neu, wenn Personen geändert werden"""
    erw = st.session_state.sb_erwachsene
    kind = st.session_state.sb_kinder
    
    # Bank-Standards
    basis = 1200 if erw == "Alleinstehend" else 1600
    kinder_kosten = kind * 400
    
    st.session_state.exp_p_lebenshaltung = float(basis + kinder_kosten)

def update_bewirtschaftung():
    """Berechnet Nebenkosten neu, wenn qm geändert werden"""
    qm = st.session_state.sb_wohnflaeche
    # Faustformel: 4,00 € pro qm
    st.session_state.exp_bewirt = float(qm * 4.0)

# ==========================================
# 🛠 HELFER
# ==========================================
def eur(wert):
    return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def pdf_eur(wert):
    return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " EUR"

# ==========================================
# 🔒 PASSWORD
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = None
    if st.session_state.password_correct == True:
        return True
    
    def password_entered():
        if st.session_state["password_input"] == st.secrets["password"]:
            st.session_state.password_correct = True
            del st.session_state["password_input"]
        else:
            st.session_state.password_correct = False

    st.text_input("🔒 Passwort", type="password", on_change=password_entered, key="password_input")
    if st.session_state.password_correct == False:
        st.error("Falsches Passwort.")
    return False

if not check_password():
    st.stop()

# ==========================================
# 📄 PDF GENERATOR (MIT DETAILS)
# ==========================================
class PDF(FPDF):
    def header(self):
        self.set_fill_color(28, 58, 106)
        self.rect(0, 0, 210, 25, 'F')
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'Finanzierungs-Zertifikat', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Seite {self.page_no()}', 0, 0, 'C')
        self.set_x(-40)
        self.cell(30, 10, 'WA | 2026', 0, 0, 'R')

def create_pdf(data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    col_header = (44, 62, 80)
    col_text = (0, 0, 0)
    col_fill = (240, 240, 240)
    col_note = (100, 100, 100) # Grau für Anmerkungen

    def txt(text):
        return text.encode('latin-1', 'replace').decode('latin-1')

    # KOPF DATEN
    pdf.set_text_color(*col_header)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt(f"Analyse für: {data['name']}"), ln=True)
    pdf.set_text_color(*col_text)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, txt(f"Szenario: {data['scenario']}"), ln=True)
    pdf.ln(5)

    # 1. HAUSHALTSRECHNUNG
    pdf.set_fill_color(*col_fill)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*col_header)
    pdf.cell(0, 8, txt("1. Monatliche Haushaltsrechnung"), 0, 1, 'L', True)
    pdf.ln(2)

    # Einnahmen
    pdf.set_text_color(*col_text)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(120, 6, txt("Gesamteinnahmen (Netto):"), 0)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(70, 6, txt(f"+ {pdf_eur(data['ein'])}"), 0, 1, 'R')
    pdf.ln(2)

    # Ausgaben Detail
    pdf.set_text_color(*col_text)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt("Ausgaben (Detailliert):"), 0, 1)
    
    # Funktion für Zeilen
    def row(label, val, note=""):
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(100, 6, txt(label))
        pdf.cell(30, 6, txt(pdf_eur(val)), 0, 0, 'R')
        if note:
            pdf.set_font("Arial", "I", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(60, 6, txt(f"  ({note})"), 0, 0, 'L')
        pdf.ln()

    # Positionen
    row("Lebenshaltung (Pauschale)", data['aus_leben'], "Nahrung, Kleidung, Gesundheit, Mobilität")
    row("Bewirtschaftung (Hauskosten)", data['aus_bewirt'], f"Heizung, Wasser, Müll ({data['qm']} qm)")
    
    if data['aus_miete'] > 0:
        row("Aktuelle Kaltmiete", data['aus_miete'], "Bleibt bestehen")
    if data['aus_bestand'] > 0:
        row("Rate Bestandskredit", data['aus_bestand'])
    if data['aus_bauspar'] > 0:
        row("Sparrate (Pflicht)", data['aus_bauspar'], "Tilgungsersatz/Bausparer")
    if data['aus_konsum'] > 0:
        row("Konsumkredite", data['aus_konsum'], "Auto, Möbel, etc.")
    
    row("Puffer / Instandhaltung", data['aus_puffer'])

    # Summe Ausgaben
    pdf.ln(1)
    pdf.cell(100, 0, "", "T") # Linie
    pdf.cell(30, 0, "", "T")
    pdf.ln(1)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(100, 6, txt("Summe Ausgaben:"))
    pdf.set_text_color(180, 0, 0)
    pdf.cell(30, 6, txt(f"- {pdf_eur(data['aus'])}"), 0, 1, 'R')

    # ERGEBNIS
    pdf.ln(4)
    pdf.set_fill_color(230, 240, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*col_header)
    pdf.cell(120, 10, txt("Verfügbarer Betrag (Freie Rate):"), 0, 0, 'L', True)
    pdf.cell(70, 10, txt(f"{pdf_eur(data['frei'])}"), 0, 1, 'R', True)
    pdf.ln(8)

    # 2. VERGLEICH (WENN VORHANDEN)
    if data['diff_miete'] is not None:
         pdf.set_fill_color(*col_fill)
         pdf.set_font("Arial", "B", 12)
         pdf.set_text_color(*col_header)
         pdf.cell(0, 8, txt("2. Vergleich: Miete vs. Eigentum"), 0, 1, 'L', True)
         pdf.ln(2)
         
         pdf.set_text_color(0,0,0)
         pdf.set_font("Arial", "", 10)
         pdf.cell(100, 6, txt("Bisherige Warmmiete:"))
         pdf.cell(30, 6, txt(pdf_eur(data['alt_warm'])), 0, 1, 'R')
         
         pdf.cell(100, 6, txt("Neue Belastung (Rate + Nebenkosten):"))
         pdf.cell(30, 6, txt(pdf_eur(data['neu_last'])), 0, 1, 'R')
         
         diff = data['diff_miete']
         if diff > 0:
             pdf.set_text_color(180, 0, 0)
             pdf.set_font("Arial", "B", 10)
             pdf.cell(0, 8, txt(f"-> Mehrbelastung: {pdf_eur(diff)}"), 0, 1)
         else:
             pdf.set_text_color(0, 100, 0)
             pdf.set_font("Arial", "B", 10)
             pdf.cell(0, 8, txt(f"-> Ersparnis: {pdf_eur(abs(diff))}"), 0, 1)
         pdf.ln(5)

    # 3. MAX KAUFPREIS
    pdf.set_fill_color(*col_fill)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*col_header)
    pdf.cell(0, 8, txt("3. Maximaler Kaufpreis (Kalkulation)"), 0, 1, 'L', True)
    pdf.ln(2)

    pdf.set_text_color(0,0,0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, txt(f"Basis: {data['zins']}% Zins | {data['tilg']}% Tilgung"), ln=True)
    pdf.ln(2)

    pdf.set_draw_color(28, 58, 106)
    pdf.set_line_width(0.5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(120, 10, txt("Max. Kaufpreis der Immobilie:"), 1)
    pdf.cell(70, 10, txt(f"{pdf_eur(data['kaufpreis'])}"), 1, 1, 'R')
    pdf.set_font("Arial", "", 11)
    pdf.cell(120, 8, txt("dazu Kaufnebenkosten:"), 1)
    pdf.cell(70, 8, txt(f"+ {pdf_eur(data['nk'])}"), 1, 1, 'R')
    pdf.cell(120, 8, txt("abzüglich Eigenkapital:"), 1)
    pdf.cell(70, 8, txt(f"- {pdf_eur(data['ek'])}"), 1, 1, 'R')
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(120, 10, txt("Notwendiges Bankdarlehen:"), 1, 0, 'L', True)
    pdf.cell(70, 10, txt(f"{pdf_eur(data['kredit'])}"), 1, 1, 'R', True)

    # 4. WUNSCH OBJEKT
    if data['wunsch_preis'] > 0:
        pdf.ln(8)
        pdf.set_fill_color(*col_fill)
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(*col_header)
        pdf.cell(0, 8, txt(f"4. Prüfung Wunsch-Objekt ({pdf_eur(data['wunsch_preis'])})"), 0, 1, 'L', True)
        pdf.ln(2)
        
        pdf.set_text_color(0,0,0)
        pdf.set_font("Arial", "", 11)
        pdf.cell(120, 8, txt("Erforderliche Rate für dieses Objekt:"), 0)
        pdf.cell(70, 8, txt(f"{pdf_eur(data['wunsch_rate'])}"), 0, 1, 'R')
        
        pdf.ln(2)
        diff = data['wunsch_rate'] - data['frei']
        
        if data['wunsch_rate'] <= data['frei']:
            pdf.set_fill_color(200, 255, 200)
            pdf.set_text_color(0, 100, 0)
            status = "PASST INS BUDGET"
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, txt(f"Ergebnis: {status}"), 1, 1, 'C', True)
        else:
            pdf.set_fill_color(255, 200, 200)
            pdf.set_text_color(180, 0, 0)
            status = "ÜBERSTEIGT BUDGET"
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, txt(f"Ergebnis: {status} (Fehlt: {pdf_eur(diff)})"), 1, 1, 'C', True)
            
    pdf.ln(10)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, txt("Hinweis: Dies ist eine unverbindliche Modellrechnung."))
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 💾 LOAD LOGIC
# ==========================================
defaults = {
    "kinder": 1,
    "gehalt_h": 3000,
    "gehalt_p": 0,
    "ek": 60000,
    "kunde": "Kunde",
    "aktuelle_miete": 1000,
    "wohnflaeche": 120,
    "exp_bewirt": 480.0,      # Default Wert
    "exp_p_lebenshaltung": 1600.0 # Default Wert
}

def load_data_callback():
    uploaded = st.session_state.get('json_loader')
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            for key, value in data.items():
                st.session_state[key] = value
            st.toast("✅ Daten geladen!", icon="🎉")
        except Exception as e:
            st.error(f"Fehler: {e}")

# ==========================================
# UI & INPUTS
# ==========================================
st.title("🏡 Profi-Finanzierungscheck")

with st.expander("📂 Speichern / Laden", expanded=False):
    col_dl, col_ul = st.columns(2)
    with col_ul:
        st.file_uploader("JSON laden", type=["json"], key="json_loader", on_change=load_data_callback)
    with col_dl:
        st.info("Download-Button erscheint ganz unten!")

# --- SIDEBAR ---
st.sidebar.header("1. Projekt & Nutzung")
kunden_name = st.sidebar.text_input("Name", value=defaults["kunde"], key="sb_name")

nutzungsart = st.sidebar.radio("Zweck", ["Eigenheim (Selbst)", "Eigenheim + Einlieger", "Kapitalanlage"], key="sb_nutzung")

# TRIGGER: Wenn hier geändert wird, feuert update_bewirtschaftung
wohnflaeche = st.sidebar.number_input(
    "Wohnfläche (m²)", 
    value=defaults["wohnflaeche"], 
    step=10, min_value=0, 
    key="sb_wohnflaeche",
    on_change=update_bewirtschaftung, # <--- WICHTIG!
    help="Basis für die Berechnung der Nebenkosten (4€/qm)."
)

aktuelle_warmmiete = 0.0
neue_miete_einnahme = 0.0

if nutzungsart == "Eigenheim (Selbst)":
    st.sidebar.info("Alte Miete entfällt.")
    aktuelle_warmmiete = st.sidebar.number_input("Aktuelle Warmmiete", value=defaults["aktuelle_miete"], step=50, min_value=0, key="sb_akt_miete")
elif nutzungsart == "Eigenheim + Einlieger":
    st.sidebar.success("Zusatz-Einnahmen!")
    aktuelle_warmmiete = st.sidebar.number_input("Aktuelle Warmmiete", value=defaults["aktuelle_miete"], step=50, min_value=0, key="sb_akt_miete")
    neue_miete_einnahme = st.sidebar.number_input("Mieteinnahme Neu (Kalt)", value=500, step=50, min_value=0, key="sb_neue_miete_mix")
else:
    st.sidebar.warning("Alte Miete bleibt.")
    aktuelle_warmmiete = st.sidebar.number_input("Aktuelle Warmmiete", value=defaults["aktuelle_miete"], step=50, min_value=0, key="sb_akt_miete")
    neue_miete_einnahme = st.sidebar.number_input("Mieteinnahme Neu (Kalt)", value=600, step=50, min_value=0, key="sb_neue_miete_ka")

st.sidebar.header("2. Haushalt")
# TRIGGER: Wenn Personen geändert werden, feuert update_lebenshaltung
anzahl_erwachsene = st.sidebar.radio("Personen", ["Alleinstehend", "Paar (2 Personen)"], index=1, key="sb_erwachsene", on_change=update_lebenshaltung)
anzahl_kinder = st.sidebar.number_input("Kinder", value=defaults["kinder"], step=1, min_value=0, key="sb_kinder", on_change=update_lebenshaltung)

# PAUSCHALEN BLOCK
st.sidebar.markdown("---")
st.sidebar.subheader("Ausgaben (Bank-Logik)")

# Initialisierung der Session State Werte, falls noch nicht vorhanden
if "exp_p_lebenshaltung" not in st.session_state:
    update_lebenshaltung() # Einmalig berechnen beim Start
if "exp_bewirt" not in st.session_state:
    update_bewirtschaftung() # Einmalig berechnen beim Start

# EINGABE: Lebenshaltung (Vorbelegt durch Funktion, aber änderbar)
var_lebenshaltung = st.sidebar.number_input(
    "Lebenshaltung (Pauschale)", 
    key="exp_p_lebenshaltung", # Verknüpft mit Session State
    step=50.0, min_value=0.0,
    help="Enthält: Essen, Kleidung, Gesundheit (auch Zuzahlungen Diabetes etc.), Mobilität, Versicherungen. Quelle: Destatis."
)
st.sidebar.markdown("[📊 Quelle Destatis (Konsum)](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Einkommen-Konsum-Lebensbedingungen/Konsumausgaben-Lebenshaltungskosten/_inhalt.html)")

# EINGABE: Bewirtschaftung (Vorbelegt durch qm, aber änderbar)
var_bewirtschaftung = st.sidebar.number_input(
    "Bewirtschaftung (Nebenkosten)", 
    key="exp_bewirt", # Verknüpft mit Session State
    step=10.0, min_value=0.0,
    help=f"Automatisch berechnet: {wohnflaeche} m² x 4,00 €. Enthält Heizung, Wasser, Müll, Grundsteuer."
)
st.sidebar.markdown("[📊 Quelle Mieterbund](https://www.mieterbund.de/service/betriebskostenspiegel.html)")

var_puffer = st.sidebar.number_input("Instandhaltungs-Puffer", value=250, step=50, min_value=0, help="Rücklagen für Reparaturen.")

# WEITERE FINANZEN
st.sidebar.header("3. Einnahmen & Kredite")
gehalt_haupt = st.sidebar.number_input("Gehalt Haupt", value=defaults["gehalt_h"], step=50, min_value=0, key="sb_gehalt_h")
gehalt_partner = st.sidebar.number_input("Gehalt Partner", value=defaults["gehalt_p"], step=50, min_value=0, key="sb_gehalt_p") if anzahl_erwachsene == "Paar (2 Personen)" else 0
kindergeld = anzahl_kinder * 250
sonstiges = st.sidebar.number_input("Sonstiges / Bonus", value=0, step=50, min_value=0, key="sb_sonst")

konsum = st.sidebar.number_input("Konsumkredite (Rate)", value=0, step=50, min_value=0, key="sb_konsum", help="Auto, Handy, Ratenzahlung")
bauspar = st.sidebar.number_input("Sparraten Pflicht", value=0, step=50, min_value=0, key="sb_bauspar", help="Bausparer, Tilgungsaussetzung")

# BESTAND & MARKT
st.sidebar.header("4. Markt & Bestand")
eigenkapital = st.sidebar.number_input("Eigenkapital", value=defaults["ek"], step=1000, min_value=0, key="sb_ek")
zins = st.sidebar.number_input("Zins (%)", value=3.8, step=0.1, min_value=0.1, key="sb_zins")
tilgung = st.sidebar.number_input("Tilgung (%)", value=2.0, step=0.1, min_value=0.0, key="sb_tilgung")
nk_prozent = 6.5 + 2.0 + 3.57 # Grunderwerb + Notar + Makler

# BESTAND
miete_bestand_anrechenbar = 0.0
rate_bestand = 0.0
if st.sidebar.checkbox("Immobilienbestand?", key="sb_hat_bestand"):
    miete_raw = st.sidebar.number_input("Mieteinnahmen Bestand", value=0, min_value=0)
    rate_bestand = st.sidebar.number_input("Rate Bestand", value=0, min_value=0)
    miete_bestand_anrechenbar = miete_raw * 0.75 # 75% Ansatz

# WUNSCH
wunsch_preis = st.sidebar.number_input("Check: Kaufpreis Objekt", value=0, step=5000, min_value=0, key="sb_wunsch_preis")

# ==========================================
# BERECHNUNG
# ==========================================
# 1. Mieteinnahmen Neu
miete_neu_calc = 0.0
if nutzungsart != "Eigenheim (Selbst)":
    miete_neu_calc = neue_miete_einnahme * 0.80 # 80% Ansatz bei Neuvermietung

# 2. Belastung durch alte Miete
belastung_alte_miete = aktuelle_warmmiete if nutzungsart == "Kapitalanlage" else 0.0

# 3. Summen
einnahmen = gehalt_haupt + gehalt_partner + kindergeld + sonstiges + miete_bestand_anrechenbar + miete_neu_calc
ausgaben = var_lebenshaltung + var_bewirtschaftung + var_puffer + konsum + bauspar + rate_bestand + belastung_alte_miete
frei = einnahmen - ausgaben

# 4. Max Kaufpreis
annuitaet = zins + tilgung
max_kredit = (frei * 12 * 100) / annuitaet if (frei > 0 and annuitaet > 0) else 0
max_preis = (max_kredit + eigenkapital) / (1 + (nk_prozent/100))

# 5. Wunsch Objekt
wunsch_rate = 0.0
diff_miete = None
if wunsch_preis > 0:
    invest = wunsch_preis * (1 + (nk_prozent/100))
    bedarf = invest - eigenkapital
    wunsch_rate = (bedarf * annuitaet) / 100 / 12

# Vergleich Miete vs Eigentum (Zahlungsschock)
if aktuelle_warmmiete > 0 and nutzungsart != "Kapitalanlage":
    neue_wohnkosten = frei + var_bewirtschaftung + var_puffer # Rate + NK + Puffer
    diff_miete = neue_wohnkosten - aktuelle_warmmiete # Positiv = Teurer

# ==========================================
# UI OUTPUT
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 Haushaltsrechnung")
    
    # Einnahmen Tabelle
    df_in = pd.DataFrame({
        "Posten": ["Gehälter", "Kindergeld", "Sonstiges", "Miete (bereinigt)"],
        "Betrag": [gehalt_haupt+gehalt_partner, kindergeld, sonstiges, miete_bestand_anrechenbar+miete_neu_calc]
    })
    st.dataframe(df_in[df_in["Betrag"] > 0], hide_index=True, use_container_width=True)
    st.success(f"Einnahmen: **{eur(einnahmen)}**")

    st.markdown("---")
    
    # Ausgaben Tabelle
    df_out = pd.DataFrame({
        "Posten": ["Lebenshaltung (Pauschale)", "Bewirtschaftung (Haus)", "Puffer", "Kredite/Sparraten", "Bestands-Last", "Alte Miete"],
        "Betrag": [var_lebenshaltung, var_bewirtschaftung, var_puffer, konsum+bauspar, rate_bestand, belastung_alte_miete]
    })
    st.dataframe(df_out[df_out["Betrag"] > 0], hide_index=True, use_container_width=True)
    st.error(f"Ausgaben: **{eur(ausgaben)}**")

with col2:
    st.subheader("🏠 Ergebnis")
    
    if frei < 0:
        st.error(f"⚠️ **Unterdeckung: {eur(abs(frei))}**")
    else:
        st.info(f"🏦 Verfügbare Rate: **{eur(frei)}**")
        
        # VERGLEICH ANZEIGE
        if diff_miete is not None:
            st.markdown("#### Miete vs. Eigentum")
            if diff_miete > 0:
                st.warning(f"Du zahlst **{eur(diff_miete)}** mehr als jetzt (Warm).")
            else:
                st.success(f"Du sparst **{eur(abs(diff_miete))}** gegenüber jetzt.")
            st.caption(f"Alte Miete: {eur(aktuelle_warmmiete)} vs. Neue Belastung (Rate+NK+Puffer).")
            st.markdown("---")

        if wunsch_preis > 0:
            st.write(f"**Check {eur(wunsch_preis)} Objekt:**")
            col_a, col_b = st.columns(2)
            col_a.metric("Nötige Rate", eur(wunsch_rate))
            if wunsch_rate <= frei:
                col_b.success("✅ MACHBAR")
            else:
                col_b.error("❌ ZU TEUER")
                st.caption(f"Fehlt: {eur(wunsch_rate - frei)}")

    # PDF EXPORT
    pdf_data = {
        "name": kunden_name, "scenario": nutzungsart, "ein": einnahmen, "aus": ausgaben, 
        "frei": frei, "zins": zins, "tilg": tilgung, "kaufpreis": max_preis, 
        "nk": max_preis * (nk_prozent/100), "ek": eigenkapital, "kredit": max_kredit,
        "wunsch_preis": wunsch_preis, "wunsch_rate": wunsch_rate,
        # Details für PDF
        "aus_leben": var_lebenshaltung, "aus_bewirt": var_bewirtschaftung, "qm": wohnflaeche,
        "aus_puffer": var_puffer, "aus_konsum": konsum, "aus_bauspar": bauspar,
        "aus_bestand": rate_bestand, "aus_miete": belastung_alte_miete,
        # Vergleich
        "diff_miete": diff_miete, "alt_warm": aktuelle_warmmiete, "neu_last": (frei + var_bewirtschaftung + var_puffer) if frei > 0 else 0
    }
    
    pdf_bytes = create_pdf(pdf_data)
    st.download_button("📄 PDF Expose erstellen", data=pdf_bytes, file_name="Finanzcheck.pdf", mime="application/pdf")

# JSON SAVE
save_data = st.session_state.to_dict()
json_str = json.dumps({k: v for k,v in save_data.items() if k.startswith(("sb_", "exp_"))})
st.download_button("💾 Daten sichern (JSON)", json_str, "daten.json", "application/json")
