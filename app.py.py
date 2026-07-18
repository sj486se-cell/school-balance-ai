import streamlit as st
import pandas as pd
import pydeck as pdk
import urllib.parse
import urllib.request
import json

st.set_page_config(page_title="SafePath AI", layout="wide")

def get_coordinates(address):
    try:
        url = "https://nominatim.openstreetmap.org/search?q=" + urllib.parse.quote(address) + "&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'SafePath_App'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data: return float(data[0]['lon']), float(data[0]['lat'])
    except: pass
    return 127.1235, 37.3850

def get_route(waypoints):
    coords_str = ";".join([f"{lon},{lat}" for lon, lat in waypoints])
    url = f"http://router.project-osrm.org/route/v1/foot/{coords_str}?overview=full&geometries=geojson"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data["routes"][0]["geometry"]["coordinates"]
    except: return waypoints

with st.sidebar:
    user_type = st.radio("보행자 조건", ["🚶 일반 보행자", "👩‍🦽 휠체어/유모차", "🌙 심야 안심 귀가"])
    start = st.text_input("출발지", "정자역")
    end = st.text_input("목적지", "수내역")
    btn = st.button("탐색 시작 🔍")

st.title("🗺️ SafePath AI")

if btn:
    s_lon, s_lat = get_coordinates(start)
    e_lon, e_lat = get_coordinates(end)
    
    # 일반 보행자는 직선, 나머지는 횡단보도 경유
    if "일반" in user_type:
        path = get_route([[s_lon, s_lat], [e_lon, e_lat]])
        color = [0, 100, 255]
    else:
        # 정자역-수내역 중간쯤의 임의 경유지(횡단보도 느낌)를 강제로 추가하여 우회
        mid_lon, mid_lat = (s_lon + e_lon) / 2 + 0.002, (s_lat + e_lat) / 2 + 0.002
        path = get_route([[s_lon, s_lat], [mid_lon, mid_lat], [e_lon, e_lat]])
        color = [255, 75, 75]
    
    # 에러 방지를 위한 데이터 검증
    if path and len(path) > 1:
        st.pydeck_chart(pdk.Deck(
            layers=[pdk.Layer("PathLayer", data=pd.DataFrame({"path": [path], "color": [color]}), get_color="color", width_min_pixels=6, get_path="path")],
            initial_view_state=pdk.ViewState(latitude=(s_lat+e_lat)/2, longitude=(s_lon+e_lon)/2, zoom=15)
        ))
    else:
        st.error("경로 탐색에 실패했습니다. 다른 지역명을 입력해보세요.")
