import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Immo-Finanz Master", layout="wide")

st.title("🏡 Profi-Finanzierungscheck")
st.markdown("### Umfassende Haushalts- & Budgetanalyse")

# ==========================================
# SIDEBAR: EINGABEN
# ==========================================

st.sidebar.header("1. Haushalt & Familie")
anzahl_erwachsene = st.sidebar.radio("Antragsteller", ["Alleinstehend", "Paar (2 Personen)"], index=1)
anzahl_kinder = st.sidebar.number_input("Anzahl Kinder (unter 18)", value=1, step=1)

# --- NEU: EXPERTEN-EINSTELLUNGEN (Hier machst du alles variabel) ---
with st.sidebar.expander("⚙️ Experten-Werte ändern (Kindergeld etc.)", expanded=False):
    st.write("**Bank-Pauschalen & Sätze:**")
    var_kindergeld = st.number_input("Kindergeld pro Kind (€)", value=250, step=10)
    var_pauschale_single = st.number_input("Lebenshaltung Single (€)", value=1200, step=50)
    var_pauschale_paar = st.number_input("Lebenshaltung Paar (€)", value=1600, step=50)
    var_pauschale_kind = st.number_input("Lebenshaltung pro Kind (€)", value=400, step=25)
    var_bewirtschaftung = st.number_input("Bewirtschaftung Neu (€)", value=450, step=50, help="Nebenkosten für das neue Haus (Strom, Gas, Wasser, Rücklagen)")
    var_notar = st.number_input("Notar & Grundbuch (%)", value=2.0, step=0.1)

st.sidebar.header("2. Einnahmen (Monatlich Netto)")
gehalt_haupt = st.sidebar.number_input("Gehalt Hauptverdiener", value=3000, step=50)
gehalt_partner = st.sidebar.number_input("Gehalt Partner/in", value=1800, step=50) if anzahl_erwachsene == "Paar (2 Personen)" else 0
nebeneinkommen = st.sidebar.number_input("Minijob / Nebentätigkeit", value=0, step=50)
sonstiges_einkommen = st.sidebar.number_input("Sonstiges (Unterhalt, Pflegeg.)", value=0, step=50)

# Berechnung mit deinen VARIABLEN Werten
kindergeld_betrag = anzahl_kinder * var_kindergeld

st.sidebar.header("3. Immobilien-Bestand (V+V)")
hat_bestand = st.sidebar.checkbox("Vermietung oder Verpachtung vorhanden?", value=True)

anrechenbare_miete = 0.0
bestand_rate = 0.0

if hat_bestand:
    with st.sidebar.expander("Details Bestandsobjekte", expanded=True):
        miete_kalt_pacht = st.number_input("Kaltmiete / Pacht-Einnahmen", value=1200, step=50)
        bestand_rate = st.number_input("Rate für Bestands-Kredite", value=800, step=50)
        
        # Sicherheitsabschlag Bank (Variabel)
        haircut = st.slider("Bank-Ansatz (%)", 60, 90, 75, help="Wie viel % der Miete erkennt die Bank an?")
        anrechenbare_miete = miete_kalt_pacht * (haircut / 100)
        st.caption(f"Bank rechnet an: {anrechenbare_miete:.2f} €")

st.sidebar.header("4. Eigenkapital & Markt")
eigenkapital = st.sidebar.number_input("Eigenkapital (Cash/Depot)", value=60000, step=1000)
zins_satz = st.sidebar.number_input("Sollzins (%)", value=3.8, step=0.1)
tilgung_satz = st.sidebar.number_input("Tilgung (%)", value=2.0, step=0.1)

st.sidebar.header("5. Kaufnebenkosten")
grunderwerbsteuer_prozent = st.sidebar.number_input("Grunderwerbsteuer (%)", value=6.5, step=0.5)
makler_prozent = st.sidebar.number_input("Makler (%)", value=3.57, step=0.5)

# ==========================================
# BERECHNUNGS-LOGIK
# ==========================================

# 1. Ausgaben-Automatik (Jetzt basierend auf deinen Eingaben oben)
basis_pauschale = var_pauschale_paar if anzahl_erwachsene == "Paar (2 Personen)" else var_pauschale_single
kinder_pauschale_gesamt = anzahl_kinder * var_pauschale_kind
gesamt_lebenshaltung = basis_pauschale + kinder_pauschale_gesamt

puffer = 250 # Sicherheitsreserve (könnte man auch noch variabel machen, wenn man will)

# Sonstige Kredite
konsum_kredite = st.sidebar.number_input("Raten Konsumkredite (Auto etc.)", value=0, step=50)

# 2. Einnahmen Summierung
total_einnahmen = gehalt_haupt + gehalt_partner + nebeneinkommen + sonstiges_einkommen + kindergeld_betrag + anrechenbare_miete

# 3. Ausgaben Summierung
total_ausgaben = gesamt_lebenshaltung + bestand_rate + konsum_kredite + var_bewirtschaftung + puffer

# 4. Freier Betrag
freier_betrag = total_einnahmen - total_ausgaben

# 5. Max Finanzierungssumme
if freier_betrag > 0:
    annuitaet = zins_satz + tilgung_satz
    max_darlehen = (freier_betrag * 12 * 100) / annuitaet
else:
    max_darlehen = 0

# 6. Kaufpreis Rückrechnung (Nutzt jetzt die variable Notar-Gebühr)
nebenkosten_faktor = (grunderwerbsteuer_prozent + var_notar + makler_prozent) / 100 
gesamt_budget = max_darlehen + eigenkapital
max_kaufpreis = gesamt_budget / (1 + nebenkosten_faktor)

# ==========================================
# ANZEIGE
# ==========================================

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💰 Einnahmen & Ausgaben")
    
    # Einnahmen Tabelle
    st.markdown("**Einnahmen (monatlich)**")
    df_in = pd.DataFrame({
        "Posten": ["Gehalt Haupt", "Gehalt Partner", f"Kindergeld ({var_kindergeld}€/Kind)", "Minijob/Sonst.", "V+V (bereinigt)"],
        "Betrag": [gehalt_haupt, gehalt_partner, kindergeld_betrag, nebeneinkommen+sonstiges_einkommen, anrechenbare_miete]
    })
    df_in = df_in[df_in["Betrag"] > 0]
    st.dataframe(df_in, hide_index=True, use_container_width=True)
    st.info(f"Gesamteinnahmen: **{total_einnahmen:,.2f} €**")

    # Ausgaben Tabelle
    st.markdown("**Ausgaben (Pauschalen & Verpflichtungen)**")
    df_out = pd.DataFrame({
        "Posten": [
            f"Lebenshaltung (Basis: {basis_pauschale}€)", 
            f"Lebenshaltung Kinder ({var_pauschale_kind}€/Kind)",
            "Rate Bestandsimmobilie", 
            "Konsumkredite", 
            "Bewirtschaftung (Neu)", 
            "Sicherheits-Puffer"
        ],
        "Betrag": [basis_pauschale, kinder_pauschale_gesamt, bestand_rate, konsum_kredite, var_bewirtschaftung, puffer]
    })
    df_out = df_out[df_out["Betrag"] > 0] # Zeige nur Zeilen mit Werten > 0
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
        st.caption(f"Inkl. {nk_wert:,.0f} € Kaufnebenkosten (Notar {var_notar}%, Steuer {grunderwerbsteuer_prozent}%, Makler {makler_prozent}%)")
        
        st.markdown("---")
        st.write(f"**Benötigtes Bankdarlehen: {max_darlehen:,.0f} €**")

# Visueller Check
st.divider()

# Balkendiagramm
fig = px.bar(
    x=["Einnahmen", "Ausgaben", "Frei"],
    y=[total_einnahmen, total_ausgaben, freier_betrag],
    color=["1", "2", "3"], 
    color_discrete_sequence=["green", "red", "blue"],
    title="Liquiditäts-Check"
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)