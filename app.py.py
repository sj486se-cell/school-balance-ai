import streamlit as st
import pandas as pd
import pydeck as pdk

# 데이터 유지
if 'reports' not in st.session_state:
    st.session_state.reports = pd.DataFrame(columns=['lat', 'lon', 'type', 'desc'])

st.title("♿ SafePath: 배리어 프리 제보 시스템")

# 시연용 좌표 가이드 (심사위원에게 보여줄 내용)
st.info("💡 **시연 방법:** 아래 입력창에 원하는 위치의 좌표를 넣고 제보하면 지도에 즉시 반영됩니다. (예: 위도 37.3850, 경도 127.1235)")

with st.sidebar:
    st.subheader("제보 데이터 입력")
    # 좌표 입력창
    lat = st.number_input("위도 입력", value=37.3850, format="%.6f")
    lon = st.number_input("경도 입력", value=127.1235, format="%.6f")
    
    r_type = st.selectbox("유형", ["계단", "턱", "공사중"])
    desc = st.text_input("메모")
    
    if st.button("제보 등록"):
        new_row = pd.DataFrame({'lat': [lat], 'lon': [lon], 'type': [r_type], 'desc': [desc]})
        st.session_state.reports = pd.concat([st.session_state.reports, new_row], ignore_index=True)

# 지도 그리기
if not st.session_state.reports.empty:
    st.pydeck_chart(pdk.Deck(
        layers=[pdk.Layer("ScatterplotLayer", st.session_state.reports, get_position="[lon, lat]", get_color=[255,0,0], get_radius=20, pickable=True)],
        initial_view_state=pdk.ViewState(latitude=37.3850, longitude=127.1235, zoom=15),
        tooltip={"html": "<b>{type}</b>: {desc}"}
    ))
