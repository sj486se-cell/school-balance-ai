import streamlit as st
import urllib.request
import urllib.parse
import json
import re
import datetime
import time
from openai import OpenAI  # OpenAI 라이브러리 추가

st.set_page_config(page_title="School Balance AI", page_icon="🍱", layout="wide")

# ============================================================
# ★ API KEY 입력 설정
# ============================================================
NEIS_API_KEY = "여기에_NEIS_API_KEY를_입력하세요"
OPENAI_API_KEY = "sk-proj-a1b2c3d4e5f6g7h8..."  # 실제 본인의 API 키 입력 (sk- 로 시작함)
# OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

# ============================================================
# CSS 스타일링
# ============================================================
st.markdown("""
<style>
.main-title{ font-size:42px; font-weight:bold; color:#2E8B57; }
.sub-title{ color:#666666; font-size:18px; margin-bottom: 20px;}
.ai-report { background-color: #f1f8ff; padding: 20px; border-radius: 10px; border: 1px solid #cce5ff; font-size: 16px; line-height: 1.6; margin-bottom: 20px; }
.physics-card { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 25px; border-radius: 12px; margin-top: 20px; margin-bottom: 20px; }
.eco-card { background-color: #f1faee; border: 1px solid #a8dadc; padding: 25px; border-radius: 12px; margin-top: 20px; margin-bottom: 20px; }
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
st.markdown("<div class='sub-title'>영양 밸런스 + 기초 체력 + 기후 위기(잔반) 통합 해결 AI 솔루션</div>", unsafe_allow_html=True)
st.divider()

# ============================================================
# 핵심 로직 함수 모음
# ============================================================
def search_school(keyword):
    try:
        url = f"https://open.neis.go.kr/hub/schoolInfo?Type=json&SCHUL_NM={urllib.parse.quote(keyword)}"
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
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&ATPT_OFCDC_SC_CODE={edu_code}&SD_SCHUL_CODE={school_code}&MLSV_YMD={meal_date}"
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
            if match:
                nutrition[name] = float(match.group())
            else:
                nutrition[name] = 0.0
    return nutrition

def calculate_score(nutrition):
    score = 100
    if nutrition.get("단백질", 0) < 20: score -= 15
    if nutrition.get("지방", 0) > 25: score -= 10
    if nutrition.get("탄수화물", 0) > 150: score -= 10
    return max(score, 0)

# 🌟 [AI 연동 핵심] OpenAI API를 사용하여 실시간 스트리밍 답변을 생성하는 함수
def generate_ai_report_stream(food_name, score, calorie, nutrition, leftover):
    prompt = f"""
    당신은 영양학, 열역학, 기후위기 전문가인 '생체 & 기후 대사 AI 의사'입니다.
    다음 제공된 데이터를 바탕으로 학생에게 전달할 융합 과학 기반 리포트를 작성해 주세요.
    
    [식단 데이터]
    - 음식 명칭: {food_name}
    - 섭취 칼로리: {calorie} kcal
    - 영양 성분 정보: {json.dumps(nutrition, ensure_ascii=False)}
    - 자체 영양 점수: {score}점 (100점 만점)
    - 사용자가 남긴 잔반 비율: {leftover}%
    
    [작성 가이드라인]
    1. 친절하면서도 전문적인 의사 어조(예: "~입니다", "~를 추천합니다")를 사용하세요.
    2. 영양 성분(탄수화물, 단백질, 지방)의 비율이 인체 대사(혈당 스파이크, 근육 합성 등)에 미치는 영향을 과학적으로 짚어주세요.
    3. 잔반 비율({leftover}%)에 따른 환경적 영향(탄소 배출, 소각 에너지)을 경고하거나 칭찬해 주세요. (0%면 극찬, 높으면 경고)
    4. 너무 길지 않게 핵심만 3~4문장 내외로 요약해 주세요. 이모지를 적절히 섞어주세요.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 가성비가 좋고 빠른 gpt-4o-mini 모델 활용
            messages=[
                {"role": "system", "content": "너는 영양학 및 기후 대사 과학 고문이야."},
                {"role": "user", "content": prompt}
            ],
            stream=True # 스트리밍 활성화
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"⚠️ AI 로드 중 오류가 발생했습니다: {str(e)}"

# 저녁 처방 수식 로직
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

# 운동 처방 수식 로직
def get_activity_prescription(delta_kcal):
    if delta_kcal > 400:
        return {"exercise": "인터벌 러닝 20분 + 버피 30개", "effect": "최대 산소 섭취량(VO2 max) 증가", "reason": "대량의 잉여 에너지를 최단 시간에 연소하고, 심폐 능력을 강제적으로 끌어올리는 고강도 처방입니다."}
    elif delta_kcal > 150:
        return {"exercise": "자전거 타기 30분 + 스쿼트 3세트", "effect": "하체 근력 강화 및 기초 대사량 증진", "reason": "관절에 무리를 주지 않으면서 가장 큰 근육을 사용하여 에너지를 효율적으로 태웁니다."}
    elif delta_kcal > 0:
        return {"exercise": "빠르게 걷기 30분 (파워워킹)", "effect": "혈류 순환 촉진 및 식후 인슐린 조절", "reason": "식후 인슐린 저항성을 낮추는 데 가장 효과적인 강도로 일상 활동량을 보완합니다."}
    else:
        return {"exercise": "전신 스트레칭 및 코어(플랭크)", "effect": "체형 교정 및 코어 근육 안정화", "reason": "이미 열평형이 맞으므로, 학생들을 위한 척추 교정 및 자세 교정에 집중합니다."}


# ============================================================
# 세션 상태(Session State) 초기화
# ============================================================
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
if "current_food_name" not in st.session_state:
    st.session_state.current_food_name = ""
if "current_score" not in st.session_state:
    st.session_state.current_score = 0
if "current_nutrition" not in st.session_state:
    st.session_state.current_nutrition = {}
if "current_cal" not in st.session_state:
    st.session_state.current_cal = 0.0
if "menu_list" not in st.session_state:
    st.session_state.menu_list = []

# ============================================================
# 사이드바 입력창
# ============================================================
with st.sidebar:
    st.header("⚙️ 기초 정보 입력")
    user_weight = st.number_input("나의 몸무게 (kg) - 체력 계산용", min_value=30.0, max_value=120.0, value=50.0, step=1.0)
    
    st.divider()
    st.markdown("**🌍 기후 위기 대응 (잔반 데이터)**")
    leftover_rate = st.slider("오늘 잔반을 얼마나 남기셨나요? (%)", 0, 100, 0, step=5)
    st.caption("남긴 음식물 쓰레기의 온실가스 배출량을 분석합니다.")
    st.divider()
    
    mode = st.radio("분석 모드", ["🏫 학교 급식", "🏠 자율 식단"])
    st.divider()

    if mode == "🏫 학교 급식":
        school_keyword = st.text_input("학교 검색", "서현중학교")
        meal_date = st.date_input("급식 날짜", datetime.date.today())
        meal_btn = st.button("🍱 통합 분석 시작", use_container_width=True)
    else:
        user_food = st.text_area("오늘 먹은 음식", "불닭볶음면, 참치김밥, 콜라")
        analyze_btn = st.button("🤖 통합 분석 시작", use_container_width=True)

# ============================================================
# 데이터 연동 및 상태 저장
# ============================================================
if mode == "🏫 학교 급식" and meal_btn:
    with st.spinner("급식 및 생체 데이터 분석 중..."):
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
            else:
                st.error("해당 날짜의 급식 정보를 찾을 수 없습니다.")
        else:
            st.error("학교를 찾을 수 없습니다.")

elif mode == "🏠 자율 식단" and analyze_btn:
    food_db = {
        "라면": {"calorie": 500, "탄수화물": 70, "단백질": 10, "지방": 15},
        "마라탕": {"calorie": 800, "탄수화물": 90, "단백질": 20, "지방": 40},
        "불닭볶음면": {"calorie": 550, "탄수화물": 80, "단백질": 12, "지방": 18},
        "김밥": {"calorie": 450, "탄수화물": 65, "단백질": 12, "지방": 14},
        "치킨": {"calorie": 700, "탄수화물": 20, "단백질": 40, "지방": 35},
        "콜라": {"calorie": 150, "탄수화물": 40, "단백질": 0, "지방": 0}
    }
    with st.spinner("자율 식단 및 기후 데이터 분석 중..."):
        time.sleep(1)
    foods = [f.strip() for f in user_food.split(",")]
    total = {"calorie": 0, "탄수화물": 0, "단백질": 0, "지방": 0}
    for food in foods:
        for name, data in food_db.items():
            if name in food:
                for k in total:
                    total[k] += data[k]
                break
    
    st.session_state.menu_list = foods
    st.session_state.current_cal = total["calorie"]
    st.session_state.current_score = calculate_score(total)
    st.session_state.current_food_name = user_food
    st.session_state.current_nutrition = total
    st.session_state.analyzed = True

# ============================================================
# 메인 화면 대시보드 렌더링
# ============================================================
if st.session_state.analyzed:
    if mode == "🏫 학교 급식" and st.session_state.menu_list:
        st.success(f"✅ {st.session_state.current_food_name} 데이터 연동 완료")
        st.markdown(" ".join([f"`{f}`" for f in st.session_state.menu_list]))
        
    st.header("📊 기초 영양 지표")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💯 Health Score", f"{st.session_state.current_score}점")
    c2.metric("제공된 총 칼로리", f"{st.session_state.current_cal} kcal")
    c3.metric("탄수화물", f"{st.session_state.current_nutrition.get('탄수화물', 0)}g")
    c4.metric("지방", f"{st.session_state.current_nutrition.get('지방', 0)}g")
    st.progress(st.session_state.current_score / 100)

    st.markdown("---")
    st.header("🔬 융합 과학: 인체 에너지 & 기후 위기 동시 해결 시뮬레이션")
    st.caption("섭취한 에너지는 '체력 증진 처방'으로, 낭비된 음식물은 '열역학 방정식'을 통해 환경 기여도로 계산합니다.")
    
    # 💥 시뮬레이션 버튼 작동 시 OpenAI가 실시간으로 분석 문장을 뽑아냄
    if st.button("✨ 초고속 AI 통합 시뮬레이션 가동", type="primary"):
        with st.container():
            st.markdown('<div class="ai-report">', unsafe_allow_html=True)
            # st.write_stream을 활용하여 ChatGPT의 대답이 타이핑되듯 흘러나오게 구현
            st.write_stream(generate_ai_report_stream(
                st.session_state.current_food_name, 
                st.session_state.current_score, 
                st.session_state.current_cal,
                st.session_state.current_nutrition,
                leftover_rate
            ))
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 아래 물리 및 에코 시뮬레이션 카드 레이아웃 유지
            col_phys, col_eco = st.columns(2)
            with col_phys:
                st.markdown('<div class="physics-card">', unsafe_allow_html=True)
                st.subheader("🏃 인체 에너지 열평형")
                st.write("잉여 칼로리를 **줄(Joule)**로 변환하여 물리적 '일'을 계산합니다.")
                st.latex(r"W = \Delta E_p = m \cdot g \cdot h")
                
                actual_cal = st.session_state.current_cal * (1 - leftover_rate/100)
                estimated_bmr = 600
                delta_e_kcal = actual_cal - estimated_bmr
                
                if delta_e_kcal > 0:
                    surplus_joules = delta_e_kcal * 4184
                    g, step_height = 9.8, 0.2
                    work_per_step = user_weight * g * step_height
                    steps_needed = int(surplus_joules / work_per_step)
                    
                    st.error(f"🚨 **열평형 붕괴:** {delta_e_kcal:.1f} kcal 잉여 에너지 발생")
                    st.info(f"💡 이를 태우기 위해 중력을 거슬러 약 **{steps_needed:,}개의 계단**을 올라야 완벽한 열평형을 이룰 수 있습니다.")
                else:
                    st.success("✅ 잉여 에너지가 없는 완벽한 열역학적 평형 상태입니다.")
                    st.latex(r"\Delta E \approx 0")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_eco:
                st.markdown('<div class="eco-card">', unsafe_allow_html=True)
                st.subheader("🌍 잔반 소각 열역학 (Eco-Thermo)")
                st.write("남긴 음식물 쓰레기의 수분을 증발시키고 소각하는 데 필요한 열에너지를 계산합니다.")
                st.latex(r"Q = c \cdot m \cdot \Delta T + L \cdot m")
                
                wasted_mass_kg = 0.6 * (leftover_rate / 100)
                if leftover_rate > 0:
                    heat_wasted_kj = wasted_mass_kg * 4.18 * 80 + wasted_mass_kg * 2260
                    co2_emission = wasted_mass_kg * 1.58
                    
                    st.error(f"🚨 **자원 낭비 및 기후 위기 악화**")
                    st.write(f"- **버려진 식량:** {wasted_mass_kg*1000:.0f} g")
                    st.write(f"- **소각 낭비 열에너지:** {heat_wasted_kj:,.0f} kJ (약 {heat_wasted_kj/3600:.1f} kWh 낭비)")
                    st.info(f"💡 이 잔반을 태우느라 대기에 약 **{co2_emission:.2f} kg의 이산화탄소($CO_2$)**가 배출되어 온난화를 가속합니다.")
                else:
                    st.success("🎉 **Zero Waste 달성!**")
                    st.write("잔반을 전혀 남기지 않아 소각에 필요한 열에너지 낭비와 온실가스 배출을 100% 막아냈습니다. 지구를 구하셨습니다!")
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown("### 🧾 최종 처방전 발급")
            col_diet, col_ex = st.columns(2)
            
            diet_plan = get_dinner_prescription(st.session_state.current_nutrition)
            with col_diet:
                st.markdown(f"""
                <div class="prescription-card">
                    <div class="prescription-title">🍽️ 영양 밸런스 복구 처방전</div>
                    <p class="p-text">💡 <b>저녁 추천 메뉴:</b> <span class="highlight-diet">{diet_plan['menu']}</span></p>
                    <p class="p-text">🧬 <b>타겟 효과:</b> {diet_plan['effect']}</p>
                    <hr style="border: 0; border-top: 1px dashed #6c757d; margin: 15px 0;">
                    <p class="p-text" style="font-size: 14px; color: #adb5bd;">사유: {diet_plan['reason']}</p>
                </div>
                """, unsafe_allow_html=True)

            ex_plan = get_activity_prescription(delta_e_kcal)
            with col_ex:
                st.markdown(f"""
                <div class="exercise-card">
                    <div class="exercise-title">🏃‍♂️ 기초 체력 증진 처방전</div>
                    <p class="p-text">🔥 <b>필요 활동량:</b> <span class="highlight-ex">{ex_plan['exercise']}</span></p>
                    <p class="p-text">💪 <b>타겟 효과:</b> {ex_plan['effect']}</p>
                    <hr style="border: 0; border-top: 1px dashed #6c757d; margin: 15px 0;">
                    <p class="p-text" style="font-size: 14px; color: #adb5bd;">사유: {ex_plan['reason']}</p>
                </div>
                """, unsafe_allow_html=True)
