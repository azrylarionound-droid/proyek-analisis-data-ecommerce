# Proyek Analisis Data: E-Commerce Public Dataset (Olist Brazil) ✨

Proyek ini menganalisis data pesanan marketplace Olist (Brasil) periode **Januari 2017 – Agustus 2018** untuk menjawab tiga pertanyaan bisnis:

1. Bagaimana tren pesanan dan revenue bulanan, dan berapa pertumbuhan revenue Jan–Agu 2018 dibanding 2017?
2. Kategori produk apa saja yang menjadi 10 besar penyumbang revenue, dan berapa kontribusinya?
3. Berapa selisih review score antara pesanan terlambat dan tepat waktu, dan state mana dengan keterlambatan tertinggi?

Analisis lanjutan yang dilakukan: **RFM Analysis**, **Geospatial Analysis** (folium), dan **Clustering dengan Manual Grouping & Binning**.

## Struktur Proyek

```
submission/
├── dashboard/
│   ├── dashboard.py          # aplikasi Streamlit
│   └── main_data.csv         # data bersih hasil notebook (dipakai dashboard)
├── data/                     # dataset mentah (9 file CSV)
├── Proyek_Analisis_Data.ipynb
├── README.md
├── requirements.txt
└── url.txt                   # tautan dashboard Streamlit Cloud
```

## Setup Environment - Anaconda

```
conda create --name main-ds python=3.11
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal

```
mkdir proyek_analisis_data
cd proyek_analisis_data
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Menjalankan Notebook

Buka `Proyek_Analisis_Data.ipynb` di Jupyter Notebook/JupyterLab/VS Code dari folder proyek (agar path `data/` terbaca), lalu jalankan **Run All**. Notebook juga akan membuat ulang `dashboard/main_data.csv`.

## Menjalankan Dashboard Streamlit

Dari folder proyek (`submission/`):

```
streamlit run dashboard/dashboard.py
```

Dashboard akan terbuka di `http://localhost:8501`. Gunakan sidebar untuk memfilter **rentang tanggal** dan **state pelanggan**. Tersedia lima tab: Tren Penjualan, Kategori Produk, Pengiriman & Review, RFM & Segmentasi, dan Geospasial.

## Dashboard Online

Tautan dashboard yang sudah di-deploy ada di `url.txt`.
