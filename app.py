from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st
import io

st.set_page_config(
    page_title="Quản Lý & Báo Cáo Tiến Độ GPON 2026",
    page_icon="🔒",
    layout="wide",
)

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwCeCROZKl1_t4iRB9aDdgXJW-43X-N8KUVWvsZiMA5j8bNRwhu5Okx4yavGG1FvydM2Q/exec"
# ĐÃ CẬP NHẬT ĐÚNG ID TỪ LINK CỦA BẠN
SHEET_ID = "1wUSpmt-4SyB-yyXmOn5Yox6nCRq7NuLHRpklvisJIuw"

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

@st.cache_data(ttl=600)
def load_data():
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(csv_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Không thể tải dữ liệu (Mã lỗi: {response.status_code})")
    df_main = pd.read_csv(io.StringIO(response.text))
    df_main.columns = [str(c).strip() for c in df_main.columns]
    return df_main

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")
    st.stop()

# Khôi phục các hàm tìm cột thông minh
def get_col(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower(): return col
    return None

def get_cols_by_keywords(df, keywords):
    return [col for col in df.columns if any(kw in col.lower() for kw in keywords)]

col_tram = get_col(df_raw, ["trạm băng rộng", "trạm", "tram"])
col_doitac = get_col(df_raw, ["đối tác", "đơn vị"])
col_keocap = get_col(df_raw, ["kéo cáp", "keo cap"])
col_hannoi = get_col(df_raw, ["hàn nối", "han noi"])
col_tu_giao = get_col(df_raw, ["tủ", "tu"])
cols_cap_giao = get_cols_by_keywords(df_raw, ["12fo", "24fo"])

# Logic lọc nhà thầu
if user["role"] == "admin":
    df = df_raw.copy()
else:
    df = df_raw[df_raw[col_doitac].str.contains(user["role"], case=False, na=False)].copy() if col_doitac else df_raw.copy()

tram_list = [str(t).strip() for t in df[col_tram].dropna().unique().tolist() if str(t).strip() != ""] if col_tram else []

# Khôi phục các Tab
tab1, tab2, tab3 = st.tabs(["📈 Thống Kê Tiến Độ", "🏗️ 1. Báo Cáo Thi Công", "📅 2. Kế Hoạch Thi Công"])

with tab1:
    if st.button("🔄 Làm Mới Dữ Liệu"):
        st.cache_data.clear()
        st.rerun()
    st.dataframe(df, use_container_width=True)

with tab2:
    with st.form("bao_cao", clear_on_submit=True):
        tram = st.selectbox("Chọn Trạm:", options=tram_list)
        keo = st.number_input("Mét cáp:", 0)
        han = st.number_input("Số tủ hàn:", 0)
        if st.form_submit_button("🚀 Gửi Báo Cáo"):
            requests.post(WEB_APP_URL, json={"action": "bao_cao", "Tram": tram, "Met": keo, "Han": han, "Doi": user["name"]})
            st.success("Đã gửi!")

with tab3:
    st.write("Tính năng kế hoạch...")
