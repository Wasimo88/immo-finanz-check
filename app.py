import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Immo-Finanz Master", layout="wide")

# ==========================================
# 🔒 SICHERHEITS-CHECK (PASSWORT)
# ==========================================
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Erstmaliger Start: Session State initialisieren
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # Wenn Passwort schon korrekt war, direkt reinlassen
    if st.session_state["password_correct"]:
        return True

    # Eingabefeld zeigen
    st.text_input(
        "🔒 Bitte Passwort eingeben", type="password", on_change=password_entered, key="password"
    )
    
    if "password_correct" in st.session_state and st.session_state["password_correct"] == False:
        st.error("😕 Passwort falsch")

    return False

if not check_password():
    st.stop()  # Hier stoppt die App, wenn kein Passwort da ist!

# ==========================================
# AB HIER BEGINNT DEINE EIGENTLICHE APP
# ==========================================

st.title("🏡 Profi-Finanzierungscheck")
st.markdown("### Umfassende Haushalts- & Budgetanalyse")

# --- SIDEBAR: EINGABEN ---
st.sidebar.header("1. Haushalt & Familie")
anzahl_erwachsene = st.sidebar.radio("Antragsteller", ["Alleinstehend", "Paar (2 Personen)"], index=1)
anzahl_kinder = st.sidebar.number_input("Anzahl Kinder (unter 18)", value=1, step=1, min_value=0)

# --- EXPERTEN-EINSTELLUNGEN ---
with st.sidebar.expander("⚙️ Experten-Werte ändern (Kindergeld etc.)", expanded=False):
    st.write("**Bank-Pauschalen & Sätze:**")
    var_kindergeld = st.number_input("Kindergeld pro Kind (€)", value=250, step=10, min_value=0)
    var_pauschale_single = st.number_input("Lebenshaltung Single (€)", value=1200, step=50, min_value=0)
    var_pauschale_paar = st.number_input("Lebenshaltung Paar (€)", value=1600, step=50, min_value=0)
    var_pauschale_kind = st.number_input("Lebenshaltung pro Kind (€)", value=400, step=25, min_value=0)
    var_bewirtschaftung = st.number_input("Bewirtschaftung Neu (€)", value=450, step=50, min_value=0)
    var_notar = st.number_input("Notar & Grundbuch (%)", value=2.0, step=0.1, min_value=0.0, format="%.2f")

st.sidebar.header("2. Einnahmen (Monatlich Netto)")
gehalt_haupt = st.sidebar.number_input("Gehalt Hauptverdiener", value=3000, step=50, min_value=0)
gehalt_partner = st.sidebar.number_input("Gehalt Partner/in", value=1800, step=50, min_value=0) if anzahl_erwachsene == "Paar (2 Personen)" else 0
nebeneinkommen = st.sidebar.number_input("Minijob / Nebentätigkeit", value=0, step=50, min_value=0)
sonstiges_einkommen = st.sidebar.number_input("Sonstiges (Unterhalt, Pflegeg.)", value=0, step=50, min_value=0)

kindergeld_betrag = anzahl_kinder * var_kindergeld

st.sidebar.header("3. Immobilien-Bestand (V+V)")
hat_bestand = st.sidebar.checkbox("Vermietung oder Verpachtung vorhanden?", value=True)

anrechenbare_miete = 0.0
bestand_rate = 0.0

if hat_bestand:
    with st.sidebar.expander("Details Bestandsobjekte", expanded=True):
        miete_kalt_pacht = st.number_input("Kaltmiete / Pacht-Einnahmen", value=1200, step=50, min_value=0)
        bestand_rate = st.number_input("Rate für Bestands-Kredite", value=800, step=50, min_value=0)
        haircut = st.slider("Bank-Ansatz (%)", 60, 90, 75)
        anrechenbare_miete = miete_kalt_pacht * (haircut / 100)
        st.caption(f"Bank rechnet an: {anrechenbare_miete:.2f} €")

st.sidebar.header("4. Eigenkapital & Markt")
eigenkapital = st.sidebar.number_input("Eigenkapital (Cash/Depot)", value=60000, step=1000, min_value=0)
zins_satz = st.sidebar.number_input("Sollzins (%)", value=3.8, step=0.1, min_value=0.1, format="%.2f")
tilgung_satz = st.sidebar.number_input("Tilgung (%)", value=2.0, step=0.1, min_value=0.0, format="%.2f")

st.sidebar.header("5. Kaufnebenkosten")
grunderwerbsteuer_prozent = st.sidebar.number_input("Grunderwerbsteuer (%)", value=6.5, step=0.5, min_value=0.0, format="%.2f")
makler_prozent = st.sidebar.number_input("Makler (%)", value=3.57, step=0.5, min_value=0.0, format="%.2f")

# --- BERECHNUNG ---
basis_pauschale = var_pauschale_paar if anzahl_erwachsene == "Paar (2 Personen)" else var_pauschale_single
kinder_pauschale_gesamt = anzahl_kinder * var_pauschale_kind
gesamt_lebenshaltung = basis_pauschale + kinder_pauschale_gesamt
puffer = 250 
konsum_kredite = st.sidebar.number_input("Raten Konsumkredite (Auto etc.)", value=0, step=50, min_value=0)

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

# --- ANZEIGE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💰 Einnahmen & Ausgaben")
    df_in = pd.DataFrame({
        "Posten": ["Gehalt Haupt", "Gehalt Partner", f"Kindergeld", "Minijob/Sonst.", "V+V (bereinigt)"],
        "Betrag": [gehalt_haupt, gehalt_partner, kindergeld_betrag, nebeneinkommen+sonstiges_einkommen, anrechenbare_miete]
    })
    df_in = df_in[df_in["Betrag"] > 0.01]
    st.dataframe(df_in, hide_index=True, use_container_width=True)
    st.info(f"Gesamteinnahmen: **{total_einnahmen:,.2f} €**")

    df_out = pd.DataFrame({
        "Posten": ["Lebenshaltung", "Lebenshaltung Kinder", "Rate Bestandsimmobilie", "Konsumkredite", "Bewirtschaftung (Neu)", "Sicherheits-Puffer"],
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

# Grafik (Mobil-Optimiert: staticPlot=True)
fig = px.bar(
    x=["Einnahmen", "Ausgaben", "Frei"],
    y=[total_einnahmen, total_ausgaben, max(freier_betrag, 0)],
    color=["1", "2", "3"], 
    color_discrete_sequence=["green", "red", "blue"],
    title="Liquiditäts-Check"
)
fig.update_layout(showlegend=False)

# HIER IST DER FIX FÜR DAS HANDY:
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
