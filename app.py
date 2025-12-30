import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime
import json
from PIL import Image
import io
from openai import OpenAI

# Carica variabili ambiente
load_dotenv()

# Configurazione pagina
st.set_page_config(
    page_title="DVR PRO - Paradigma+",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Personalizzato con colori Paradigma+
st.markdown("""
<style>
    /* Colori Paradigma+ */
    :root {
        --primary: #1B3A57;
        --accent: #FF6B6B;
        --bg: #F8F9FA;
    }
    
    /* Header personalizzato */
    .main-header {
        background: linear-gradient(135deg, #1B3A57 0%, #2C5F8D 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .accent-text {
        color: #FF6B6B;
        font-weight: 600;
    }
    
    /* Bottoni */
    .stButton>button {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(255, 107, 107, 0.3);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        background-color: transparent;
        border-radius: 8px;
        color: #1B3A57;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1B3A57 0%, #2C5F8D 100%);
        color: white !important;
    }
    
    /* Sezioni */
    .section-header {
        background: #1B3A57;
        color: white;
        padding: 1rem;
        border-radius: 8px 8px 0 0;
        margin-top: 1.5rem;
        font-weight: 600;
    }
    
    .section-content {
        background: white;
        padding: 1.5rem;
        border-radius: 0 0 8px 8px;
        border: 2px solid #E5E7EB;
    }
    
    /* Alert successo */
    .success-message {
        background: #10B981;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Report Box */
    .report-box {
        background: #F9FAFB;
        border: 2px solid #E5E7EB;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .report-title {
        font-weight: 600;
        color: #1B3A57;
        margin-bottom: 0.5rem;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Inizializza Supabase
@st.cache_resource
def init_supabase():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

supabase = init_supabase()

# Inizializza OpenAI per Whisper
@st.cache_resource
def init_openai():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

openai_client = init_openai()

# Inizializza session state
if 'checklist_id' not in st.session_state:
    st.session_state.checklist_id = None
if 'checklist_data' not in st.session_state:
    st.session_state.checklist_data = {}

# Header
st.markdown("""
<div class="main-header">
    <h1>🛡️ DVR PRO - <span class="accent-text">PARADIGMA+</span></h1>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Sistema Intelligente Valutazione Rischi</p>
</div>
""", unsafe_allow_html=True)

# Funzioni helper
def save_checklist(data):
    """Salva checklist in Supabase"""
    try:
        data['updated_at'] = datetime.now().isoformat()
        
        if st.session_state.checklist_id:
            # Update
            result = supabase.table('checklists').update(data).eq('id', st.session_state.checklist_id).execute()
        else:
            # Insert
            result = supabase.table('checklists').insert(data).execute()
            st.session_state.checklist_id = result.data[0]['id']
        
        return True
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")
        return False

def upload_file_to_supabase(file, path):
    """Upload file su Supabase Storage"""
    try:
        file_bytes = file.read()
        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.name}"
        full_path = f"{path}/{file_name}"
        
        supabase.storage.from_('checklist-files').upload(full_path, file_bytes)
        
        # Get public URL
        url = supabase.storage.from_('checklist-files').get_public_url(full_path)
        return url
    except Exception as e:
        st.error(f"Errore upload: {e}")
        return None

def transcribe_audio(audio_file):
    """Trascrizione audio con Whisper"""
    try:
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="it"
        )
        return transcript.text
    except Exception as e:
        st.error(f"Errore trascrizione: {e}")
        return None

# Sidebar - Selezione/Creazione Checklist
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/1B3A57/FFFFFF?text=PARADIGMA%2B", use_container_width=True)
    
    st.markdown("### 📋 Gestione Checklist")
    
    # Nuova checklist
    if st.button("➕ Nuova Checklist", use_container_width=True):
        st.session_state.checklist_id = None
        st.session_state.checklist_data = {}
        st.rerun()
    
    # Carica checklist esistenti
    try:
        checklists = supabase.table('checklists').select('id, ragione_sociale, created_at, status').order('created_at', desc=True).limit(10).execute()
        
        if checklists.data:
            st.markdown("### 📂 Checklist Recenti")
            for cl in checklists.data:
                status_emoji = "✅" if cl['status'] == 'completa' else "⏳"
                if st.button(f"{status_emoji} {cl['ragione_sociale'][:20]}", key=cl['id'], use_container_width=True):
                    st.session_state.checklist_id = cl['id']
                    # Carica dati
                    result = supabase.table('checklists').select('*').eq('id', cl['id']).execute()
                    st.session_state.checklist_data = result.data[0]
                    st.rerun()
    except:
        pass

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📍 SOPRALLUOGO", "💻 COMPLETAMENTO", "📊 REPORT FINALE", "🚀 GENERA DVR"])

# ============================================
# TAB 1: SOPRALLUOGO
# ============================================
with tab1:
    st.markdown('<div class="section-header">🏢 DATI AZIENDA</div>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            ragione_sociale = st.text_input(
                "Ragione Sociale",
                value=st.session_state.checklist_data.get('ragione_sociale', ''),
                key='ragione_sociale'
            )
            
            ateco = st.text_input(
                "Codice ATECO",
                value=st.session_state.checklist_data.get('ateco', ''),
                placeholder="Es: 25.11.00",
                key='ateco'
            )
            
            datore_lavoro = st.text_input(
                "Datore di Lavoro",
                value=st.session_state.checklist_data.get('datore_lavoro', {}).get('nome', '') if isinstance(st.session_state.checklist_data.get('datore_lavoro'), dict) else '',
                key='datore_lavoro'
            )
        
        with col2:
            sede = st.text_area(
                "Sede Operativa",
                value=st.session_state.checklist_data.get('sede', ''),
                height=100,
                placeholder="Via, Città, CAP, Provincia",
                key='sede'
            )
            
            n_dipendenti = st.number_input(
                "Numero Dipendenti",
                min_value=0,
                value=st.session_state.checklist_data.get('n_dipendenti', 0),
                key='n_dipendenti'
            )
            
            rspp_tipo = st.selectbox(
                "RSPP",
                ["Datore Lavoro", "Interno", "Esterno"],
                index=0,
                key='rspp_tipo'
            )
    
    # LUOGHI DI LAVORO - NUOVA SEZIONE
    st.markdown('<div class="section-header">🏭 LUOGHI DI LAVORO</div>', unsafe_allow_html=True)
    
    if 'luoghi_lavoro' not in st.session_state:
        st.session_state.luoghi_lavoro = st.session_state.checklist_data.get('luoghi_lavoro', [])
    
    with st.expander("➕ Aggiungi Luogo di Lavoro"):
        luogo_nome = st.text_input("Nome Luogo", placeholder="Es: Ufficio Amministrativo, Magazzino, Officina...", key='new_luogo_nome')
        luogo_mq = st.number_input("Superficie (mq)", min_value=0, key='new_luogo_mq')
        luogo_note = st.text_area("Note Descrittive", placeholder="Caratteristiche, layout, particolarità...", key='new_luogo_note')
        
        # Audio per descrizione
        st.markdown("**🎤 Dettatura Vocale**")
        luogo_audio = st.file_uploader("Registra descrizione vocale", type=['mp3', 'wav', 'm4a'], key='new_luogo_audio')
        
        if luogo_audio:
            with st.spinner("Trascrizione in corso..."):
                trascrizione = transcribe_audio(luogo_audio)
                if trascrizione:
                    st.success("✅ Trascrizione completata!")
                    luogo_note = st.text_area("Trascrizione", value=trascrizione, key='new_luogo_note_transcript')
        
        luogo_foto = st.file_uploader("📷 Foto Luogo", type=['jpg', 'png'], accept_multiple_files=True, key='new_luogo_foto')
        
        if st.button("✅ Aggiungi Luogo"):
            if luogo_nome:
                nuovo_luogo = {
                    'nome': luogo_nome,
                    'superficie_mq': luogo_mq,
                    'note': luogo_note,
                    'foto': []
                }
                st.session_state.luoghi_lavoro.append(nuovo_luogo)
                st.success(f"✅ Luogo {luogo_nome} aggiunto!")
                st.rerun()
    
    if st.session_state.luoghi_lavoro:
        for idx, luogo in enumerate(st.session_state.luoghi_lavoro):
            with st.expander(f"🏭 {luogo['nome']} - {luogo.get('superficie_mq', 0)} mq"):
                st.write(f"**Note:** {luogo.get('note', 'N/A')}")
                if st.button("🗑️ Rimuovi", key=f'remove_luogo_{idx}'):
                    st.session_state.luoghi_lavoro.pop(idx)
                    st.rerun()
    
    # DIPENDENTI
    st.markdown('<div class="section-header">👥 ELENCO DIPENDENTI</div>', unsafe_allow_html=True)
    
    if 'dipendenti' not in st.session_state:
        st.session_state.dipendenti = st.session_state.checklist_data.get('dipendenti', [])
    
    # Aggiungi dipendente
    with st.expander("➕ Aggiungi Dipendente"):
        col1, col2, col3 = st.columns(3)
        with col1:
            dip_nome = st.text_input("Nome", key='new_dip_nome')
        with col2:
            dip_cognome = st.text_input("Cognome", key='new_dip_cognome')
        with col3:
            dip_mansione = st.text_input("Mansione", key='new_dip_mansione')
        
        st.markdown("**📄 Documenti**")
        col1, col2, col3 = st.columns(3)
        with col1:
            doc_id = st.file_uploader("Carta Identità", type=['pdf', 'jpg', 'png'], key='new_dip_id')
        with col2:
            doc_formazione = st.file_uploader("Attestati Formazione", type=['pdf', 'jpg', 'png'], accept_multiple_files=True, key='new_dip_form')
        with col3:
            doc_idoneita = st.file_uploader("Idoneità Sanitaria", type=['pdf', 'jpg', 'png'], key='new_dip_idon')
        
        if st.button("✅ Aggiungi Dipendente"):
            if dip_nome or dip_cognome:
                nuovo_dip = {
                    'nome': dip_nome,
                    'cognome': dip_cognome,
                    'mansione': dip_mansione,
                    'documenti': []
                }
                st.session_state.dipendenti.append(nuovo_dip)
                st.success(f"✅ Dipendente {dip_nome} {dip_cognome} aggiunto!")
                st.rerun()
    
    # Lista dipendenti
    if st.session_state.dipendenti:
        for idx, dip in enumerate(st.session_state.dipendenti):
            with st.expander(f"👤 {dip['nome']} {dip['cognome']} - {dip.get('mansione', 'N/A')}"):
                if st.button("🗑️ Rimuovi", key=f'remove_dip_{idx}'):
                    st.session_state.dipendenti.pop(idx)
                    st.rerun()
    
    # ATTREZZATURE
    st.markdown('<div class="section-header">⚙️ ELENCO ATTREZZATURE</div>', unsafe_allow_html=True)
    
    if 'attrezzature' not in st.session_state:
        st.session_state.attrezzature = st.session_state.checklist_data.get('attrezzature', [])
    
    with st.expander("➕ Aggiungi Attrezzatura"):
        col1, col2 = st.columns(2)
        with col1:
            attr_nome = st.text_input("Nome Attrezzatura", key='new_attr_nome')
            attr_marca = st.text_input("Marca", key='new_attr_marca')
        with col2:
            attr_modello = st.text_input("Modello", key='new_attr_modello')
            attr_note = st.text_area("Note", key='new_attr_note', height=80)
        
        attr_foto = st.file_uploader("📷 Foto Attrezzatura", type=['jpg', 'png'], accept_multiple_files=True, key='new_attr_foto')
        
        if st.button("✅ Aggiungi Attrezzatura"):
            if attr_nome:
                nuova_attr = {
                    'nome': attr_nome,
                    'marca': attr_marca,
                    'modello': attr_modello,
                    'note': attr_note,
                    'foto': []
                }
                st.session_state.attrezzature.append(nuova_attr)
                st.success(f"✅ Attrezzatura {attr_nome} aggiunta!")
                st.rerun()
    
    if st.session_state.attrezzature:
        for idx, attr in enumerate(st.session_state.attrezzature):
            with st.expander(f"⚙️ {attr['nome']} - {attr.get('marca', '')} {attr.get('modello', '')}"):
                st.write(f"**Note:** {attr.get('note', 'N/A')}")
                if st.button("🗑️ Rimuovi", key=f'remove_attr_{idx}'):
                    st.session_state.attrezzature.pop(idx)
                    st.rerun()
    
    # ANTINCENDIO
    st.markdown('<div class="section-header">🔥 CHECK ANTINCENDIO</div>', unsafe_allow_html=True)
    
    soggetta_scia = st.radio(
        "Azienda soggetta a SCIA antincendio?",
        ["Sì", "No", "Da verificare"],
        key='soggetta_scia'
    )
    
    if soggetta_scia == "No":
        st.info("📋 Verifica Conformità Mini Codice D.M. 03/09/2021")
        
        check_items = [
            "Reazione al fuoco materiali conforme",
            "Compartimentazione adeguata",
            "Vie di esodo libere e segnalate",
            "Estintori adeguati e verificati",
            "Segnaletica sicurezza conforme",
            "Illuminazione emergenza funzionante"
        ]
        
        checks = {}
        for item in check_items:
            checks[item] = st.checkbox(item, key=f'check_{item}')
        
        nc_antincendio = st.text_area("❌ Non Conformità Rilevate", key='nc_antincendio')
    
    # RISCHI ESTESO CON NOTE
    st.markdown('<div class="section-header">⚠️ VALUTAZIONE RISCHI DETTAGLIATA</div>', unsafe_allow_html=True)
    
    rischi_completi = [
        "Scivolamento e cadute a livello",
        "Cadute dall'alto",
        "Urti, colpi, impatti, compressioni",
        "Tagli, punture, abrasioni",
        "Schiacciamento",
        "Elettrico",
        "Rumore",
        "Vibrazioni",
        "Rischio chimico",
        "Movimentazione Manuale Carichi (MMC)",
        "Videoterminali (VDT)",
        "Lavori in quota",
        "Incendio ed esplosione",
        "Biologico",
        "Radiazioni",
        "Microclima",
        "Illuminazione",
        "Stress lavoro-correlato",
        "Posture incongrue",
        "Lavoro notturno",
        "Lavoro solitario",
        "Differenze di genere, età, provenienza"
    ]
    
    if 'rischi_selezionati' not in st.session_state:
        st.session_state.rischi_selezionati = st.session_state.checklist_data.get('rischi_selezionati', {})
    
    st.markdown("**Seleziona i rischi presenti e aggiungi note per ognuno:**")
    
    # Mostra rischi in colonne
    col1, col2, col3 = st.columns(3)
    
    for idx, rischio in enumerate(rischi_completi):
        with [col1, col2, col3][idx % 3]:
            is_selected = st.checkbox(rischio, value=rischio in st.session_state.rischi_selezionati, key=f'rischio_check_{idx}')
            
            if is_selected:
                note = st.text_area(
                    f"Note per '{rischio}'",
                    value=st.session_state.rischi_selezionati.get(rischio, {}).get('note', ''),
                    key=f'rischio_note_{idx}',
                    height=100,
                    placeholder="Descrivi il rischio specifico, la gravità, le misure..."
                )
                
                # Audio per note rischio
                audio_rischio = st.file_uploader(
                    f"🎤 Dettatura per '{rischio}'",
                    type=['mp3', 'wav', 'm4a'],
                    key=f'rischio_audio_{idx}'
                )
                
                if audio_rischio:
                    with st.spinner("Trascrizione in corso..."):
                        trascrizione = transcribe_audio(audio_rischio)
                        if trascrizione:
                            st.success("✅ Trascrizione completata!")
                            note = st.text_area(
                                f"Trascrizione '{rischio}'",
                                value=trascrizione,
                                key=f'rischio_note_transcript_{idx}'
                            )
                
                st.session_state.rischi_selezionati[rischio] = {
                    'presente': True,
                    'note': note
                }
            elif rischio in st.session_state.rischi_selezionati:
                del st.session_state.rischi_selezionati[rischio]
    
    # FOTO GENERALI
    st.markdown('<div class="section-header">📷 FOTO AMBIENTI</div>', unsafe_allow_html=True)
    
    foto_ambienti = st.file_uploader(
        "Carica foto ambienti di lavoro",
        type=['jpg', 'png'],
        accept_multiple_files=True,
        key='foto_ambienti'
    )
    
    # NON CONFORMITÀ
    st.markdown('<div class="section-header">❌ NON CONFORMITÀ RILEVATE</div>', unsafe_allow_html=True)
    
    if 'non_conformita' not in st.session_state:
        st.session_state.non_conformita = st.session_state.checklist_data.get('non_conformita', [])
    
    with st.expander("➕ Aggiungi Non Conformità"):
        nc_desc = st.text_area("Descrizione Non Conformità", key='new_nc_desc')
        
        # Audio per NC
        nc_audio = st.file_uploader("🎤 Dettatura NC", type=['mp3', 'wav', 'm4a'], key='new_nc_audio')
        
        if nc_audio:
            with st.spinner("Trascrizione in corso..."):
                trascrizione = transcribe_audio(nc_audio)
                if trascrizione:
                    st.success("✅ Trascrizione completata!")
                    nc_desc = st.text_area("Trascrizione NC", value=trascrizione, key='new_nc_desc_transcript')
        
        nc_priorita = st.select_slider("Priorità", options=["Bassa", "Media", "Alta"], key='new_nc_priorita')
        nc_foto = st.file_uploader("Foto NC", type=['jpg', 'png'], key='new_nc_foto')
        
        if st.button("✅ Aggiungi NC"):
            if nc_desc:
                nuova_nc = {
                    'descrizione': nc_desc,
                    'priorita': nc_priorita,
                    'foto_url': None
                }
                st.session_state.non_conformita.append(nuova_nc)
                st.success("✅ Non conformità aggiunta!")
                st.rerun()
    
    if st.session_state.non_conformita:
        for idx, nc in enumerate(st.session_state.non_conformita):
            priority_emoji = {"Bassa": "🟢", "Media": "🟡", "Alta": "🔴"}
            with st.expander(f"{priority_emoji[nc['priorita']]} {nc['descrizione'][:50]}..."):
                st.write(f"**Priorità:** {nc['priorita']}")
                if st.button("🗑️ Rimuovi", key=f'remove_nc_{idx}'):
                    st.session_state.non_conformita.pop(idx)
                    st.rerun()
    
    # NOTE
    note_sopralluogo = st.text_area(
        "📝 Note Sopralluogo",
        value=st.session_state.checklist_data.get('note_sopralluogo', ''),
        height=150,
        key='note_sopralluogo'
    )
    
    # SALVA
    st.markdown("---")
    if st.button("💾 SALVA SOPRALLUOGO", type="primary", use_container_width=True):
        data_to_save = {
            'ragione_sociale': ragione_sociale,
            'sede': sede,
            'ateco': ateco,
            'n_dipendenti': n_dipendenti,
            'datore_lavoro': {'nome': datore_lavoro},
            'rspp': {'tipo': rspp_tipo},
            'luoghi_lavoro': st.session_state.luoghi_lavoro,
            'dipendenti': st.session_state.dipendenti,
            'attrezzature': st.session_state.attrezzature,
            'soggetta_scia_antincendio': soggetta_scia,
            'rischi_selezionati': st.session_state.rischi_selezionati,
            'non_conformita': st.session_state.non_conformita,
            'note_sopralluogo': note_sopralluogo,
            'status': 'bozza'
        }
        
        if save_checklist(data_to_save):
            st.markdown('<div class="success-message">✅ Sopralluogo salvato con successo!</div>', unsafe_allow_html=True)

# ============================================
# TAB 2: COMPLETAMENTO
# ============================================
with tab2:
    if not st.session_state.checklist_id:
        st.warning("⚠️ Completa prima il sopralluogo nel Tab 1")
    else:
        # OFFERTA COMMERCIALE - NUOVA SEZIONE
        st.markdown('<div class="section-header">💼 OFFERTA COMMERCIALE SERVIZI</div>', unsafe_allow_html=True)
        
        if 'servizi_offerta' not in st.session_state:
            st.session_state.servizi_offerta = st.session_state.checklist_data.get('servizi_offerta', [])
        
        with st.expander("➕ Aggiungi Servizio"):
            serv_nome = st.text_input("Nome Servizio", placeholder="Es: Piano Emergenza, Formazione Antincendio, Visite Mediche...", key='new_serv_nome')
            serv_categoria = st.selectbox(
                "Categoria Servizio",
                ["📄 DOCUMENTO", "🎓 FORMAZIONE", "🏥 SORVEGLIANZA SANITARIA"],
                key='new_serv_cat'
            )
            
            # Campi specifici per categoria
            if serv_categoria == "📄 DOCUMENTO":
                serv_ore = st.number_input("Ore necessarie per produzione documento", min_value=0.5, step=0.5, key='new_serv_ore')
                serv_dettaglio = f"{serv_ore} ore"
                
            elif serv_categoria == "🎓 FORMAZIONE":
                serv_n_persone = st.number_input("Numero persone da formare", min_value=1, key='new_serv_persone')
                serv_ore_corso = st.number_input("Ore corso", min_value=1, key='new_serv_ore_corso')
                serv_dettaglio = f"{serv_n_persone} persone - {serv_ore_corso}h"
                
            elif serv_categoria == "🏥 SORVEGLIANZA SANITARIA":
                st.markdown("**Dipendenti per mansione:**")
                mansioni_ss = {}
                n_mansioni_ss = st.number_input("Quante mansioni diverse?", min_value=1, max_value=10, key='new_serv_n_mans')
                
                for i in range(int(n_mansioni_ss)):
                    col1, col2 = st.columns(2)
                    with col1:
                        mans_nome = st.text_input(f"Mansione {i+1}", key=f'new_serv_mans_{i}')
                    with col2:
                        mans_n_dip = st.number_input(f"N. dipendenti", min_value=1, key=f'new_serv_ndip_{i}')
                    
                    if mans_nome:
                        mansioni_ss[mans_nome] = mans_n_dip
                
                serv_dettaglio = json.dumps(mansioni_ss)
            
            serv_note = st.text_area("Note aggiuntive", key='new_serv_note')
            serv_prezzo = st.number_input("Prezzo indicativo (€)", min_value=0.0, step=50.0, key='new_serv_prezzo')
            
            if st.button("✅ Aggiungi Servizio"):
                if serv_nome:
                    nuovo_servizio = {
                        'nome': serv_nome,
                        'categoria': serv_categoria,
                        'dettaglio': serv_dettaglio,
                        'note': serv_note,
                        'prezzo': serv_prezzo
                    }
                    st.session_state.servizi_offerta.append(nuovo_servizio)
                    st.success(f"✅ Servizio {serv_nome} aggiunto!")
                    st.rerun()
        
        if st.session_state.servizi_offerta:
            st.markdown("### 📋 Servizi in Offerta")
            
            # Raggruppa per categoria
            documenti = [s for s in st.session_state.servizi_offerta if s['categoria'] == "📄 DOCUMENTO"]
            formazione = [s for s in st.session_state.servizi_offerta if s['categoria'] == "🎓 FORMAZIONE"]
            sorveglianza = [s for s in st.session_state.servizi_offerta if s['categoria'] == "🏥 SORVEGLIANZA SANITARIA"]
            
            if documenti:
                st.markdown("#### 📄 Documenti")
                for idx, serv in enumerate(documenti):
                    with st.expander(f"{serv['nome']} - {serv['dettaglio']} - €{serv['prezzo']}"):
                        st.write(f"**Note:** {serv.get('note', 'N/A')}")
                        if st.button("🗑️ Rimuovi", key=f'remove_serv_doc_{idx}'):
                            st.session_state.servizi_offerta.remove(serv)
                            st.rerun()
            
            if formazione:
                st.markdown("#### 🎓 Formazione")
                for idx, serv in enumerate(formazione):
                    with st.expander(f"{serv['nome']} - {serv['dettaglio']} - €{serv['prezzo']}"):
                        st.write(f"**Note:** {serv.get('note', 'N/A')}")
                        if st.button("🗑️ Rimuovi", key=f'remove_serv_form_{idx}'):
                            st.session_state.servizi_offerta.remove(serv)
                            st.rerun()
            
            if sorveglianza:
                st.markdown("#### 🏥 Sorveglianza Sanitaria")
                for idx, serv in enumerate(sorveglianza):
                    with st.expander(f"{serv['nome']} - €{serv['prezzo']}"):
                        try:
                            mansioni = json.loads(serv['dettaglio'])
                            for mans, n in mansioni.items():
                                st.write(f"- {mans}: {n} dipendenti")
                        except:
                            st.write(serv['dettaglio'])
                        st.write(f"**Note:** {serv.get('note', 'N/A')}")
                        if st.button("🗑️ Rimuovi", key=f'remove_serv_ss_{idx}'):
                            st.session_state.servizi_offerta.remove(serv)
                            st.rerun()
            
            # Totale offerta
            totale_offerta = sum(s['prezzo'] for s in st.session_state.servizi_offerta)
            st.markdown(f"### 💰 Totale Offerta: **€ {totale_offerta:,.2f}**")
        
        # FORMAZIONE OBBLIGATORIA
        st.markdown('<div class="section-header">🎓 FORMAZIONE OBBLIGATORIA</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 Antincendio")
            livello_antincendio = st.selectbox(
                "Livello Formazione Richiesto",
                ["Livello 1 (4h)", "Livello 2 (8h)", "Livello 3 (16h)", "Non necessario"],
                key='livello_antincendio'
            )
            note_antincendio = st.text_area("Note", key='note_antincendio')
        
        with col2:
            st.subheader("🚑 Primo Soccorso")
            gruppo_ps = st.selectbox(
                "Gruppo Azienda",
                ["Gruppo A (16h)", "Gruppo B (12h)", "Gruppo C (12h)", "Non necessario"],
                key='gruppo_ps'
            )
            note_ps = st.text_area("Note", key='note_ps')
        
        # MANSIONI
        st.markdown('<div class="section-header">👷 MANSIONI AZIENDALI</div>', unsafe_allow_html=True)
        
        if 'mansioni' not in st.session_state:
            st.session_state.mansioni = st.session_state.checklist_data.get('mansioni', [])
        
        with st.expander("➕ Aggiungi Mansione"):
            mans_nome = st.text_input("Nome Mansione", placeholder="Es: Operaio Generico", key='new_mans_nome')
            mans_n_lav = st.number_input("N. Lavoratori", min_value=0, key='new_mans_n')
            
            st.markdown("**🎤 Descrizione Dettagliata Mansione**")
            st.info("💡 Usa il microfono per dettare la descrizione completa")
            
            mans_desc = st.text_area(
                "Descrizione",
                placeholder="Descrivi dettagliatamente: attività svolte, responsabilità, attrezzature utilizzate, rischi specifici...",
                height=200,
                key='new_mans_desc'
            )
            
            # Audio per mansione
            mans_audio = st.file_uploader("🎤 Dettatura Mansione", type=['mp3', 'wav', 'm4a'], key='new_mans_audio')
            
            if mans_audio:
                with st.spinner("Trascrizione in corso..."):
                    trascrizione = transcribe_audio(mans_audio)
                    if trascrizione:
                        st.success("✅ Trascrizione completata!")
                        mans_desc = st.text_area("Trascrizione Mansione", value=trascrizione, key='new_mans_desc_transcript')
            
            if st.button("✅ Aggiungi Mansione"):
                if mans_nome:
                    nuova_mans = {
                        'nome': mans_nome,
                        'n_lavoratori': mans_n_lav,
                        'descrizione': mans_desc
                    }
                    st.session_state.mansioni.append(nuova_mans)
                    st.success(f"✅ Mansione {mans_nome} aggiunta!")
                    st.rerun()
        
        if st.session_state.mansioni:
            st.markdown("### 📋 Mansioni Inserite")
            for idx, mans in enumerate(st.session_state.mansioni):
                with st.expander(f"👷 {mans['nome']} ({mans['n_lavoratori']} lavoratori)"):
                    st.write(f"**Descrizione:** {mans['descrizione'][:200]}..." if len(mans['descrizione']) > 200 else mans['descrizione'])
                    if st.button("🗑️ Rimuovi", key=f'remove_mans_{idx}'):
                        st.session_state.mansioni.pop(idx)
                        st.rerun()
        
        # DESCRIZIONI DETTAGLIATE
        st.markdown('<div class="section-header">📝 DESCRIZIONI DETTAGLIATE</div>', unsafe_allow_html=True)
        
        st.markdown("**🎤 Descrizione Luoghi di Lavoro**")
        desc_luoghi = st.text_area(
            "Descrivi i luoghi di lavoro",
            value=st.session_state.checklist_data.get('desc_luoghi_lavoro', ''),
            height=200,
            placeholder="Usa microfono per descrivere ambienti, layout, caratteristiche...",
            key='desc_luoghi'
        )
        
        # Audio per luoghi
        audio_luoghi = st.file_uploader("🎤 Dettatura Luoghi", type=['mp3', 'wav', 'm4a'], key='audio_luoghi')
        
        if audio_luoghi:
            with st.spinner("Trascrizione in corso..."):
                trascrizione = transcribe_audio(audio_luoghi)
                if trascrizione:
                    st.success("✅ Trascrizione completata!")
                    desc_luoghi = st.text_area("Trascrizione Luoghi", value=trascrizione, key='desc_luoghi_transcript')
        
        st.markdown("**🎤 Ciclo Lavorativo Generale**")
        ciclo_lav = st.text_area(
            "Descrivi il ciclo lavorativo",
            value=st.session_state.checklist_data.get('ciclo_lavorativo', ''),
            height=200,
            placeholder="Usa microfono per descrivere il processo produttivo generale...",
            key='ciclo_lav'
        )
        
        # Audio per ciclo
        audio_ciclo = st.file_uploader("🎤 Dettatura Ciclo", type=['mp3', 'wav', 'm4a'], key='audio_ciclo')
        
        if audio_ciclo:
            with st.spinner("Trascrizione in corso..."):
                trascrizione = transcribe_audio(audio_ciclo)
                if trascrizione:
                    st.success("✅ Trascrizione completata!")
                    ciclo_lav = st.text_area("Trascrizione Ciclo", value=trascrizione, key='ciclo_lav_transcript')
        
        st.markdown("**🎤 Misure di Prevenzione Presenti**")
        misure_prev = st.text_area(
            "Descrivi misure già presenti",
            value=st.session_state.checklist_data.get('misure_prevenzione', ''),
            height=200,
            placeholder="Usa microfono per descrivere DPI, protezioni, procedure già in atto...",
            key='misure_prev'
        )
        
        # Audio per misure
        audio_misure = st.file_uploader("🎤 Dettatura Misure", type=['mp3', 'wav', 'm4a'], key='audio_misure')
        
        if audio_misure:
            with st.spinner("Trascrizione in corso..."):
                trascrizione = transcribe_audio(audio_misure)
                if trascrizione:
                    st.success("✅ Trascrizione completata!")
                    misure_prev = st.text_area("Trascrizione Misure", value=trascrizione, key='misure_prev_transcript')
        
        # PIANO MIGLIORAMENTO
        st.markdown('<div class="section-header">📈 PIANO DI MIGLIORAMENTO</div>', unsafe_allow_html=True)
        
        if 'piano_miglioramento' not in st.session_state:
            st.session_state.piano_miglioramento = st.session_state.checklist_data.get('piano_miglioramento', [])
        
        with st.expander("➕ Aggiungi Azione Migliorativa"):
            st.markdown("**🎤 Descrizione Azione**")
            azione_desc = st.text_area(
                "Descrivi l'azione",
                placeholder="Usa microfono per descrivere l'intervento di miglioramento...",
                key='new_azione_desc'
            )
            
            # Audio per azione
            azione_audio = st.file_uploader("🎤 Dettatura Azione", type=['mp3', 'wav', 'm4a'], key='new_azione_audio')
            
            if azione_audio:
                with st.spinner("Trascrizione in corso..."):
                    trascrizione = transcribe_audio(azione_audio)
                    if trascrizione:
                        st.success("✅ Trascrizione completata!")
                        azione_desc = st.text_area("Trascrizione Azione", value=trascrizione, key='new_azione_desc_transcript')
            
            col1, col2 = st.columns(2)
            with col1:
                azione_resp = st.text_input("Responsabile", key='new_azione_resp')
            with col2:
                azione_scad = st.date_input("Scadenza", key='new_azione_scad')
            
            if st.button("✅ Aggiungi Azione"):
                if azione_desc:
                    nuova_azione = {
                        'descrizione': azione_desc,
                        'responsabile': azione_resp,
                        'scadenza': str(azione_scad)
                    }
                    st.session_state.piano_miglioramento.append(nuova_azione)
                    st.success("✅ Azione aggiunta!")
                    st.rerun()
        
        if st.session_state.piano_miglioramento:
            for idx, azione in enumerate(st.session_state.piano_miglioramento):
                with st.expander(f"📌 {azione['descrizione'][:50]}..."):
                    st.write(f"**Responsabile:** {azione.get('responsabile', 'N/A')}")
                    st.write(f"**Scadenza:** {azione.get('scadenza', 'N/A')}")
                    if st.button("🗑️ Rimuovi", key=f'remove_azione_{idx}'):
                        st.session_state.piano_miglioramento.pop(idx)
                        st.rerun()
        
        # SALVA COMPLETAMENTO
        st.markdown("---")
        if st.button("💾 SALVA COMPLETAMENTO", type="primary", use_container_width=True):
            data_to_save = {
                'servizi_offerta': st.session_state.servizi_offerta,
                'livello_formazione_antincendio': livello_antincendio,
                'gruppo_primo_soccorso': gruppo_ps,
                'mansioni': st.session_state.mansioni,
                'desc_luoghi_lavoro': desc_luoghi,
                'ciclo_lavorativo': ciclo_lav,
                'misure_prevenzione': misure_prev,
                'piano_miglioramento': st.session_state.piano_miglioramento,
                'status': 'completa'
            }
            
            # Merge con dati esistenti
            existing_data = st.session_state.checklist_data.copy()
            existing_data.update(data_to_save)
            
            if save_checklist(existing_data):
                st.markdown('<div class="success-message">✅ Completamento salvato con successo!</div>', unsafe_allow_html=True)

# ============================================
# TAB 3: REPORT FINALE
# ============================================
with tab3:
    if not st.session_state.checklist_id:
        st.warning("⚠️ Completa prima i dati nei Tab precedenti")
    else:
        st.markdown('<div class="section-header">📊 REPORT COMPLETO CHECKLIST</div>', unsafe_allow_html=True)
        
        data = st.session_state.checklist_data
        
        # DATI AZIENDA
        st.markdown("### 🏢 Dati Azienda")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ragione Sociale", data.get('ragione_sociale', 'N/A'))
            st.metric("ATECO", data.get('ateco', 'N/A'))
        with col2:
            st.metric("N. Dipendenti", data.get('n_dipendenti', 0))
            st.metric("Datore Lavoro", data.get('datore_lavoro', {}).get('nome', 'N/A'))
        with col3:
            st.metric("RSPP", data.get('rspp', {}).get('tipo', 'N/A'))
            st.metric("Stato", "✅ Completa" if data.get('status') == 'completa' else "⏳ Bozza")
        
        st.markdown(f"**Sede:** {data.get('sede', 'N/A')}")
        
        # LUOGHI DI LAVORO
        st.markdown("### 🏭 Luoghi di Lavoro")
        luoghi = data.get('luoghi_lavoro', [])
        if luoghi:
            for luogo in luoghi:
                st.markdown(f"""
                <div class="report-box">
                    <div class="report-title">📍 {luogo['nome']}</div>
                    <p><strong>Superficie:</strong> {luogo.get('superficie_mq', 0)} mq</p>
                    <p><strong>Note:</strong> {luogo.get('note', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessun luogo di lavoro inserito")
        
        # DIPENDENTI
        st.markdown("### 👥 Dipendenti")
        dipendenti = data.get('dipendenti', [])
        if dipendenti:
            st.write(f"**Totale dipendenti inseriti:** {len(dipendenti)}")
            for dip in dipendenti:
                st.markdown(f"- **{dip['nome']} {dip['cognome']}** - {dip.get('mansione', 'N/A')}")
        else:
            st.info("Nessun dipendente inserito")
        
        # ATTREZZATURE
        st.markdown("### ⚙️ Attrezzature")
        attrezzature = data.get('attrezzature', [])
        if attrezzature:
            st.write(f"**Totale attrezzature:** {len(attrezzature)}")
            for attr in attrezzature:
                st.markdown(f"- **{attr['nome']}** - {attr.get('marca', '')} {attr.get('modello', '')}")
        else:
            st.info("Nessuna attrezzatura inserita")
        
        # RISCHI
        st.markdown("### ⚠️ Rischi Identificati")
        rischi = data.get('rischi_selezionati', {})
        if rischi:
            st.write(f"**Totale rischi identificati:** {len(rischi)}")
            for rischio, info in rischi.items():
                if info.get('presente'):
                    st.markdown(f"""
                    <div class="report-box">
                        <div class="report-title">⚠️ {rischio}</div>
                        <p><strong>Note:</strong> {info.get('note', 'Nessuna nota')}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Nessun rischio selezionato")
        
        # NON CONFORMITÀ
        st.markdown("### ❌ Non Conformità")
        nc = data.get('non_conformita', [])
        if nc:
            st.write(f"**Totale non conformità:** {len(nc)}")
            for item in nc:
                priority_emoji = {"Bassa": "🟢", "Media": "🟡", "Alta": "🔴"}
                st.markdown(f"""
                <div class="report-box">
                    <div class="report-title">{priority_emoji[item['priorita']]} Priorità {item['priorita']}</div>
                    <p>{item['descrizione']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessuna non conformità rilevata")
        
        # MANSIONI
        st.markdown("### 👷 Mansioni")
        mansioni = data.get('mansioni', [])
        if mansioni:
            st.write(f"**Totale mansioni:** {len(mansioni)}")
            for mans in mansioni:
                st.markdown(f"""
                <div class="report-box">
                    <div class="report-title">👷 {mans['nome']} ({mans['n_lavoratori']} lavoratori)</div>
                    <p>{mans['descrizione'][:300]}{'...' if len(mans['descrizione']) > 300 else ''}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessuna mansione inserita")
        
        # FORMAZIONE
        st.markdown("### 🎓 Formazione Obbligatoria")
        st.markdown(f"- **Antincendio:** {data.get('livello_formazione_antincendio', 'Non specificato')}")
        st.markdown(f"- **Primo Soccorso:** {data.get('gruppo_primo_soccorso', 'Non specificato')}")
        
        # OFFERTA COMMERCIALE
        st.markdown("### 💼 Offerta Commerciale")
        servizi = data.get('servizi_offerta', [])
        if servizi:
            st.write(f"**Totale servizi in offerta:** {len(servizi)}")
            
            # Raggruppa per categoria
            documenti = [s for s in servizi if s['categoria'] == "📄 DOCUMENTO"]
            formazione = [s for s in servizi if s['categoria'] == "🎓 FORMAZIONE"]
            sorveglianza = [s for s in servizi if s['categoria'] == "🏥 SORVEGLIANZA SANITARIA"]
            
            if documenti:
                st.markdown("#### 📄 Documenti")
                for serv in documenti:
                    st.markdown(f"- **{serv['nome']}** - {serv['dettaglio']} - €{serv['prezzo']}")
            
            if formazione:
                st.markdown("#### 🎓 Formazione")
                for serv in formazione:
                    st.markdown(f"- **{serv['nome']}** - {serv['dettaglio']} - €{serv['prezzo']}")
            
            if sorveglianza:
                st.markdown("#### 🏥 Sorveglianza Sanitaria")
                for serv in sorveglianza:
                    st.markdown(f"- **{serv['nome']}** - €{serv['prezzo']}")
            
            totale = sum(s['prezzo'] for s in servizi)
            st.markdown(f"### 💰 **Totale Offerta: € {totale:,.2f}**")
        else:
            st.info("Nessun servizio in offerta")
        
        # DESCRIZIONI DETTAGLIATE
        st.markdown("### 📝 Descrizioni Dettagliate")
        
        if data.get('desc_luoghi_lavoro'):
            st.markdown("**Luoghi di Lavoro:**")
            st.text_area("", value=data.get('desc_luoghi_lavoro'), height=150, disabled=True, key='report_luoghi')
        
        if data.get('ciclo_lavorativo'):
            st.markdown("**Ciclo Lavorativo:**")
            st.text_area("", value=data.get('ciclo_lavorativo'), height=150, disabled=True, key='report_ciclo')
        
        if data.get('misure_prevenzione'):
            st.markdown("**Misure di Prevenzione:**")
            st.text_area("", value=data.get('misure_prevenzione'), height=150, disabled=True, key='report_misure')
        
        # PIANO MIGLIORAMENTO
        st.markdown("### 📈 Piano di Miglioramento")
        piano = data.get('piano_miglioramento', [])
        if piano:
            st.write(f"**Totale azioni:** {len(piano)}")
            for azione in piano:
                st.markdown(f"""
                <div class="report-box">
                    <div class="report-title">📌 {azione['descrizione'][:100]}</div>
                    <p><strong>Responsabile:</strong> {azione.get('responsabile', 'N/A')}</p>
                    <p><strong>Scadenza:</strong> {azione.get('scadenza', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessuna azione di miglioramento")
        
        # NOTE
        if data.get('note_sopralluogo'):
            st.markdown("### 📝 Note Sopralluogo")
            st.text_area("", value=data.get('note_sopralluogo'), height=100, disabled=True, key='report_note')
        
        # PULSANTE STAMPA/EXPORT
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🖨️ STAMPA REPORT", use_container_width=True):
                st.info("💡 Usa Ctrl+P o Cmd+P per stampare questa pagina come PDF")

# ============================================
# TAB 4: GENERA DVR
# ============================================
with tab4:
    if not st.session_state.checklist_id:
        st.warning("⚠️ Completa prima i dati nei Tab precedenti")
    else:
        st.markdown('<div class="section-header">📊 ANTEPRIMA DATI</div>', unsafe_allow_html=True)
        
        # Mostra riepilogo
        data = st.session_state.checklist_data
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏢 Azienda", data.get('ragione_sociale', 'N/A'))
            st.metric("👥 Dipendenti", len(data.get('dipendenti', [])))
        
        with col2:
            st.metric("🏭 Luoghi Lavoro", len(data.get('luoghi_lavoro', [])))
            st.metric("⚙️ Attrezzature", len(data.get('attrezzature', [])))
        
        with col3:
            st.metric("👷 Mansioni", len(data.get('mansioni', [])))
            st.metric("⚠️ Rischi", len(data.get('rischi_selezionati', [])))
        
        with col4:
            st.metric("❌ Non Conformità", len(data.get('non_conformita', [])))
            st.metric("💼 Servizi Offerta", len(data.get('servizi_offerta', [])))
        
        st.markdown("---")
        
        # Pulsante Genera DVR (FINTO per ora)
        st.markdown("""
         <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #1B3A57 0%, #2C5F8D 100%); border-radius: 15px; margin: 2rem 0;">
            <h2 style="color: white; margin-bottom: 1rem;">🚀 Generazione DVR con AI</h2>
            <p style="color: rgba(255,255,255,0.8); margin-bottom: 2rem;">
                Il sistema analizzerà tutti i dati inseriti e genererà automaticamente<br>
                il Documento di Valutazione dei Rischi completo e conforme al D.Lgs. 81/08
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 GENERA DVR", type="primary", use_container_width=True):
                st.warning("⚠️ **Funzione in fase di sviluppo**")
                st.info("""
                📅 **Disponibile tra 2-3 giorni**
                
                Il DVR verrà generato automaticamente con intelligenza artificiale basandosi su:
                - Dati aziendali inseriti
                - Luoghi di lavoro con foto e descrizioni
                - Mansioni e descrizioni dettagliate
                - Rischi identificati con note specifiche
                - Misure di prevenzione
                - Piano di miglioramento
                - Offerta commerciale servizi
                
                💡 L'AI verificherà anche eventuali DPI mancanti o non conformità non rilevate durante il sopralluogo.
                """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #6B7280;">
    <p style="margin: 0;">Powered by <strong style="color: #1B3A57;">PARADIGMA+</strong></p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.875rem;">Sistema DVR PRO v2.0 - Dicembre 2024</p>
</div>
""", unsafe_allow_html=True)