import streamlit as st
import pandas as pd
import urllib.request
import urllib.parse
import json
import re
import datetime
import time

st.set_page_config(page_title="School Balance AI", layout="wide")

# ============================================================
# API KEY 설정
# ============================================================
API_KEY = "여기에_API_KEY를_입력하세요"

# ============================================================
# 핵심 함수 (학교급식 + 영양분석)
# ============================================================
def search_school(keyword):
    try:
        url = f"https://open.neis.go.kr/hub/schoolInfo?Type=json&SCHUL_NM={urllib.parse.quote(keyword)}"
        if API_KEY and API_KEY != "여기에_API_KEY를_입력하세요": url += f"&KEY={API_KEY}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [{"name": r["SCHUL_NM"], "edu_code": r["ATPT_OFCDC_SC_CODE"], "school_code": r["SD_SCHUL_CODE"]} for r in data["schoolInfo"][1]["row"]]
    except: return []

def get_meal(edu_code, school_code, meal_date):
    try:
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&ATPT_OFCDC_SC_CODE={edu_code}&SD_SCHUL_CODE={school_code}&MLSV_YMD={meal_date}"
        if API_KEY and API_KEY != "여기에_API_KEY를_입력하세요": url += f"&KEY={API_KEY}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            row = data["mealServiceDietInfo"][1]["row"][0]
            menu = [re.sub(r"[0-9\.\(\)]", "", food).strip() for food in row["DDISH_NM"].split("<br/>")]
            return {"menu": menu, "calorie": row["CAL_INFO"], "nutrition": row["NTR_INFO"]}
    except: return None

def parse_nutrition(text):
    nutrition = {}
    if not text: return nutrition
    for item in text.split("<br/>"):
        if ":" in item:
            name, value = item.split(":", 1)
            name = re.sub(r"\(.*?\)", "", name).strip()
            match = re.search(r"[\d.]+", value)
            nutrition[name] = float(match.group()) if match else 0
    return nutrition

# ============================================================
# UI (사이드바)
# ============================================================
with st.sidebar:
    st.header("⚙️ 기초 정보 입력")
    user_weight = st.number_input("몸무게 (kg)", value=50.0)
    leftover_rate = st.slider("잔반 비율 (%)", 0, 100, 0)
    mode = st.radio("모드", ["🏫 학교 급식", "🏠 자율 식단"])
    
    if mode == "🏫 학교 급식":
        school_keyword = st.text_input("학교 검색", "서현중학교")
        meal_date = st.date_input("날짜", datetime.date(2026, 7, 2))
    else:
        user_food = st.text_area("먹은 음식", "불닭볶음면, 참치김밥, 콜라")
    
    run_btn = st.button("🚀 통합 분석 시작", type="primary")

# ============================================================
# 메인 로직
# ============================================================
st.title("🍱 School Balance AI")

if run_btn:
    if mode == "🏫 학교 급식":
        schools = search_school(school_keyword)
        if schools:
            meal = get_meal(schools[0]["edu_code"], schools[0]["school_code"], meal_date.strftime("%Y%m%d"))
            if meal:
                st.session_state.result = {"type": "급식", "name": schools[0]["name"], "cal": float(re.search(r"[\d.]+", meal["calorie"]).group()), "nutri": parse_nutrition(meal["nutrition"]), "left": leftover_rate}
            else: st.error("급식 정보 없음")
    else:
        st.session_state.result = {"type": "자율", "name": user_food, "cal": 700, "nutri": {"탄수화물": 80, "단백질": 20, "지방": 30}, "left": leftover_rate}

# 결과 출력
if "result" in st.session_state:
    res = st.session_state.result
    st.success(f"{res['name']} 분석 완료")
    st.metric("칼로리", f"{res['cal']} kcal")
    
    if st.button("✨ 심층 영양 및 물리 처방전 보기"):
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏃 물리적 활동 처방")
            st.write(f"잉여 에너지 소모를 위해 계단 {(res['cal']-600)*4184/(user_weight*9.8*0.2):,.0f}개를 오르세요!")
        with c2:
            st.subheader("🌍 기후 위기 처방")
            st.write(f"잔반으로 인한 이산화탄소 배출: {res['left']/100*0.6*1.58:.2f} kg")
