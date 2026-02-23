import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PT. REZEKI KENCANA", layout="wide")

file_path = "master_data_produksi.xlsx"
file_blok_path = "data_produksi.xlsx" # <-- Tambahkan ini

# --- FUNGSI UTILITAS ---
def get_base64_logo(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None
    except: return None

@st.cache_data(ttl=0)
def load_data(path):
    try:
        d_dash = pd.read_excel(path, sheet_name="Dashboard")
        d_prod = pd.read_excel(path, sheet_name="Prod Afd")
        d_bb = pd.read_excel(path, sheet_name="Budget & BBC")
        d_mentah = pd.read_excel(path, sheet_name="Grading Mentah")
        d_mengkal = pd.read_excel(path, sheet_name="Grading Mengkal")
        
        for df in [d_dash, d_prod, d_bb, d_mentah, d_mengkal]:
            df['Tanggal'] = pd.to_datetime(df['Tanggal'])

        cols = ['Tanggal', 'Afd A (JJG)', 'Afd A %', 'Afd B (JJG)', 'Afd B %', 'Afd C (JJG)', 'Afd C %', 
                'Afd D (JJG)', 'Afd D %', 'Afd E (JJG)', 'Afd E %', 'Afd F (JJG)', 'Afd F %', 'ESTATE (JJG)', 'ESTATE %']
        d_mentah.columns = cols
        d_mengkal.columns = cols
        
        for df in [d_mentah, d_mengkal]:
            for col in df.columns:
                if '%' in col:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')
        return d_dash, d_prod, d_bb, d_mentah, d_mengkal
    except:
        return [pd.DataFrame()]*5
@st.cache_data(ttl=0)
def load_data_blok(path):
    try:
        # Membaca 5 sheet baru
        d_tbs = pd.read_excel(path, sheet_name="tbs")
        d_ton = pd.read_excel(path, sheet_name="tonase")
        d_yph = pd.read_excel(path, sheet_name="yph")
        d_brd = pd.read_excel(path, sheet_name="brondol")
        d_bjr = pd.read_excel(path, sheet_name="bjr")
        return d_tbs, d_ton, d_yph, d_brd, d_bjr
    except:
        return [pd.DataFrame()]*5
def add_summary_row(df, label="TOTAL", current_afd_cols=[]):
    if df.empty: return df
    summary_data = {'Tgl': label}
    for col in df.columns:
        if col == 'Tgl': continue
        numeric_col = pd.to_numeric(df[col], errors='coerce')
        if any(x in col.upper() for x in ['(J)', 'AKTUAL', 'AKP', 'RESTAN', 'TOTAL', 'CURAH', 'LUAS']) or col in current_afd_cols:
            summary_data[col] = numeric_col.sum()
        elif '%' in col or 'TK' in col.upper():
            summary_data[col] = numeric_col.mean()
        else:
            summary_data[col] = pd.NA
    return pd.concat([df, pd.DataFrame([summary_data])], ignore_index=True)

def style_total_row(row):
    is_total = row['Tgl'] in ['TOTAL', 'TOTAL / RERATA']
    return ['background-color: #204348; color: white; font-weight: bold' if is_total else '' for _ in row]

def create_gauge(title, value, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        number = {'suffix': "%", 'font': {'size': 18}, 'valueformat':'.1f'},
        title = {'text': title, 'font': {'size': 13}},
        gauge = {
            'axis': {'range': [0, 120], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'steps': [
                {'range': [0, 85], 'color': '#fee2e2'},
                {'range': [85, 100], 'color': '#fef9c3'},
                {'range': [100, 120], 'color': '#dcfce7'}]
        }
    ))
    fig.update_layout(height=150, margin=dict(l=25, r=25, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- STYLE & HEADER ---
logo_base64 = get_base64_logo("logo.png")
logo_html = f'<img src="data:image/png;base64,{logo_base64}" style="height:30px; vertical-align:middle; margin-right:10px;">' if logo_base64 else ""

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; background-color: #f8fafc; }}
    .main-header {{ background-color: #1e2d5b; color: white; display: flex; align-items: center; justify-content: center; position: fixed;
        top: 0; left: 0; width: 100%; z-index: 1001; height: 45px; font-weight: 700; font-size: 16px; }}
    .block-container {{ padding-top: 55px !important; padding-bottom: 20px !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    
    /* STYLE UNTUK KARTU METRIK */
    .metric-card {{ background-color: white; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
    .metric-label {{ color: #64748b; font-size: 10px; font-weight: 600; text-transform: uppercase; }}
    .metric-value {{ color: #1e293b; font-size: 19px; font-weight: 700; }}
    
    /* WARNA INDIKATOR KIRI */
    .metric-card.green {{ border-left: 5px solid #22c55e; }}
    .metric-card.yellow {{ border-left: 5px solid #eab308; }}
    .metric-card.blue {{ border-left: 5px solid #3b82f6; }}
    .metric-card.red {{ border-left: 5px solid #ef4444; }}
    .metric-card.orange {{ border-left: 5px solid #f97316; }} /* <-- Tambahkan di sini, di dalam tanda petik */
    
    
    </style>
    <div class="main-header">{logo_html} PT. REZEKI KENCANA - PRODUCTION SYSTEM</div>
    """, unsafe_allow_html=True)

# --- LOAD DATA ---
df_dash, df_prod, df_bb, df_mentah, df_mengkal = load_data(file_path)
df_tbs, df_ton, df_yph, df_brd, df_bjr = load_data_blok(file_blok_path) # <-- Tambahkan ini

if not df_dash.empty:
    # Filter Bar
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 0.6, 0.6, 0.8])
    with f_col1: st.markdown("### 📊 Ringkasan Produksi")
    with f_col2: start_date = st.date_input("Mulai", df_dash['Tanggal'].min(), label_visibility="collapsed")
    with f_col3: end_date = st.date_input("Selesai", df_dash['Tanggal'].max(), label_visibility="collapsed")
    with f_col4:
        csv = df_dash.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Data", data=csv, file_name='produksi.csv', mime='text/csv', use_container_width=True)

    sd, ed = pd.to_datetime(start_date), pd.to_datetime(end_date)
    
    def filter_and_format(df, s, e):
        temp = df[(df['Tanggal'] >= s) & (df['Tanggal'] <= e)].copy()
        temp.insert(0, 'Tgl', temp['Tanggal'].dt.strftime('%d/%m'))
        return temp.drop(columns=['Tanggal'])

    f_dash = filter_and_format(df_dash, sd, ed)
    f_mentah = filter_and_format(df_mentah, sd, ed)
    f_mengkal = filter_and_format(df_mengkal, sd, ed)
    f_prod = filter_and_format(df_prod, sd, ed)

    tabs = st.tabs(["Dashboard Utama", "Distribusi Afdeling", "Grading Mentah", "Grading Mengkal", "Summary Blok"])

# --- TAB 1: DASHBOARD ---
    with tabs[0]:
        # Perhitungan data
        bulan_aktif, tahun_aktif = sd.month, sd.year
        prod_mtd = df_dash[(df_dash['Tanggal'].dt.month == bulan_aktif) & (df_dash['Tanggal'].dt.year == tahun_aktif)]['Aktual Produksi'].sum()
        mask_bb = (df_bb['Tanggal'].dt.month == bulan_aktif) & (df_bb['Tanggal'].dt.year == tahun_aktif)
        total_budget = pd.to_numeric(df_bb.loc[mask_bb, [c for c in df_bb.columns if 'budget' in c.lower()][0]], errors='coerce').sum() if mask_bb.any() else 0
        total_bbc = pd.to_numeric(df_bb.loc[mask_bb, [c for c in df_bb.columns if 'bbc' in c.lower()][0]], errors='coerce').sum() if mask_bb.any() else 0

        # --- BARIS 1 & 2 DENGAN FLEXBOX (AGAR TETAP KIRI-KANAN DI HP) ---
        
        # Variabel Data
        val_prod = f_dash["Aktual Produksi"].sum()
        val_akp = f_dash["AKP"].sum()
        pct_budget = (prod_mtd/total_budget*100 if total_budget>0 else 0)
        pct_bbc = (prod_mtd/total_bbc*100 if total_bbc>0 else 0)
        avg_m = f_mentah["ESTATE %"].mean() if not f_mentah.empty else 0
        avg_mk = f_mengkal["ESTATE %"].mean() if not f_mengkal.empty else 0
        val_ch = f_dash[[c for c in f_dash.columns if 'curah' in c.lower()][0]].sum() if any('curah' in c.lower() for c in f_dash.columns) else 0
        val_tk = f_dash[[c for c in f_dash.columns if 'tk' in c.lower() and 'panen' in c.lower()][0]].mean() if any('tk' in c.lower() for c in f_dash.columns) else 0

        # Logika Status Warna
        m_status = "green" if avg_m < 0 else ("orange" if avg_m <= 0.2 else "red")
        mk_status = "green" if avg_mk < 2 else ("orange" if avg_mk <= 5 else "red")

        # CSS Flexbox Container
        st.markdown("""
            <style>
                .flex-container {
                    display: flex;
                    flex-wrap: nowrap; /* Memaksa tetap satu baris */
                    gap: 10px;
                    margin-bottom: 10px;
                    width: 100%;
                }
                .flex-item {
                    flex: 1; /* Membagi lebar rata */
                    min-width: 0; /* Menghindari overflow */
                }
                /* Kecilkan font sedikit khusus untuk HP agar tidak terpotong */
                @media (max-width: 640px) {
                    .metric-value { font-size: 14px !important; }
                    .metric-label { font-size: 8px !important; }
                }
            </style>
        """, unsafe_allow_html=True)

        # RENDER BARIS ATAS
        st.markdown(f"""
            <div class="flex-container">
                <div class="flex-item">
                    <div class="metric-card green"><div class="metric-label">Produksi</div><div class="metric-value">{val_prod:,.0f}m</div></div>
                </div>
                <div class="flex-item">
                    <div class="metric-card yellow"><div class="metric-label">Total AKP</div><div class="metric-value">{val_akp:,.1f}m</div></div>
                </div>
                <div class="flex-item">
                    <div class="metric-card green"><div class="metric-label">Budget</div><div class="metric-value">{pct_budget:,.1f}%</div></div>
                </div>
                <div class="flex-item">
                    <div class="metric-card red"><div class="metric-label">BBC</div><div class="metric-value">{pct_bbc:,.1f}%</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # RENDER BARIS BAWAH
        st.markdown(f"""
            <div class="flex-container">
                <div class="flex-item">
                    <div class="metric-card {m_status}"><div class="metric-label">Mentah</div><div class="metric-value">{avg_m:,.1f}%</div></div>
                </div>
                <div class="flex-item">
                    <div class="metric-card {mk_status}"><div class="metric-label">Mengkal</div><div class="metric-value">{avg_mk:,.1f}%</div></div>
                </div>
                <div class="flex-item">
                    <div class="metric-card blue"><div class="metric-label">C. Hujan</div><div class="metric-value">{val_ch:,.0f}mm</div></div>
                </div>
                <div class="flex-item">
                    <div class="metric-card yellow"><div class="metric-label">TK Panen</div><div class="metric-value">{val_tk:,.0f}</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Baris 2: Grafik Produksi & Tabel Log
        c_body1, c_body2 = st.columns([2, 1])
        with c_body1:
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=f_dash['Tgl'], y=f_dash['Aktual Produksi'], mode='lines+markers', line=dict(color='#1e2d5b', width=3, shape='spline'), fill='tozeroy', fillcolor='rgba(30, 45, 91, 0.1)', name='Ton'))
            fig_p.update_layout(title="<b>Tren Produksi Harian (Mt)</b>", height=350, margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False), hovermode="x unified")
            st.plotly_chart(fig_p, use_container_width=True)
        with c_body2:
            st.markdown("<b>Log Produksi Terakhir</b>", unsafe_allow_html=True)
            st.dataframe(f_dash[['Tgl', 'Aktual Produksi', 'AKP', 'Restan']].tail(10), use_container_width=True, height=315, hide_index=True)

        # Baris 3: Grafik Tren Grading (YANG TADI HILANG)
        # Baris 3: Grafik Tren Grading (Disamakan dengan gaya Tren Produksi)
        st.markdown("<b>📈 Tren Kualitas Grading (Estate %)</b>", unsafe_allow_html=True)
        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            fig_m = go.Figure()
            fig_m.add_trace(go.Scatter(
                x=f_mentah['Tgl'], 
                y=f_mentah['ESTATE %'], 
                mode='lines+markers', 
                line=dict(color='#3b82f6', width=3, shape='spline'), # width & spline disamakan
                fill='tozeroy', 
                fillcolor='rgba(59, 130, 246, 0.1)', 
                name='Mentah %'
            ))
            fig_m.update_layout(
                title="Tren Mentah (%)", 
                height=280, 
                margin=dict(l=10, r=10, t=40, b=10), 
                plot_bgcolor='rgba(0,0,0,0)', 
                xaxis=dict(showgrid=False),
                hovermode="x unified"
            )
            st.plotly_chart(fig_m, use_container_width=True, config={'displayModeBar': False})

        with g_col2:
            fig_mk = go.Figure()
            fig_mk.add_trace(go.Scatter(
                x=f_mengkal['Tgl'], 
                y=f_mengkal['ESTATE %'], 
                mode='lines+markers', 
                line=dict(color='#ef4444', width=3, shape='spline'), # width & spline disamakan
                fill='tozeroy', 
                fillcolor='rgba(239, 68, 68, 0.1)', 
                name='Mengkal %'
            ))
            fig_mk.update_layout(
                title="Tren Mengkal (%)", 
                height=280, 
                margin=dict(l=10, r=10, t=40, b=10), 
                plot_bgcolor='rgba(0,0,0,0)', 
                xaxis=dict(showgrid=False),
                hovermode="x unified"
            )
            st.plotly_chart(fig_mk, use_container_width=True, config={'displayModeBar': False})
    # --- TAB 2: DISTRIBUSI AFDELING ---
    with tabs[1]:
        afd_cols = [c for c in f_prod.columns if 'Afd' in c and '(Ton)' in c]
        if afd_cols:
            col_g, col_t = st.columns([1, 1.2])
            with col_g:
                df_sum_afd = f_prod[afd_cols].sum().reset_index()
                df_sum_afd.columns = ['Afd', 'Ton']
                st.plotly_chart(px.bar(df_sum_afd, x='Afd', y='Ton', text_auto='.1f', color_discrete_sequence=['#1e2d5b'], title="Total Produksi per Afdeling"), use_container_width=True)
            with col_t:
                df_res = add_summary_row(f_prod, "TOTAL", afd_cols + ['TOTAL'])
                st.dataframe(df_res.style.apply(style_total_row, axis=1).format(precision=2), use_container_width=True, hide_index=True, height=500)

    # --- TAB 3 & 4: GRADING ---
    for i, (name, df_target) in enumerate([("Mentah", f_mentah), ("Mengkal", f_mengkal)]):
        with tabs[i+2]:
            st.markdown(f"### Detail Data {name}")
            df_sum = add_summary_row(df_target, "TOTAL / RERATA")
            f_dict = {c: "{:.2f}%" for c in df_sum.columns if '%' in c}
            f_dict.update({c: "{:,.0f}" for c in df_sum.columns if '(JJG)' in c})
            st.dataframe(df_sum.style.apply(style_total_row, axis=1).format(f_dict, na_rep=""), use_container_width=True, height=550, hide_index=True)
# --- TAB 5: SUMMARY BLOK (FILE BARU) ---
with tabs[4]:
    st.markdown("### 📋 Summary Produksi Per Blok")
    
    # Pilihan Sheet
    sub_tab = st.radio("Pilih Data:", ["TBS", "Tonase", "YPH", "Brondol", "BJR"], horizontal=True)
    
    # Mapping Data
    map_data = {
        "TBS": df_tbs, "Tonase": df_ton, "YPH": df_yph, 
        "Brondol": df_brd, "BJR": df_bjr
    }
    
    # Ambil dataframe asli dan buat salinan untuk tampilan (agar data asli tidak rusak)
    raw_df = map_data[sub_tab]
    
    if not raw_df.empty:
        # --- PROSES FORMAT TANGGAL ---
        active_df = raw_df.copy()
        
        # Fungsi untuk mengubah kolom tanggal menjadi 'MMM YYYY' (misal: Jan 2024)
        new_columns = {}
        for col in active_df.columns:
            try:
                # Coba ubah kolom menjadi datetime, jika berhasil format ke 'MMM YYYY'
                dt_col = pd.to_datetime(col)
                new_columns[col] = dt_col.strftime('%b %Y')
            except:
                # Jika bukan tanggal (misal kolom 'Blok'), biarkan apa adanya
                new_columns[col] = col
        
        active_df = active_df.rename(columns=new_columns)
        # ----------------------------

        # Layout: Tabel di kiri, Grafik rata-rata di kanan
        c_bl1, c_bl2 = st.columns([1.5, 1])
        
        with c_bl1:
            st.markdown(f"**Tabel Data {sub_tab}**")
            st.dataframe(active_df, use_container_width=True, height=500, hide_index=True)
        
        with c_bl2:
            st.markdown(f"**Grafik Perbandingan {sub_tab}**")
            
            # Cari kolom numerik pada dataframe yang sudah diformat
            numeric_cols = active_df.select_dtypes(include=['number']).columns
            
            if not numeric_cols.empty:
                # Ambil kolom terakhir (bulan terbaru)
                latest_col = numeric_cols[-1]
                top_10 = active_df.nlargest(10, latest_col)
                
                fig_blok = px.bar(
                    top_10, 
                    x=active_df.columns[0], # Kolom nama blok
                    y=latest_col,
                    title=f"Top 10 Blok ({latest_col})",
                    color_discrete_sequence=['#f97316']
                )
                fig_blok.update_layout(height=450, margin=dict(l=0,r=0,t=40,b=0))
                st.plotly_chart(fig_blok, use_container_width=True)
    else:
        st.warning("Data tidak ditemukan atau file data_produksi.xlsx belum siap.")
# Auto-refresh
if os.path.exists(file_path):
    mtime = os.path.getmtime(file_path)
    if "last_mtime" not in st.session_state: st.session_state.last_mtime = mtime
    if st.session_state.last_mtime != mtime:
        st.session_state.last_mtime = mtime
        st.rerun()