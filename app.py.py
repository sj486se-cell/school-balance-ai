import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="SafePath: 배리어 프리 제보 지도", layout="wide")

# 1. 초기 데이터 (AI가 판단한 기본 위험 구간)
if 'reports' not in st.session_state:
    st.session_state.reports = pd.DataFrame([
        {'lat': 37.3850, 'lon': 127.1235, 'type': 'AI 경고', 'desc': '급경사로 예상되는 구간입니다.'},
        {'lat': 37.3820, 'lon': 127.1260, 'type': 'AI 경고', 'desc': '보도블록 파손 가능성이 높습니다.'}
    ])

# 2. 사이드바: 제보 폼
with st.sidebar:
    st.title("📍 위험 제보하기")
    st.write("지도를 클릭한 후 위치 정보와 메모를 남겨주세요.")
    
    # 클릭한 좌표를 받을 입력창 (사용자가 지도에서 클릭한 값을 여기에 넣음)
    click_lat = st.number_input("클릭한 위도", format="%.6f")
    click_lon = st.number_input("클릭한 경도", format="%.6f")
    
    with st.form("new_report"):
        r_type = st.selectbox("장애 유형", ["계단", "높은 턱", "공사중", "기타"])
        desc = st.text_input("상세 메모")
        if st.form_submit_button("제보 등록"):
            new_report = pd.DataFrame({'lat': [click_lat], 'lon': [click_lon], 'type': [r_type], 'desc': [desc]})
            st.session_state.reports = pd.concat([st.session_state.reports, new_report], ignore_index=True)

# 3. 메인 화면
st.title("♿ SafePath: 사용자 참여형 배리어 프리 지도")
st.write("지도 위를 클릭하여 위험 요소를 직접 제보하고, AI가 분석한 안전 경로를 확인하세요.")

# PyDeck 지도 시각화
view_state = pdk.ViewState(latitude=37.3850, longitude=127.1235, zoom=15)

# 툴팁 및 클릭 이벤트 정의
layer = pdk.Layer(
    "ScatterplotLayer",
    data=st.session_state.reports,
    get_position="[lon, lat]",
    get_color="type == 'AI 경고' ? [255, 165, 0, 200] : [255, 0, 0, 200]",
    get_radius=20,
    pickable=True,
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"html": "<b>유형:</b> {type}<br/><b>상세:</b> {desc}"},
    # 지도 클릭 시 좌표를 가져오는 설정 (streamlit의 기본 기능 활용)
    map_style="road"
))

st.info("💡 팁: 실제 시연 시에는 지도를 클릭하여 나오는 좌표값을 복사해서 위도/경도 입력창에 넣는 방식으로 사용자 참여를 보여주세요!")
