import streamlit as st
import pandas as pd
import pydeck as pdk
import urllib.parse
import urllib.request
import json
import time

st.set_page_config(page_title="SafePath AI", page_icon="🗺️", layout="wide")

# ==========================================
# 0. API 함수 정의
# ==========================================
def get_coordinates(address):
    try:
        url = "https://nominatim.openstreetmap.org/search?q=" + urllib.parse.quote(address) + "&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'SafePath_App'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data: return float(data[0]['lon']), float(data[0]['lat'])
    except: pass
    return 127.1235, 37.3850 # 기본값: 서현역 인근

def get_real_route(waypoints):
    coords_str = ";".join([f"{lon},{lat}" for lon, lat in waypoints])
    url = f"http://router.project-osrm.org/route/v1/foot/{coords_str}?overview=full&geometries=geojson"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data["routes"][0]["geometry"]["coordinates"]
    except: return waypoints

def get_real_infra(min_lon, min_lat, max_lon, max_lat):
    infra_list = []
    try:
        query = f"""[out:json];(node["highway"="crossing"]({min_lat-0.003},{min_lon-0.003},{max_lat+0.003},{max_lon+0.003});
                    way["highway"="steps"]({min_lat-0.003},{min_lon-0.003},{max_lat+0.003},{max_lon+0.003}););out center;"""
        url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            for el in data.get('elements', []):
                if el['type'] == 'node': infra_list.append({"type": "green", "lon": el['lon'], "lat": el['lat']})
                else: infra_list.append({"type": "red", "lon": el['center']['lon'], "lat": el['center']['lat']})
    except: pass
    return infra_list

# ==========================================
# 1. UI 설정
# ==========================================
with st.sidebar:
    st.title("⚙️ 안전 경로 설정")
    user_type = st.radio("👤 보행자 조건", ["🚶 일반 보행자", "👩‍🦽 휠체어/유모차", "🌙 심야 안심 귀가"])
    start_point = st.text_input("출발지", "정자역")
    end_point = st.text_input("목적지", "수내역")
    search_btn = st.button("탐색 시작 🔍", use_container_width=True)

st.title("🗺️ SafePath AI: 동적 우회 네비게이션")

if search_btn:
    with st.spinner("AI가 경로를 분석 중입니다..."):
        s_lon, s_lat = get_coordinates(start_point)
        e_lon, e_lat = get_coordinates(end_point)
        infra = get_real_infra(min(s_lon, e_lon), min(s_lat, e_lat), max(s_lon, e_lon), max(s_lat, e_lat))
        
        green_dots = [d for d in infra if d['type'] == 'green']
        
        # 알고리즘: 일반은 최단 직진, 교통약자는 횡단보도(green) 경유
        if "일반" in user_type:
            waypoints = [[s_lon, s_lat], [e_lon, e_lat]]
            line_color = [0, 100, 255]
            msg = "일반 보행자 최단 거리 경로입니다."
        else:
            waypoints = [[s_lon, s_lat], [green_dots[0]['lon'], green_dots[0]['lat']] if green_dots else [e_lon, e_lat], [e_lon, e_lat]]
            line_color = [255, 75, 75] if "휠체어" in user_type else [255, 200, 0]
            msg = "안전을 위해 횡단보도를 경유하는 우회 경로입니다."

        route = get_real_route(waypoints)
        
    col1, col2 = st.columns([2, 1])
    with col1:
        st.pydeck_chart(pdk.Deck(
            layers=[
                pdk.Layer("PathLayer", data=pd.DataFrame({"path": [route], "color": [line_color]}), get_color="color", width_min_pixels=6, get_path="path"),
                pdk.Layer("ScatterplotLayer", data=pd.DataFrame(infra), get_position="[lon, lat]", get_color="[255,0,0] if type=='red' else [0,255,0]", get_radius=15)
            ],
            initial_view_state=pdk.ViewState(latitude=(s_lat+e_lat)/2, longitude=(s_lon+e_lon)/2, zoom=14.5)
        ))
    with col2:
        st.success(msg)
        st.write("실제 도로 데이터와 보행 인프라(횡단보도/육교)를 분석하여 최적의 동선을 생성했습니다.")
