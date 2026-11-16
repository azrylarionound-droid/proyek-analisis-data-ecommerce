"""Dashboard Streamlit – Analisis E-Commerce Public Dataset (Olist Brazil).

Jalankan dari folder proyek:  streamlit run dashboard/dashboard.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Olist E-Commerce Dashboard", page_icon="🛒", layout="wide")

# ----------------------------------------------------------------- gaya visual
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#c9c8c2"
TEXT, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
RAMP = ["#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#104281"]
plt.rcParams.update({
    "axes.axisbelow": True,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "axes.titlecolor": TEXT,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 10, "legend.frameon": False,
})


def fmt_brl(x, pos=None):
    if abs(x) >= 1e6:
        return f"R$ {x / 1e6:,.1f} jt"
    if abs(x) >= 1e3:
        return f"R$ {x / 1e3:,.0f} rb"
    return f"R$ {x:,.0f}"


def hbar(ax, labels, values, highlight_n=3, fmt=lambda v: f"{v:,.0f}"):
    """Bar horizontal terurut; n teratas disorot biru, sisanya abu-abu."""
    labels, values = list(labels)[::-1], list(values)[::-1]
    n = len(values)
    ax.barh(labels, values, color=[BLUE if i >= n - highlight_n else GRAY for i in range(n)], height=0.68)
    for i, v in enumerate(values):
        ax.text(v + max(values) * 0.01, i, fmt(v), va="center", fontsize=9, color=TEXT)
    ax.set_xlim(0, max(values) * 1.25)
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)


# ----------------------------------------------------------------- data
DATA_PATH = Path(__file__).parent / "main_data.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                                             "order_estimated_delivery_date"])
    df["is_late"] = df.is_late.astype(bool)
    df["category"] = df.product_category_name_english.str.replace("_", " ")
    return df


main_df = load_data()
min_date = main_df.order_purchase_timestamp.min().date()
max_date = main_df.order_purchase_timestamp.max().date()

# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🛒 Olist E-Commerce")
    st.caption("Pesanan *delivered*, Januari 2017 – Agustus 2018")
    date_range = st.date_input("Rentang tanggal pembelian", value=(min_date, max_date),
                               min_value=min_date, max_value=max_date)
    states = sorted(main_df.customer_state.unique())
    sel_states = st.multiselect("State pelanggan", states, default=[],
                                placeholder="Semua state")
    st.divider()
    st.caption("Sumber data: Olist Brazilian E-Commerce Public Dataset")

if not isinstance(date_range, (list, tuple)) or len(date_range) != 2:
    st.info("Pilih tanggal awal dan akhir pada sidebar.")
    st.stop()
start_date, end_date = date_range

mask = (main_df.order_purchase_timestamp.dt.date >= start_date) & \
       (main_df.order_purchase_timestamp.dt.date <= end_date)
if sel_states:
    mask &= main_df.customer_state.isin(sel_states)
items_df = main_df[mask]
orders_df = items_df.drop_duplicates("order_id")   # satu baris per pesanan

if orders_df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

# ----------------------------------------------------------------- header & KPI
st.title("Dashboard Analisis E-Commerce Olist")
st.caption(f"Periode {start_date:%d %b %Y} – {end_date:%d %b %Y}"
           + (f" · State: {', '.join(sel_states)}" if sel_states else " · Semua state"))

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total pesanan", f"{orders_df.order_id.nunique():,}")
k2.metric("Total revenue", fmt_brl(orders_df.payment_value.sum()))
k3.metric("Rata-rata nilai pesanan", f"R$ {orders_df.payment_value.mean():,.2f}")
k4.metric("Rata-rata review", f"{orders_df.review_score.mean():.2f} / 5")
k5.metric("Pesanan terlambat", f"{orders_df.is_late.mean():.1%}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Tren Penjualan", "🏷️ Kategori Produk", "🚚 Pengiriman & Review",
                                        "👥 RFM & Segmentasi", "🗺️ Geospasial"])

# ----------------------------------------------------------------- tab 1
with tab1:
    st.subheader("Bagaimana tren pesanan dan revenue bulanan?")
    monthly = orders_df.set_index("order_purchase_timestamp").resample("MS").agg(
        {"order_id": "nunique", "payment_value": "sum"}).rename(
        columns={"order_id": "orders", "payment_value": "revenue"})
    c1, c2 = st.columns(2)
    for col, (field, title, fmt) in zip(
            (c1, c2), [("orders", "Jumlah pesanan per bulan", lambda v, p: f"{v:,.0f}"),
                       ("revenue", "Revenue per bulan", fmt_brl)]):
        fig, ax = plt.subplots(figsize=(7, 3.6))
        ax.plot(monthly.index, monthly[field], color=BLUE, linewidth=2, marker="o", markersize=4)
        peak = monthly[field].idxmax()
        ax.scatter(peak, monthly[field].max(), s=80, color=ORANGE, zorder=3, edgecolor="white", linewidth=2)
        ax.annotate(f"Puncak {peak:%b %Y}: {fmt(monthly[field].max(), None)}", (peak, monthly[field].max()),
                    xytext=(0, 9), textcoords="offset points", ha="center", fontsize=8, fontweight="bold")
        ax.set_ylim(0, monthly[field].max() * 1.2)
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt))
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b\n%Y"))
        ax.set_title(title)
        col.pyplot(fig)
        plt.close(fig)

    years = orders_df.order_purchase_timestamp.dt.year
    if {2017, 2018}.issubset(set(years)):
        ja = orders_df[orders_df.order_purchase_timestamp.dt.month <= 8]
        cmp = ja.groupby([ja.order_purchase_timestamp.dt.month, ja.order_purchase_timestamp.dt.year]) \
            .payment_value.sum().unstack().reindex(columns=[2017, 2018]).fillna(0)
        if cmp[2017].sum() > 0:
            growth = cmp[2018].sum() / cmp[2017].sum() - 1
            fig, ax = plt.subplots(figsize=(12, 3.6))
            x = np.arange(len(cmp)); w = 0.38
            ax.bar(x - w / 2 - 0.01, cmp[2017], w, color=GRAY, label="2017")
            ax.bar(x + w / 2 + 0.01, cmp[2018], w, color=BLUE, label="2018")
            month_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu"]
            ax.set_xticks(x, [month_names[m - 1] for m in cmp.index])
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_brl))
            ax.set_ylim(0, cmp.values.max() * 1.18)
            ax.legend(loc="upper left", ncols=2)
            ax.set_title(f"Revenue Jan–Agu: 2018 vs 2017 ({growth:+.0%})")
            st.pyplot(fig)
            plt.close(fig)
    st.info("Puncak terjadi pada November 2017 (Black Friday). Revenue Jan–Agu 2018 naik ±143% dibanding "
            "periode yang sama 2017, tetapi pertumbuhan bulanan sepanjang 2018 cenderung datar.")

# ----------------------------------------------------------------- tab 2
with tab2:
    st.subheader("Kategori produk apa yang menyumbang revenue terbesar?")
    top_n = st.slider("Jumlah kategori ditampilkan", 5, 20, 10)
    cat = items_df.groupby("category").agg(revenue=("price", "sum"), items=("price", "count"),
                                           avg_price=("price", "mean")).sort_values("revenue", ascending=False)
    total = cat.revenue.sum()
    share = cat.head(top_n).revenue.sum() / total
    m1, m2 = st.columns(2)
    m1.metric(f"Kontribusi {top_n} kategori teratas", f"{share:.1%}")
    m2.metric("Jumlah kategori aktif", f"{len(cat)}")
    c1, c2 = st.columns(2)
    with c1:
        d = cat.head(top_n)
        fig, ax = plt.subplots(figsize=(7, 0.42 * top_n + 1))
        hbar(ax, d.index, d.revenue, fmt=lambda v: f"{fmt_brl(v)} ({v / total:.1%})")
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(fmt_brl))
        ax.set_title(f"Top {top_n} kategori berdasarkan revenue")
        st.pyplot(fig); plt.close(fig)
    with c2:
        d = cat.sort_values("items", ascending=False).head(top_n)
        fig, ax = plt.subplots(figsize=(7, 0.42 * top_n + 1))
        hbar(ax, d.index, d["items"], fmt=lambda v: f"{v:,.0f} item")
        ax.set_title(f"Top {top_n} kategori berdasarkan item terjual")
        st.pyplot(fig); plt.close(fig)
    st.info("Health & beauty, watches & gifts, dan bed bath table adalah 3 penyumbang revenue terbesar. "
            "Watches & gifts unggul karena harga rata-rata per item tinggi, bukan karena volume.")

# ----------------------------------------------------------------- tab 3
with tab3:
    st.subheader("Apakah keterlambatan pengiriman menurunkan review score?")
    grp = orders_df.groupby("is_late").agg(orders=("order_id", "nunique"), review=("review_score", "mean"))
    grp.index = grp.index.map({False: "Tepat waktu", True: "Terlambat"})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        fig, ax = plt.subplots(figsize=(5, 4))
        colors = [BLUE if i == "Tepat waktu" else ORANGE for i in grp.index]
        bars = ax.bar(grp.index, grp.review, color=colors, width=0.55)
        for b, v in zip(bars, grp.review):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"{v:.2f}", ha="center", fontweight="bold")
        ax.set_ylim(0, 5); ax.set_ylabel("Rata-rata review (1–5)")
        title = "Rata-rata review score"
        if len(grp) == 2:
            title += f" (selisih {grp.review.iloc[0] - grp.review.iloc[1]:.2f})"
        ax.set_title(title)
        st.pyplot(fig); plt.close(fig)
    with c2:
        bins = [0, 7, 14, 21, 30, np.inf]
        labels = ["≤ 7 hari", "8–14 hari", "15–21 hari", "22–30 hari", "> 30 hari"]
        dg = orders_df.assign(group=pd.cut(orders_df.delivery_days, bins=bins, labels=labels)) \
            .groupby("group", observed=False).review_score.apply(lambda s: (s <= 2).mean() * 100)
        fig, ax = plt.subplots(figsize=(7.5, 4))
        ax.bar(labels, dg.values, color=RAMP, width=0.65)
        for i, v in enumerate(dg.values):
            if not np.isnan(v):
                ax.text(i, v + 0.8, f"{v:.1f}%", ha="center", fontsize=9)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
        ax.set_title("% review 1–2 bintang per kelompok waktu kirim (binning)")
        st.pyplot(fig); plt.close(fig)

    state = orders_df.groupby("customer_state").agg(orders=("order_id", "nunique"),
                                                    late=("is_late", "mean")).sort_values("late", ascending=False)
    state["late"] *= 100
    min_orders = st.slider("Minimal jumlah pesanan per state", 0, 500, 30, step=10)
    state = state[state.orders >= min_orders]
    if not state.empty:
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.bar(state.index, state.late, color=[ORANGE if i < 5 else GRAY for i in range(len(state))], width=0.7)
        nat = orders_df.is_late.mean() * 100
        ax.axhline(nat, color=MUTED, linewidth=1)
        ax.text(len(state) - 0.5, nat + 0.4, f"Rata-rata {nat:.1f}%", ha="right", color=MUTED, fontsize=9)
        for i, v in enumerate(state.late.head(5)):
            ax.text(i, v + 0.4, f"{v:.0f}%", ha="center", fontsize=8)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
        ax.set_title("% pesanan terlambat per state (oranye = 5 tertinggi)")
        st.pyplot(fig); plt.close(fig)
    st.info("Pesanan terlambat rata-rata mendapat review ±2 poin lebih rendah. State di timur laut "
            "(AL, MA, SE, PI, CE) memiliki tingkat keterlambatan tertinggi.")

# ----------------------------------------------------------------- tab 4
with tab4:
    st.subheader("Siapa pelanggan terbaik? (RFM Analysis)")
    ref_date = orders_df.order_purchase_timestamp.max().normalize() + pd.Timedelta(days=1)
    rfm = orders_df.groupby("customer_unique_id").agg(
        last=("order_purchase_timestamp", "max"), frequency=("order_id", "nunique"),
        monetary=("payment_value", "sum")).reset_index()
    rfm["recency"] = (ref_date - rfm["last"].dt.normalize()).dt.days

    r1, r2, r3 = st.columns(3)
    r1.metric("Rata-rata recency", f"{rfm.recency.mean():.0f} hari")
    r2.metric("Rata-rata frequency", f"{rfm.frequency.mean():.2f} pesanan")
    r3.metric("Rata-rata monetary", f"R$ {rfm.monetary.mean():,.2f}")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, (col, asc, title) in zip(axes, [("recency", True, "Recency terkecil (hari)"),
                                            ("frequency", False, "Frequency terbanyak"),
                                            ("monetary", False, "Monetary terbesar (BRL)")]):
        d = rfm.sort_values(col, ascending=asc).head(5)
        ax.bar(d.customer_unique_id.str[:8] + "…", d[col], color=BLUE, width=0.6)
        for i, v in enumerate(d[col]):
            ax.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
        ax.set_title(title); ax.tick_params(axis="x", rotation=35)
    st.pyplot(fig); plt.close(fig)

    if len(rfm) >= 5:
        rfm["R"] = pd.qcut(rfm.recency.rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
        rfm["F"] = pd.cut(rfm.frequency, [0, 1, 2, np.inf], labels=[1, 3, 5]).astype(int)
        rfm["M"] = pd.qcut(rfm.monetary.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
        names = ["Champions", "Loyal", "Big Spender Baru", "Pelanggan Baru", "Perlu Perhatian",
                 "Berisiko (High Value)"]
        rfm["segment"] = np.select([
            (rfm.R >= 4) & (rfm.F >= 3), rfm.F >= 3, (rfm.R >= 4) & (rfm.M >= 4),
            rfm.R >= 4, rfm.R == 3, rfm.M >= 4], names, default="Hibernasi")
        order = names + ["Hibernasi"]
        seg = rfm.groupby("segment").agg(customers=("customer_unique_id", "count"),
                                         revenue=("monetary", "sum")).reindex(order).fillna(0)
        seg["cust_%"] = seg.customers / seg.customers.sum() * 100
        seg["rev_%"] = seg.revenue / seg.revenue.sum() * 100

        fig, axes = plt.subplots(1, 2, figsize=(14, 4.2), sharey=True)
        y = np.arange(len(seg))[::-1]
        hl = ["Big Spender Baru", "Berisiko (High Value)"]
        cols = [BLUE if s in hl else GRAY for s in seg.index]
        for ax, col, title in zip(axes, ["cust_%", "rev_%"], ["Porsi pelanggan", "Porsi revenue"]):
            ax.barh(y, seg[col], color=cols, height=0.65)
            for yi, v in zip(y, seg[col]):
                ax.text(v + 0.4, yi, f"{v:.1f}%", va="center", fontsize=9)
            ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
            ax.grid(axis="x", color=GRID); ax.grid(axis="y", visible=False)
            ax.set_title(title)
        axes[0].set_yticks(y, seg.index)
        st.pyplot(fig); plt.close(fig)
        with st.expander("Aturan segmentasi (manual grouping)"):
            st.markdown("""
- **Skor**: R & M = kuintil (5 terbaik); F = 1 pesanan → 1, 2 pesanan → 3, ≥3 pesanan → 5
- **Champions**: R ≥ 4 & F ≥ 3 · **Loyal**: F ≥ 3
- **Big Spender Baru**: R ≥ 4 & M ≥ 4 · **Pelanggan Baru**: R ≥ 4
- **Perlu Perhatian**: R = 3 · **Berisiko (High Value)**: R ≤ 2 & M ≥ 4 · **Hibernasi**: sisanya
""")
            st.dataframe(seg.style.format({"customers": "{:,.0f}", "revenue": "R$ {:,.0f}",
                                           "cust_%": "{:.1f}%", "rev_%": "{:.1f}%"}))

# ----------------------------------------------------------------- tab 5
with tab5:
    st.subheader("Di mana pelanggan berada dan wilayah mana yang sering terlambat?")
    geo = orders_df.dropna(subset=["lat", "lng"])
    sample = geo.sample(min(len(geo), 20000), random_state=42)
    sample = sample.assign(color=np.where(sample.is_late, "#eb6834cc", "#2a78d655"))
    st.map(sample, latitude="lat", longitude="lng", color="color", size=2500)
    st.caption(f"Sampel {len(sample):,} pesanan. Biru = tepat waktu, oranye = terlambat.")

    by_state = orders_df.groupby("customer_state").agg(
        pesanan=("order_id", "nunique"), revenue=("payment_value", "sum"),
        terlambat=("is_late", "mean"), review=("review_score", "mean")).sort_values("revenue", ascending=False)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        d = by_state.head(10)
        fig, ax = plt.subplots(figsize=(7, 4.6))
        hbar(ax, d.index, d.revenue, fmt=lambda v: f"{fmt_brl(v)} ({v / by_state.revenue.sum():.0%})")
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(fmt_brl))
        ax.set_title("Top 10 state berdasarkan revenue")
        st.pyplot(fig); plt.close(fig)
    with c2:
        st.dataframe(by_state.style.format({"pesanan": "{:,.0f}", "revenue": "R$ {:,.0f}",
                                            "terlambat": "{:.1%}", "review": "{:.2f}"}), height=420)

st.caption("Proyek Analisis Data · Dicoding · Data: Olist Brazilian E-Commerce Public Dataset")
