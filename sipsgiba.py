import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import seaborn as sns
import plotly.express as px
import xlsxwriter
from io import BytesIO

# Konfigurasi halaman
st.set_page_config(
    page_title="SIPSGIBA",
    page_icon="logo.png",
    layout="wide"
)

# Fungsi koneksi database
def get_connection():
    try:
        connection = mysql.connector.connect(
            host="sql12.freesqldatabase.com",
            user="sql12794225",
            password="EjNsJCx7HG",
            database="sql12794225",
            port=3306
        )
        return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Fungsi login
def login_user(username, password):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        query = "SELECT * FROM user WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    return None

# Inisialisasi session state
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "df" not in st.session_state:
    st.session_state.df = None
if "df_clustered" not in st.session_state:
    st.session_state.df_clustered = None
if "selected_columns" not in st.session_state:
    st.session_state.selected_columns = None
if "num_clusters" not in st.session_state:
    st.session_state.num_clusters = 3
if "selected_data" not in st.session_state:
    st.session_state.selected_data = None
if "menu" not in st.session_state:
    st.session_state.menu = "menu"
if "df_normalized" not in st.session_state:
    st.session_state.df_normalized = None

def show_data(df):
    st.dataframe(df)

# Fungsi logout
def logout():
    st.session_state.is_logged_in = False
    st.session_state.user = None
    st.session_state.menu = "Beranda"

# Tampilkan hanya jika belum login
if not st.session_state.is_logged_in:
    st.markdown("<h2 style='text-align:center;'>SIPSGIBA</h2>", unsafe_allow_html=True)
    left, center, right = st.columns([13, 9, 13])
    with center:
        st.image("logo.png", width=250)
        st.markdown("<h4 style='text-align:center;'>Sistem Informasi Pemetaan Status Gizi Balita</h4>", unsafe_allow_html=True)

    left, center, right = st.columns([3, 7, 3])
    with center:
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="Masukkan Username Anda")
            password = st.text_input("Password", type="password", placeholder="Masukkan Password Anda")
            login_btn = st.form_submit_button("Login")

    if login_btn:
        if not username or not password:
            left, center, right = st.columns([3, 9, 3])
            with center:
                st.warning("Username dan Password tidak boleh kosong!")
        else:
            user = login_user(username, password)
            if user:
                st.session_state.is_logged_in = True
                st.session_state.user = username
                st.session_state.menu = "Beranda"
                st.rerun()  # Refresh halaman untuk menampilkan menu beranda
            else:
                left, center, right = st.columns([3, 9, 3])
            with center:
                st.error("Username atau password salah!")
else:
    # Sidebar: Navigasi (hanya tampil jika sudah login)
    with st.sidebar:
        col1, col2 = st.columns([1, 10])
    with col1:
        st.markdown("### ")  # Ukuran besar, sejajar
    with col2:
        left, center, right = st.columns([10, 9, 10])
        st.image("logo.png", width=180)
        st.write("<h1 style='text-align:center;'>SIPSGIBA</h1>", unsafe_allow_html=True)
        st.markdown("-----")
        menu = option_menu(
        menu_title=None,
        options=["Beranda", "Unggah File", "Perhitungan Clustering", "Diagram Hasil Clustering"],
        icons=["house", "cloud-upload", "calculator", "bar-chart"],
        default_index=["Beranda", "Unggah File", "Perhitungan Clustering", "Diagram Hasil Clustering"].index(st.session_state.menu),
        orientation="vertical",
        styles={
        "container": {"padding": "0!important", "background-color": "transparent"},
        "icon": {"color": "#000000", "font-size": "14px"},
        "nav-link": {"font-size": "14px", "color": "#262730", "text-align": "left", "margin": "0", "padding": "10px 4px", "font-family": "arial", "background-color": "transparent", "border-radius": "6px"},
        "nav-link-selected": {"background-color": "#FFFFFF", "color": "#000000", "font-weight": "600", "border": "1px solid #CCCCCC", "box-shadow": "0 1px 3px rgba(0, 0, 0, 0.1)", "border-radius": "6px", "padding": "10px 4px"},
    }
)
        st.markdown("-----")
        logout_col1, logout_col2, logout_col3 = st.columns([2, 3, 2])
    with logout_col2:
        if st.button("Logout"):
            logout()
            st.rerun()  # Refresh halaman untuk menampilkan form login

    # Konten Halaman Berdasarkan Menu
    if menu == "Beranda":
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.write("#### Selamat Datang di SIPSGIBA👋")
        st.write("""
        SIPSGIBA adalah singkatan dari Sistem Informasi Pemetaan Status Gizi Balita.
                 
        SIPSGIBA merupakan sebuah sistem informasi berbasis digital yang dirancang untuk mengelola, memantau, dan menganalisis data status gizi balita di suatu wilayah.  
       
        Tujuan utama dari sistem ini adalah membantu tenaga kesehatan dan pemerintah daerah dalam pengambilan keputusan yang lebih tepat sasaran terkait intervensi gizi, penyuluhan kesehatan, serta perencanaan program pencegahan dan penanggulangan masalah gizi.
        """)

    elif menu == "Unggah File":
        st.markdown("### Unggah File CSV")
        st.markdown("*Pastikan data yang diunggah lengkap, terutama pada kolom numerik seperti: Usia (bulan), Berat, Tinggi, ZS BB/U, ZS TB/U, dan ZS BB/TB.*")
    
        uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.df = df
                st.success("File berhasil diupload!")
                
                st.markdown("### Data Awal")
                with st.expander("Berikut ini adalah data dari hasil file yang telah diunggah", expanded=True):
                    show_data(df)
                
                numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
                exclude_cols = ["no", "nomor", "id"]
                numeric_cols = [col for col in numeric_cols if col.lower() not in exclude_cols]

                if not numeric_cols:
                    st.error("File CSV tidak mengandung kolom numerik.")
                else:
                    # Normalisasi data menggunakan decimal scaling
                    df_normalized = df.copy()
                    for col in numeric_cols:
                        if col.lower() in ["no", "nomor"]: 
                            continue
                        max_value = df_normalized[col].max()
                        if max_value != 0:  # Hindari pembagian dengan nol
                            df_normalized[col] = (df_normalized[col] / max_value).round(3)

                        st.session_state.df_normalized = df_normalized
                        st.session_state.selected_columns = numeric_cols
                    
                    st.markdown("### Data Normalisasi")
                    with st.expander("Berikut ini adalah data dari hasil normalisasi (proses mengubah nilai-nilai data ke skala yang sama)", expanded=True):
                        show_data(st.session_state.df_normalized)
                    
                    st.markdown("### Konfigurasi Clustering")
                    cols1, cols2 = st.columns(2)
                    
                    with cols1:
                        selected_columns = st.multiselect(
                            "Pilih kolom numerik untuk clustering",
                            numeric_cols,
                            placeholder="Silahkan pilih variabel untuk melanjutkan",
                            key="cols_selector"
                        )
                        st.session_state.selected_columns = selected_columns
                        
                    with cols2:
                        num_clusters = st.slider(
                            "Jumlah cluster (k)",
                            1, 10, 1,
                            key="cluster_slider"
                        )
                        st.session_state.num_clusters = num_clusters

                    # Jumlah data
                    jumlah_data = len(df_normalized)

                    # Hitung titik centroid otomatis berdasarkan rumus (n Data)/(Cluster_i + 1)
                    centroid_positions = []
                    for i in range(num_clusters):
                        posisi = int(jumlah_data / (i + 2))  # Karena rumus: n / (cluster_id + 1)
                        centroid_positions.append(posisi)

                    st.markdown("### Titik Awal Centroid")
                    st.info(f"Jumlah data: {df_normalized.shape[0]}")
                    st.info("Menentukan Titik Awal Centroid: **(n Data) / (n Cluster + 1)**")

                    for i, posisi in enumerate(centroid_positions):
                        st.markdown(f"- **C{i+1}** = {jumlah_data} / ({i+1}+1) = {jumlah_data // (i+2)} → Titik centroid diambil dari data ke-**{posisi}**" )

                    if selected_columns:
                        st.markdown("### Masukkan Titik Awal Centroid")
                        sample_df = df_normalized[selected_columns].copy()
                        st.info("Mohon kurangi 1 saat memilih baris data sebagai titik centroid (karena indeks dimulai dari 0).")
                        
                        centroid_cols = st.columns(num_clusters)
                        selected_data = []
                        
                        for i in range(num_clusters):
                            with centroid_cols[i]:
                                st.markdown(f"### Centroid {i+1}")
                                
                                row_idx = st.selectbox(
                                    f"Pilih baris untuk centroid awal {i+1}",
                                    options=sample_df.index,
                                    format_func=lambda x: f"Baris {x}",
                                    key=f"centroid_{i}"
                                )
                                
                                selected_values = df_normalized.loc[row_idx, selected_columns].values
                                st.write(dict(zip(selected_columns, selected_values)))
                                selected_data.append(selected_values)
                        
                        st.session_state.selected_data = selected_data
                        st.success("Konfigurasi disimpan!")

            except Exception as e:
                st.error(f"Error: {str(e)}")
        elif st.session_state.df is not None:
            show_data(st.session_state.df)
            st.info("File sebelumnya masih tersedia. Upload file baru jika ingin mengganti.")
    
    elif menu == "Perhitungan Clustering":
        st.markdown("### Proses Clustering dari Data Normalisasi")
        with st.expander("Klik tombol 'Jalankan Clustering' untuk mendapatkan hasil Clustering)", expanded=True):
        
                if st.session_state.df_normalized is not None:
                 show_data(st.session_state.df_normalized)
            
        try:
            if st.button("Jalankan Clustering"):
                df = st.session_state.df_normalized
                selected_columns = st.session_state.selected_columns
                selected_data = st.session_state.selected_data
                num_clusters = st.session_state.num_clusters

                # Konversi ke array
                X = df[selected_columns].values
                initial_centroids = np.array(selected_data)

                kmeans = KMeans(
                    n_clusters=num_clusters,
                    init=initial_centroids,
                    n_init=1
                )
                clusters = kmeans.fit_predict(X)

                df_clustered = df.copy()
                df_clustered['Cluster'] = clusters + 1
                st.session_state.df_clustered = df_clustered

                st.success("Clustering berhasil!")

                st.subheader("Hasil Clustering")
                with st.expander("Berikut ini adalah data dari hasil clustering", expanded=True):
                    st.dataframe(df_clustered.sort_values("Cluster"))

                st.subheader("Titik Akhir Centroid")
                with st.expander("Berikut ini adalah data dari titik akhir centroid", expanded=True):
                    cluster_stats = df_clustered.groupby("Cluster")[selected_columns].mean().round(3)
                    st.write(cluster_stats)

                if len(selected_columns) == 2:
                    st.subheader("Visualisasi Cluster")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.scatter(X[:, 0], X[:, 1], c=clusters, cmap='viridis', edgecolor='k', alpha=0.7)
                    ax.scatter(initial_centroids[:, 0], initial_centroids[:, 1], c='red', s=200, marker='*', label='Centroid Awal', edgecolor='k')
                    ax.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], c='blue', s=200, marker='X', label='Centroid Akhir', edgecolor='k')
                    ax.set_xlabel(selected_columns[0])
                    ax.set_ylabel(selected_columns[1])
                    ax.set_title("Visualisasi K-Means Clustering")
                    ax.legend()
                    ax.grid(True)
                    st.pyplot(fig)

        except Exception as e:
            st.error(f"Terjadi error: {str(e)}")
        else:
         if not (
        st.session_state.df_normalized is not None and
        st.session_state.selected_columns and
        st.session_state.selected_data
    ):
            st.warning("Silahkan unggah file, konfigurasi clustering, dan pilih centroid terlebih dahulu di menu **Unggah File**.")
            st.markdown(
    "<hr style='margin-top:50px; margin-bottom:10px;'>",
    unsafe_allow_html=True
)

    elif menu == "Diagram Hasil Clustering":
        st.markdown("### Hasil Clustering dengan K-Means dan PCA")
        
        if st.session_state.df_clustered is not None:
            show_data(st.session_state.df_clustered)
            
            df_clustered = st.session_state.df_clustered
            selected_columns = st.session_state.selected_columns
            X = df_clustered[selected_columns].values

            #Add a download button for the clustered DataFrame as Excel
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_clustered.to_excel(writer, sheet_name='Clustered Data', index=False)
            excel_buffer.seek(0)

            st.download_button(
                label="Unduh Data Excel",
                data=excel_buffer,
                file_name="data_clustered.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X)

            # Gabungkan PCA dan cluster ke dataframe
            df_pca = pd.DataFrame(data=X_pca, columns=['Dim1', 'Dim2'])
            df_pca['Cluster'] = df_clustered['Cluster']
            df_pca['Posyandu'] = df_clustered['Posyandu'] if 'Posyandu' in df_clustered.columns else "Tidak diketahui"
            df_pca['Cluster'] = df_pca['Cluster'].astype(str)

            # Gunakan plotly express untuk plot interaktif dengan Posyandu sebagai tooltip
            custom_color_map = {
                '1': '#43AA8B',
                '2': '#F9C74F'
                }
            custom_symbol_map = {
                '1': 'circle',   # Lingkaran
                '2': 'circle'     # Silang
                }
            fig = px.scatter(
                df_pca,
                x="Dim1",
                y="Dim2",
                color="Cluster",
                symbol="Cluster",
                hover_name="Posyandu",
                title="Visualisasi Clustering menggunakan PCA",
                color_discrete_map=custom_color_map,
                symbol_map=custom_symbol_map
                )
            fig.update_traces(marker=dict(size=12, line=dict(width=0.5, color='black')))
            # Tambahkan label persentase komponen utama
            fig.update_layout(
                xaxis_title=f"Dim1 ({pca.explained_variance_ratio_[0]*100:.1f}%)",
                yaxis_title=f"Dim2 ({pca.explained_variance_ratio_[1]*100:.1f}%)",
                legend_title_text='Cluster',
                width=800,
                height=800
            )

            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Keterangan Cluster")
            st.markdown("""
            - **Cluster 1**: Prioritas – Menunjukkan kelompok balita yang perlu mendapatkan penyuluhan.
            - **Cluster 2**: Tidak Prioritas – Menunjukkan kelompok balita dengan kondisi relatif baik.
            """)

        else:
            st.warning("Silahkan lakukan clustering terlebih dahulu di menu **Hasil Perhitungan Clustering**")
            st.markdown(
    "<hr style='margin-top:50px; margin-bottom:10px;'>",
    unsafe_allow_html=True
)
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    st.markdown("---")     
    st.markdown(
    "<p style='text-align:center; font-size: 14px;'>© 2025 Puskesmas Tanah Sareal</p>",
    unsafe_allow_html=True
)