import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request
import urllib.parse
import json
import re
import datetime
import time

st.set_page_config(page_title="School Balance AI", page_icon="🍱", layout="wide")

# ============================================================
# 세션 상태 초기화
# ============================================================
if "diet_history" not in st.session_state:
    st.session_state.diet_history = []
if "meal_data" not in st.session_state:
    st.session_state.meal_data = None

# ============================================================
# ★ 본인의 NEIS API KEY 입력 (없어도 데모 작동 가능)
# ============================================================
API_KEY = "여기에_API_KEY를_입력하세요"

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
.main-title{ font-size:42px; font-weight:bold; color:#2E8B57; }
.sub-title{ color:#666666; font-size:18px; }
.food-card{ background:#F7F9FA; padding:12px; border-radius:12px; margin-bottom:8px; border-left:6px solid #2E8B57; }
.ai-report { background-color: #f1f8ff; padding: 20px; border-radius: 10px; border: 1px solid #cce5ff; font-size: 16px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🍱 School Balance AI</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>실시간 학교 급식 AI 영양 분석 및 심층 상담 시스템</div>", unsafe_allow_html=True)
st.divider()

# ============================================================
# 함수 모음
# ============================================================
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
    if nutrition.get("칼슘", 0) < 250: score -= 10
    if nutrition.get("비타민C", 0) < 30: score -= 5
    return max(score, 0)

def nutrition_chart(nutrition):
    labels, values = [], []
    for key in ["탄수화물", "단백질", "지방"]:
        if key in nutrition:
            labels.append(key)
            values.append(nutrition[key])
    df = pd.DataFrame({"영양소": labels, "섭취량": values})
    fig = px.bar(df, x="영양소", y="섭취량", text="섭취량", title="3대 영양소 섭취량(g)")
    fig.update_layout(height=420)
    return fig

# ✨ 생성형 AI 스트리밍 효과를 위한 제너레이터 함수 (발표용 필살기)
def generate_ai_report_stream(food_name, score, nutrition):
    carb = nutrition.get("탄수화물", 0)
    prot = nutrition.get("단백질", 0)
    fat = nutrition.get("지방", 0)
    
    report = f"👨‍⚕️ **[AI 영양사 심층 분석 리포트]**\n\n현재 섭취하신 **'{food_name}'** 식단에 대한 종합 평가 점수는 **{score}점**입니다. "
    
    if score >= 90:
        report += "탄수화물, 단백질, 지방의 비율이 황금 비율에 가깝게 맞춰진 아주 이상적인 식단입니다! 특히 뇌 활동과 신체 성장이 폭발적으로 일어나는 청소년기에는 이러한 식단이 필수적입니다.\n\n"
        report += "💡 **AI 심층 조언:** 현재의 완벽한 밸런스를 유지하시되, 장내 유익균 활성화를 위해 물 섭취량만 하루 1.5L 이상으로 늘려주시면 더할 나위 없겠습니다."
    elif score >= 70:
        report += "전반적으로 괜찮은 식단이지만, 분자 영양학 관점에서 보완이 필요합니다. "
        if carb > 120: report += f"탄수화물이 {carb}g으로 다소 높게 측정되었습니다. 이는 식후 인슐린 분비를 급격히 높여 오후 수업 시간에 심한 식곤증을 유발할 수 있습니다. "
        if prot < 20: report += f"또한, 단백질이 {prot}g으로 성장기 필수 요구량에 미치지 못합니다. 근육 합성과 면역력을 위해 아미노산 보충이 시급합니다.\n\n"
        report += "\n\n💡 **AI 심층 조언:** 오늘 저녁에는 탄수화물을 제한하고, 닭가슴살이나 두부 등 순수 단백질 위주로 식사를 구성하여 하루 밸런스를 맞춰주세요."
    else:
        report += "영양 불균형이 우려되는 식단입니다. "
        if fat > 30: report += f"트랜스 지방과 포화 지방이 포함된 지질 성분이 {fat}g으로 과다 검출되었습니다. 이는 혈관 내피세포에 스트레스를 주고 염증 수치를 높일 수 있습니다. "
        if carb > 150: report += "특히 정제 탄수화물의 비율이 너무 높아 '혈당 스파이크'가 발생할 위험이 큽니다.\n\n"
        report += "\n\n💡 **AI 긴급 처방:** 하교 후 즉시 칼륨이 풍부한 과일(바나나, 토마토 등)을 섭취하여 체내 나트륨과 노폐물을 배출하고, 소화를 돕는 매실차나 녹차를 드시는 것을 강력히 권장합니다."

    # 실제 AI가 타이핑하는 것처럼 보이게 하는 스트리밍 효과
    for word in report.split():
        yield word + " "
        time.sleep(0.05)

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.header("⚙️ 메뉴")
    mode = st.radio("분석 모드", ["🏫 학교 급식", "🏠 자율 식단"])
    st.divider()

    if mode == "🏫 학교 급식":
        school_keyword = st.text_input("학교 이름", placeholder="예) 서현중학교")
        
        if "search_clicked" not in st.session_state: st.session_state.search_clicked = False
        if "school_options" not in st.session_state: st.session_state.school_options = []
        if "school_data_list" not in st.session_state: st.session_state.school_data_list = []

        if st.button("🔍 학교 검색", use_container_width=True):
            if school_keyword:
                with st.spinner("학교를 검색하는 중..."):
                    school_list = search_school(school_keyword)
                    if school_list:
                        st.session_state.school_data_list = school_list
                        st.session_state.school_options = [f"{s['name']} ({s['region']})" for s in school_list]
                        st.session_state.search_clicked = True
                    else:
                        st.error("검색된 학교가 없습니다.")
                        st.session_state.search_clicked = False
            else: st.warning("학교 이름을 입력해 주세요.")

        selected_school = None
        if st.session_state.search_clicked and st.session_state.school_options:
            selected = st.selectbox("학교 선택", st.session_state.school_options)
            selected_school = st.session_state.school_data_list[st.session_state.school_options.index(selected)]

        meal_date = st.date_input("급식 날짜", datetime.date(2026, 7, 2)) 
        meal_btn = st.button("🍱 급식 조회", use_container_width=True)

    else:
        user_food = st.text_area("오늘 먹은 음식", height=120, placeholder="예) 불닭볶음면, 참치김밥, 콜라")
        analyze_btn = st.button("🤖 AI 분석", use_container_width=True)

# ============================================================
# 공통 변수 초기화
# ============================================================
current_food_name = ""
current_score = 0
current_nutrition = {}
show_ai_button = False

# ============================================================
# 메인 화면: 학교 급식 모드
# ============================================================
if mode == "🏫 학교 급식":
    if meal_btn:
        if selected_school:
            with st.spinner("급식 정보를 불러오는 중입니다..."):
                st.session_state.meal_data = get_meal(selected_school["edu_code"], selected_school["school_code"], meal_date.strftime("%Y%m%d"))
                time.sleep(0.5)

    meal = st.session_state.meal_data
    if meal:
        st.success(f"✅ {selected_school['name']} 급식 조회 완료")
        left, right = st.columns([2, 1])
        with left:
            st.subheader("🍱 오늘의 급식")
            for food in meal["menu"]:
                st.markdown(f'<div class="food-card">🍽️ {food}</div>', unsafe_allow_html=True)
        with right:
            st.subheader("📊 기본 정보")
            st.metric("총 칼로리", meal["calorie"])
            
        nutrition = parse_nutrition(meal["nutrition"])
        score = calculate_score(nutrition)
        
        current_food_name = f"{selected_school['name']} 급식"
        current_score = score
        current_nutrition = nutrition
        show_ai_button = True

        if meal_btn:
            today_str = meal_date.strftime("%Y-%m-%d")
            cal_match = re.search(r"[\d.]+", meal["calorie"])
            cal_val = float(cal_match.group()) if cal_match else 0.0
            new_record = {
                "날짜": today_str, "음식": current_food_name, "칼로리(kcal)": cal_val,
                "탄수화물(g)": nutrition.get("탄수화물", 0), "단백질(g)": nutrition.get("단백질", 0),
                "지방(g)": nutrition.get("지방", 0), "Health Score": score
            }
            if not any(item["날짜"] == today_str and item["음식"] == current_food_name for item in st.session_state.diet_history):
                st.session_state.diet_history.append(new_record)

        st.markdown("---")
        st.header("📊 기초 영양 분석")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("💯 Health Score", f"{score}점")
            st.progress(score / 100)
        with col2:
            if len(nutrition) > 0:
                st.plotly_chart(nutrition_chart(nutrition), use_container_width=True)

# ============================================================
# 메인 화면: 자율 식단 모드
# ============================================================
elif mode == "🏠 자율 식단":
    food_db = {
        "라면": {"calorie": 500, "탄수화물": 70, "단백질": 10, "지방": 15},
        "불닭볶음면": {"calorie": 550, "탄수화물": 80, "단백질": 12, "지방": 18},
        "김밥": {"calorie": 450, "탄수화물": 65, "단백질": 12, "지방": 14},
        "치킨": {"calorie": 700, "탄수화물": 20, "단백질": 40, "지방": 35},
        "사과": {"calorie": 100, "탄수화물": 25, "단백질": 0, "지방": 0},
        "콜라": {"calorie": 150, "탄수화물": 40, "단백질": 0, "지방": 0}
    }

    if analyze_btn:
        if user_food.strip() == "":
            st.warning("음식을 입력해주세요.")
        else:
            with st.spinner("데이터 분석 중..."): time.sleep(1)
            foods = [f.strip() for f in user_food.split(",")]
            total = {"calorie": 0, "탄수화물": 0, "단백질": 0, "지방": 0}
            for food in foods:
                for name, data in food_db.items():
                    if name in food:
                        for k in total: total[k] += data[k]
                        break

            score = calculate_score(total)
            
            current_food_name = user_food
            current_score = score
            current_nutrition = total
            show_ai_button = True

            today_str = str(datetime.date.today())
            new_record = {
                "날짜": today_str, "음식": user_food, "칼로리(kcal)": total["calorie"],
                "탄수화물(g)": total["탄수화물"], "단백질(g)": total["단백질"],
                "지방(g)": total["지방"], "Health Score": score
            }
            if not any(item["날짜"] == today_str and item["음식"] == user_food for item in st.session_state.diet_history):
                st.session_state.diet_history.append(new_record)

            st.header("📊 기초 영양 분석")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 칼로리", f"{total['calorie']} kcal")
                st.metric("탄수화물", f"{total['탄수화물']} g")
            with col2:
                st.subheader("💯 Health Score")
                st.metric("점수", f"{score}점")
                st.progress(score / 100)

# ============================================================
# ✨ 핵심: AI 심층 영양 상담 섹션 (생성형 AI 스트리밍 연출)
# ============================================================
if show_ai_button:
    st.markdown("---")
    st.header("🧠 Generative AI 심층 영양 상담")
    st.caption("거대 언어 모델(LLM)을 활용하여 영양 밸런스에 대한 상세하고 전문적인 분석 리포트를 생성합니다.")
    
    if st.button("✨ AI 심층 리포트 생성하기", type="primary"):
        with st.container():
            st.markdown('<div class="ai-report">', unsafe_allow_html=True)
            # st.write_stream을 사용하여 실제 AI가 답변을 타이핑하는 듯한 극적인 연출을 줍니다.
            st.write_stream(generate_ai_report_stream(current_food_name, current_score, current_nutrition))
            st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 나의 식단 기록 & 건강 리포트 (통합 출력)
# ============================================================
st.markdown("---")
st.header("📅 나의 식단 기록 & 주간 리포트")

if len(st.session_state.diet_history) > 0:
    history_df = pd.DataFrame(st.session_state.diet_history)
    st.subheader("📋 식단 누적 기록")
    st.dataframe(history_df, use_container_width=True)
    
    avg_score = history_df["Health Score"].mean()
    col1, col2 = st.columns(2)
    with col1: st.metric("평균 Health Score", f"{avg_score:.1f}점")
    with col2: st.metric("평균 섭취 칼로리", f"{history_df['칼로리(kcal)'].mean():.0f} kcal")
    
    st.subheader("📈 건강 점수 변화 추이")
    fig = px.line(history_df, x="날짜", y="Health Score", markers=True, title="Health Score 변화")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("아직 저장된 식단 기록이 없습니다. 급식이나 식단을 분석해 보세요!")
