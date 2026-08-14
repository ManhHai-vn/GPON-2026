from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Quản Lý & Báo Cáo Tiến Độ GPON 2026", layout="wide")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwCeCROZKl1_t4iRB9aDdgXJW-43X-N8KUVWvsZiMA5j8bNRwhu5Okx4yavGG1FvydM2Q/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wUSpmt-4SyB-yyXmOn5Yox6nCRq7NuLHRpklvisJIuw/edit?usp=sharing"

USERS = {
    "admin": {"pass": "admin123", "role": "admin", "name": "Quản Trị Viên (Admin)"},
    "xuanlong": {"pass": "xl123", "role": "Xuân Long", "name": "Đối Tác Xuân Long"},
    "vcc": {"pass": "vcc123", "role": "VCC", "name": "Đối Tác VCC"},
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔒 ĐĂNG NHẬP HỆ THỐNG")
    user_in = st.text_input("Username").strip().lower()
    pass_in = st.text_input("Password", type="password")
    if st.button("Đăng nhập"):
        if user_in in USERS and USERS[user_in]["pass"] == pass_in:
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = USERS[user_in]
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu!")
    st.stop()

user = st.session_state["user_info"]
st.sidebar.title(f"👤 {user['name']}")
if st.sidebar.button("🚪 Đăng xuất"):
    st.session_state["logged_in"] = False
    st.rerun()

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    df = conn.read(spreadsheet=SHEET_URL, worksheet="0")
    df.columns = [str(c).strip() for c in df.columns]
    return df

df_raw = load_data()

def get_col(df, names):
    for n in names:
        for c in df.columns:
            if n.lower() in c.lower(): return c
    return None

col_tram = get_col(df_raw, ["trạm"])
col_doitac = get_col(df_raw, ["đối tác"])
col_keocap = get_col(df_raw, ["kéo cáp", "keo cap"])
col_laptu = get_col(df_raw, ["lắp tủ", "lap tu"])
cols_cap_giao = [c for c in df_raw.columns if "12fo" in c.lower() or "24fo" in c.lower()]
col_tu_giao = get_col(df_raw, ["tủ", "tu"])
col_hannoi = get_col(df_raw, ["hàn nối", "han noi"])

df = df_raw[df_raw[col_doitac].str.contains(user["role"], case=False, na=False)].copy() if user["role"] != "admin" and col_doitac else df_raw.copy()
tram_list = [str(t).strip() for t in df[col_tram].dropna().unique().tolist() if str(t).strip() != ""] if col_tram else []

tab1, tab2, tab3 = st.tabs(["📈 Thống Kê", "🏗️ Báo Cáo", "📅 Kế Hoạch"])

with tab1:
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown(f"### 📊 Tiến độ thi công - {user['name']}")
    with col_btn:
        if st.button("🔄 Làm mới", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # --- TẠO BÁO CÁO ZALO (CHỈ ADMIN) ---
    if user["role"] == "admin":
        with st.expander("📱 Tạo nhanh nội dung báo cáo Zalo", expanded=True):
            c1, c2 = st.columns([2, 1])
            with c1:
                ngay = st.date_input("Ngày báo cáo", datetime.now())
                so_doi = st.number_input("Số đội thi công", min_value=1, value=1)
                tram_tc = st.multiselect("Trạm đang thi công", tram_list)
                noi_dung = st.text_input("Kế hoạch tiếp theo", "tiếp tục triển khai các trạm chưa hoàn thành.")
            with c2:
                st.write("")
                st.write("")
                if st.button("✨ Tổng hợp báo cáo Zalo", use_container_width=True):
                    zalo_text = f"PHT VCC & Xuân Long báo cáo ngày {ngay.strftime('%d/%m')}:\n"
                    has_d = False
                    for _, row in df.iterrows():
                        t_n = row[col_tram] if col_tram and col_tram in row else "Trạm"
                        k = pd.to_numeric(row[col_keocap], errors='coerce') if col_keocap and col_keocap in row else 0
                        k = k if pd.notna(k) else 0
                        if k > 0:
                            has_d = True
                            zalo_text += f"- Trạm {t_n}: Kéo {int(k):,}m\n"
                    if not has_d:
                        zalo_text += "(Chưa có dữ liệu kéo cáp thực tế)\n"
                    zalo_text += f"\nKế hoạch ngày {(ngay+timedelta(1)).strftime('%d/%m')} ({so_doi} đội tại: {', '.join(tram_tc)}): {noi_dung}"
                    st.code(zalo_text)
        st.markdown("---")
    
    # --- THỐNG KÊ AN TOÀN (KHÔNG BAO GIỜ LỖI KEYERROR) ---
    tong_tram = len(df)
    tong_km = (pd.to_numeric(df[col_keocap], errors='coerce').sum() / 1000.0) if col_keocap and col_keocap in df.columns else 0.0
    tong_tu = pd.to_numeric(df[col_laptu], errors='coerce').sum() if col_laptu and col_laptu in df.columns else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng trạm", tong_tram)
    c2.metric("Tổng km cáp", f"{tong_km:.2f} km")
    c3.metric("Tổng tủ đã lắp", f"{int(tong_tu):,}")
    
    st.markdown("---")
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🏗️ Báo cáo sản lượng thi công")
    with st.form("bcao", clear_on_submit=True):
        tram = st.selectbox("Chọn Trạm", tram_list)
        keo = st.number_input("Kéo cáp (mét)", min_value=0, step=10)
        tu = st.number_input("Số tủ lắp", min_value=0, step=1)
        if st.form_submit_button("🚀 Gửi Báo Cáo"):
            payload = {"action": "bao_cao_thi_cong", "Tram": tram, "Doi_Tao": user["role"], "Da_keo_cap": keo, "So_tu_lap": tu}
            requests.post(WEB_APP_URL, json=payload)
            st.success("Đã gửi báo cáo thành công!")
            st.cache_data.clear()

with tab3:
    st.subheader("📅 Kế hoạch thi công")
    with st.form("khoach", clear_on_submit=True):
        nd = st.text_area("Chi tiết kế hoạch")
        if st.form_submit_button("🚀 Gửi Kế Hoạch"):
            payload = {"action": "ke_hoach_ngay", "Doi_Tao": user["role"], "Ke_hoach_ngay": nd}
            requests.post(WEB_APP_URL, json=payload)
            st.success("Đã gửi kế hoạch thành công!")
            st.cache_data.clear()
