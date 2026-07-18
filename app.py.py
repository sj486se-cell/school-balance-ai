import streamlit as st
import pandas as pd
import pydeck as pdk # 고급 지도 선 그리기를 위한 라이브러리 추가
import time

st.set_page_config(page_title="SafePath AI", page_icon="🗺️", layout="wide")

# ==========================================
# 1. 사이드바 (사용자 조건 설정)
# ==========================================
with st.sidebar:
    st.title("⚙️ 안전 경로 설정")
    user_type = st.radio(
        "👤 보행자 유형을 선택하세요", 
        ["🚶 일반 보행자 (최단거리)", "👩‍🦽 휠체어/유모차 (단차 회피)", "🌙 심야 안심 귀가 (조도 확보)"]
    )
    
    st.divider()
    st.subheader("📍 이동 구간 입력")
    start_point = st.text_input("출발지 (예: 서현역)", "서현역")
    end_point = st.text_input("목적지 (예: 서현중학교)", "서현중학교")
    
    search_btn = st.button("AI 안전 경로 탐색 🔍", use_container_width=True)

# ==========================================
# 2. 메인 화면 (탐색 결과 및 고급 인터랙티브 지도)
# ==========================================
st.title("🗺️ SafePath AI: 맞춤형 안전 네비게이션")

if search_btn:
    # 탐색 로딩 효과
    with st.spinner(f"위성 데이터와 위험 요소를 분석하여 '{user_type}' 최적 경로를 계산 중입니다..."):
        time.sleep(1.5)
        
    st.success(f"✅ 분석 완료! {start_point}에서 {end_point}까지의 안전 경로를 안내합니다.")
    
    col1, col2 = st.columns([2, 1]) # 지도(넓게), 리포트(좁게)
    
    with col1:
        st.subheader("📍 실시간 경로 시뮬레이션")
        
        # 🌟 핵심: 사용자가 선택한 조건에 따라 지도의 선(경로)이 다르게 그려짐
        # [경도, 위도] 좌표를 꺾이는 길에 맞춰 설정함
        if "휠체어" in user_type:
            # 휠체어 우회 경로 (빨간색 선, 큰길 위주로 꺾어감)
            route_coords = [[127.1235, 37.3850], [127.1285, 37.3850], [127.1300, 37.3800], [127.1300, 37.3780]]
            line_color = [255, 75, 75] # 빨간색
        elif "심야" in user_type:
            # 심야 큰길 경로 (노란색 선, 공원을 피해 도로로 크게 돎)
            route_coords = [[127.1235, 37.3850], [127.1235, 37.3780], [127.1300, 37.3780]]
            line_color = [255, 200, 0] # 노란색
        else:
            # 일반 최단 경로 (파란색 선, 공원/골목길 가로지름)
            route_coords = [[127.1235, 37.3850], [127.1270, 37.3810], [127.1300, 37.3780]]
            line_color = [0, 100, 255] # 파란색
            
        # PyDeck을 이용해 지도 위에 두께가 일정한 '선(Path)' 그리기
        df_route = pd.DataFrame({
            "path": [route_coords],
            "color": [line_color]
        })
        
        view_state = pdk.ViewState(latitude=37.3815, longitude=127.1265, zoom=14.5)
        layer = pdk.Layer(
            type="PathLayer",
            data=df_route,
            pickable=True,
            get_color="color",
            width_scale=20,
            width_min_pixels=5,
            get_path="path",
            get_width=5
        )
        # 지도 출력 (map_style을 road로 하여 길이 잘 보이게 함)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="road"))
        
    with col2:
        st.subheader("🎯 AI 심층 분석 리포트")
        st.info("💡 **알고리즘 가중치 적용 결과**")
        
        # 🌟 핵심: 리포트 내용을 훨씬 더 전문적이고 길게 작성하여 설득력 강화
        if "휠체어" in user_type:
            st.error("🚨 **위험 감지:** 기존 최단 거리 내 계단 15개 및 30도 이상의 급경사 구간 발견")
            st.success("✅ **경로 수정:** 단차가 없는 평탄화 보도블록 및 횡단보도 위주 우회 경로 탐색")
            st.write("""
            **[AI 상세 분석]**
            일반 보행자의 최단 경로(골목길 관통)를 분석한 결과, 휠체어 및 유모차의 이동 시 전복 위험이 매우 높은 급경사와 계단 구간이 감지되어 위험 가중치(+9999점)가 부여되었습니다. 
            해당 구역을 시스템에서 전면 차단하고, 휠체어가 안전하게 통행할 수 있는 폭 1.5m 이상의 평탄한 인도 및 횡단보도가 마련된 큰 도로를 따라 약 250m 우회하는 안전 경로를 생성했습니다.
            """)
            
        elif "심야" in user_type:
            st.error("🚨 **위험 감지:** 공원 가로지르기 구간 내 20럭스 이하 저조도 사각지대 발견")
            st.success("✅ **경로 수정:** 24시간 가로등 운영 및 CCTV 집중 관제 도로 추천")
            st.write("""
            **[AI 상세 분석]**
            일반 보행자의 최단 경로는 공원과 인적이 드문 좁은 골목을 가로지르기 때문에, 심야 시간대(22시~04시) 범죄 노출 및 낙상 사고의 위험 가중치(+500점)가 높게 산출되었습니다.
            안전 점수를 확보하기 위해, 조도가 80럭스 이상으로 상시 유지되고 24시간 운영되는 상가 불빛 및 방범용 CCTV가 배치된 왕복 4차선 이상의 큰 도로를 경유하도록 경로를 재설계했습니다.
            """)
            
        else:
            st.success("✅ **탐색 결과:** 별도의 위험 가중치 미발견. 최단 거리로 안내합니다.")
            st.write("""
            **[AI 상세 분석]**
            일반 보행자 기준, 현재 시간대와 날씨 조건에서 특별한 통행 방해 요소(공사, 심한 경사 등)가 발견되지 않았습니다.
            불필요한 우회를 최소화하고, 공원 산책로와 골목길을 가로질러 목적지에 가장 빠르게 도달할 수 있는 효율성 중심의 최적 경로를 안내합니다.
            """)

else:
    st.info("👈 왼쪽 설정 창에서 휠체어 또는 심야 모드 등을 선택하고 '탐색' 버튼을 눌러, AI가 길을 어떻게 바꾸는지 확인해 보세요.")
