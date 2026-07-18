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
# ★ API KEY 설정
# ============================================================
NEIS_API_KEY = "여기에_NEIS_API_KEY를_입력하세요"
GEMINI_API_KEY = "" 

# ============================================================
# CSS 스타일 설정
# ============================================================
st.markdown("""
<style>
.main-title{ font-size:42px; font-weight:bold; color:#2E8B57; }
.sub-title{ color:#666666; font-size:18px; margin-bottom: 20px;}
.food-card{ background:#F7F9FA; padding:12px; border-radius:12px; margin-bottom:8px; border-left:6px solid #2E8B57; }
.physics-card { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 25px; border-radius: 12px; margin-top: 20px; margin-bottom: 20px; }
.eco-card { background-color: #f1faee; border: 1px solid #a8dadc; padding: 25px; border-radius: 12px; margin-top: 20px; margin-bottom: 20px; }
.ai-report { background-color: #f1f8ff; padding: 20px; border-radius: 10px; border: 1px solid #cce5ff; font-size: 16px; line-height: 1.6; margin-bottom: 20px; }
.prescription-card { background-color: #2b3035; color: #ffffff; padding: 25px; border-radius: 12px; border-left: 8px solid #20c997; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-top: 10px; height: 100%;}
.prescription-title { color: #20c997; margin-top: 0; font-size: 22px; font-weight: bold; border-bottom: 1px solid #495057; padding-bottom: 10px; margin-bottom: 15px;}
.exercise-card { background-color: #2b3035; color: #ffffff; padding: 25px; border-radius: 12px; border-left: 8px solid #ff6b6b; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-top: 10px; height: 100%;}
.exercise-title { color: #ff6b6b; margin-top: 0; font-size: 22px; font-weight: bold; border-bottom: 1px solid #495057; padding-bottom: 10px; margin-bottom: 15px;}
.p-text { font-size: 16px; margin-bottom: 8px; color: #e9ecef; }
.highlight-diet { color: #20c997; font-weight: bold; }
.highlight-ex { color: #ff6b6b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🍱 School Balance AI Pro</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>생성형 AI + 영양 밸런스 + 물리 대사 + 기후 위기 통합 해결 솔루션</div>", unsafe_allow_html=True)
st.divider()

def search_school(keyword):
    try:
        url = f"[https://open.neis.go.kr/hub/schoolInfo?Type=json&SCHUL_NM=](https://open.neis.go.kr/hub/schoolInfo?Type=json&SCHUL_NM=){urllib.parse.quote(keyword)}"
        if NEIS_API_KEY and NEIS_API_KEY != "여기에_NEIS_API_KEY를_입력하세요": 
            url += f"&KEY={NEIS_API_KEY}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = data["schoolInfo"][1]["row"]
        return [{"name": r["SCHUL_NM"], "region": r["ATPT_OFCDC_SC_NM"], "edu_code": r["ATPT_OFCDC_SC_CODE"], "school_code": r["SD_SCHUL_CODE"]} for r in rows]
    except: 
        return []

def get_meal(edu_code, school_code, meal_date):
    try:
        url = f"[https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&ATPT_OFCDC_SC_CODE=](https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&ATPT_OFCDC_SC_CODE=){edu_code}&SD_SCHUL_CODE={school_code}&MLSV_YMD={meal_date}"
        if NEIS_API_KEY and NEIS_API_KEY != "여기에_NEIS_API_KEY를_입력하세요": 
            url += f"&KEY={NEIS_API_KEY}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        row = data["mealServiceDietInfo"][1]["row"][0]
        menu = [re.sub(r"[0-9\.\(\)]", "", food).strip() for food in row["DDISH_NM"].split("<br/>")]
        return {"menu": menu, "calorie": row["CAL_INFO"], "nutrition": row["NTR_INFO"]}
    except: 
        return None

def parse_nutrition(text):
    nutrition = {}
    if not text: return nutrition
    for item in text.split("<br/>"):
        if ":" in item:
            name, value = item.split(":", 1)
            name = re.sub(r"\(.*?\)", "", name).strip()
            match = re.search(r"[\d.]+", value)
            if match: nutrition[name] = float(match.group())
            else: nutrition[name] = 0.0
    return nutrition

def calculate_score(nutrition):
    score = 100
    if nutrition.get("단백질", 0) < 20: score -= 15
    if nutrition.get("지방", 0) > 25: score -= 10
    if nutrition.get("탄수화물", 0) > 150: score -= 10
    return max(score, 0)

# ============================================================
# ✨ 생성형 AI 대사 엔진
# ============================================================
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def clean_ai_json(text):
    """안전하게 AI가 준 텍스트에서 JSON 부분만 추출하는 헬퍼 함수"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def ai_parse_free_diet(user_food_text):
    if not GEMINI_API_KEY:
        total = {"calorie": 0.0, "탄수화물": 0.0, "단백질": 0.0, "지방": 0.0}
        food_db = {"라면": [500, 70, 10, 15], "마라탕": [800, 90, 20, 40], "불닭볶음면": [550, 80, 12, 18], "김밥": [450, 65, 12, 14], "치킨": [700, 20, 40, 35], "콜라": [150, 40, 0, 0]}
        for f in user_food_text.split(","):
            for name, v in food_db.items():
                if name in f.strip():
                    total["calorie"] += v[0]; total["탄수화물"] += v[1]; total["단백질"] += v[2]; total["지방"] += v[3]
        return total

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        사용자가 먹은 음식 리스트를 보고 총 칼로리(kcal), 탄수화물(g), 단백질(g), 지방(g)을 추정해줘.
        음식: {user_food_text}
        설명 없이 아래 양식의 순수한 JSON 객체 하나만 반환해.
        {{"calorie": 500, "탄수화물": 70, "단백질": 10, "지방": 15}}
        """
        response = model.generate_content(prompt)
        clean_text = clean_ai_json(response.text)
        return json.loads(clean_text)
    except Exception:
        return {"calorie": 550.0, "탄수화물": 75.0, "단백질": 12.0, "지방": 16.0}

def generate_super_ai_report(food_name, score, nutrition, leftover, weight, delta_kcal):
    if not GEMINI_API_KEY:
        report = f"👨‍⚕️ **[융합 과학 기반 생체 & 기후 대사 리포트]**\n\n오늘 섭취하신 **'{food_name}'**의 대사 밸런스 점수는 **{score}점**이며, 잔반 비율은 **{leftover}%**로 측정되었습니다. "
        report += "탄수화물과 지방 위주의 식단으로 혈당 스파이크가 우려됩니다. " if score < 90 else "매우 훌륭한 영양 밸런스입니다. "
        report += "또한 잔반이 많아 소각 시 대량의 온실가스가 발생합니다." if leftover > 20 else "잔반 제로 활동으로 탄소 배출 저감에 기여하셨습니다."
        for word in report.split():
            yield word + " "
            time.sleep(0.01)
        return

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        당신은 영양학, 운동생리학, 기후과학 전문 의사입니다. 
        [입력 데이터]
        - 식단명: {food_name}
        - 점수: {score}점
        - 상세: 탄수화물 {nutrition.get('탄수화물',0)}g, 단백질 {nutrition.get('단백질',0)}g, 지방 {nutrition.get('지방',0)}g
        - 잔반: {leftover}%
        - 잉여 에너지: {delta_kcal} kcal

        첫 줄은 "👨‍⚕️ **[AI 융합 과학 대사 분석 리포트]**"로 시작하고, 생체 대사와 환경(잔반) 영향을 250자 내외로 엮어 설명해.
        """
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            yield chunk.text
    except:
        yield "AI 리포트 생성 중 연결 오류가 발생했습니다. 하단의 분석 카드를 참고해 주세요."

def get_ai_prescriptions(nutrition, delta_kcal, leftover):
    if not GEMINI_API_KEY:
        carb = nutrition.get("탄수화물", 0); prot = nutrition.get("단백질", 0); fat = nutrition.get("지방", 0)
        if carb > 120 or fat > 30: diet = {"menu": "연어 아보카도 샐러드 & 단호박 1/2개", "effect": "혈당 스파이크 진정 및 삼투압 복구", "reason": "과다 섭취된 정제 탄수화물과 나트륨 배출을 위해 칼륨과 오메가-3를 처방합니다."}
        elif prot < 20: diet = {"menu": "수비드 닭가슴살 퀴노아 덮밥", "effect": "근육 합성 대사 촉진", "reason": "결핍된 필수 아미노산을 골든타임에 공급하여 수면 중 성장 호르몬 분비를 유도합니다."}
        else: diet = {"menu": "소고기 우둔살 구이 & 해조류 비빔밥", "effect": "에너지 평형 유지 및 철분 안정화", "reason": "낮 동안 이룩한 열평형 상태를 유지하며 부족하기 쉬운 미네랄을 보충합니다."}
        
        if delta_kcal > 400: ex = {"exercise": "인터벌 러닝 20분 + 버피 30개", "effect": "최대 산소 섭취량(VO2 max) 증가", "reason": "대량의 잉여 에너지를 최단 시간에 연소하고, 심폐 능력을 강제적으로 끌어올리는 고강도 처방입니다."}
        elif delta_kcal > 150: ex = {"exercise": "자전거 타기 30분 + 스쿼트 3세트", "effect": "하체 근력 강화 및 기초 대사량 증진", "reason": "관절에 무리를 주지 않으면서 가장 큰 근육을 사용하여 에너지를 효율적으로 태웁니다."}
        else: ex = {"exercise": "빠르게 걷기 30분 (파워워킹)", "effect": "혈류 순환 촉진 및 식후 인슐린 조절", "reason": "식후 인슐린 저항성을 낮추는 데 가장 효과적인 강도로 일상 활동량을 보완합니다."}
        return diet, ex

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        사용자 정보를 바탕으로 영양 처방과 운동 처방을 내려줘.
        탄수화물 {nutrition.get('탄수화물',0)}g, 단백질 {nutrition.get('단백질',0)}g, 지방 {nutrition.get('지방',0)}g
        잉여 칼로리: {delta_kcal} kcal

        아래 양식의 순수 JSON 텍스트 하나만 반환해.
        {{
            "diet_menu": "추천 식단명",
            "diet_effect": "생체 타겟 효과",
            "diet_reason": "처방 사유 1줄",
            "ex_name": "추천 운동명",
            "ex_effect": "대사 타겟 효과",
            "ex_reason": "운동 사유 1줄"
        }}
        """
        response = model.generate_content(prompt)
        clean_text = clean_ai_json(response.text)
        res = json.loads(clean_text)
        
        return (
            {"menu": res["diet_menu"], "effect": res["diet_effect"], "reason": res["diet_reason"]},
            {"exercise": res["ex_name"], "effect": res["ex_effect"], "reason": res["ex_reason"]}
        )
    except:
        return {"menu": "신선한 두부 샐러드", "effect": "혈당 완화", "reason": "균형 회복용"}, {"exercise": "가벼운 산책 30분", "effect": "지방 연소", "reason": "안전 대사율 확보"}

# ============================================================
# 세션 상태 초기화
# ============================================================
if "analyzed" not in st.session_state: st.session_state.analyzed = False
if "current_food_name" not in st.session_state: st.session_state.current_food_name = ""
if "current_score" not in st.session_state: st.session_state.current_score = 0
if "current_nutrition" not in st.session_state: st.session_state.current_nutrition = {}
if "current_cal" not in st.session_state: st.session_state.current_cal = 0.0
if "menu_list" not in st.session_state: st.session_state.menu_list = []

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.header("⚙️ 시스템 설정 및 입력")
    global_gemini_key = st.text_input("🔑 Gemini API KEY (선택)", value=GEMINI_API_KEY, type="password")
    if global_gemini_key:
        GEMINI_API_KEY = global_gemini_key
        genai.configure(api_key=GEMINI_API_KEY)
        
    st.divider()
    user_weight = st.number_input("나의 몸무게 (kg) - 생체역학용", min_value=30.0, max_value=120.0, value=50.0, step=1.0)
    
    st.markdown("**🌍 기후 위기 대응 (잔반율 데이터)**")
    leftover_rate = st.slider("오늘 잔반을 얼마나 남기셨나요? (%)", 0, 100, 0, step=5)
    st.caption("남겨진 식량이 소각될 때 소모되는 비열과 잠열, CO2 배출량을 역학적으로 추적합니다.")
    st.divider()
    
    mode = st.radio("급식 분석 모드 선택", ["🏫 학교 급식 (NEIS API)", "🏠 자율 식단 (Generative AI)"])
    st.divider()

    if mode == "🏫 학교 급식 (NEIS API)":
        school_keyword = st.text_input("학교 이름 검색", "서현중학교")
        meal_date = st.date_input("급식 타겟 날짜", datetime.date.today())
        meal_btn = st.button("🍱 통합 과학 분석 시작", use_container_width=True)
    else:
        user_food = st.text_area("오늘 먹은 음식 입력", "마라탕, 꿔바로우, 버블티")
        analyze_btn = st.button("🤖 AI 영양 소환 및 분석", use_container_width=True)

# ============================================================
# 데이터 연동 로직
# ============================================================
if mode == "🏫 학교 급식 (NEIS API)" and meal_btn:
    with st.spinner("데이터 동기화 중..."):
        schools = search_school(school_keyword)
        if schools:
            target = schools[0]
            meal = get_meal(target["edu_code"], target["school_code"], meal_date.strftime("%Y%m%d"))
            if meal:
                st.session_state.menu_list = meal["menu"]
                nutrition = parse_nutrition(meal["nutrition"])
                match = re.search(r"[\d.]+", meal["calorie"])
                st.session_state.current_cal = float(match.group()) if match else 0.0
                st.session_state.current_score = calculate_score(nutrition)
                st.session_state.current_food_name = f"{target['name']} 급식"
                st.session_state.current_nutrition = nutrition
                st.session_state.analyzed = True
            else: st.error("해당 날짜에 급식 데이터가 없습니다.")
        else: st.error("학교를 찾을 수 없습니다.")

elif mode == "🏠 자율 식단 (Generative AI)" and analyze_btn:
    with st.spinner("AI가 음식 데이터를 분석 중입니다..."):
        ai_data = ai_parse_free_diet(user_food)
        st.session_state.menu_list = [f.strip() for f in user_food.split(",")]
        st.session_state.current_cal = ai_data["calorie"]
        st.session_state.current_nutrition = {"탄수화물": ai_data.get("탄수화물", 0), "단백질": ai_data.get("단백질", 0), "지방": ai_data.get("지방", 0)}
        st.session_state.current_score = calculate_score(st.session_state.current_nutrition)
        st.session_state.current_food_name = user_food
        st.session_state.analyzed = True

# ============================================================
# 대시보드 출력
# ============================================================
if st.session_state.analyzed:
    st.success(f"✅ [{st.session_state.current_food_name}] 분석 완료")
    if mode == "🏫 학교 급식 (NEIS API)":
        st.markdown(" ".join([f"`{f}`" for f in st.session_state.menu_list]))
        
    st.header("📊 기초 영양 지표")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💯 Health Score", f"{st.session_state.current_score}점")
    c2.metric("제공된 총 칼로리", f"{st.session_state.current_cal:.1f} kcal")
    c3.metric("탄수화물", f"{st.session_state.current_nutrition.get('탄수화물', 0):.1f}g")
    c4.metric("지방", f"{st.session_state.current_nutrition.get('지방', 0):.1f}g")
    st.progress(st.session_state.current_score / 100)

    st.markdown("---")
    st.header("🔬 융합 과학: 인체 에너지 & 기후 위기 동시 해결 시뮬레이션")
    
    if st.button("✨ 초고속 AI 통합 시뮬레이션 가동", type="primary"):
        with st.container():
            actual_cal = st.session_state.current_cal * (1 - leftover_rate/100)
            estimated_bmr = 600
            delta_e_kcal = actual_cal - estimated_bmr
            
            st.markdown('<div class="ai-report">', unsafe_allow_html=True)
            st.write_stream(generate_super_ai_report(
                st.session_state.current_food_name, 
                st.session_state.current_score, 
                st.session_state.current_nutrition, 
                leftover_rate, 
                user_weight,
                delta_e_kcal
            ))
            st.markdown('</div>', unsafe_allow_html=True)
            
            col_phys, col_eco = st.columns(2)
            
            with col_phys:
                st.markdown('<div class="physics-card">', unsafe_allow_html=True)
                st.subheader("🏃 인체 에너지 열평형")
                st.latex(r"W = \Delta E_p = m \cdot g \cdot h")
                
                if delta_e_kcal > 0:
                    surplus_joules = delta_e_kcal * 4184
                    g, step_height = 9.8, 0.2
                    work_per_step = user_weight * g * step_height
                    steps_needed = int(surplus_joules / work_per_step)
                    
                    st.error(f"🚨 **생체 열평형 붕괴:** {delta_e_kcal:.1f} kcal 잉여 검출")
                    st.info(f"💡 복구를 위해 약 **{steps_needed:,}개의 계단**을 올라야 합니다.")
                else:
                    st.success("✅ 완벽한 인체 열역학적 평형 상태입니다.")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_eco:
                st.markdown('<div class="eco-card">', unsafe_allow_html=True)
                st.subheader("🌍 잔반 소각 열역학 (Eco-Thermo)")
                st.latex(r"Q = c \cdot m \cdot \Delta T + L \cdot m")
                
                wasted_mass_kg = 0.6 * (leftover_rate / 100)
                
                if leftover_rate > 0:
                    heat_wasted_kj = wasted_mass_kg * 4.18 * 80 + wasted_mass_kg * 2260
                    co2_emission = wasted_mass_kg * 1.58
                    
                    st.error(f"🚨 **기후 자원 손실 경고**")
                    st.write(f"- **소각 대상 잔반량:** {wasted_mass_kg*1000:.0f} g")
                    st.write(f"- **소각 낭비 열량:** {heat_wasted_kj:,.0f} kJ")
                    st.info(f"💡 대기 중으로 **{co2_emission:.2f} kg의 $CO_2$**가 누적됩니다.")
                else:
                    st.success("🎉 **Zero Waste 달성!** 쓰레기 처리에 사용될 에너지를 절약했습니다.")
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown("### 🧾 최종 융합 과학 처방전 발급")
            col_diet, col_ex = st.columns(2)
            
            diet_plan, ex_plan = get_ai_prescriptions(st.session_state.current_nutrition, delta_e_kcal, leftover_rate)
            
            with col_diet:
                st.markdown(f"""
                <div class="prescription-card">
                    <div class="prescription-title">🍽️ 영양 복구 처방전</div>
                    <p class="p-text">💡 <b>저녁 메뉴:</b> <span class="highlight-diet">{diet_plan['menu']}</span></p>
                    <p class="p-text">🧬 <b>생체 효과:</b> {diet_plan['effect']}</p>
                    <hr style="border: 0; border-top: 1px dashed #6c757d; margin: 15px 0;">
                    <p class="p-text" style="font-size: 14px; color: #adb5bd;"><b>AI 소견:</b> {diet_plan['reason']}</p>
                </div>
                """, unsafe_allow_html=True)

            with col_ex:
                st.markdown(f"""
                <div class="exercise-card">
                    <div class="exercise-title">🏃‍♂️ 기초 체력 증진 처방전</div>
                    <p class="p-text">🔥 <b>추천 활동:</b> <span class="highlight-ex">{ex_plan['exercise']}</span></p>
                    <p class="p-text">💪 <b>대사 효과:</b> {ex_plan['effect']}</p>
                    <hr style="border: 0; border-top: 1px dashed #6c757d; margin: 15px 0;">
                    <p class="p-text" style="font-size: 14px; color: #adb5bd;"><b>AI 소견:</b> {ex_plan['reason']}</p>
                </div>
                """, unsafe_allow_html=True)
