import streamlit as st

# --- Konfiguration der Seite ---
st.set_page_config(page_title="Haushaltsrechner Pro", layout="wide")

st.title("💰 Haushaltsrechnung & Finanzierungs-Check")

# --- SIDEBAR: Eingabedaten ---
st.sidebar.header("1. Einkommen & Haushalt")

# FIX: min_value=0 verhindert negative Eingaben bei allen Feldern

gehalt_haupt = st.sidebar.number_input(
    "Gehalt Hauptverdiener (netto)", 
    value=3000, 
    step=50, 
    min_value=0  # Verhindert Minus
)

gehalt_partner = st.sidebar.number_input(
    "Gehalt Partner (netto)", 
    value=520, 
    step=50, 
    min_value=0  # Verhindert Minus
)

# Kinderlogik: Anzahl bestimmt Kindergeld + Ausgabenpauschale
anzahl_kinder = st.sidebar.number_input(
    "Anzahl Kinder", 
    value=2, 
    step=1, 
    min_value=0  # Verhindert negative Kinder
)

kindergeld_pro_kind = 250 # Aktueller Satz 2025
# Berechnung als Standardwert, aber änderbar (nicht negativ)
kindergeld_ges = st.sidebar.number_input(
    "Kindergeld (Gesamt)", 
    value=anzahl_kinder * kindergeld_pro_kind,
    min_value=0  # Verhindert Minus
)

sonstiges = st.sidebar.number_input(
    "Sonstige Einnahmen (Bonus/Miete)", 
    value=500, 
    step=50, 
    min_value=0  # Verhindert Minus
)

# Summe Einnahmen berechnen
summe_einnahmen = gehalt_haupt + gehalt_partner + kindergeld_ges + sonstiges

st.sidebar.markdown("---")
st.sidebar.header("2. Aktuelle Wohnsituation")
st.sidebar.info("Wichtig für den Vergleich 'Miete vs. Eigentum'")

aktuelle_warmmiete = st.sidebar.number_input(
    "Aktuelle Warmmiete", 
    value=1200, 
    step=50, 
    min_value=0
)

aktuelle_qm = st.sidebar.number_input(
    "Aktuelle Wohnfläche (m²)", 
    value=80, 
    step=5, 
    min_value=0
)

st.sidebar.markdown("---")
st.sidebar.header("3. Neues Objekt (Planung)")

neue_qm = st.sidebar.number_input(
    "Geplante Wohnfläche (m²)", 
    value=140, 
    step=5, 
    min_value=0
)

rate_wunsch = st.sidebar.number_input(
    "Geschätzte Kreditrate (Bank)", 
    value=1600, 
    step=50, 
    min_value=0
)


# --- HAUPTBEREICH: Ausgaben-Logik ---

st.header("Monatliche Ausgaben (Kalkulation)")

# Spalten für bessere Optik
col1, col2 = st.columns(2)

with col1:
    st.subheader("Lebenshaltung")
    
    # LOGIK: Bank-Pauschalen berechnen
    # 1. Erwachsener = 1000, 2. Erwachsener = 400, pro Kind = 300
    erwachsene_haushalt = 2 if gehalt_partner > 0 else 1 
    pauschale_calc = 1000 + (400 if erwachsene_haushalt > 1 else 0) + (300 * anzahl_kinder)
    
    st.markdown(f"**Vorschlag Bank:** *{pauschale_calc} €* (basierend auf {erwachsene_haushalt} Erw. + {anzahl_kinder} Kindern)")
    
    ausgabe_lebenshaltung = st.number_input(
        "Lebenshaltungskosten (Pauschale)", 
        value=pauschale_calc,
        min_value=0, # Auch hier keine negativen Ausgaben
        help="Deckt Essen, Kleidung, Mobilität, Hobby und Gesundheit (z.B. Zuzahlungen Diabetes/Medikamente). Basis: Existenzminimum + Puffer."
    )
    
    with st.expander("ℹ️ Offizielle Datenquelle (Destatis)"):
        st.markdown("Vergleichswerte findest du beim Statistischen Bundesamt:")
        st.markdown("[Laufende Wirtschaftsrechnungen (Destatis)](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Einkommen-Konsum-Lebensbedingungen/Konsumausgaben-Lebenshaltungskosten/_inhalt.html)")

with col2:
    st.subheader("Wohnnebenkosten (Neu)")
    
    # LOGIK: Bewirtschaftungskosten (4 € pro qm)
    calc_basis_qm = neue_qm if neue_qm > 0 else 120
    bewirtschaftung_calc = calc_basis_qm * 4.0 
    
    st.markdown(f"**Vorschlag Bank:** *{bewirtschaftung_calc:.0f} €* (ca. 4,00 €/m² bei {calc_basis_qm} m²)")
    
    ausgabe_bewirtschaftung = st.number_input(
        "Bewirtschaftung (Strom, Heizung, Wasser)", 
        value=float(bewirtschaftung_calc),
        step=10.0,
        min_value=0.0, # Keine negativen Nebenkosten
        help="Enthält: Heizung, Strom, Wasser, Müll, Grundsteuer, Gebäudeversicherung. Faustformel: 3,50€ - 4,50€ pro qm."
    )

    with st.expander("ℹ️ Offizielle Datenquelle (Mieterbund)"):
        st.markdown("Durchschnittswerte liefert der Betriebskostenspiegel:")
        st.markdown("[Deutscher Mieterbund - Betriebskostenspiegel](https://www.mieterbund.de/service/betriebskostenspiegel.html)")

# Puffer Logik (1 € pro qm)
puffer_calc = calc_basis_qm * 1.0
if puffer_calc < 200: puffer_calc = 200 # Minimum Puffer

ausgabe_puffer = st.number_input(
    "Instandhaltungs-Puffer (Rücklagen)", 
    value=float(puffer_calc),
    min_value=0.0,
    help="Rücklage für Reparaturen am Haus (Heizung, Dach) oder Ersatzbeschaffung (Waschmaschine, Auto, medizinisches Gerät)."
)

# --- GESAMTRECHNUNG ---
summe_ausgaben_haushalt = ausgabe_lebenshaltung + ausgabe_bewirtschaftung + ausgabe_puffer
verfuegbar_fuer_rate = summe_einnahmen - summe_ausgaben_haushalt
rest_nach_rate = verfuegbar_fuer_rate - rate_wunsch

st.markdown("---")

# --- ERGEBNIS-ANZEIGE ---
col_res1, col_res2, col_res3 = st.columns(3)

with col_res1:
    st.metric(label="Summe Einnahmen", value=f"{summe_einnahmen:,.2f} €")

with col_res2:
    st.metric(label="Summe Lebenshaltung & Hausgeld", value=f"{summe_ausgaben_haushalt:,.2f} €", delta="- Kosten", delta_color="inverse")

with col_res3:
    st.metric(label="Max. verfügbar für Rate", value=f"{verfuegbar_fuer_rate:,.2f} €")

# --- FAZIT & VERGLEICH ---
st.markdown("### 📊 Ergebnis & Analyse")

final_col1, final_col2 = st.columns(2)

with final_col1:
    st.write(f"**Geplante Kreditrate:** {rate_wunsch:,.2f} €")
    if rest_nach_rate > 0:
        st.success(f"✅ Die Rechnung geht auf! Du hast noch **{rest_nach_rate:,.2f} €** monatlichen Überschuss.")
    else:
        st.error(f"⚠️ Achtung! Dir fehlen monatlich **{rest_nach_rate:,.2f} €**. Bitte Ausgaben prüfen oder Rate senken.")

with final_col2:
    st.subheader("Vergleich: Miete vs. Eigentum")
    
    # Vorher: Warmmiete
    # Nachher: Kreditrate + Bewirtschaftung + Puffer (Alles was das Wohnen kostet)
    wohnkosten_neu = rate_wunsch + ausgabe_bewirtschaftung + ausgabe_puffer
    differenz = wohnkosten_neu - aktuelle_warmmiete
    
    st.write(f"Alte Wohnkosten (Warm): **{aktuelle_warmmiete:,.2f} €**")
    st.write(f"Neue Wohnkosten (Rate+Nebenk.+Puffer): **{wohnkosten_neu:,.2f} €**")
    
    if differenz > 0:
        st.warning(f"📈 **Mehrbelastung:** Du musst monatlich **{differenz:,.2f} € mehr** aufbringen als bisher.")
    else:
        st.success(f"📉 **Ersparnis:** Du zahlst monatlich **{abs(differenz):,.2f} € weniger** als bisher.")
