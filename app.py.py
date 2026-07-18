import streamlit as st
import pandas as pd

# 1. 앱 기본 설정
st.set_page_config(page_title="안전 경로 시뮬레이터", page_icon="🗺️")
st.title("🗺️ 보행 약자 맞춤형 안전 경로 시뮬레이터")
st.write("사용자의 이동 조건에 맞춰 알고리즘이 **가장 안전하고 최적화된 경로**를 분석하여 추천합니다.")

st.divider()

# 2. 사용자 입력 받기
st.header("👤 이동 조건 설정")
user_type = st.radio(
    "어떤 조건으로 이동하시나요?", 
    ["🚶 일반 보행자", "👩‍🦽 휠체어/유모차 탑승자", "🌙 심야 안심 귀가"]
)

# 3. 파이썬 딕셔너리: 경로 데이터베이스 구축
# distance: 거리, stairs: 계단 유무, steep: 경사도, lighting: 가로등 밝기
routes = {
    "경로 A (최단거리 골목길)": {"distance": 500, "stairs": True, "steep": False, "lighting": "low"},
    "경로 B (조금 먼 우회로)": {"distance": 800, "stairs": False, "steep": False, "lighting": "medium"},
    "경로 C (큰길 상가거리)": {"distance": 1000, "stairs": False, "steep": True, "lighting": "high"}
}

# 4. 안전 가중치 알고리즘 (핵심 로직)
scores = {}
for name, info in routes.items():
    # 기본 위험도: 거리가 멀수록 조금씩 증가 (100m당 10점)
    score = info["distance"] * 0.1 
    
    # 휠체어/유모차 탑승자 조건 알고리즘
    if "휠체어" in user_type:
        if info["stairs"]:
            score += 9999  # 계단이 있으면 이동 불가 (무한대 페널티)
        if info["steep"]:
            score += 50    # 경사가 심하면 가중치 부여
            
    # 심야 안심 귀가 조건 알고리즘
    if "심야" in user_type:
        if info["lighting"] == "low":
            score += 100   # 어두운 골목길은 매우 위험
        elif info["lighting"] == "high":
            score -= 30    # 밝은 길은 안전 점수 혜택
            
    scores[name] = score

# 가장 위험도 점수가 낮은 최적 경로 찾기
best_route = min(scores, key=scores.get)

st.divider()

# 5. 분석 결과 및 데이터 시각화 출력
st.header("🎯 AI 최적 경로 분석 결과")

if scores[best_route] >= 9999:
    st.error("🚨 선택하신 조건으로 안전하게 이동할 수 있는 경로가 없습니다. 우회로 확보가 시급합니다!")
else:
    st.success(f"🏆 추천 안전 경로: **{best_route}**")
    st.write(f"선택하신 '{user_type}' 조건에서 위험 가중치가 가장 낮은 최적의 경로입니다.")

# 시각화를 위해 점수가 너무 높은(9999) 통제 구역은 차트에서 150점으로 보정
chart_data = {
    "경로": list(scores.keys()),
    "위험 점수": [s if s < 9999 else 150 for s in scores.values()]
}
df = pd.DataFrame(chart_data)

st.subheader("📊 경로별 위험도 비교 (낮을수록 안전)")
# 막대그래프로 시각화
st.bar_chart(df.set_index("경로"), color="#4CAF50")

st.info("💡 **알고리즘 요약:** 휠체어 탑승 시 계단 경로를 차단하고, 심야 시간대에는 조도(가로등) 데이터를 분석하여 안전 가중치를 부여했습니다.")
