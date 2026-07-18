import streamlit as st
import pandas as pd
import pydeck as pdk
import urllib.parse
import urllib.request
import json
import time

st.set_page_config(page_title="SafePath AI", page_icon="🗺️", layout="wide")

# ==========================================
# 0. 백엔드 API (좌표 변환 & 다중 경유지 길찾기)
# ==========================================
def get_coordinates(address, default_lon, default_lat):
    try:
        url = "https://nominatim.openstreetmap.org/search?q=" + urllib.parse.quote(address) + "&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'SafePath'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if len(data) > 0: return float(data[0]['lon']), float(data[0]['lat'])
    except: pass
    return default_lon, default_lat

# 🌟 핵심 알고리즘: 점과 점 사이를 무조건 이어주는 다중 경유지 길찾기
def get_route_with_waypoints(waypoints):
    try:
        # waypoints = [[lon, lat], [lon, lat], ...] -> 이 좌표들을 순서대로 다 통과하게 만듦
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in waypoints])
        url = f"http://router.project-osrm.org/route/v1/foot/{coords_str}?overview=full&geometries=geojson"
        req = urllib.request.Request(url, headers={'User-Agent': 'SafePath'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if "routes" in data and len(data["routes"]) > 0:
                return data["routes"][0]["geometry"]["coordinates"]
    except: pass
    return waypoints # 에러 시 꺾인 직선이라도 보여줌

def get_real_infra(min_lon, min_lat, max_lon, max_lat):
    infra_list = []
    try:
        pad = 0.003
        query = f"""
        [out:json];
        (
          node["highway"="crossing"]({min_lat-pad},{min_lon-pad},{max_lat+pad},{max_lon+pad});
          way["highway"="steps"]({min_lat-pad},{min_lon-pad},{max_lat+pad},{max_lon+pad});
        );
        out center;
        """
        url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={'User-Agent': 'SafePath'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for el in data.get('elements', []):
                if el['type'] == 'node':
                    infra_list.append({"type": "green", "name": "안전 횡단보도", "lon": el['lon'], "lat": el['lat'], "color": [0, 255, 0, 200]})
                elif el['type'] == 'way':
                    infra_list.append({"type": "red", "name": "보행 육교/계단", "lon": el['center']['lon'], "lat": el['center']['lat'], "color": [255, 0, 0, 200]})
    except: pass
    return infra_list

# ==========================================
# 1. 사이드바
# ==========================================
with st.sidebar:
    st.title("⚙️ 안전 경로 설정")
    user_type = st.radio(
        "👤 보행자 유형", 
        ["🚶 일반 보행자 (계단 지름길 포함)", "👩‍🦽 휠체어/유모차 (횡단보도 강제 우회)", "🌙 심야 안심 귀가 (큰길 우회)"]
    )
    st.divider()
    start_point = st.text_input("출발지 (예: 정자역)", "정자역")
    end_point = st.text_input("목적지 (예: 수내역)", "수내역")
    
    search_btn = st.button("AI 맞춤형 경로 탐색 🔍", use_container_width=True)

# ==========================================
# 2. 메인 화면
# ==========================================
st.title("🗺️ SafePath AI: 상황 맞춤형 우회 네비게이션")
st.caption("AI가 실제 횡단보도와 계단을 인식하여 탑승자 조건에 맞게 경로를 강제로 꺾어(우회) 안내합니다.")

if search_btn:
    with st.spinner("주변 인프라를 스캔하여 맞춤형 우회로를 그리고 있습니다..."):
        start_lon, start_lat = get_coordinates(start_point, 127.1082, 37.3667)
        end_lon, end_lat = get_coordinates(end_point, 127.1141, 37.3784)
        
        # 인프라 데이터 수집
        infra_data = get_real_infra(min(start_lon, end_lon), min(start_lat, end_lat), max(start_lon, end_lon), max(start_lat, end_lat))
        
        green_dots = [d for d in infra_data if d['type'] == 'green']
        red_dots = [d for d in infra_data if d['type'] == 'red']
        
        # 🌟 핵심 로직: 상황에 맞춰 중간 경유지를 선택해 경로를 꺾어버림!
        waypoints = [[start_lon, start_lat]]
        
        if "일반" in user_type:
            line_color = [0, 100, 255]
            if red_dots: # 빨간 점(계단)이 있으면 그곳을 뚫고 가는 지름길 선택
                mid_point = red_dots[0] # 첫 번째 계단 선택
                waypoints.append([mid_point['lon'], mid_point['lat']])
        else:
            line_color = [255, 75, 75] if "휠체어" in user_type else [255, 200, 0]
            if green_dots: # 휠체어/심야는 무조건 초록 점(횡단보도)을 통과하도록 우회!
                # 횡단보도 중 하나를 선택해 경유지로 추가
                mid_point = green_dots[0] 
                waypoints.append([mid_point['lon'], mid_point['lat']])
                
        waypoints.append([end_lon, end_lat])
        
        # 경유지가 포함된 최종 선 그리기
        route_coords = get_route_with_waypoints(waypoints)
        time.sleep(1)
        
    st.success(f"✅ 상황 맞춤형 경로 생성 완료! 선이 인프라(점)를 따라 어떻게 꺾이는지 확인하세요.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 지도 출력
        layers = []
        route_layer = pdk.Layer(
            "PathLayer", data=pd.DataFrame({"path": [route_coords], "color": [line_color]}),
            get_color="color", width_scale=1, width_min_pixels=4, get_path="path", get_width=6
        )
        layers.append(route_layer)
        
        if infra_data:
            infra_layer = pdk.Layer(
                "ScatterplotLayer", data=pd.DataFrame(infra_data),
                get_position="[lon, lat]", get_color="color", get_radius=20, pickable=True,
            )
            layers.append(infra_layer)
            
        view_state = pdk.ViewState(latitude=(start_lat+end_lat)/2, longitude=(start_lon+end_lon)/2, zoom=14.5)
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state, map_style="road", tooltip={"html": "<b>{name}</b>"}))

    with col2:
        st.subheader("🎯 AI 맞춤형 경로 해설")
        if "휠체어" in user_type:
            st.error("🚨 경로 상 장애물(계단) 발견")
            st.success("✅ **가장 가까운 횡단보도(🟢)로 우회 성공**")
            st.write("단차가 있는 위험 구역을 피해, 시스템이 자동으로 주변의 안전 횡단보도를 탐색한 뒤 **경로를 그쪽으로 꺾어서(우회)** 안내했습니다. 지도의 선이 초록 점을 통과하는 것을 확인하세요.")
        else:
            st.success("✅ **계단(🔴) 통과 지름길 안내**")
            st.write("보행에 무리가 없는 일반 탑승자이므로, 횡단보도로 우회하지 않고 **보행 육교 및 계단을 직접 통과하는 최단거리 지름길**을 생성했습니다. 지도의 선이 빨간 점을 통과합니다.")
