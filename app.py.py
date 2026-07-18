import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. 페이지 설정
st.set_page_config(page_title="SafePath: 배리어 프리 지도", layout="wide")

# 2. 데이터 제보 세션 상태 (메모리 저장)
if 'reports' not in st.session_state:
    st.session_state.reports = pd.DataFrame(columns=['lat', 'lon', 'type', 'desc'])

# 3. 사이드바: 제보 및 필터
with st.sidebar:
    st.title("📍 배리어 프리 제보")
    with st.form("report_form"):
        st.write("불편한 곳을 공유해주세요!")
        lat = st.number_input("위도", value=37.3850)
        lon = st.number_input("경도", value=127.1235)
        r_type = st.selectbox("장애 유형", ["계단", "높은 턱", "공사중", "기타"])
        desc = st.text_input("상세 내용")
        if st.form_submit_button("제보하기"):
            new_data = pd.DataFrame({'lat': [lat], 'lon': [lon], 'type': [r_type], 'desc': [desc]})
            st.session_state.reports = pd.concat([st.session_state.reports, new_data], ignore_index=True)

# 4. 메인 화면
st.title("♿ SafePath: 배리어 프리 이동 지도")
st.write("휠체어와 유모차도 안심하고 다닐 수 있는 길을 찾습니다.")

# 지도 레이어 구성
layers = []
if not st.session_state.reports.empty:
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=st.session_state.reports,
        get_position="[lon, lat]",
        get_color="[255, 0, 0, 200]",
        get_radius=30,
        pickable=True,
    ))

st.pydeck_chart(pdk.Deck(
    layers=layers,
    initial_view_state=pdk.ViewState(latitude=37.3850, longitude=127.1235, zoom=14),
    tooltip={"html": "<b>유형:</b> {type}<br/><b>상세:</b> {desc}"}
))

# 5. 알고리즘 로직 (간략화)
st.subheader("💡 휠체어 맞춤형 경로 분석")
col1, col2 = st.columns(2)
with col1:
    st.info("기본 경로: 정자역 -> 수내역 (직선거리)")
with col2:
    if len(st.session_state.reports) > 0:
        st.error(f"알고리즘이 {len(st.session_state.reports)}개의 제보된 장애물을 피해 우회 경로를 생성합니다.")
    else:
        st.success("장애물 보고 없음: 최단 거리 주행 가능")
