from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Quản Lý & Báo Cáo Tiến Độ GPON 2026",
    page_icon="🔒",
    layout="wide",
)

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwaTaqtylnHfBkgC0jJDiU8n1tVVTmILtC9sjdNebIGVBBat7Yji-0WRF1HvSwJTpl4iQ/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1VPbF7bLk6JF97kJEGw-TW1JEheUf4etfDO5bLsphyGs/edit#gid=0"

USERS = {
    "admin": {"pass": "admin123", "role": "admin", "name": "Quản Trị Viên (Admin)"},
    "xuanlong": {"pass": "xl123", "role": "Xuân Long", "name": "Đối Tác Xuân Long"},
    "vcc": {"pass": "vcc123", "role": "VCC", "name": "Đối Tác VCC"},
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None

if not st.session_state["logged_in"]:
    st.title("🔒 ĐĂNG NHẬP HỆ THỐNG GPON 2026")
    with st.form("login_form"):
        username = st.text_input("Username:").strip().lower()
        password = st.text_input("Password:", type="password")
        if st.form_submit_button("Đăng nhập"):
            if username in USERS and USERS[username]["pass"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = USERS[username]
                st.rerun()
            else:
                st.error("Sai thông tin!")
    st.stop()

user = st.session_state["user_info"]
st.sidebar.write(f"👤 **{user['name']}** | Quyền: `{user['role']}`")
if st.sidebar.button("🚪 Đăng xuất"):
    st.session_state["logged_in"] = False
    st.rerun()

st.title("📊 HỆ THỐNG QUẢN LÝ TIẾN ĐỘ GPON 2026")
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    df = conn.read(spreadsheet=SHEET_URL, worksheet="0")
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Lỗi tải dữ liệu: {e}")
    st.stop()

# Xử lý lọc dữ liệu theo đối tác
col_doitac = next((c for c in df_raw.columns if "đối tác" in c.lower() or "đơn vị" in c.lower()), None)
if user["role"] == "admin":
    df = df_raw.copy()
else:
    df = df_raw[df_raw[col_doitac].str.contains(user["role"], case=False, na=False)].copy() if col_doitac else df_raw.copy()

tab1, tab2, tab3 = st.tabs(["📈 Bảng Điều Khiển", "🏗️ Báo Cáo Thi Công", "📅 Kế Hoạch"])

with tab1:
    st.subheader(f"📌 Tổng quan ({user['role']})")
    df_filtered = df.copy()
    
    # Chỉ số tiến độ
    total_tram = len(df_filtered)
    c1, c2, c3 = st.columns(3)
    c1.metric("Số trạm quản lý", total_tram)
    
    col_hodan = next((c for c in df.columns if "hộ dân" in c.lower()), None)
    if col_hodan:
        c2.metric("Tổng hộ dân", f"{pd.to_numeric(df_filtered[col_hodan], errors='coerce').sum():,.0f}")
    
    col_cong = next((c for c in df.columns if "số cổng" in c.lower()), None)
    if col_cong:
        c3.metric("Tổng số cổng", f"{pd.to_numeric(df_filtered[col_cong], errors='coerce').sum():,.0f}")
        
    st.dataframe(df_filtered, use_container_width=True)

with tab2:
    st.subheader("🏗️ Báo cáo thi công")
    with st.form("form_tc", clear_on_submit=True):
        tram_col = next((c for c in df.columns if "trạm" in c.lower()), df.columns[0])
        s_tram = st.selectbox("Chọn trạm:", df[tram_col].unique())
        keo = st.number_input("Mét cáp đã kéo:", min_value=0)
        han = st.number_input("Số tủ đã hàn:", min_value=0)
        if st.form_submit_button("Gửi báo cáo"):
            payload = {"action": "bao_cao_thi_cong", "Tram": s_tram, "Doi_Tao": user["role"], "Da_keo_cap": keo, "so_tu_han_noi": han}
            requests.post(WEB_APP_URL, json=payload)
            st.success("Đã gửi!")

with tab3:
    st.subheader("📅 Kế hoạch thi công")
    # Form Kế hoạch tương tự như code cũ của bạn...
    st.info("Tab này dùng để gửi kế hoạch ngày mai.")
