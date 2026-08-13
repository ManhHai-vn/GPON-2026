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

# ⚠️ Nhớ kiểm tra đúng đường link Web App Apps Script của bạn
WEB_APP_URL = (
    "https://script.google.com/macros/s/THAY_LINK_WEB_APP_CUA_BAN_VAO_DAY/exec"
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1VPbF7bLk6JF97kJEGw-TW1JEheUf4etfDO5bLsphyGs/edit#gid=0"

USERS = {
    "admin": {
        "pass": "admin123",
        "role": "admin",
        "name": "Quản Trị Viên (Admin)",
    },
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
                st.success("Đăng nhập thành công!")
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
col_diachi = get_col(df_raw, ["địa chỉ", "dịa chỉ", "địa bàn"])
col_doitac = get_col(df_raw, ["đối tác", "đơn vị"])
col_hodan = get_col(df_raw, ["tổng hộ dân", "hộ dân"])
col_cong = get_col(df_raw, ["tổng số cổng", "số cổng"])

if user["role"] == "admin":
    df = df_raw.copy()
else:
    if col_doitac:
        df = df_raw[
            df_raw[col_doitac].str.contains(user["role"], case=False, na=False)
        ].copy()
    else:
        df = df_raw.copy()

# TẠO DANH SÁCH TRẠM DÙNG CHO SỔ XUỐNG (DROPDOWN)
tram_list = []
if col_tram:
    tram_list = [
        str(t).strip()
        for t in df[col_tram].dropna().unique().tolist()
        if str(t).strip() != ""
    ]

# TẠO CÁC TAB CHỨC NĂNG (ĐỔI TÊN TAB THEO YÊU CẦU)
tab1, tab2, tab3 = st.tabs([
    "📈 Bảng Điều Khiển Tiến Độ",
    "🏗️ 1. Báo Cáo Thi Công",
    "📅 2. Kế Hoạch Thi Công",
])

# ==========================================
# TAB 1: TIẾN ĐỘ TỔNG QUAN
# ==========================================
with tab1:
    st.subheader(
        f"📌 Tổng quan dữ liệu ({'Toàn bộ' if user['role']=='admin' else user['role']})"
    )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        dia_ban_list = (
            df[col_diachi].dropna().unique().tolist() if col_diachi else []
        )
        selected_diaban = st.multiselect("Lọc theo Địa chỉ:", options=dia_ban_list)
    with col_f2:
        doitac_list = (
            df[col_doitac].dropna().unique().tolist() if col_doitac else []
        )
        selected_doitac = st.multiselect(
            "Lọc theo Đối tác:",
            options=doitac_list,
            disabled=(user["role"] != "admin"),
        )

    df_filtered = df.copy()
    if selected_diaban and col_diachi:
        df_filtered = df_filtered[df_filtered[col_diachi].isin(selected_diaban)]
    if selected_doitac and col_doitac and user["role"] == "admin":
        df_filtered = df_filtered[df_filtered[col_doitac].isin(selected_doitac)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Số trạm quản lý", len(df_filtered))
    if col_hodan:
        c2.metric(
            "Tổng số hộ dân",
            f"{pd.to_numeric(df_filtered[col_hodan], errors='coerce').sum():,.0f}",
        )
    if col_cong:
        c3.metric(
            "Tổng số cổng",
            f"{pd.to_numeric(df_filtered[col_cong], errors='coerce').sum():,.0f}",
        )

    st.markdown("---")
    st.subheader("📋 Danh sách các trạm thi công")
    st.dataframe(df_filtered, use_container_width=True)

# ==========================================
# TAB 2: BẢNG 1 - BÁO CÁO THI CÔNG
# ==========================================
with tab2:
    st.subheader("🏗️ Báo cáo sản lượng thi công thực tế")

    with st.form("form_bao_cao_thi_cong", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            ngay_baocao = st.date_input(
                "Ngày thực hiện (Ngay):", datetime.now(), key="tc_ngay"
            )
            selected_tram = st.selectbox(
                "Chọn Trạm thi công (Tram):",
                options=tram_list,
                key="tc_tram",
            )
            doi_tao = st.text_input(
                "Đơn vị (Doi_Tao):", value=user["name"], disabled=True
            )

        with col2:
            da_keo_cap = st.number_input(
                "Khối lượng đã kéo cáp - mét (Da keo cap):",
                min_value=0,
                step=10,
                key="tc_keo",
            )
            so_tu_han = st.number_input(
                "Số tủ đã hàn nối (so tu han noi):",
                min_value=0,
                step=1,
                key="tc_han",
            )
            ghi_chu = st.text_area(
                "Ghi chú (Ghi chú):",
                placeholder="Nhập vướng mắc, khó khăn nếu có...",
                key="tc_ghichu",
            )

        btn_submit_tc = st.form_submit_button("🚀 Gửi Báo Cáo Thi Công")

        if btn_submit_tc:
            if not selected_tram:
                st.warning("Vui lòng chọn Trạm thi công!")
            else:
                payload = {
                    "action": "bao_cao_thi_cong",
                    "Ngay": str(ngay_baocao),
                    "Tram": selected_tram,
                    "Doi_Tao": user["role"],
                    "Da_keo_cap": da_keo_cap,
                    "so_tu_han_noi": so_tu_han,
                    "Ghi_chu": ghi_chu,
                }
                try:
                    res = requests.post(WEB_APP_URL, json=payload)
                    if res.status_code == 200:
                        st.success(
                            "✅ Đã lưu Báo cáo Thi công vào Google Sheets (tab Baocao_Tiendo) thành công!"
                        )
                        st.cache_data.clear()
                    else:
                        st.error(f"Lỗi kết nối Web App: {res.status_code}")
                except Exception as ex:
                    st.error(f"Lỗi gửi dữ liệu: {ex}")

# ==========================================
# TAB 3: BẢNG 2 - KẾ HOẠCH THI CÔNG (MẶC ĐỊNH NGÀY N+1)
# ==========================================
with tab3:
    st.subheader("📅 Báo cáo kế hoạch thi công")

    with st.form("form_ke_hoach_ngay", clear_on_submit=True):
        col1, col2 = st.columns(2)

        # Tính toán Ngày N+1 (mặc định là ngày mai)
        ngay_mai = datetime.now() + timedelta(days=1)

        with col1:
            ngay_kh = st.date_input(
                "Ngày kế hoạch (Ngay):", value=ngay_mai, key="kh_ngay"
            )
            so_doi = st.number_input(
                "Số lượng đội thi công (Số đội):",
                min_value=1,
                step=1,
                key="kh_sodoi",
            )
            ten_doi = st.text_input(
                "Tên đội thi công (Tên đội):",
                placeholder="Ví dụ: Đội 1 - Xuân Long",
                key="kh_tendoi",
            )

        with col2:
            selected_tram_keo = st.multiselect(
                "Trạm dự kiến kéo cáp (Trạm kéo):",
                options=tram_list,
                placeholder="Chọn trạm kéo cáp...",
                key="kh_tramkeo",
            )
            selected_tram_han = st.multiselect(
                "Trạm dự kiến hàn nối (Trạm hàn):",
                options=tram_list,
                placeholder="Chọn trạm hàn nối...",
                key="kh_tramhan",
            )
            ke_hoach_ngay = st.text_area(
                "Nội dung kế hoạch chi tiết (Ke hoach ngay):",
                placeholder="Ví dụ: Đội 1 triển khai kéo 300m cáp...",
                key="kh_noidung",
            )

        btn_submit_kh = st.form_submit_button("🚀 Gửi Báo Cáo Kế Hoạch")

        if btn_submit_kh:
            str_tram_keo = ", ".join(selected_tram_keo)
            str_tram_han = ", ".join(selected_tram_han)

            payload = {
                "action": "ke_hoach_ngay",
                "Ngay": str(ngay_kh),
                "Doi_Tao": user["role"],
                "So_doi": so_doi,
                "Ten_doi": ten_doi,
                "Tram_keo": str_tram_keo,
                "Tram_han": str_tram_han,
                "Ke_hoach_ngay": ke_hoach_ngay,
            }
            try:
                res = requests.post(WEB_APP_URL, json=payload)
                if res.status_code == 200:
                    st.success(
                        "✅ Đã lưu Kế hoạch ngày vào Google Sheets (tab Kehoach_Ngay) thành công!"
                    )
                    st.cache_data.clear()
                else:
                    st.error(f"Lỗi kết nối Web App: {res.status_code}")
            except Exception as ex:
                st.error(f"Lỗi gửi dữ liệu: {ex}")
