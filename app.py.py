import streamlit as st
import urllib.request
import urllib.parse
import json
import re
import datetime
import time

st.set_page_config(page_title="School Balance AI", page_icon="🍱", layout="wide")

# ============================================================
# API KEY 설정
# ============================================================
API_KEY = "여기에_API_KEY를_입력하세요"

# ============================================================
# CSS 및 함수 (이전과 동일)
# ============================================================
st.markdown("""
<style>
.main-title{ font-size:42px; font-weight:bold; color:#2E8B57; }
.sub-title{ color:#666666; font-size:18px; margin-bottom: 20px;}
.food-card{ background:#F7F9FA; padding:12px; border-radius:12px; margin-bottom:8px; border-left:6px solid #2E8B57; }
.physics-card { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 25px; border-radius: 12px; margin-top: 20px; margin-bottom: 20px; }
.ai-report { background-color: #f1f8ff; padding: 20px; border-radius: 10px; border: 1px solid #cce5ff; font-size: 16px; line-height: 1.6; margin-bottom: 20px; }
.prescription-card { background-color: #2b3035; color: #ffffff; padding: 25px; border-radius: 12px; border-left: 8px solid #20c997; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-top: 10px;}
.prescription-title { color: #20c997; margin-top: 0; font-size: 22px; font-weight: bold; border-bottom: 1px solid #495057; padding-bottom: 10px; margin-bottom: 15px;}
.exercise-card { background-color: #2b3035; color: #ffffff; padding: 25px; border-radius: 12px; border-left: 8px solid #ff6b6b; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-top: 10px;}
.exercise-title { color: #ff6b6b; margin-top: 0; font-size: 22px; font-weight: bold; border-bottom: 1px solid #495057; padding-bottom: 10px; margin-bottom: 15px;}
.p-text { font-size: 16px; margin-bottom: 8px; color: #e9ecef; }
.highlight-diet { color: #20c997; font-weight: bold; }
.highlight-ex { color: #ff6b6b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ... [중간의 search_school, get_meal, parse_nutrition, calculate_score, get_dinner_prescription, get_activity_prescription, generate_ai_report_stream 함수는 이전과 동일하게 유지] ...

def search_school(keyword):
    try:
        url = f"https://open.neis.go.kr/hub/schoolInfo?Type=json&SCHUL_NM={urllib.parse.quote(keyword)}"
        if API_KEY and API_KEY != "여기에_API_KEY를_입력하세요": url += f"&KEY={API_KEY}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = data["schoolInfo"][1]["row"]
        return [{"name": r["SCHUL_NM"], "region": r["ATPT_OFCDC_SC_NM"], "edu_code": r["ATPT_OFCDC_SC_CODE"], "school_code": r["SD_SCHUL_CODE"]} for r in rows]
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

def calculate_score(nutrition):
    score = 100
    if nutrition.get("단백질", 0) < 20: score -= 15
    if nutrition.get("지방", 0) > 25: score -= 10
    if nutrition.get("탄수화물", 0) > 150: score -= 10
    return max(score, 0)

def get_dinner_prescription(nutrition):
    carb = nutrition.get("탄수화물", 0)
    prot = nutrition.get("단백질", 0)
    fat = nutrition.get("지방", 0)
    if carb > 120 or fat > 30: return {"menu": "연어 아보카도 샐러드 & 단호박 1/2개", "effect": "혈당 스파이크 진정 및 삼투압 복구", "reason": "정제 탄수화물과 나트륨 배출을 위해 칼륨과 오메가-3를 처방합니다."}
    elif prot < 20: return {"menu": "수비드 닭가슴살 퀴노아 덮밥", "effect": "근육 합성 대사 촉진", "reason": "필수 아미노산을 골든타임에 공급합니다."}
    else: return {"menu": "소고기 우둔살 구이 & 해조류 비빔밥", "effect": "에너지 평형 유지 및 철분 안정화", "reason": "낮 동안 이룩한 열평형 상태를 유지합니다."}

def get_activity_prescription(delta_kcal):
    if delta_kcal > 400: return {"exercise": "인터벌 러닝 20분", "effect": "심폐지구력 극대화", "reason": "고강도 처방입니다."}
    elif delta_kcal > 150: return {"exercise": "자전거 타기 30분", "effect": "하체 근력 강화", "reason": "효율적인 에너지 연소에 좋습니다."}
    else: return {"exercise": "전신 스트레칭", "effect": "체형 교정", "reason": "척추 교정에 집중합니다."}

def generate_ai_report_stream(food_name, score, leftover):
    report = f"👨‍⚕️ 분석 결과, '{food_name}'의 점수는 {score}점, 잔반은 {leftover}%입니다. "
    for word in report.split(): yield word + " "; time.sleep(0.01)

# ============================================================
# 메인 로직 (버튼 통합)
# ============================================================
st.markdown("<div class='main-title'>🍱 School Balance AI</div>", unsafe_allow_html=True)

with st.sidebar:
    user_weight = st.number_input("나의 몸무게 (kg)", value=50.0)
    leftover_rate = st.slider("잔반 비율 (%)", 0, 100, 0)
    mode = st.radio("모드", ["🏫 학교 급식", "🏠 자율 식단"])
    
    # 버튼 하나로 통합
    run_btn = st.button("🚀 통합 분석 시작", type="primary", use_container_width=True)
    
    if mode == "🏫 학교 급식":
        school_keyword = st.text_input("학교", "서현중학교")
        meal_date = st.date_input("날짜", datetime.date(2026, 7, 2))

# 실행 로직
if run_btn:
    # 데이터 수집 (상태 저장)
    if mode == "🏫 학교 급식":
        schools = search_school(school_keyword)
        if schools:
            target = schools[0]
            meal = get_meal(target["edu_code"], target["school_code"], meal_date.strftime("%Y%m%d"))
            if meal:
                st.session_state.current_data = {"name": f"{target['name']} 급식", "cal": float(re.search(r"[\d.]+", meal["calorie"]).group()) if re.search(r"[\d.]+", meal["calorie"]) else 0.0, "nutri": parse_nutrition(meal["nutrition"])}
            else: st.error("급식 정보 없음")
    else:
        # 자율 식단 로직
        st.session_state.current_data = {"name": "자율 식단", "cal": 700, "nutri": {"탄수화물": 80, "단백질": 20, "지방": 30}}

# 결과 출력 (데이터가 있을 때만)
if "current_data" in st.session_state and st.session_state.current_data:
    data = st.session_state.current_data
    score = calculate_score(data["nutri"])
    
    st.header("📊 분석 결과")
    st.metric("Health Score", f"{score}점")
    
    if st.button("✨ 상세 처방전 생성"):
        st.write_stream(generate_ai_report_stream(data["name"], score, leftover_rate))
        # 처방전 카드 출력 로직...
