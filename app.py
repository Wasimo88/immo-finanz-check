import streamlit as st
import pandas as pd
import plotly.express as px
import json
from fpdf import FPDF

# --- KONFIGURATION ---
st.set_page_config(page_title="Immo-Finanz Master", layout="wide")

# ==========================================
# 🔒 SICHERHEITS-CHECK
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password_input"] == st.secrets["password"]:
            st.session_state.password_correct = True
            del st.session_state["password_input"]
        else:
            st.session_state.password_correct = False

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = None

    if st.session_state.password_correct == True:
        return True

    st.text_input(
        "🔒 Bitte Passwort eingeben", 
        type="password", 
        on_change=password_entered, 
        key="password_input"
    )
    
    if st.session_state.password_correct == False:
        st.error("😕 Passwort falsch. Bitte erneut versuchen.")

    return False

if not check_password():
    st.stop()

# ==========================================
# 📄 PDF GENERATOR
# ==========================================
def create_pdf(data_dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    def txt(text):
        return text.encode('latin-1', 'replace').decode('latin-1')

    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt("Finanzierungs-Vorprüfung"), ln=True, align='C')
    pdf.ln(10)

    # Info
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt(f"Kunde: {data_dict['name']}"), ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, txt(f"Szenario: {data_dict['scenario']}"), ln=True)
    pdf.ln(5)

    # Rechnung
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt("1. Budget-Ermittlung"), ln=True)
    pdf.set_font("Arial", "", 12)
    
    pdf.cell(100, 8, txt("Einnahmen (netto):"), 0)
    pdf.cell(50, 8, txt(f"{data_dict['ein']:,.2f} EUR"), 0, 1, 'R')
    
    pdf.cell(100, 8, txt("Ausgaben (inkl. Puffer & Bestand):"), 0)
    pdf.cell(50, 8, txt(f"- {data_dict['aus']:,.2f} EUR"), 0, 1, 'R')
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, txt("Verfügbar für NEUE Rate:"), 0)
    pdf.cell(50, 10, txt(f"{data_dict['frei']:,.2f} EUR"), 0, 1, 'R')
    pdf.ln(5)

    # Ergebnis Max
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt("2. Maximal machbarer Kaufpreis"), ln=True)
    pdf.set_font("Arial", "", 12)

    pdf.cell(100, 8, txt(f"Kalkulation mit: {data_dict['zins']}% Zins | {data_dict['tilg']}% Tilgung"), 0, 1)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(100, 10, txt("Max. Kaufpreis (Immobilie):"), 1, 0, 'L', True)
    pdf.cell(50, 10, txt(f"{data_dict['kaufpreis']:,.0f} EUR"), 1, 1, 'R', True)
    
    pdf.cell(100, 10, txt("Dazu Kaufnebenkosten:"), 1, 0, 'L')
    pdf.cell(50, 10, txt(f"{data_dict['nk']:,.0f} EUR"), 1, 1, 'R')
    
    pdf.cell(100, 10, txt("Eigenkapital:"), 1, 0, 'L')
    pdf.cell(50, 10, txt(f"{data_dict['ek']:,.0f} EUR"), 1, 1, 'R')

    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, txt("Notwendiges Darlehen:"), 1, 0, 'L')
    pdf.cell(50, 10, txt(f"{data_dict['kredit']:,.0f} EUR"), 1, 1, 'R')

    # Optional: Konkretes Objekt
    if data_dict['wunsch_preis'] > 0:
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, txt("3. Prüfung Wunsch-Objekt"), ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(100, 8, txt(f"Wunsch-Preis: {data_dict['wunsch_preis']:,.0f} EUR"), 0, 1)
        pdf.cell(100, 8, txt(f"Benötigte Rate: {data_dict['wunsch_rate']:,.2f} EUR"), 0, 1)
        
        status = "MACHBAR" if data_dict['wunsch_rate'] <= data_dict['frei'] else "NICHT MACHBAR"
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, txt(f"Ergebnis: {status}"), ln=True)

    pdf.ln(20)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, txt("Hinweis: Unverbindliche Modellrechnung. Keine Kreditzusage."))

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 💾 SPEICHERN & LADEN
# ==========================================

defaults = {
    "kinder": 1,
    "gehalt_h": 3000,
    "gehalt_p": 0,
    "ek": 60000,
    "kunde": "Kunde",
    "aktuelle_miete": 1000
}

def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            for key, value in data.items():
                st.session_state[key] = value
            st.success(f"✅ Daten geladen!")
            st.rerun()
        except:
            st.error("Fehler beim Laden.")

# ==========================================
# HAUPT-APP UI
# ==========================================

st.title("🏡 Profi-Finanzierungscheck")

# --- DATEI UPLOAD ---
with st.expander("📂 Daten Speichern / Laden", expanded=False):
    col_dl, col_ul = st.columns(2)
    with col_ul:
        uploaded_file = st.file_uploader("JSON laden", type=["json"])
        if uploaded_file:
            load_data(uploaded_file)
    with col_dl:
        st.write("Sicherung:")
        st.info("Button ist unten in der Sidebar!")

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.header("1. Projekt-Daten")
kunden_name = st.sidebar.text_input("Name des Kunden", value=defaults["kunde"], key="sb_name")

nutzungsart = st.sidebar.radio(
    "Verwendungszweck", 
    [
        "Eigenheim (Nur Selbstbezug)", 
        "Eigenheim mit Vermietung (Einliegerw./MFH)", 
        "Kapitalanlage (Reine Vermietung)"
    ], 
    key="sb_nutzung"
)

aktuelle_warmmiete = 0.0
neue_miete_einnahme = 0.0

if nutzungsart == "Eigenheim (Nur Selbstbezug)":
    st.sidebar.info("ℹ️ Alte Miete fällt weg.")
    aktuelle_warmmiete = st.sidebar.number_input("Vergleich: Aktuelle Warmmiete", value=defaults["aktuelle_miete"], step=50, key="sb_akt_miete")
elif nutzungsart == "Eigenheim mit Vermietung (Einliegerw./MFH)":
    st.sidebar.success("ℹ️ ZUSÄTZLICHE Einnahmen durch Vermietung!")
    aktuelle_warmmiete = st.sidebar.number_input("Vergleich: Aktuelle Warmmiete", value=defaults["aktuelle_miete"], step=50, key="sb_akt_miete")
    neue_miete_einnahme = st.sidebar.number_input("Geplante Mieteinnahme (Kalt)", value=500, step=50, key="sb_neue_miete_mix")
elif nutzungsart == "Kapitalanlage (Reine Vermietung)":
    st.sidebar.warning("ℹ️ Alte Miete bleibt als Belastung.")
    aktuelle_warmmiete = st.sidebar.number_input("Aktuelle Warmmiete (bleibt)", value=defaults["aktuelle_miete"], step=50, key="sb_akt_miete")
    neue_miete_einnahme = st.sidebar.number_input("Geplante Mieteinnahme (Kalt)", value=600, step=50, key="sb_neue_miete_ka")

st.sidebar.markdown("---")
st.sidebar.header("2. Haushalt & Familie")
anzahl_erwachsene = st.sidebar.radio("Antragsteller", ["Alleinstehend", "Paar (2 Personen)"], index=1, key="sb_erwachsene")
anzahl_kinder = st.sidebar.number_input("Anzahl Kinder", value=defaults["kinder"], step=1, min_value=0, key="sb_kinder")

with st.sidebar.expander("⚙️ Experten-Werte", expanded=False):
    var_kindergeld = st.number_input("Kindergeld (€)", value=250, step=10, min_value=0, key="exp_kindergeld")
    var_pauschale_single = st.number_input("LH Single (€)", value=1200, step=50, min_value=0, key="exp_p_single")
    var_pauschale_paar = st.number_input("LH Paar (€)", value=1600, step=50, min_value=0, key="exp_p_paar")
    var_pauschale_kind = st.number_input("LH Kind (€)", value=400, step=25, min_value=0, key="exp_p_kind")
    var_bewirtschaftung = st.number_input("Bewirtschaftung Neu (€)", value=450, step=50, min_value=0, key="exp_bewirt")
    var_haircut_neu = st.number_input("Risikoabschlag Miete Neu (%)", value=80, step=5, max_value=100, key="exp_haircut_neu")
    var_notar = st.number_input("Notar (%)", value=2.0, step=0.1, min_value=0.0, format="%.2f", key="exp_notar")

st.sidebar.header("3. Einnahmen (Netto)")
gehalt_haupt = st.sidebar.number_input("Gehalt Hauptverdiener", value=defaults["gehalt_h"], step=50, min_value=0, key="sb_gehalt_h")
gehalt_partner = st.sidebar.number_input("Gehalt Partner/in", value=defaults["gehalt_p"], step=50, min_value=0, key="sb_gehalt_p") if anzahl_erwachsene == "Paar (2 Personen)" else 0
nebeneinkommen = st.sidebar.number_input("Minijob / Nebentätigkeit", value=0, step=50, min_value=0, key="sb_neben")
sonstiges_einkommen = st.sidebar.number_input("Sonstiges", value=0, step=50, min_value=0, key="sb_sonst")

st.sidebar.header("4. Bestands-Immobilien")
hat_bestand = st.sidebar.checkbox("Schon Immobilien vorhanden?", value=False, key="sb_hat_bestand")

anrechenbare_miete_bestand = 0.0
bestand_rate = 0.0
bauspar_rate = 0.0 # NEU

if hat_bestand:
    with st.sidebar.expander("Details Bestand", expanded=True):
        miete_kalt_pacht = st.number_input("Kaltmiete Einnahmen", value=0, step=50, min_value=0, key="sb_miete")
        bestand_rate = st.number_input("Rate Bestands-Kredit (Bank)", value=0, step=50, min_value=0, key="sb_bestand_rate")
        
        # HIER IST DAS NEUE FELD FÜR DEINE SPARRATE
        bauspar_rate = st.number_input("Bausparrate / Tilgungsersatz", value=0, step=50, min_value=0, key="sb_bauspar", help="Monatliche Sparrate zur Zinssicherung (z.B. Bausparvertrag), die zwingend gezahlt werden muss.")
        
        haircut = st.slider("Bank-Ansatz Miete (%)", 60, 90, 75, key="sb_haircut")
        anrechenbare_miete_bestand = miete_kalt_pacht * (haircut / 100)

st.sidebar.header("5. Eigenkapital & Markt")
eigenkapital = st.sidebar.number_input("Eigenkapital", value=defaults["ek"], step=1000, min_value=0, key="sb_ek")
zins_satz = st.sidebar.number_input("Sollzins (%)", value=3.8, step=0.1, min_value=0.1, format="%.2f", key="sb_zins")
tilgung_satz = st.sidebar.number_input("Tilgung (%)", value=2.0, step=0.1, min_value=0.0, format="%.2f", key="sb_tilgung")

st.sidebar.header("6. Kaufnebenkosten")
grunderwerbsteuer_prozent = st.sidebar.number_input("Grunderwerbsteuer (%)", value=6.5, step=0.5, min_value=0.0, format="%.2f", key="sb_grunderwerb")
makler_prozent = st.sidebar.number_input("Makler (%)", value=3.57, step=0.5, min_value=0.0, format="%.2f", key="sb_makler")
konsum_kredite = st.sidebar.number_input("Konsumkredite (Auto etc.)", value=0, step=50, min_value=0, key="sb_konsum")

# --- NEU: KONKRETER OBJEKT CHECK ---
st.sidebar.markdown("---")
st.sidebar.header("7. Konkretes Objekt prüfen (Optional)")
wunsch_kaufpreis = st.sidebar.number_input("Kaufpreis Wunsch-Immobilie", value=0, step=5000, min_value=0, key="sb_wunsch_preis", help="Gib hier einen Preis ein, um zu prüfen, ob dieses konkrete Haus ins Budget passt.")


# ==========================================
# LOGIK & BERECHNUNG
# ==========================================

# 1. Pauschalen
basis_pauschale = var_pauschale_paar if anzahl_erwachsene == "Paar (2 Personen)" else var_pauschale_single
kinder_pauschale_gesamt = anzahl_kinder * var_pauschale_kind
kindergeld_betrag = anzahl_kinder * var_kindergeld
puffer = 250 

# 2. Nutzungsart
belastung_durch_aktuelle_miete = 0.0
einnahme_neues_objekt_kalkuliert = 0.0

if nutzungsart == "Kapitalanlage (Reine Vermietung)":
    belastung_durch_aktuelle_miete = aktuelle_warmmiete
    einnahme_neues_objekt_kalkuliert = neue_miete_einnahme * (var_haircut_neu / 100)
elif nutzungsart == "Eigenheim mit Vermietung (Einliegerw./MFH)":
    belastung_durch_aktuelle_miete = 0.0
    einnahme_neues_objekt_kalkuliert = neue_miete_einnahme * (var_haircut_neu / 100)
else: 
    belastung_durch_aktuelle_miete = 0.0
    einnahme_neues_objekt_kalkuliert = 0.0

# 3. Summen
total_einnahmen = (gehalt_haupt + gehalt_partner + nebeneinkommen + 
                   sonstiges_einkommen + kindergeld_betrag + 
                   anrechenbare_miete_bestand + einnahme_neues_objekt_kalkuliert)

gesamt_lebenshaltung = basis_pauschale + kinder_pauschale_gesamt

# HIER WIRD DIE BAUSPARRATE ABGEZOGEN
total_ausgaben = (gesamt_lebenshaltung + bestand_rate + bauspar_rate + konsum_kredite + 
                  var_bewirtschaftung + puffer + belastung_durch_aktuelle_miete)

freier_betrag = total_einnahmen - total_ausgaben

# 4. Finanzierung MAXIMAL
nebenkosten_faktor = (grunderwerbsteuer_prozent + var_notar + makler_prozent) / 100 

if freier_betrag > 0:
    annuitaet = zins_satz + tilgung_satz
    max_darlehen = (freier_betrag * 12 * 100) / annuitaet if annuitaet > 0 else 0
else:
    max_darlehen = 0

gesamt_budget = max_darlehen + eigenkapital
max_kaufpreis = gesamt_budget / (1 + nebenkosten_faktor)
nk_wert = max_kaufpreis * nebenkosten_faktor

# 5. Konkreter Objekt Check (Wunsch-Immobilie)
wunsch_rate = 0.0
wunsch_nebenkosten = 0.0
wunsch_darlehen = 0.0
wunsch_check_ok = False

if wunsch_kaufpreis > 0:
    wunsch_nebenkosten = wunsch_kaufpreis * nebenkosten_faktor
    wunsch_invest = wunsch_kaufpreis + wunsch_nebenkosten
    wunsch_darlehen = wunsch_invest - eigenkapital
    
    if wunsch_darlehen > 0:
        # Rate = Kredit * Annuität / 1200
        wunsch_rate = (wunsch_darlehen * (zins_satz + tilgung_satz)) / 100 / 12
    else:
        wunsch_rate = 0 # Voll mit EK bezahlt
        
    if wunsch_rate <= freier_betrag:
        wunsch_check_ok = True
    else:
        wunsch_check_ok = False

# ==========================================
# DOWNLOAD JSON
# ==========================================
export_data = {
    "sb_name": kunden_name,
    "sb_nutzung": nutzungsart,
    "sb_akt_miete": aktuelle_warmmiete,
    "sb_neue_miete_mix": neue_miete_einnahme if nutzungsart == "Eigenheim mit Vermietung (Einliegerw./MFH)" else 0,
    "sb_neue_miete_ka": neue_miete_einnahme if nutzungsart == "Kapitalanlage (Reine Vermietung)" else 0,
    "sb_erwachsene": anzahl_erwachsene,
    "sb_kinder": anzahl_kinder,
    "sb_gehalt_h": gehalt_haupt,
    "sb_gehalt_p": gehalt_partner,
    "sb_neben": nebeneinkommen,
    "sb_sonst": sonstiges_einkommen,
    "sb_hat_bestand": hat_bestand,
    "sb_miete": miete_kalt_pacht if hat_bestand else 0,
    "sb_bestand_rate": bestand_rate if hat_bestand else 0,
    "sb_bauspar": bauspar_rate, # NEU
    "sb_ek": eigenkapital,
    "sb_zins": zins_satz,
    "sb_tilgung": tilgung_satz,
    "sb_grunderwerb": grunderwerbsteuer_prozent,
    "sb_makler": makler_prozent,
    "sb_konsum": konsum_kredite,
    "sb_wunsch_preis": wunsch_kaufpreis # NEU
}
json_string = json.dumps(export_data)
safe_filename = f"{kunden_name.replace(' ', '_')}_Finanzcheck.json"

with col_dl:
    st.download_button(
        label=f"💾 Daten sichern (JSON)",
        data=json_string,
        file_name=safe_filename,
        mime="application/json"
    )

# ==========================================
# ANZEIGE
# ==========================================
st.divider()
st.markdown(f"### 🎯 Analyse für: {kunden_name}")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💰 Haushaltsrechnung")
    
    # Einnahmen
    df_in_dict = {
        "Posten": ["Gehalt Haupt", "Gehalt Partner", "Kindergeld", "Sonstiges", "Miete Bestand (netto)", "Miete Neu (kalk.)"],
        "Betrag": [gehalt_haupt, gehalt_partner, kindergeld_betrag, nebeneinkommen+sonstiges_einkommen, anrechenbare_miete_bestand, einnahme_neues_objekt_kalkuliert]
    }
    df_in = pd.DataFrame(df_in_dict)
    df_in = df_in[df_in["Betrag"] > 0.01]
    st.dataframe(df_in, hide_index=True, use_container_width=True)
    st.success(f"Summe Einnahmen: **{total_einnahmen:,.2f} €**")

    # Ausgaben
    st.markdown("---")
    ausgaben_liste = [
        ("Lebenshaltung", gesamt_lebenshaltung),
        ("Rate Bestand (Kredit)", bestand_rate),
        ("Bausparer / Tilgungsaussetzung", bauspar_rate), # HIER ANGEZEIGT
        ("Konsumkredite", konsum_kredite),
        ("Aktuelle Miete", belastung_durch_aktuelle_miete),
        ("Bewirtschaftung (Neu)", var_bewirtschaftung),
        ("Sicherheits-Puffer", puffer)
    ]
    df_out = pd.DataFrame(ausgaben_liste, columns=["Posten", "Betrag"])
    df_out = df_out[df_out["Betrag"] > 0.01]
    st.dataframe(df_out, hide_index=True, use_container_width=True)
    st.error(f"Summe Ausgaben: **{total_ausgaben:,.2f} €**")

with col2:
    st.subheader("🏠 Ergebnis & Rate")
    
    if freier_betrag < 0:
        st.warning(f"⚠️ **Budget nicht ausreichend!** Fehlbetrag: {abs(freier_betrag):,.2f} €")
    else:
        st.info(f"🏦 Verfügbares Budget (Rate): **{freier_betrag:,.2f} €**")
        
        # --- WUNSCH OBJEKT CHECK ---
        if wunsch_kaufpreis > 0:
            st.markdown("---")
            st.markdown(f"### 🔎 Check: {wunsch_kaufpreis:,.0f} € Immobilie")
            
            col_a, col_b = st.columns(2)
            col_a.write(f"Nötige Rate:")
            col_a.write(f"**{wunsch_rate:,.2f} €**")
            
            col_b.write("Ergebnis:")
            if wunsch_check_ok:
                col_b.success("✅ PASST!")
            else:
                col_b.error("❌ ZU TEUER")
                diff = wunsch_rate - freier_betrag
                st.caption(f"Es fehlen monatlich {diff:,.2f} €")
                
            with st.expander("Details zur Rechnung"):
                st.write(f"Kaufpreis: {wunsch_kaufpreis:,.0f} €")
                st.write(f"+ Nebenkosten: {wunsch_nebenkosten:,.0f} €")
                st.write(f"- Eigenkapital: {eigenkapital:,.0f} €")
                st.write(f"= Darlehen: {wunsch_darlehen:,.0f} €")
            
            st.markdown("---")

        # --- MAXIMAL RECHNUNG ---
        st.caption("Maximal machbarer Kaufpreis (Theoretisch):")
        st.metric(label="Max. Kaufpreis", value=f"{max_kaufpreis:,.0f} €")
        
        # PDF GENERIERUNG
        pdf_data = {
            "name": kunden_name,
            "scenario": nutzungsart,
            "ein": total_einnahmen,
            "aus": total_ausgaben,
            "frei": freier_betrag,
            "zins": zins_satz,
            "tilg": tilgung_satz,
            "kaufpreis": max_kaufpreis,
            "nk": nk_wert,
            "ek": eigenkapital,
            "kredit": max_darlehen,
            "wunsch_preis": wunsch_kaufpreis,
            "wunsch_rate": wunsch_rate
        }
        
        pdf_bytes = create_pdf(pdf_data)
        
        st.download_button(
            label="📄 Als PDF-Zertifikat exportieren",
            data=pdf_bytes,
            file_name=f"{kunden_name.replace(' ', '_')}_Zertifikat.pdf",
            mime="application/pdf",
        )

st.divider()

# Grafik mit Markierung für Wunsch-Rate
fig = px.bar(
    x=["Einnahmen", "Ausgaben", "Budget"],
    y=[total_einnahmen, total_ausgaben, max(freier_betrag, 0)],
    color=["1", "2", "3"], 
    color_discrete_sequence=["green", "red", "blue"],
    title=f"Liquiditäts-Check: {kunden_name}"
)

# Wenn Wunschpreis aktiv, zeichnen wir eine Linie ein
if wunsch_kaufpreis > 0:
    fig.add_hline(y=wunsch_rate, line_dash="dot", annotation_text="Nötige Rate (Wunsch)", annotation_position="top right", line_color="orange")

fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
