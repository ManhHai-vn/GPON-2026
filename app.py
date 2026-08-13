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

col_km_giao = get_col(df_raw, ["kéo cáp", "keo cap", "km"])
col_tu_giao = get_col(df_raw, ["hàn nối", "han noi", "tủ"])

col_keocap = get_col(df_raw, ["kéo cáp", "keo cap"])
col_hannoi = get_col(df_raw, ["hàn nối", "han noi"])

if user["role"] == "admin":
    df = df_raw.copy()
else:
    df = df_raw[df_raw[col_doitac].str.contains(user["role"], case=False, na=False)].copy() if col_doitac else df_raw.copy()

tram_list = [str(t).strip() for t in df[col_tram].dropna().unique().tolist() if str(t).strip() != ""] if col_tram else []

tab1, tab2, tab3 = st.tabs(["📈 Thống Kê Tiến Độ", "🏗️ 1. Báo Cáo Thi Công", "📅 2. Kế Hoạch Thi Công"])

with tab1:
    if user["role"] == "admin":
        st.markdown("### 📊 Tổng quan tiến độ thi công - Hai Nhà Thầu (VCC & Xuân Long)")
        
        def generate_export_data():
            export_rows = []
            def process_contractor_export(contractor_title, keywords):
                if col_doitac:
                    mask = False
                    for kw in keywords:
                        mask = mask | df_raw[col_doitac].str.contains(kw, case=False, na=False)
                    df_sub = df_raw[mask].copy()
                else:
                    df_sub = pd.DataFrame()
                
                export_rows.append({"Tên Trạm": f"=== NHÀ THẦU: {contractor_title.upper()} ===", "Kéo cáp (mét)": "", "Hàn nối": ""})
                total_keo_val = 0
                total_han_val = 0
                
                for _, row in df_sub.iterrows():
                    t_name = row[col_tram] if col_tram else ""
                    k_val = pd.to_numeric(row[col_keocap], errors='coerce') if col_keocap else 0
                    h_val = pd.to_numeric(row[col_hannoi], errors='coerce') if col_hannoi else 0
                    
                    if pd.notna(k_val): total_keo_val += k_val
                    if pd.notna(h_val): total_han_val += h_val
                    
                    export_rows.append({
                        "Tên Trạm": t_name,
                        "Kéo cáp (mét)": k_val if pd.notna(k_val) else 0,
                        "Hàn nối": h_val if pd.notna(h_val) else 0
                    })
                
                export_rows.append({
                    "Tên Trạm": f"SUM ({contractor_title})",
                    "Kéo cáp (mét)": total_keo_val,
                    "Hàn nối": total_han_val
                })
                export_rows.append({"Tên Trạm": "", "Kéo cáp (mét)": "", "Hàn nối": ""})

            process_contractor_export("VCC", ["vcc"])
            process_contractor_export("Xuân Long", ["xuân", "xuan", "long"])
            
            df_export = pd.DataFrame(export_rows)
            return df_export.to_csv(index=False).encode('utf-8-sig')

        csv_data = generate_export_data()
        st.download_button(
            label="📥 Tải Xuống File Tổng Hợp (CSV)",
            data=csv_data,
            file_name=f"TongHop_TienDo_GPON_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
        st.markdown("---")

        # --- BẢNG TỔNG HỢP SỐ LIỆU ĐƯỢC GIAO (KM TRIỂN KHAI & TỦ HÀN NỐI) ---
        st.markdown("#### 📋 Bảng tổng hợp số liệu được giao theo nhà thầu")
        
        def get_contractor_summary_row(contractor_name, keywords):
            if col_doitac:
                mask = False
                for kw in keywords:
                    mask = mask | df_raw[col_doitac].str.contains(kw, case=False, na=False)
                df_sub = df_raw[mask].copy()
            else:
                df_sub = pd.DataFrame()
            
            val_km = pd.to_numeric(df_sub[col_km_giao], errors='coerce').sum() if col_km_giao else 0.0
            km_trien_khai = val_km / 1000.0 if val_km > 100 else val_km # Quy đổi sang km nếu đơn vị là mét
            so_tu = pd.to_numeric(df_sub[col_tu_giao], errors='coerce').sum() if col_tu_giao else 0
            
            return {
                "Nhà thầu": contractor_name,
                "KM triển khai": round(km_trien_khai, 2),
                "Tủ hàn nối": int(so_tu)
            }

        row_vcc = get_contractor_summary_row("VCC", ["vcc"])
        row_xl = get_contractor_summary_row("Xuân Long", ["xuân", "xuan", "long"])
        
        df_summary_table = pd.DataFrame([row_vcc, row_xl])
        
        total_row = {
            "Nhà thầu": "TỔNG CỘNG",
            "KM triển khai": round(df_summary_table["KM triển khai"].sum(), 2),
            "Tủ hàn nối": int(df_summary_table["Tủ hàn nối"].sum())
        }
        df_summary_table = pd.concat([df_summary_table, pd.DataFrame([total_row])], ignore_index=True)
        
        st.dataframe(df_summary_table, use_container_width=True, hide_index=True)
        st.markdown("---")

        col_vcc, col_xl = st.columns(2)

        def render_contractor_stats(contractor_name, keywords):
            st.markdown(f"#### 🏢 Nhà thầu: {contractor_name}")
            if col_doitac:
                mask = False
                for kw in keywords:
                    mask = mask | df_raw[col_doitac].str.contains(kw, case=False, na=False)
                df_sub = df_raw[mask].copy()
            else:
                df_sub = pd.DataFrame()

            if len(df_sub) > 0:
                tram_giao = len(df_sub)
                
                if col_keocap:
                    df_sub[col_keocap] = pd.to_numeric(df_sub[col_keocap], errors='coerce').fillna(0)
                    tram_tc = len(df_sub[df_sub[col_keocap] > 0])
                    tong_km = df_sub[col_keocap].sum() / 1000.0  
                else:
                    tram_tc = 0
                    tong_km = 0.0

                if col_hannoi:
                    df_sub[col_hannoi] = pd.to_numeric(df_sub[col_hannoi], errors='coerce').fillna(0)
                    tram_han = len(df_sub[df_sub[col_hannoi] > 0])
                else:
                    tram_han = 0

                with st.container(border=True):
                    st.metric("Trạm được giao", tram_giao)
                    st.metric("Trạm đã thi công", tram_tc)
                    st.metric("Trạm đã hàn", tram_han)
                    st.metric("Tổng số km đã kéo", f"{tong_km:,.2f} km")
            else:
                st.info(f"Chưa có dữ liệu cho {contractor_name}")

        with col_vcc:
            render_contractor_stats("VCC", ["vcc"])

        with col_xl:
            render_contractor_stats("Xuân Long", ["xuân", "xuan", "long"])

        st.markdown("---")
        st.markdown("### 📋 Danh sách chi tiết toàn bộ trạm")
        st.dataframe(df_raw, use_container_width=True, hide_index=True)

    else:
        st.markdown(f"### 📊 Tổng quan tiến độ ({user['role']})")
        with st.container(border=True):
            m1, m2, m3 = st.columns(3)
            m1.metric("Số trạm quản lý", len(df))
            if col_hodan:
                m2.metric("Tổng số hộ dân", f"{pd.to_numeric(df[col_hodan], errors='coerce').sum():,.0f}")
            if col_cong:
                m3.metric("Tổng số cổng", f"{pd.to_numeric(df[col_cong], errors='coerce').sum():,.0f}")

        if len(df) > 0:
            st.markdown("### 📑 Tổng hợp khối lượng thi công")
            total_tram = len(df)
            total_keo = pd.to_numeric(df[col_keocap], errors='coerce').sum() if col_keocap else 0
            total_han = pd.to_numeric(df[col_hannoi], errors='coerce').sum() if col_hannoi else 0
            
            df_summary = pd.DataFrame([{
                "Tổng số trạm được giao": total_tram,
                "Tổng thi công kéo cáp (mét)": f"{total_keo:,.1f}",
                "Tổng hàn nối": f"{total_han:,.0f}"
            }])
            st.dataframe(df_summary, use_container_width=True, hide_index=True)

        st.markdown("### 📋 Danh sách chi tiết các trạm")
        cols_hien_thi = [c for c in [col_tram, col_keocap, col_hannoi] if c]
        if cols_hien_thi:
            st.dataframe(df[cols_hien_thi], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

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
