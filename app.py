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
    st.stop()

user = st.session_state["user_info"]
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    df = conn.read(spreadsheet=SHEET_URL, worksheet="0")
    df.columns = [str(c).strip() for c in df.columns]
    return df

df_raw = load_data()
# Các hàm lấy cột và lọc dữ liệu (giống bản gốc)
def get_col(df, names):
    for n in names:
        for c in df.columns:
            if n.lower() in c.lower(): return c
    return None

col_tram = get_col(df_raw, ["trạm"])
col_doitac = get_col(df_raw, ["đối tác"])
col_keocap = get_col(df_raw, ["kéo cáp"])
col_laptu = get_col(df_raw, ["lắp tủ"])

df = df_raw[df_raw[col_doitac].str.contains(user["role"], case=False, na=False)].copy() if user["role"] != "admin" else df_raw.copy()
tram_list = [str(t).strip() for t in df[col_tram].dropna().unique().tolist() if str(t).strip() != ""]

tab1, tab2, tab3 = st.tabs(["📈 Thống Kê", "🏗️ Báo Cáo", "📅 Kế Hoạch"])

with tab1:
    st.markdown(f"### 📊 Tiến độ thi công - {user['name']}")
    
    # --- PHẦN TẠO BÁO CÁO ZALO (CHỈ ADMIN THẤY) ---
    if user["role"] == "admin":
        with st.expander("📱 Tạo nhanh nội dung báo cáo Zalo", expanded=True):
            c1, c2 = st.columns(2)
            ngay = c1.date_input("Ngày báo cáo", datetime.now())
            so_doi = c1.number_input("Số đội thi công", 1)
            tram_tc = c1.multiselect("Trạm đang thi công", tram_list)
            noi_dung = c2.text_input("Kế hoạch", "tiếp tục triển khai các trạm chưa hoàn thành.")
            if c2.button("✨ Tổng hợp báo cáo"):
                zalo_text = f"PHT VCC & Xuân Long báo cáo ngày {ngay.strftime('%d/%m')}:\n"
                for _, row in df.iterrows():
                    k = pd.to_numeric(row[col_keocap], errors='coerce') or 0
                    if k > 0: zalo_text += f"- Trạm {row[col_tram]}: Kéo {int(k):,}m\n"
                zalo_text += f"\nKế hoạch ngày { (ngay+timedelta(1)).strftime('%d/%m') } ({so_doi} đội tại: {', '.join(tram_tc)}): {noi_dung}"
                st.code(zalo_text)
    
    # --- PHẦN THỐNG KÊ CHI TIẾT (KHÔI PHỤC ĐẦY ĐỦ) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng trạm", len(df))
    col2.metric("Tổng km cáp", f"{pd.to_numeric(df[col_keocap], errors='coerce').sum()/1000:.2f} km")
    col3.metric("Tổng tủ đã lắp", f"{pd.to_numeric(df[col_laptu], errors='coerce').sum():,.0f}")
    
    st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("🏗️ Gửi báo cáo sản lượng")
    with st.form("bcao", clear_on_submit=True):
        tram = st.selectbox("Chọn Trạm", tram_list)
        keo = st.number_input("Kéo cáp (mét)", 0)
        tu = st.number_input("Số tủ lắp", 0)
        if st.form_submit_button("🚀 Gửi"):
            requests.post(WEB_APP_URL, json={"action": "bao_cao_thi_cong", "Tram": tram, "Doi_Tao": user["role"], "Da_keo_cap": keo, "So_tu_lap": tu})
            st.success("Đã gửi thành công!")

with tab3:
    st.subheader("📅 Kế hoạch thi công")
    with st.form("khoach", clear_on_submit=True):
        nd = st.text_area("Chi tiết kế hoạch")
        if st.form_submit_button("🚀 Gửi"):
            requests.post(WEB_APP_URL, json={"action": "ke_hoach_ngay", "Doi_Tao": user["role"], "Ke_hoach_ngay": nd})
            st.success("Đã gửi!")
