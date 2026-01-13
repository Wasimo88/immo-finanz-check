import streamlit as st
import pandas as pd
import plotly.express as px
import json

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
# 💾 SPEICHERN & LADEN LOGIK
# ==========================================

defaults = {
    "kinder": 1,
    "gehalt_h": 3000,
    "gehalt_p": 0,
    "ek": 60000,
    "kunde": "Kunde" # Default Name
}

def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            for key, value in data.items():
                st.session_state[key] = value
            st.success(f"✅ Daten für '{data.get('sb_name', 'Unbekannt')}' geladen!")
            st.rerun()
        except:
            st.error("Fehler beim Laden der Datei.")

# ==========================================
# HAUPT-APP
# ==========================================

st.title("🏡 Profi-Finanzierungscheck")

# --- DATEI UPLOAD ---
with st.expander("📂 Kundendaten Speichern / Laden", expanded=False):
    col_dl, col_ul = st.columns(2)
    
    with col_ul:
        uploaded_file = st.file_uploader("Alten Stand laden (.json)", type=["json"])
        if uploaded_file:
            load_data(uploaded_file)
            
    with col_dl:
        st.write("Aktuellen Stand sichern:")
        st.info("Der Dateiname wird unten automatisch aus dem Kundennamen generiert.")

# --- SIDEBAR: EINGABEN ---
st.sidebar.header("1. Kunden-Daten")

# NEU: KUNDENNAME FÜR DATEINAME
kunden_name = st.sidebar.text_input("Name des Kunden / Objekts", value=defaults["kunde"], key="sb_name", help="Wird für den Dateinamen beim Speichern verwendet.")

st.sidebar.markdown("---")
st.sidebar.header("2. Haushalt & Familie")

anzahl_erwachsene = st.sidebar.radio("Antragsteller", ["Alleinstehend", "Paar (2 Personen)"], index=1, key="sb_erwachsene")
anzahl_kinder = st.sidebar.number_input("Anzahl Kinder", value=defaults["kinder"], step=1, min_value=0, key="sb_kinder")

with st.sidebar.expander("⚙️ Experten-Werte", expanded=False):
    var_kindergeld = st.number_input("Kindergeld (€)", value=250, step=10, min_value=0, key="exp_kindergeld")
    var_pauschale_single = st.number_input("LH Single (€)", value=1200, step=50, min_value=0, key="exp_p_single")
    var_pauschale_paar = st.number_input("LH Paar (€)", value=1600, step=50, min_value=0, key="exp_p_paar")
    var_pauschale_kind = st.number_input("LH Kind (€)", value=400, step=25, min_value=0, key="exp_p_kind")
    var_bewirtschaftung = st.number_input("Bewirtschaftung (€)", value=450, step=50, min_value=0, key="exp_bewirt")
    var_notar = st.number_input("Notar (%)", value=2.0, step=0.1, min_value=0.0, format="%.2f", key="exp_notar")

st.sidebar.header("3. Einnahmen (Netto)")
gehalt_haupt = st.sidebar.number_input("Gehalt Hauptverdiener", value=defaults["gehalt_h"], step=50, min_value=0, key="sb_gehalt_h")
gehalt_partner = st.sidebar.number_input("Gehalt Partner/in", value=defaults["gehalt_p"], step=50, min_value=0, key="sb_gehalt_p") if anzahl_erwachsene == "Paar (2 Personen)" else 0
nebeneinkommen = st.sidebar.number_input("Minijob / Nebentätigkeit", value=0, step=50, min_value=0, key="sb_neben")
sonstiges_einkommen = st.sidebar.number_input("Sonstiges", value=0, step=50, min_value=0, key="sb_sonst")

kindergeld_betrag = anzahl_kinder * var_kindergeld

st.sidebar.header("4. Immobilien-Bestand")
hat_bestand = st.sidebar.checkbox("Vermietung vorhanden?", value=True, key="sb_hat_bestand")

anrechenbare_miete = 0.0
bestand_rate = 0.0

if hat_bestand:
    with st.sidebar.expander("Details Bestand", expanded=True):
        miete_kalt_pacht = st.number_input("Kaltmiete Einnahmen", value=1200, step=50, min_value=0, key="sb_miete")
        bestand_rate = st.number_input("Rate Bestands-Kredit", value=800, step=50, min_value=0, key="sb_bestand_rate")
        haircut = st.slider("Bank-Ansatz Miete (%)", 60, 90, 75, key="sb_haircut")
        anrechenbare_miete = miete_kalt_pacht * (haircut / 100)
        st.caption(f"Bank rechnet an: {anrechenbare_miete:.2f} €")

st.sidebar.header("5. Eigenkapital & Markt")
eigenkapital = st.sidebar.number_input("Eigenkapital", value=defaults["ek"], step=1000, min_value=0, key="sb_ek")
zins_satz = st.sidebar.number_input("Sollzins (%)", value=3.8, step=0.1, min_value=0.1, format="%.2f", key="sb_zins")
tilgung_satz = st.sidebar.number_input("Tilgung (%)", value=2.0, step=0.1, min_value=0.0, format="%.2f", key="sb_tilgung")

st.sidebar.header("6. Kaufnebenkosten")
grunderwerbsteuer_prozent = st.sidebar.number_input("Grunderwerbsteuer (%)", value=6.5, step=0.5, min_value=0.0, format="%.2f", key="sb_grunderwerb")
makler_prozent = st.sidebar.number_input("Makler (%)", value=3.57, step=0.5, min_value=0.0, format="%.2f", key="sb_makler")

# --- BERECHNUNG ---
basis_pauschale = var_pauschale_paar if anzahl_erwachsene == "Paar (2 Personen)" else var_pauschale_single
kinder_pauschale_gesamt = anzahl_kinder * var_pauschale_kind
gesamt_lebenshaltung = basis_pauschale + kinder_pauschale_gesamt
puffer = 250 
konsum_kredite = st.sidebar.number_input("Konsumkredite (Auto)", value=0, step=50, min_value=0, key="sb_konsum")

total_einnahmen = gehalt_haupt + gehalt_partner + nebeneinkommen + sonstiges_einkommen + kindergeld_betrag + anrechenbare_miete
total_ausgaben = gesamt_lebenshaltung + bestand_rate + konsum_kredite + var_bewirtschaftung + puffer
freier_betrag = total_einnahmen - total_ausgaben

if freier_betrag > 0:
    annuitaet = zins_satz + tilgung_satz
    if annuitaet > 0:
        max_darlehen = (freier_betrag * 12 * 100) / annuitaet
    else:
        max_darlehen = 0
else:
    max_darlehen = 0

nebenkosten_faktor = (grunderwerbsteuer_prozent + var_notar + makler_prozent) / 100 
gesamt_budget = max_darlehen + eigenkapital
max_kaufpreis = gesamt_budget / (1 + nebenkosten_faktor)

# --- DOWNLOAD BUTTON LOGIK (MIT NAMENS-GENERATOR) ---
export_data = {
    "sb_name": kunden_name, # Name mit speichern
    "sb_erwachsene": anzahl_erwachsene,
    "sb_kinder": anzahl_kinder,
    "sb_gehalt_h": gehalt_haupt,
    "sb_gehalt_p": gehalt_partner,
    "sb_neben": nebeneinkommen,
    "sb_sonst": sonstiges_einkommen,
    "sb_hat_bestand": hat_bestand,
    "sb_miete": miete_kalt_pacht if hat_bestand else 0,
    "sb_bestand_rate": bestand_rate if hat_bestand else 0,
    "sb_ek": eigenkapital,
    "sb_zins": zins_satz,
    "sb_tilgung": tilgung_satz,
    "sb_grunderwerb": grunderwerbsteuer_prozent,
    "sb_makler": makler_prozent,
    "sb_konsum": konsum_kredite
}
json_string = json.dumps(export_data)

# Dateiname bereinigen (Leerzeichen zu Unterstrichen)
safe_filename = f"{kunden_name.replace(' ', '_')}_Finanzcheck.json"

with col_dl:
    st.download_button(
        label=f"💾 '{safe_filename}' speichern", # Button zeigt jetzt den Namen an!
        data=json_string,
        file_name=safe_filename,
        mime="application/json"
    )

# --- ANZEIGE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"💰 Analyse für: {kunden_name}") # Name auch hier anzeigen
    
    st.markdown("**Einnahmen (monatlich)**")
    df_in = pd.DataFrame({
        "Posten": ["Gehalt Haupt", "Gehalt Partner", f"Kindergeld", "Minijob/Sonst.", "V+V (bereinigt)"],
        "Betrag": [gehalt_haupt, gehalt_partner, kindergeld_betrag, nebeneinkommen+sonstiges_einkommen, anrechenbare_miete]
    })
    df_in = df_in[df_in["Betrag"] > 0.01]
    st.dataframe(df_in, hide_index=True, use_container_width=True)
    st.info(f"Gesamteinnahmen: **{total_einnahmen:,.2f} €**")

    st.markdown("**Ausgaben**")
    df_out = pd.DataFrame({
        "Posten": ["Lebenshaltung", "Lebenshaltung Kinder", "Rate Bestand", "Konsumkredite", "Bewirtschaftung (Neu)", "Puffer"],
        "Betrag": [basis_pauschale, kinder_pauschale_gesamt, bestand_rate, konsum_kredite, var_bewirtschaftung, puffer]
    })
    df_out = df_out[df_out["Betrag"] > 0.01]
    st.dataframe(df_out, hide_index=True, use_container_width=True)
    st.error(f"Gesamtbelastung: **{total_ausgaben:,.2f} €**")

with col2:
    st.subheader("🏠 Ergebnis")
    if freier_betrag < 0:
        st.warning(f"⚠️ **Budget überschritten!**\n\nFehlbetrag: {abs(freier_betrag):,.2f} €")
    else:
        st.success(f"Verfügbar für neue Rate: **{freier_betrag:,.2f} €**")
        st.markdown("### Maximaler Kaufpreis")
        st.metric(label="Immobilienwert", value=f"{max_kaufpreis:,.0f} €")
        nk_wert = max_kaufpreis * nebenkosten_faktor
        st.caption(f"Inkl. {nk_wert:,.0f} € Kaufnebenkosten")
        st.markdown("---")
        st.write(f"**Benötigtes Bankdarlehen: {max_darlehen:,.0f} €**")

st.divider()

# Grafik (Mobil-Optimiert)
fig = px.bar(
    x=["Einnahmen", "Ausgaben", "Frei"],
    y=[total_einnahmen, total_ausgaben, max(freier_betrag, 0)],
    color=["1", "2", "3"], 
    color_discrete_sequence=["green", "red", "blue"],
    title=f"Liquiditäts-Check: {kunden_name}"
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
