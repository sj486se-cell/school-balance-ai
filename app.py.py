import streamlit as st
import urllib.request
import urllib.parse
import json
import re
import datetime
import time

st.set_page_config(page_title="School Balance AI", page_icon="🍱", layout="wide")

# ============================================================
# ★ 본인의 NEIS API KEY 입력
# ============================================================
API_KEY = "여기에_API_KEY를_입력하세요"

# ============================================================
# CSS
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

st.markdown("<div class='main-title'>🍱 School Balance AI</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>열역학 기반 영양 밸런스 및 기초 체력 증진 더블 처방 시스템</div>", unsafe_allow_html=True)
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
    return max(score, 0)

# 식단 처방 알고리즘
def get_dinner_prescription(nutrition):
    carb = nutrition.get("탄수화물", 0)
    prot = nutrition.get("단백질", 0)
    fat = nutrition.get("지방", 0)
    
    if carb > 120 or fat > 30:
        return {"menu": "연어 아보카도 샐러드 & 단호박 1/2개", "effect": "혈당 스파이크 진정 및 삼투압 복구", "reason": "과다 섭취된 정제 탄수화물과 나트륨 배출을 위해 칼륨과 오메가-3를 처방합니다."}
    elif prot < 20:
        return {"menu": "수비드 닭가슴살 퀴노아 덮밥", "effect": "근육 합성 대사 촉진", "reason": "결핍된 필수 아미노산을 골든타임에 공급하여 수면 중 성장 호르몬 분비를 유도합니다."}
    else:
        return {"menu": "소고기 우둔살 구이 & 해조류 비빔밥", "effect": "에너지 평형 유지 및 철분 안정화", "reason": "낮 동안 이룩한 열평형 상태를 유지하며 부족하기 쉬운 미네랄을 보충합니다."}

# ✨ [신규] 체력 증진 및 활동량 처방 알고리즘
def get_activity_prescription(delta_kcal):
    if delta_kcal > 400:
        return {"exercise": "인터벌 러닝 20분 + 버피 30개", "effect": "최대 산소 섭취량(VO2 max) 증가 및 심폐지구력 극대화", "reason": "대량의 잉여 에너지를 최단 시간에 연소하고, 기초 체력의 핵심인 심폐 능력을 강제적으로 끌어올리는 고강도 처방입니다."}
    elif delta_kcal > 150:
        return {"exercise": "자전거 타기 30분 + 스쿼트 3세트", "effect": "하체 근력(대퇴사두근) 강화 및 기초 대사량 증진", "reason": "관절에 무리를 주지 않으면서 가장 큰 근육을 사용하여 에너지를 효율적으로 태우고 활동량을 채웁니다."}
    elif delta_kcal > 0:
        return {"exercise": "빠르게 걷기 30분 (파워워킹)", "effect": "생활 속 활동량 증가 및 혈류 순환 촉진", "reason": "일상적인 활동량 부족을 보완하며, 식후 인슐린 저항성을 낮추는 데 가장 효과적인 강도입니다."}
    else:
        return {"exercise": "가벼운 전신 스트레칭 및 코어(플랭크)", "effect": "체형 교정 및 코어 근육 안정화", "reason": "이미 열평형이 맞으므로, 과도한 유산소보다는 앉아있는 시간이 긴 학생들을 위한 척추 교정에 집중합니다."}

def generate_ai_report_stream(food_name, score):
    report = f"👨‍⚕️ **[융합 과학 기반 생체 대사 예측]**\n\n분석 결과, 섭취하신 **'{food_name}'**의 영양·대사 밸런스 점수는 **{score}점**입니다. "
    if score >= 90:
        report += "황금 비율에 가까운 식단으로, 신진대사가 최적화되어 에너지가 효율적으로 연소되는 훌륭한 상태입니다."
    else:
        report += "고탄수화물 및 고칼로리로 인해 혈액 내 포도당 농도가 급상승하고 있습니다. 세포 내 삼투압 불균형 및 잉여 지방 축적이 우려되므로, 하단의 '식단 해독'과 '기초 체력 증진' 더블 처방을 반드시 병행하십시오."
    for word in report.split():
        yield word + " "
        time.sleep(0.05)

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.header("⚙️ 기초 정보 입력")
    user_weight = st.number_input("나의 몸무게 (kg) - 활동량 계산용", min_value=30.0, max_value=120.0, value=50.0, step=1.0)
    st.divider()
    
    mode = st.radio("분석 모드", ["🏫 학교 급식", "🏠 자율 식단"])
    st.divider()

    if mode == "🏫 학교 급식":
        school_keyword = st.text_input("학교 검색", "서현중학교")
        meal_date = st.date_input("급식 날짜", datetime.date(2026, 7, 2)) 
        meal_btn = st.button("🍱 급식 조회", use_container_width=True)
    else:
        user_food = st.text_area("오늘 먹은 음식", "불닭볶음면, 참치김밥, 콜라")
        analyze_btn = st.button("🤖 AI 분석", use_container_width=True)

# ============================================================
# 공통 변수 
# ============================================================
current_food_name = ""
current_score = 0
current_nutrition = {}
current_cal = 0.0
show_ai_button = False

# ============================================================
# 데이터 수집 
# ============================================================
if mode == "🏫 학교 급식" and meal_btn:
    with st.spinner("급식 데이터 분석 중..."):
        schools = search_school(school_keyword)
        if schools:
            target = schools[0]
            meal = get_meal(target["edu_code"], target["school_code"], meal_date.strftime("%Y%m%d"))
            if meal:
                st.success(f"✅ {target['name']} 데이터 연동 완료")
                st.markdown(" ".join([f"`{f}`" for f in meal["menu"]]))
                nutrition = parse_nutrition(meal["nutrition"])
                current_cal = float(re.search(r"[\d.]+", meal["calorie"]).group()) if re.search(r"[\d.]+", meal["calorie"]) else 0.0
                current_score = calculate_score(nutrition)
                current_food_name = f"{target['name']} 급식"
                current_nutrition = nutrition
                show_ai_button = True
        else: st.error("학교를 찾을 수 없습니다.")

elif mode == "🏠 자율 식단" and analyze_btn:
    food_db = {
        "라면": {"calorie": 500, "탄수화물": 70, "단백질": 10, "지방": 15},
        "마라탕": {"calorie": 800, "탄수화물": 90, "단백질": 20, "지방": 40},
        "불닭볶음면": {"calorie": 550, "탄수화물": 80, "단백질": 12, "지방": 18},
        "김밥": {"calorie": 450, "탄수화물": 65, "단백질": 12, "지방": 14},
        "치킨": {"calorie": 700, "탄수화물": 20, "단백질": 40, "지방": 35},
        "콜라": {"calorie": 150, "탄수화물": 40, "단백질": 0, "지방": 0}
    }
    with st.spinner("생체 데이터 분석 중..."): time.sleep(1)
    foods = [f.strip() for f in user_food.split(",")]
    total = {"calorie": 0, "탄수화물": 0, "단백질": 0, "지방": 0}
    for food in foods:
        for name, data in food_db.items():
            if name in food:
                for k in total: total[k] += data[k]
                break
    current_cal = total["calorie"]
    current_score = calculate_score(total)
    current_food_name = user_food
    current_nutrition = total
    show_ai_button = True

# ============================================================
# 메인 분석 리포트
# ============================================================
if show_ai_button:
    st.header("📊 기초 영양 지표")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💯 Health Score", f"{current_score}점")
    c2.metric("총 섭취 칼로리", f"{current_cal} kcal")
    c3.metric("탄수화물", f"{current_nutrition.get('탄수화물', 0)}g")
    c4.metric("지방", f"{current_nutrition.get('지방', 0)}g")
    st.progress(current_score / 100)

    st.markdown("---")
    st.header("🔬 융합 과학: 식습관 & 체력 더블 처방 시스템")
    st.caption("섭취 에너지를 물리학적 '일(Work)'로 환산하여 활동량 부족을 해결하고, 분자 영양학 기반 식단을 동시에 처방합니다.")
    
    if st.button("✨ 체내 열평형 시뮬레이션 및 처방받기", type="primary"):
        with st.container():
            # 1. AI 텍스트 리포트
            st.markdown('<div class="ai-report">', unsafe_allow_html=True)
            st.write_stream(generate_ai_report_stream(current_food_name, current_score))
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 2. 물리(역학적 에너지) 시뮬레이션 UI
            st.markdown('<div class="physics-card">', unsafe_allow_html=True)
            st.subheader("🔥 역학적 에너지 변환 시뮬레이터")
            
            st.latex(r"1 \text{ kcal} = 4,184 \text{ Joules} \quad | \quad \text{Work } (W) = \Delta E_p = m \cdot g \cdot h")
            
            estimated_bmr = 600 
            delta_e_kcal = current_cal - estimated_bmr
            
            if delta_e_kcal > 0:
                surplus_joules = delta_e_kcal * 4184
                g = 9.8 
                step_height = 0.2 
                work_per_step = user_weight * g * step_height 
                steps_needed = int(surplus_joules / work_per_step)
                
                st.error(f"🚨 **열평형 상태 붕괴:** {delta_e_kcal:.1f} kcal의 잉여 에너지가 발생했습니다.")
                pc1, pc2, pc3 = st.columns(3)
                pc1.metric("잉여 열에너지 ($\Delta E$)", f"{delta_e_kcal:.1f} kcal")
                pc2.metric("변환된 역학 에너지 ($W$)", f"{surplus_joules:,.0f} J")
                pc3.metric("물리적 극복치 (계단)", f"{steps_needed:,} 계단", delta="중력 퍼텐셜 에너지 극복", delta_color="inverse")
                
                st.info(f"💡 {user_weight}kg의 질량을 가진 사용자가 중력을 극복하고 {surplus_joules:,.0f}J의 일을 수행하려면, 약 **{steps_needed:,}개의 계단**을 올라야 완벽한 열평형을 이룰 수 있습니다. 이를 현실적인 활동량으로 변환하여 처방합니다.")
            else:
                st.success("✅ **완벽한 열평형:** 잉여 에너지가 발생하지 않았습니다.")
                st.latex(r"\Delta E \approx 0 \quad \text{(열역학적 평형 상태)}")
                
            st.markdown('</div>', unsafe_allow_html=True)
            time.sleep(0.5)
            
            # 3. ✨ [눈길을 사로잡는 더블 처방전 카드 UI]
            col_diet, col_ex = st.columns(2)
            
            # (1) 식습관 개선 처방전 (영양학)
            diet_plan = get_dinner_prescription(current_nutrition)
            with col_diet:
                st.markdown(f"""
                <div class="prescription-card">
                    <div class="prescription-title">🧾 영양 밸런스 복구 처방전</div>
                    <p class="p-text">🍽️ <b>저녁 추천 메뉴:</b> <span class="highlight-diet">{diet_plan['menu']}</span></p>
                    <p class="p-text">🧬 <b>타겟 효과:</b> {diet_plan['effect']}</p>
                    <hr style="border: 0; border-top: 1px dashed #6c757d; margin: 15px 0;">
                    <p class="p-text" style="font-size: 14px; color: #adb5bd;">💡 <b>AI 사유:</b> {diet_plan['reason']}</p>
                </div>
                """, unsafe_allow_html=True)

            # (2) 기초 체력 증진 처방전 (물리학/체육학)
            ex_plan = get_activity_prescription(delta_e_kcal)
            with col_ex:
                st.markdown(f"""
                <div class="exercise-card">
                    <div class="exercise-title">🏃‍♂️ 기초 체력 증진 처방전</div>
                    <p class="p-text">🔥 <b>필요 활동량:</b> <span class="highlight-ex">{ex_plan['exercise']}</span></p>
                    <p class="p-text">💪 <b>타겟 효과:</b> {ex_plan['effect']}</p>
                    <hr style="border: 0; border-top: 1px dashed #6c757d; margin: 15px 0;">
                    <p class="p-text" style="font-size: 14px; color: #adb5bd;">💡 <b>AI 사유:</b> {ex_plan['reason']}</p>
                </div>
                """, unsafe_allow_html=True)
