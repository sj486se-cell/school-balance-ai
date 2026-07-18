import streamlit as st
import urllib.request
import urllib.parse
import json
import re
import datetime
import time
import google.generativeai as genai

st.set_page_config(page_title="School Balance AI Pro", page_icon="🍱", layout="wide")

# ============================================================
# 기본 설정
# ============================================================
NEIS_API_KEY = "여기에_NEIS_API_KEY를_입력하세요"
GEMINI_API_KEY = ""

# CSS 설정
st.markdown("""
<style>
.main-title{ font-size:42px; font-weight:bold; color:#2E8B57; }
.ai-report { background-color: #f1f8ff; padding: 20px; border-radius: 10px; border: 1px solid #cce5ff; }
</style>
""", unsafe_allow_html=True)

# 필수 함수들
def search_school(keyword):
    try:
        url = f"https://open.neis.go.kr/hub/schoolInfo?Type=json&SCHUL_NM={urllib.parse.quote(keyword)}"
        if NEIS_API_KEY and NEIS_API_KEY != "여기에_NEIS_API_KEY를_입력하세요": url += f"&KEY={NEIS_API_KEY}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
        return [{"name": r["SCHUL_NM"], "edu_code": r["ATPT_OFCDC_SC_CODE"], "school_code": r["SD_SCHUL_CODE"]} for r in data["schoolInfo"][1]["row"]]
    except: return []

def get_meal(edu_code, school_code, meal_date):
    try:
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&ATPT_OFCDC_SC_CODE={edu_code}&SD_SCHUL_CODE={school_code}&MLSV_YMD={meal_date}"
        if NEIS_API_KEY and NEIS_API_KEY != "여기에_NEIS_API_KEY를_입력하세요": url += f"&KEY={NEIS_API_KEY}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
        row = data["mealServiceDietInfo"][1]["row"][0]
        return {"menu": [re.sub(r"[0-9\.\(\)]", "", f).strip() for f in row["DDISH_NM"].split("<br/>")], "calorie": row["CAL_INFO"], "nutrition": row["NTR_INFO"]}
    except: return None

def parse_nutrition(text):
    nutrition = {}
    if not text: return nutrition
    for item in text.split("<br/>"):
        if ":" in item:
            name, value = item.split(":", 1)
            match = re.search(r"[\d.]+", value)
            nutrition[re.sub(r"\(.*?\)", "", name).strip()] = float(match.group()) if match else 0.0
    return nutrition

def calculate_score(nutrition):
    score = 100
    if nutrition.get("단백질", 0) < 20: score -= 15
    if nutrition.get("지방", 0) > 25: score -= 10
    return max(score, 0)

# 세션 상태 초기화
if "analyzed" not in st.session_state: st.session_state.analyzed = False

# 사이드바
with st.sidebar:
    mode = st.radio("분석 모드", ["학교 급식", "자율 식단"])
    if mode == "학교 급식":
        school_keyword = st.text_input("학교 검색", "서현중학교")
        meal_date = st.date_input("날짜", datetime.date.today())
        meal_btn = st.button("분석 시작")
    else:
        user_food = st.text_area("먹은 음식", "마라탕, 김밥")
        analyze_btn = st.button("AI 분석 시작")

# 데이터 처리 로직
if mode == "학교 급식" and meal_btn:
    schools = search_school(school_keyword)
    if schools:
        meal = get_meal(schools[0]["edu_code"], schools[0]["school_code"], meal_date.strftime("%Y%m%d"))
        if meal:
            st.session_state.menu_list = meal["menu"]
            st.session_state.current_nutrition = parse_nutrition(meal["nutrition"])
            st.session_state.current_cal = 500 # 간이 설정
            st.session_state.current_score = calculate_score(st.session_state.current_nutrition)
            st.session_state.current_food_name = schools[0]["name"]
            st.session_state.analyzed = True
        else:
            st.warning("데이터가 없습니다. 날짜를 변경해보세요.")
    else:
        st.error("학교를 찾을 수 없습니다.")

# 결과 출력
if st.session_state.analyzed:
    st.header("📊 분석 결과")
    st.write(f"오늘의 점수: {st.session_state.current_score}점")
    if st.button("AI 리포트 보기"):
        st.markdown(f'<div class="ai-report">영양 밸런스 분석이 완료되었습니다. 점수: {st.session_state.current_score}</div>', unsafe_allow_html=True)
