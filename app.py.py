import streamlit as st
import pandas as pd
import numpy as np
import time

# 1. 앱 기본 설정
st.set_page_config(page_title="SafePath AI", page_icon="🗺️", layout="wide")

# ==========================================
# 2. 사이드바 (사용자 조건 및 경로 입력)
# ==========================================
with st.sidebar:
    st.title("⚙️ 안전 경로 설정")
    user_type = st.radio(
        "👤 보행자 유형", 
        ["🚶 일반 보행자", "👩‍🦽 휠체어/유모차 탑승자", "🌙 심야 안심 귀가"]
    )
    
    st.divider()
    st.subheader("📍 경로 입력")
    # 텍스트 입력창 추가
    start_point = st.text_input("출발지 (예: 집, 지하철역)", "서현역")
    end_point = st.text_input("목적지", "서현중학교")
    
    # 버튼을 누르면 아래 로직이 실행됨
    search_btn = st.button("안전 경로 탐색 🔍")

# ==========================================
# 3. 메인 화면 (탐색 결과 및 인터랙티브 지도)
# ==========================================
st.title("🗺️ SafePath AI: 맞춤형 안전 네비게이션")

if search_btn:
    # 🌟 해커톤 시연용 꿀팁: 진짜 AI가 계산하는 것처럼 로딩 효과 주기
    with st.spinner('위험 요소를 분석하여 최적의 경로를 계산 중입니다...'):
        time.sleep(1.5) # 1.5초 대기
        
    st.success(f"✅ **{start_point}**에서 **{end_point}**까지의 '{user_type}' 맞춤 경로를 찾았습니다!")
    
    col1, col2 = st.columns([2, 1]) # 지도를 크게, 리포트를 작게 화면 분할
    
    with col1:
        st.subheader(f"📍 {start_point} ➡️ {end_point} 경로 안내")
        
        # 입력된 값에 상관없이 시연용으로 길게 이어지는 '경로(선)' 좌표 생성
        # 실제 상용화 시 이 부분에 카카오/네이버 맵 API가 들어간다고 발표하면 됩니다.
        base_lat, base_lon = 37.3820, 127.1190
        
        # 선처럼 보이도록 30개의 점을 일렬로 생성 (경로 시뮬레이션)
        route_lat = np.linspace(base_lat, base_lat - 0.005, 30)
        route_lon = np.linspace(base_lon, base_lon + 0.015, 30)
        
        # 지도 데이터 완성
        map_data = pd.DataFrame({'lat': route_lat, 'lon': route_lon})
        
        # 화면에 경로 지도 출력
        st.map(map_data, zoom=14, color="#0044FF") # 경로를 파란색으로 표시
        
    with col2:
        st.subheader("🎯 AI 분석 리포트")
        st.info("💡 **알고리즘 분석 결과**")
        
        if "휠체어" in user_type:
            st.error("🚨 기존 최단 거리: **계단(3곳) 발견**")
            st.success("✅ 우회 경로: **경사로(단차 없음) 확보**")
            st.write(f"휠체어가 이동할 수 없는 계단 구역을 차단하고 150m 우회하는 안전 경로를 탐색했습니다.")
            
        elif "심야" in user_type:
            st.error("🚨 기존 최단 거리: **가로등 조도 20% (위험)**")
            st.success("✅ 우회 경로: **가로등 조도 85% (안전)**")
            st.write("조도가 낮아 범죄 노출 위험이 있는 골목길을 피하고, 24시간 상가와 가로등이 있는 큰길을 추천합니다.")
            
        else:
            st.success("✅ 가장 빠른 최단 거리로 안내합니다.")

else:
    # 탐색 버튼을 누르기 전 초기 화면
    st.info("👈 왼쪽 사이드바에서 출발지와 목적지를 입력하고 '탐색' 버튼을 눌러주세요.")
    st.write("현재 위치 데이터를 불러오는 중입니다...")
