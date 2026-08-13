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
        username = st.text_input("Tên đăng nhập (Username):").strip().lower()
        password = st.text_input("Mật khẩu (Password):", type="password")
        submit = st.form_submit_button("Đăng nhập")
        if submit:
            if username in USERS and USERS[username]["pass"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = USERS[username]
                st.rerun()
            else:
                st.error("Tài khoản hoặc mật khẩu không chính xác!")
    st.stop()

user = st.session_state["user_info"]
st.sidebar.title("👤 Thông tin tài khoản")
st.sidebar.write(f"**Người dùng:** {user['name']}")
st.sidebar.write(f"**Quyền hạn:** `{user['role']}`")
if st.sidebar.button("🚪 Đăng xuất"):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.title("📊 HỆ THỐNG QUẢN LÝ & BÁO CÁO TIẾN ĐỘ GPON 2026")
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    df_main = conn.read(spreadsheet=SHEET_URL, worksheet="0")
    df_main.columns = [str(c).strip() for c in df_main.columns]
    return df_main

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")
    st.stop()

def get_col(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower():
                return col
    return None

col_tram = get_col(df_raw, ["trạm băng rộng", "trạm bằng chữ", "trạm", "tram"])
col_diachi = get_col(df_raw, ["địa chỉ", "dịa chỉ", "địa bàn"])
col_doitac = get_col(df_raw, ["đối tác", "đơn vị"])
col_hodan = get_col(df_raw, ["tổng hộ dân", "hộ dân"])
col_cong = get_col(df_raw, ["tổng số cổng", "số cổng"])

if user["role"] == "admin":
    df = df_raw.copy()
else:
    df = df_raw[df_raw[col_doitac].str.contains(user["role"], case=False, na=False)].copy() if col_doitac else df_raw.copy()

tram_list = [str(t).strip() for t in df[col_tram].dropna().unique().tolist() if str(t).strip() != ""] if col_tram else []

tab1, tab2, tab3 = st.tabs(["📈 Thống Kê Tiến Độ", "🏗️ 1. Báo Cáo Thi Công", "📅 2. Kế Hoạch Thi Công"])

with tab1:
    st.markdown("### 🔍 Bộ lọc thông tin")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        dia_ban_list = df[col_diachi].dropna().unique().tolist() if col_diachi else []
        selected_diaban = st.multiselect("Lọc theo Địa chỉ:", options=dia_ban_list, label_visibility="collapsed")
    with col_f2:
        doitac_list = df[col_doitac].dropna().unique().tolist() if col_doitac else []
        selected_doitac = st.multiselect("Lọc theo Đối tác:", options=doitac_list, disabled=(user["role"] != "admin"), label_visibility="collapsed")

    df_filtered = df.copy()
    if selected_diaban and col_diachi:
        df_filtered = df_filtered[df_filtered[col_diachi].isin(selected_diaban)]
    if selected_doitac and col_doitac and user["role"] == "admin":
        df_filtered = df_filtered[df_filtered[col_doitac].isin(selected_doitac)]

    st.markdown("---")
    st.markdown(f"### 📊 Tổng quan tiến độ ({user['role']})")
    with st.container(border=True):
        m1, m2, m3 = st.columns(3)
        m1.metric("Số trạm quản lý", len(df_filtered))
        if col_hodan:
            m2.metric("Tổng số hộ dân", f"{pd.to_numeric(df_filtered[col_hodan], errors='coerce').sum():,.0f}")
        if col_cong:
            m3.metric("Tổng số cổng", f"{pd.to_numeric(df_filtered[col_cong], errors='coerce').sum():,.0f}")

    st.markdown("### 📋 Chi tiết danh mục trạm")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🏗️ Báo cáo sản lượng thi công thực tế")
    with st.form("form_bao_cao_thi_cong", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            ngay_baocao = st.date_input("Ngày thực hiện:", datetime.now())
            selected_tram = st.selectbox("Chọn Trạm thi công:", options=tram_list)
            doi_tao = st.text_input("Đơn vị:", value=user["name"], disabled=True)
        with col2:
            da_keo_cap = st.number_input("Khối lượng kéo cáp (mét):", min_value=0, step=10)
            so_tu_han = st.number_input("Số tủ hàn nối:", min_value=0, step=1)
            ghi_chu = st.text_area("Ghi chú:")
        if st.form_submit_button("🚀 Gửi Báo Cáo"):
            payload = {"action": "bao_cao_thi_cong", "Ngay": str(ngay_baocao), "Tram": selected_tram, "Doi_Tao": user["role"], "Da_keo_cap": da_keo_cap, "so_tu_han_noi": so_tu_han, "Ghi_chu": ghi_chu}
            requests.post(WEB_APP_URL, json=payload)
            st.success("Đã gửi!")
            st.cache_data.clear()

with tab3:
    st.subheader("📅 Báo cáo kế hoạch thi công")
    with st.form("form_ke_hoach", clear_on_submit=True):
        col1, col2 = st.columns(2)
        ngay_mai = datetime.now() + timedelta(days=1)
        with col1:
            ngay_kh = st.date_input("Ngày kế hoạch:", value=ngay_mai)
            so_doi = st.number_input("Số đội thi công:", min_value=1, step=1)
            ten_doi = st.text_input("Tên đội:")
        with col2:
            s_tram_keo = st.multiselect("Trạm kéo cáp:", options=tram_list)
            s_tram_han = st.multiselect("Trạm hàn nối:", options=tram_list)
            noidung = st.text_area("Nội dung chi tiết:")
        if st.form_submit_button("🚀 Gửi Kế Hoạch"):
            payload = {"action": "ke_hoach_ngay", "Ngay": str(ngay_kh), "Doi_Tao": user["role"], "So_doi": so_doi, "Ten_doi": ten_doi, "Tram_keo": ", ".join(s_tram_keo), "Tram_han": ", ".join(s_tram_han), "Ke_hoach_ngay": noidung}
            requests.post(WEB_APP_URL, json=payload)
            st.success("Đã gửi!")
            st.cache_data.clear()
