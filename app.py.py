import streamlit as st
import pandas as pd
import re
import datetime
import time

st.set_page_config(page_title="School Balance AI", layout="wide")

# ============================================================
# 1. 사이드바 (입력란)
# ============================================================
with st.sidebar:
    st.header("⚙️ 기초 정보 입력")
    user_weight = st.number_input("몸무게 (kg)", value=50.0)
    leftover_rate = st.slider("잔반 비율 (%)", 0, 100, 0)
    mode = st.radio("분석 모드", ["🏠 자율 식단"]) # 급식 API 키 문제 예방을 위해 우선 자율식단 고정
    user_food = st.text_area("먹은 음식 (콤마로 구분)", "불닭볶음면, 참치김밥, 콜라")
    
    # 분석 버튼
    if st.button("🚀 통합 분석 시작", type="primary"):
        # 음식 데이터베이스
        food_db = {
            "라면": {"calorie": 500, "탄수화물": 70, "단백질": 10, "지방": 15},
            "마라탕": {"calorie": 800, "탄수화물": 90, "단백질": 20, "지방": 40},
            "불닭볶음면": {"calorie": 550, "탄수화물": 80, "단백질": 12, "지방": 18},
            "김밥": {"calorie": 450, "탄수화물": 65, "단백질": 12, "지방": 14},
            "참치김밥": {"calorie": 520, "탄수화물": 68, "단백질": 18, "지방": 18},
            "치킨": {"calorie": 700, "탄수화물": 20, "단백질": 40, "지방": 35},
            "콜라": {"calorie": 150, "탄수화물": 40, "단백질": 0, "지방": 0}
        }
        
        # 분석 로직
        foods = [f.strip() for f in user_food.split(",")]
        total = {"calorie": 0, "탄수화물": 0, "단백질": 0, "지방": 0}
        for food in foods:
            for name, data in food_db.items():
                if name in food:
                    for k in total: total[k] += data[k]
        
        # 점수 계산
        score = 100 - (15 if total["단백질"] < 20 else 0) - (15 if total["지방"] > 30 else 0)
        
        # 세션 저장 (화면이 새로고침되어도 데이터 유지)
        st.session_state.result = {
            "name": user_food, "total": total, "score": max(score, 0), "leftover": leftover_rate, "weight": user_weight
        }

# ============================================================
# 2. 메인 화면 (결과 출력)
# ============================================================
st.title("🍱 School Balance AI")

if "result" in st.session_state:
    res = st.session_state.result
    
    # 기초 지표
    c1, c2, c3 = st.columns(3)
    c1.metric("Health Score", f"{res['score']}점")
    c2.metric("칼로리", f"{res['total']['calorie']} kcal")
    c3.metric("단백질", f"{res['total']['단백질']} g")
    
    st.markdown("---")
    
    # 처방 버튼 (또 다른 버튼으로 분리해서 백지 방지)
    if st.button("✨ 상세 처방전 및 열역학 분석 보기"):
        # 1. 텍스트 분석
        st.subheader("🤖 AI 영양 분석")
        st.info(f"분석 결과, '{res['name']}' 섭취 후 대사 상태는 {res['score']}점으로 추정됩니다.")
        
        # 2. 물리/환경 분석
        c_phys, c_eco = st.columns(2)
        with c_phys:
            st.subheader("🏃 물리적 활동 처방")
            delta_kcal = res['total']['calorie'] - 600
            if delta_kcal > 0:
                steps = int((delta_kcal * 4184) / (res['weight'] * 9.8 * 0.2))
                st.error(f"잉여 에너지 {delta_kcal:.0f} kcal 발생")
                st.write(f"이를 소모하려면 계단 {steps:,}개를 오르세요!")
            else:
                st.success("열평형 상태입니다.")
        
        with c_eco:
            st.subheader("🌍 에코 써모(잔반)")
            wasted = 0.6 * (res['leftover'] / 100)
            st.write(f"잔반 {res['leftover']}% 발생 시 온실가스 {wasted * 1.58:.2f} kg 배출!")

        # 3. 처방전
        st.subheader("🧾 맞춤 처방전")
        st.success("저녁 추천: 닭가슴살 샐러드")
else:
    st.write("👈 왼쪽 사이드바에서 메뉴를 입력하고 '통합 분석 시작'을 누르세요.")
