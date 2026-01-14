import streamlit as st
import pandas as pd
import plotly.express as px
import json
from fpdf import FPDF

# --- KONFIGURATION ---
st.set_page_config(page_title="Immo-Finanz Master Pro", layout="wide")

# ==========================================
# 🛠 HELFER & CALLBACKS
# ==========================================
def eur(wert):
    return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def pdf_eur(wert):
    return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " EUR"

def update_lebenshaltung():
    erw = st.session_state.sb_erwachsene
    kind = st.session_state.sb_kinder
    basis = 1200 if erw == "Alleinstehend" else 1600
    st.session_state.exp_p_lebenshaltung = float(basis + (kind * 400))

def update_bewirtschaftung():
    qm = st.session_state.sb_wohnflaeche
    st.session_state.exp_bewirt = float(qm * 4.0)

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
# 📄 PDF GENERATOR (DETAILLIERT)
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

    def txt(text):
        return text.encode('latin-1', 'replace').decode('latin-1')

    # KOPF
    pdf.set_text_color(*col_header)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt(f"Analyse für: {data['name']}"), ln=True)
    pdf.set_text_color(*col_text)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, txt(f"Szenario: {data['scenario']}"), ln=True)
    pdf.ln(5)

    # 1. HAUSHALT
    pdf.set_fill_color(*col_fill)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*col_header)
    pdf.cell(0, 8, txt("1. Monatliche Haushaltsrechnung"), 0, 1, 'L', True)
    pdf.ln(2)

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

    # EINNAHMEN DETAIL
    pdf.set_text_color(*col_text)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt("Einnahmen (Detailliert):"), 0, 1)

    row("Gehalt Hauptverdiener", data['ein_haupt'])
    if data['ein_partner'] > 0: row("Gehalt Partner", data['ein_partner'])
    if data['ein_kinder'] > 0: row("Kindergeld", data['ein_kinder'])
    if data['ein_neben'] > 0: row("Nebentätigkeit", data['ein_neben'])
    if data['ein_sonst'] > 0: row("Sonstiges", data['ein_sonst'])
    if data['ein_miete_bestand'] > 0: row("Miete Bestand (Netto)", data['ein_miete_bestand'])
    if data['ein_miete_neu'] > 0: row("Miete Neu (Kalk.)", data['ein_miete_neu'])

    pdf.ln(1)
    pdf.cell(100, 0, "", "T")
    pdf.cell(30, 0, "", "T")
    pdf.ln(1)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(100, 6, txt("Summe Einnahmen:"))
    pdf.set_text_color(0, 100, 0)
    pdf.cell(30, 6, txt(f"+ {pdf_eur(data['ein_total'])}"), 0, 1, 'R')
    pdf.ln(3)

    # AUSGABEN DETAIL
    pdf.set_text_color(*col_text)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt("Ausgaben (Detailliert):"), 0, 1)
    
    row("Lebenshaltung (Pauschale)", data['aus_leben'], "Nahrung, Kleidung, Gesundheit")
    row("Bewirtschaftung (Hauskosten)", data['aus_bewirt'], f"Heizung, Wasser ({data['qm']} qm)")
    if data['aus_miete'] > 0: row("Aktuelle Kaltmiete", data['aus_miete'], "Bleibt bestehen")
    if data['aus_bestand'] > 0: row("Rate Bestandskredit", data['aus_bestand'])
    if data['aus_bauspar'] > 0: row("Sparrate (Pflicht)", data['aus_bauspar'], "Tilgungsaussetzung")
    if data['aus_konsum'] > 0: row("Konsumkredite", data['aus_konsum'])
    row("Puffer / Rücklagen", data['aus_puffer'])

    pdf.ln(1)
    pdf.cell(100, 0, "", "T")
    pdf.cell(30, 0, "", "T")
    pdf.ln(1)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(100, 6, txt("Summe Ausgaben:"))
    pdf.set_text_color(180, 0, 0)
    pdf.cell(30, 6, txt(f"- {pdf_eur(data['aus_total'])}"), 0, 1, 'R')

    # ERGEBNIS
    pdf.ln(4)
    pdf.set_fill_color(230, 240, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*col_header)
    pdf.cell(120, 10, txt("Verfügbarer Betrag (Freie Rate):"), 0, 0, 'L', True)
    pdf.cell(70, 10, txt(f"{pdf_eur(data['frei'])}"), 0, 1, 'R', True)
    pdf.ln(8)

    # VERGLEICH
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
         pdf.cell(100, 6, txt("Neue Belastung (Rate + NK):"))
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

    # KAUFPREIS
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

    # WUNSCH
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
        diff_wunsch = data['wunsch_rate'] - data['frei']
        if data['wunsch_rate'] <= data['frei']:
            pdf.set_fill_color(200, 255, 200)
            pdf.set_text_color(0, 100, 0)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, txt("Ergebnis: PASST INS BUDGET"), 1, 1, 'C', True)
        else:
            pdf.set_fill_color(255, 200, 200)
            pdf.set_text_color(180, 0, 0)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, txt(f"Ergebnis: ÜBERSTEIGT BUDGET (Fehlt: {pdf_eur(diff_wunsch)})"), 1, 1, 'C', True)

    pdf.ln(10)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, txt("Hinweis: Dies ist eine unverbindliche Modellrechnung."))
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 💾 SPEICHERN & LADEN
# ==========================================
defaults = {
    "kinder": 1, "gehalt_h": 3000, "gehalt_p": 0, "ek": 60000,
    "kunde": "Kunde", "aktuelle_miete": 1000, "wohnflaeche": 120,
    "exp_bewirt": 480.0, "exp_p_lebenshaltung": 1600.0
}

def load_data_callback():
    uploaded = st.session_state.get('json_loader')
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            for key, value in data.items():
                st.session_state[key] = value
            st.toast("✅ Daten erfolgreich geladen!", icon="🎉")
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
        st.info("Download unten!")

# --- SIDEBAR ---
st.sidebar.header("1. Projekt & Nutzung")
if "sb_name" not in st.session_state: st.session_state.sb_name = defaults["kunde"]
kunden_name = st.sidebar.text_input("Name", key="sb_name")

OPTIONS_NUTZUNG = ["Eigenheim (Nur Selbstbezug)", "Eigenheim mit Vermietung (Einliegerw./MFH)", "Kapitalanlage (Reine Vermietung)"]
if "sb_nutzung" not in st.session_state: st.session_state.sb_nutzung = OPTIONS_NUTZUNG[0]
nutzungsart = st.sidebar.radio("Zweck", OPTIONS_NUTZUNG, key="sb_nutzung")

if "sb_wohnflaeche" not in st.session_state: st.session_state.sb_wohnflaeche = defaults["wohnflaeche"]
wohnflaeche = st.sidebar.number_input(
    "Wohnfläche (m²)", step=10, min_value=0, key="sb_wohnflaeche",
    on_change=update_bewirtschaftung, 
    help="Berechnungsgrundlage für Nebenkosten."
)

aktuelle_warmmiete = 0.0
neue_miete_einnahme = 0.0

if "sb_akt_miete" not in st.session_state: st.session_state.sb_akt_miete = defaults["aktuelle_miete"]

if nutzungsart == OPTIONS_NUTZUNG[0]:
    st.sidebar.info("Alte Miete entfällt.")
    aktuelle_warmmiete = st.sidebar.number_input("Aktuelle Warmmiete", step=50, min_value=0, key="sb_akt_miete")
elif nutzungsart == OPTIONS_NUTZUNG[1]:
    st.sidebar.success("Zusatz-Einnahmen!")
    aktuelle_warmmiete = st.sidebar.number_input("Aktuelle Warmmiete", step=50, min_value=0, key="sb_akt_miete")
    if "sb_neue_miete_mix" not in st.session_state: st.session_state.sb_neue_miete_mix = 500
    neue_miete_einnahme = st.sidebar.number_input("Mieteinnahme Neu (Kalt)", step=50, min_value=0, key="sb_neue_miete_mix")
else:
    st.sidebar.warning("Alte Miete bleibt.")
    aktuelle_warmmiete = st.sidebar.number_input("Aktuelle Warmmiete", step=50, min_value=0, key="sb_akt_miete")
    if "sb_neue_miete_ka" not in st.session_state: st.session_state.sb_neue_miete_ka = 600
    neue_miete_einnahme = st.sidebar.number_input("Mieteinnahme Neu (Kalt)", step=50, min_value=0, key="sb_neue_miete_ka")

st.sidebar.header("2. Haushalt")
if "sb_erwachsene" not in st.session_state: st.session_state.sb_erwachsene = "Paar (2 Personen)"
anzahl_erwachsene = st.sidebar.radio("Personen", ["Alleinstehend", "Paar (2 Personen)"], key="sb_erwachsene", on_change=update_lebenshaltung)

if "sb_kinder" not in st.session_state: st.session_state.sb_kinder = defaults["kinder"]
anzahl_kinder = st.sidebar.number_input("Kinder", step=1, min_value=0, key="sb_kinder", on_change=update_lebenshaltung)

st.sidebar.markdown("---")
st.sidebar.subheader("Ausgaben (Bank-Logik)")
if "exp_p_lebenshaltung" not in st.session_state: update_lebenshaltung()
if "exp_bewirt" not in st.session_state: update_bewirtschaftung()

var_lebenshaltung = st.sidebar.number_input(
    "Lebenshaltung (Pauschale)", key="exp_p_lebenshaltung", step=50.0, min_value=0.0,
    help="Enthält: Essen, Kleidung, Gesundheit (auch Zuzahlungen Diabetes), Mobilität. Quelle: Destatis."
)
st.sidebar.markdown("[📊 Quelle Destatis](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Einkommen-Konsum-Lebensbedingungen/Konsumausgaben-Lebenshaltungskosten/_inhalt.html)")

var_bewirtschaftung = st.sidebar.number_input(
    "Bewirtschaftung (Nebenkosten)", key="exp_bewirt", step=10.0, min_value=0.0,
    help=f"Automatisch: {wohnflaeche} m² x 4,00 €. (Heizung, Wasser, Müll)."
)
st.sidebar.markdown("[📊 Quelle Mieterbund](https://www.mieterbund.de/service/betriebskostenspiegel.html)")

var_puffer = st.sidebar.number_input("Instandhaltungs-Puffer", value=250, step=50, min_value=0, help="Rücklagen.")

st.sidebar.header("3. Einnahmen & Kredite")
if "sb_gehalt_h" not in st.session_state: st.session_state.sb_gehalt_h = defaults["gehalt_h"]
gehalt_haupt = st.sidebar.number_input("Gehalt Haupt", step=50, min_value=0, key="sb_gehalt_h")

gehalt_partner = 0
if anzahl_erwachsene == "Paar (2 Personen)":
    if "sb_gehalt_p" not in st.session_state: st.session_state.sb_gehalt_p = defaults["gehalt_p"]
    gehalt_partner = st.sidebar.number_input("Gehalt Partner", step=50, min_value=0, key="sb_gehalt_p")

kindergeld = anzahl_kinder * 250
if "sb_neben" not in st.session_state: st.session_state.sb_neben = 0
nebeneinkommen = st.sidebar.number_input("Minijob / Nebentätigkeit", step=50, min_value=0, key="sb_neben")
if "sb_sonst" not in st.session_state: st.session_state.sb_sonst = 0
sonstiges = st.sidebar.number_input("Sonstiges / Bonus", step=50, min_value=0, key="sb_sonst")
if "sb_konsum" not in st.session_state: st.session_state.sb_konsum = 0
konsum = st.sidebar.number_input("Konsumkredite (Rate)", step=50, min_value=0, key="sb_konsum")
if "sb_bauspar" not in st.session_state: st.session_state.sb_bauspar = 0
bauspar = st.sidebar.number_input("Sparraten Pflicht", step=50, min_value=0, key="sb_bauspar")

st.sidebar.header("4. Markt & Bestand")
if "sb_ek" not in st.session_state: st.session_state.sb_ek = defaults["ek"]
eigenkapital = st.sidebar.number_input("Eigenkapital", step=1000, min_value=0, key="sb_ek")
zins = st.sidebar.number_input("Zins (%)", value=3.8, step=0.1, min_value=0.1, key="sb_zins")
tilgung = st.sidebar.number_input("Tilgung (%)", value=2.0, step=0.1, min_value=0.0, key="sb_tilgung")
nk_prozent = 6.5 + 2.0 + 3.57 

miete_bestand_anrechenbar = 0.0
rate_bestand = 0.0
if st.sidebar.checkbox("Immobilienbestand?", key="sb_hat_bestand"):
    miete_raw = st.sidebar.number_input("Mieteinnahmen Bestand", value=0, min_value=0)
    rate_bestand = st.sidebar.number_input("Rate Bestand", value=0, min_value=0)
    miete_bestand_anrechenbar = miete_raw * 0.75 

if "sb_wunsch_preis" not in st.session_state: st.session_state.sb_wunsch_preis = 0
wunsch_preis = st.sidebar.number_input("Check: Kaufpreis Objekt", step=5000, min_value=0, key="sb_wunsch_preis")

# ==========================================
# RECHNUNG & UI OUTPUT
# ==========================================
miete_neu_calc = 0.0
if nutzungsart != OPTIONS_NUTZUNG[0]:
    miete_neu_calc = neue_miete_einnahme * 0.80 
belastung_alte_miete = aktuelle_warmmiete if nutzungsart == OPTIONS_NUTZUNG[2] else 0.0
einnahmen = gehalt_haupt + gehalt_partner + kindergeld + nebeneinkommen + sonstiges + miete_bestand_anrechenbar + miete_neu_calc
ausgaben = var_lebenshaltung + var_bewirtschaftung + var_puffer + konsum + bauspar + rate_bestand + belastung_alte_miete
frei = einnahmen - ausgaben
annuitaet = zins + tilgung
max_kredit = (frei * 12 * 100) / annuitaet if (frei > 0 and annuitaet > 0) else 0
max_preis = (max_kredit + eigenkapital) / (1 + (nk_prozent/100))

wunsch_rate = 0.0
diff_miete = None
if wunsch_preis > 0:
    invest = wunsch_preis * (1 + (nk_prozent/100))
    bedarf = invest - eigenkapital
    wunsch_rate = (bedarf * annuitaet) / 100 / 12

if aktuelle_warmmiete > 0 and nutzungsart != OPTIONS_NUTZUNG[2]:
    neue_wohnkosten = frei + var_bewirtschaftung + var_puffer
    diff_miete = neue_wohnkosten - aktuelle_warmmiete

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"### 🎯 Analyse für: {kunden_name}")
    st.subheader("💰 Haushaltsrechnung")
    
    # DETAIL EINNAHMEN
    ein_liste = []
    if gehalt_haupt > 0: ein_liste.append(["Gehalt Haupt", gehalt_haupt])
    if gehalt_partner > 0: ein_liste.append(["Gehalt Partner", gehalt_partner])
    if kindergeld > 0: ein_liste.append(["Kindergeld", kindergeld])
    if nebeneinkommen > 0: ein_liste.append(["Nebentätigkeit", nebeneinkommen])
    if sonstiges > 0: ein_liste.append(["Sonstiges", sonstiges])
    if miete_bestand_anrechenbar > 0: ein_liste.append(["Miete Bestand (Netto)", miete_bestand_anrechenbar])
    if miete_neu_calc > 0: ein_liste.append(["Miete Neu (Kalk.)", miete_neu_calc])
    
    df_in = pd.DataFrame(ein_liste, columns=["Posten", "Betrag"])
    st.dataframe(df_in, hide_index=True, use_container_width=True)
    st.success(f"Einnahmen: **{eur(einnahmen)}**")
    
    st.markdown("---")
    df_out = pd.DataFrame({
        "Posten": ["Lebenshaltung (Pauschale)", "Bewirtschaftung (Haus)", "Puffer", "Kredite/Spar", "Bestand", "Alte Miete"],
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
        if diff_miete is not None:
            st.markdown("#### Miete vs. Eigentum")
            if diff_miete > 0:
                st.warning(f"Du zahlst **{eur(diff_miete)}** mehr als jetzt.")
            else:
                st.success(f"Du sparst **{eur(abs(diff_miete))}** gegenüber jetzt.")
            st.caption("Vergleich: Alte Miete vs. Neue Rate + NK + Puffer")
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

    # DATEINAMEN MIT KUNDENNAME
    safe_name = kunden_name.replace(" ", "_")
    
    pdf_data = {
        "name": kunden_name, "scenario": nutzungsart, "ein_total": einnahmen, "aus_total": ausgaben, 
        "frei": frei, "zins": zins, "tilg": tilgung, "kaufpreis": max_preis, 
        "nk": max_preis * (nk_prozent/100), "ek": eigenkapital, "kredit": max_kredit,
        "wunsch_preis": wunsch_preis, "wunsch_rate": wunsch_rate,
        "ein_haupt": gehalt_haupt, "ein_partner": gehalt_partner, "ein_kinder": kindergeld,
        "ein_neben": nebeneinkommen, "ein_sonst": sonstiges, 
        "ein_miete_bestand": miete_bestand_anrechenbar, "ein_miete_neu": miete_neu_calc,
        "aus_leben": var_lebenshaltung, "aus_bewirt": var_bewirtschaftung, "qm": wohnflaeche,
        "aus_puffer": var_puffer, "aus_konsum": konsum, "aus_bauspar": bauspar,
        "aus_bestand": rate_bestand, "aus_miete": belastung_alte_miete,
        "diff_miete": diff_miete, "alt_warm": aktuelle_warmmiete, "neu_last": (frei + var_bewirtschaftung + var_puffer) if frei > 0 else 0
    }
    
    pdf_bytes = create_pdf(pdf_data)
    st.download_button("📄 PDF Zertifikat", data=pdf_bytes, file_name=f"{safe_name}_Finanzcheck.pdf", mime="application/pdf")

# JSON SAVE
save_data = st.session_state.to_dict()
json_str = json.dumps({k: v for k,v in save_data.items() if k.startswith(("sb_", "exp_"))})
st.download_button("💾 Daten sichern (JSON)", json_str, f"{safe_name}_Daten.json", "application/json")
