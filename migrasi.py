import pandas as pd
import sqlite3

# 1. Load Excel (Pastikan file Anda bernama data_panen_30rb.xlsx)
try:
    df = pd.read_excel('data_panen_30rb.xlsx')
    
    # 2. Pembersihan Data (Pastikan kolom Date dalam format yang benar)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 3. Simpan ke SQLite
    conn = sqlite3.connect('kebun_sawit.db')
    df.to_sql('transaksi_panen', conn, if_exists='append', index=False)
    conn.close()
    
    print(f"✅ Berhasil! {len(df)} data telah masuk ke database.")
except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")