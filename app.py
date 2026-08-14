from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Cấu hình trang
st.set_page_config(
    page_title="Quản Lý & Báo Cáo Tiến Độ GPON 2026",
    page_icon="🔒",
    layout="wide",
)

# Cấu hình kết nối
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwCeCROZKl1_t4iRB9aDdgXJW-43X-N8KUVWvsZiMA5j8bNRwhu5Okx4yavGG1FvydM2Q/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1wUSpmt-4SyB-yyXmOn5Yox6nCRq7NuLHRpklvisJIuw/edit?usp=sharing"

# Danh sách người dùng
USERS = {
    "admin": {"pass": "admin123", "role": "admin", "name": "Quản Trị Viên (Admin)"},
    "xuanlong": {"pass": "xl123", "role": "Xuân Long", "name": "Đối Tác Xuân Long"},
    "vcc": {"pass": "vcc123", "role": "VCC", "name": "Đối Tác VCC"},
}

# --- Xử lý đăng nhập ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None

if not st.session_state["logged_in"]:
    st.title("🔒 ĐĂNG NHẬP HỆ THỐNG GPON 2026")
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập:").strip().lower()
        password = st.text_input("Mật khẩu:", type="password")
        if st.form_submit_button("Đăng nhập"):
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
if st.sidebar.button("🚪 Đăng xuất"):
    st.session_state["logged_in"] = False
    st.rerun()

# --- Kết nối Google Sheets ---
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

# --- Hàm tiện ích lọc cột ---
def get_col(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower(): return col
    return None

def get_cols_by_keywords(df, keywords):
    return [col for col in df.columns if any(kw in col.lower() for kw in keywords)]

# Lấy các cột dữ liệu
col_tram = get_col(df_raw, ["trạm"])
col_doitac = get_col(df_raw, ["đối tác"])
col_keocap = get_col(df_raw, ["kéo cáp"])
col_laptu = get_col(df_raw, ["lắp tủ"])
col_tu_giao = get_col(df_raw, ["tủ"])
cols_cap_giao = get_cols_by_keywords(df_raw, ["12fo", "24fo"])
col_hannoi = get_col(df_raw, ["hàn nối"])

# Lọc dữ liệu theo quyền
df = df_raw[df_raw[col_doitac].str.contains(user["role"], case=False, na=False)].copy() if user["role"] != "admin" and col_doitac else df_raw.copy()
tram_list = [str(t).strip() for t in df[col_tram].dropna().unique().tolist() if str(t).strip() != ""] if col_tram else []

# --- Giao diện chính ---
tab1, tab2, tab3 = st.tabs(["📈 Thống Kê", "🏗️ Báo Cáo", "📅 Kế Hoạch"])

with tab1:
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown(f"### 📊 Tổng quan tiến độ ({user['role']})")
    with col_btn:
        if st.button("🔄 Làm mới"): st.cache_data.clear(); st.rerun()

    # Chỉ Admin mới thấy tính năng tạo báo cáo Zalo
    if user["role"] == "admin":
        with st.expander("📱 Tạo nhanh nội dung báo cáo Zalo", expanded=True):
            col_z1, col_z2 = st.columns([2, 1])
            with col_z1:
                ngay_zalo = st.date_input("Ngày báo cáo:", datetime.now())
                so_doi = st.number_input("Số đội:", min_value=1, value=1)
                tram_chon = st.multiselect("Trạm đang thi công:", options=tram_list)
                ke_hoach = st.text_input("Kế hoạch:", value="tiếp tục triển khai các trạm chưa hoàn thành.")
            with col_z2:
                if st.button("✨ Tổng hợp"):
                    zalo_text = f"PHT VCC & Xuân Long báo cáo ngày {ngay_zalo.strftime('%d/%m')}:\n"
                    for _, row in df.iterrows():
                        k_tt = pd.to_numeric(row[col_keocap], errors='coerce') or 0
                        l_tt = pd.to_numeric(row[col_laptu], errors='coerce') or 0
                        if k_tt > 0 or l_tt > 0:
                            zalo_text += f"- Trạm {row[col_tram]}: Kéo {int(k_tt):,}m | Tủ: {int(l_tt)}\n"
                    zalo_text += f"\nKế hoạch { (ngay_zalo+timedelta(1)).strftime('%d/%m') } ({so_doi} đội tại: {', '.join(tram_chon)}): {ke_hoach}"
                    st.code(zalo_text)
        st.markdown("---")

    # Hiển thị số liệu
    st.dataframe(df, use_container_width=True)

with tab2:
    with st.form("form_bao_cao", clear_on_submit=True):
        tram = st.selectbox("Chọn Trạm:", options=tram_list)
        keo = st.number_input("Kéo cáp (m):", min_value=0)
        tu = st.number_input("Số tủ:", min_value=0)
        if st.form_submit_button("Gửi Báo Cáo"):
            requests.post(WEB_APP_URL, json={"action": "bao_cao_thi_cong", "Tram": tram, "Doi_Tao": user["role"], "Da_keo_cap": keo, "So_tu_lap": tu})
            st.success("Đã gửi!")

with tab3:
    with st.form("form_ke_hoach", clear_on_submit=True):
        noidung = st.text_area("Kế hoạch chi tiết:")
        if st.form_submit_button("Gửi Kế Hoạch"):
            requests.post(WEB_APP_URL, json={"action": "ke_hoach_ngay", "Doi_Tao": user["role"], "Ke_hoach_ngay": noidung})
            st.success("Đã gửi!")
