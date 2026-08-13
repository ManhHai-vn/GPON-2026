import streamlit as st
import pandas as pd

# 1. Giả sử df đã được load từ Google Sheets
# df = load_data_from_sheets() 

st.title("📊 Bảng Điều Khiển Tiến Độ Thi Công")

# --- Tính toán chỉ số tiến độ ---
total_tram = len(df)
# Giả sử kéo cáp = 1 là đã xong
completed_keo_cap = df[df['Kéo cáp'] == 1]['Tổng hộ dân/node nhánh'].sum()
completed_han_noi = df[df['Hàn nối'] == 1]['Tổng hộ dân/node nhánh'].sum()
total_ho_dan = df['Tổng hộ dân/node nhánh'].sum()

# --- Hiển thị Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Tổng số trạm", total_tram)
col2.metric("Tiến độ Kéo cáp", f"{int(completed_keo_cap/total_ho_dan*100)}%", f"{int(completed_keo_cap)}/{int(total_ho_dan)} hộ")
col3.metric("Tiến độ Hàn nối", f"{int(completed_han_noi/total_ho_dan*100)}%", f"{int(completed_han_noi)}/{int(total_ho_dan)} hộ")

# --- Biểu đồ trạng thái ---
st.subheader("Trạng thái triển khai")
chart_data = pd.DataFrame({
    'Trạng thái': ['Chưa Kéo cáp', 'Đã Kéo cáp', 'Chưa Hàn nối', 'Đã Hàn nối'],
    'Số lượng': [
        total_tram - df['Kéo cáp'].sum(), 
        df['Kéo cáp'].sum(),
        total_tram - df['Hàn nối'].sum(),
        df['Hàn nối'].sum()
    ]
})

st.bar_chart(chart_data.set_index('Trạng thái'))

# --- Bảng chi tiết ---
st.subheader("Chi tiết tiến độ theo trạm")
st.dataframe(df[['Trạm băng rộng', 'Đối tác', 'Kéo cáp', 'Hàn nối']], use_container_width=True)
