# ============================================================
# School Balance AI v2.0
# PART 1 : 기본 설정 + API + 공통 함수
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request
import urllib.parse
import json
import re
import datetime
import time

# ============================================================
# 페이지 설정
# ============================================================

st.set_page_config(
    page_title="School Balance AI",
    page_icon="🍱",
    layout="wide"
)

# ============================================================
# ★ 본인의 NEIS API KEY 입력
# ============================================================

API_KEY = "여기에_API_KEY를_입력하세요"

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main-title{
    font-size:42px;
    font-weight:bold;
    color:#2E8B57;
}

.sub-title{
    color:#666666;
    font-size:18px;
}

.food-card{
    background:#F7F9FA;
    padding:12px;
    border-radius:12px;
    margin-bottom:8px;
    border-left:6px solid #2E8B57;
}

.score-title{
    font-size:30px;
    color:#2E8B57;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# 제목
# ============================================================

st.markdown(
    "<div class='main-title'>🍱 School Balance AI</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='sub-title'>실시간 학교 급식 AI 영양 분석 시스템</div>",
    unsafe_allow_html=True
)

st.divider()

# ============================================================
# 학교 검색
# ============================================================

def search_school(keyword):

    try:
        # API_KEY가 기본값이면 주소에서 KEY 파라미터를 제외합니다.
        if API_KEY == "여기에_API_KEY를_입력하세요" or not API_KEY:
            url = (
                "https://open.neis.go.kr/hub/schoolInfo"
                "?Type=json"
                f"&SCHUL_NM={urllib.parse.quote(keyword)}"
            )
        else:
            url = (
                "https://open.neis.go.kr/hub/schoolInfo"
                f"?KEY={API_KEY}"
                "&Type=json"
                f"&SCHUL_NM={urllib.parse.quote(keyword)}"
            )

        req = urllib.request.Request(url)

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        rows = data["schoolInfo"][1]["row"]

        schools = []

        for row in rows:
            schools.append({
                "name": row["SCHUL_NM"],
                "region": row["ATPT_OFCDC_SC_NM"],
                "edu_code": row["ATPT_OFCDC_SC_CODE"],
                "school_code": row["SD_SCHUL_CODE"]
            })

        return schools

    except:
        return []

# ============================================================
# 급식 조회 (파싱 버그 완벽 수정 버전)
# ============================================================

def get_meal(edu_code, school_code, meal_date):

    try:
        if API_KEY == "여기에_API_KEY를_입력하세요" or not API_KEY:
            url = (
                "https://open.neis.go.kr/hub/mealServiceDietInfo"
                "?Type=json"
                f"&ATPT_OFCDC_SC_CODE={edu_code}"
                f"&SD_SCHUL_CODE={school_code}"
                f"&MLSV_YMD={meal_date}"
            )
        else:
            url = (
                "https://open.neis.go.kr/hub/mealServiceDietInfo"
                f"?KEY={API_KEY}"
                "&Type=json"
                f"&ATPT_OFCDC_SC_CODE={edu_code}"
                f"&SD_SCHUL_CODE={school_code}"
                f"&MLSV_YMD={meal_date}"
            )

        req = urllib.request.Request(url)

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        # ✨ 핵심 수정: 리스트 내부의 첫 번째 [0] 요소를 명확히 가져옵니다.
        row = data["mealServiceDietInfo"][1]["row"][0]

        menu = row["DDISH_NM"]

        menu = [
            re.sub(r"[0-9\.\(\)]", "", food).strip()
            for food in menu.split("<br/>")
        ]

        return {
            "menu": menu,
            "calorie": row["CAL_INFO"],
            "nutrition": row["NTR_INFO"]
        }

    except Exception as e:
        # 혹시 모를 에러 추적을 위해 로그를 지우지 않고 None 반환
        return None



    try:

        url = (
            "https://open.neis.go.kr/hub/mealServiceDietInfo"
            f"?KEY={API_KEY}"
            "&Type=json"
            f"&ATPT_OFCDC_SC_CODE={edu_code}"
            f"&SD_SCHUL_CODE={school_code}"
            f"&MLSV_YMD={meal_date}"
        )

        req = urllib.request.Request(url)

        with urllib.request.urlopen(req) as response:

            data = json.loads(response.read().decode("utf-8"))

        row = data["mealServiceDietInfo"][1]["row"][0]

        menu = row["DDISH_NM"]

        menu = [

            re.sub(r"[0-9\.\(\)]", "", food).strip()

            for food in menu.split("<br/>")

        ]

        return {

            "menu": menu,
            "calorie": row["CAL_INFO"],
            "nutrition": row["NTR_INFO"]

        }

    except:

        return None

# ============================================================
# 영양정보 파싱 (개선 버전)
# ============================================================

def parse_nutrition(text):

    nutrition = {}

    if not text:
        return nutrition

    items = text.split("<br/>")

    for item in items:

        if ":" not in item:
            continue

        name, value = item.split(":", 1)

        # 단위 제거
        name = re.sub(r"\(.*?\)", "", name).strip()

        # 숫자만 추출
        match = re.search(r"[\d.]+", value)

        if match:
            nutrition[name] = float(match.group())
        else:
            nutrition[name] = 0

    return nutrition
# ============================================================
# Health Score
# ============================================================

def calculate_score(nutrition):

    score = 100

    protein = nutrition.get("단백질", 0)
    fat = nutrition.get("지방", 0)
    calcium = nutrition.get("칼슘", 0)
    vitamin_c = nutrition.get("비타민C", 0)

    if protein < 20:
        score -= 15

    if fat > 25:
        score -= 10

    if calcium < 250:
        score -= 10

    if vitamin_c < 30:
        score -= 5

    return max(score, 0)

# ============================================================
# 그래프
# ============================================================

def nutrition_chart(nutrition):

    labels = []
    values = []

    for key in nutrition:

        if key in ["탄수화물", "단백질", "지방"]:

            labels.append(key)
            values.append(nutrition[key])

    df = pd.DataFrame({

        "영양소": labels,
        "섭취량": values

    })

    fig = px.bar(

        df,

        x="영양소",

        y="섭취량",

        text="섭취량",

        title="3대 영양소 분석"

    )

    fig.update_layout(height=420)

    return fig
if "meal_data" not in st.session_state:
    st.session_state.meal_data = None
# ============================================================
# PART 2부터 이어집니다.
# ============================================================
# ============================================================
# PART 2 : Sidebar + 학교 검색 + 급식 조회
# ============================================================

with st.sidebar:

    st.header("⚙️ 메뉴")

    mode = st.radio(
        "분석 모드",
        [
            "🏫 학교 급식",
            "🏠 자율 식단"
        ]
    )

    st.divider()

    # -------------------------
    # 학교 급식 모드
    # -------------------------

    if mode == "🏫 학교 급식":

        school_keyword = st.text_input(
            "학교 이름",
            placeholder="예) 서현중학교"
        )

        # 1. 학교 검색을 위한 세션 상태 초기화
        if "search_clicked" not in st.session_state:
            st.session_state.search_clicked = False
        if "school_options" not in st.session_state:
            st.session_state.school_options = []
        if "school_data_list" not in st.session_state:
            st.session_state.school_data_list = []

        # 2. 검색 버튼 추가
        if st.button("🔍 학교 검색", use_container_width=True):
            if school_keyword:
                with st.spinner("학교를 검색하는 중..."):
                    school_list = search_school(school_keyword)
                    if school_list:
                        st.session_state.school_data_list = school_list
                        st.session_state.school_options = [
                            f"{s['name']} ({s['region']})" for s in school_list
                        ]
                        st.session_state.search_clicked = True
                    else:
                        st.error("검색된 학교가 없습니다. 정확한 이름을 입력해 주세요.")
                        st.session_state.search_clicked = False
                        st.session_state.school_options = []
            else:
                st.warning("학교 이름을 입력해 주세요.")

        # 3. 검색 성공 시에만 드롭다운 노출
        selected_school = None
        if st.session_state.search_clicked and st.session_state.school_options:
            selected = st.selectbox(
                "학교 선택",
                st.session_state.school_options
            )
            index = st.session_state.school_options.index(selected)
            selected_school = st.session_state.school_data_list[index]

        # 4. 급식 날짜 기본값을 오늘 날짜로 세팅
        meal_date = st.date_input(
            "급식 날짜",
            datetime.date.today()
        )

        meal_btn = st.button(
            "🍱 급식 조회",
            use_container_width=True
        )

    # -------------------------
    # 자율 식단 모드
    # -------------------------
    else:
        user_food = st.text_area(
            "오늘 먹은 음식",

            height=120,
            placeholder="예) 불닭볶음면, 참치김밥, 콜라"
        )

        analyze_btn = st.button(
            "🤖 AI 분석",
            use_container_width=True
        )

# ============================================================
# 메인 화면
# ============================================================

if mode == "🏫 학교 급식":
    meal = None   # ✨ 이 줄을 추가해서 meal 변수를 미리 만들어 둡니다!
    if meal_btn:

        if selected_school is None:
            st.error("학교를 선택해주세요.")
        else:
            if isinstance(selected_school, dict):
                with st.spinner("급식 정보를 불러오는 중입니다..."):
                    st.session_state.meal_data = get_meal(
                        selected_school["edu_code"],
                        selected_school["school_code"],
                        meal_date.strftime("%Y%m%d")
                    )
            else:
                st.error("선택된 학교 정보가 올바르지 않습니다. 다시 선택해 주세요.")
                st.stop()

        meal = st.session_state.meal_data
        time.sleep(0.5)



if meal is None:
    st.warning("해당 날짜의 급식 정보가 없습니다.")
    st.stop()  # ✨ 데이터가 없으면 여기서 실행을 즉시 중단시켜 아래 경고문이 안 뜨게 합니다
else:
    st.success(
        f"✅ {selected_school['name']} 급식 조회 완료"
    )
    
    left, right = st.columns([2, 1])
    
    with left:
        st.subheader("🍱 오늘의 급식")
        
        for food in meal["menu"]:
            st.markdown(
                f"- {food}"
            )

        st.markdown(
            f'<div class="food-card">🍽️ {food}</div>',
            unsafe_allow_html=True
        )

    with right:
        st.subheader("📊 기본 정보")
        
        st.metric(
            "총 칼로리",
            meal["calorie"]
        )
        
        st.write("### 교육청 영양 정보")

if mode == "🏫 학교 급식":

    if meal_btn and selected_school is not None:

        meal = st.session_state.meal_data
        if meal is not None:

            nutrition = parse_nutrition(meal["nutrition"])

            st.markdown("---")
            st.header("🤖 AI 영양 분석")

            score = calculate_score(nutrition)

            col1, col2 = st.columns([1, 2])

            # ==========================
            # Health Score
            # ==========================

            with col1:

                st.metric(
                    "💯 Health Score",
                    f"{score}점"
                )

                st.progress(score / 100)

                if score >= 90:

                    st.success("매우 균형 잡힌 급식입니다.")

                elif score >= 80:

                    st.info("좋은 식단입니다.")

                elif score >= 70:

                    st.warning("약간 부족한 영양소가 있습니다.")

                else:

                    st.error("영양 균형 개선이 필요합니다.")

            # ==========================
            # 그래프
            # ==========================

            with col2:

                if len(nutrition) > 0:

                    fig = nutrition_chart(nutrition)

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

            st.markdown("---")

            st.subheader("📋 AI 분석 결과")

            comments = []

            protein = nutrition.get("단백질", 0)
            fat = nutrition.get("지방", 0)
            carb = nutrition.get("탄수화물", 0)
            calcium = nutrition.get("칼슘", 0)
            vitamin_c = nutrition.get("비타민C", 0)

            if protein < 20:
                comments.append("🥩 단백질이 부족합니다. 계란, 두부, 우유를 함께 섭취하면 좋습니다.")

            if fat > 25:
                comments.append("🍗 지방 섭취가 많습니다. 튀김류는 조금 줄여보세요.")

            if calcium < 250:
                comments.append("🥛 칼슘이 부족합니다. 우유나 치즈를 추천합니다.")

            if vitamin_c < 30:
                comments.append("🍊 비타민 C가 부족합니다. 귤이나 사과를 먹어보세요.")

            if carb > 120:
                comments.append("🍚 탄수화물이 많은 식단입니다. 채소를 함께 먹으면 균형이 좋아집니다.")

            if len(comments) == 0:

                st.success(
                    "🎉 오늘 급식은 성장기 학생에게 매우 좋은 영양 밸런스를 가지고 있습니다!"
                )

            else:

                for c in comments:

                    st.write(c)
# ============================================================
# PART 4 : AI 추천 음식 & 영양 리포트
# ============================================================

if mode == "🏫 학교 급식":

    if meal_btn and selected_school is not None:

        meal = st.session_state.meal_data
        if meal is not None:

            nutrition = parse_nutrition(meal["nutrition"])

            st.markdown("---")
            st.header("🥗 AI 맞춤 영양 리포트")

            protein = nutrition.get("단백질", 0)
            fat = nutrition.get("지방", 0)
            carb = nutrition.get("탄수화물", 0)
            calcium = nutrition.get("칼슘", 0)
            vitamin_c = nutrition.get("비타민C", 0)

            recommend = []
            avoid = []

            # ======================
            # 추천 음식
            # ======================

            if protein < 20:
                recommend.extend([
                    "🥚 삶은 계란",
                    "🥛 우유",
                    "🧈 두부"
                ])

            if calcium < 250:
                recommend.extend([
                    "🧀 치즈",
                    "🥛 요구르트"
                ])

            if vitamin_c < 30:
                recommend.extend([
                    "🍎 사과",
                    "🍊 귤",
                    "🥝 키위"
                ])

            if fat > 25:
                avoid.extend([
                    "🍗 치킨",
                    "🍟 감자튀김"
                ])

            if carb > 120:
                avoid.extend([
                    "🍜 라면",
                    "🍞 빵"
                ])

            col1, col2 = st.columns(2)

            with col1:

                st.subheader("✅ 오늘 먹으면 좋은 음식")

                if recommend:

                    for food in sorted(set(recommend)):
                        st.success(food)

                else:

                    st.success("현재 영양 균형이 좋습니다.")

            with col2:

                st.subheader("⚠️ 조금 줄이면 좋은 음식")

                if avoid:

                    for food in sorted(set(avoid)):
                        st.warning(food)

                else:

                    st.info("특별히 제한할 음식이 없습니다.")

            st.markdown("---")

            st.subheader("📋 오늘의 종합 평가")

            # 수정 후 (정상 작동)
        if protein >= 20 and calcium >= 250 and vitamin_c >= 30:
            st.success(  # <-- 'if'보다 오른쪽으로 4칸(또는 Tab 1번) 더 들여씁니다!
                "오늘 급식은 성장기 학생에게 적합한 식단입니다.\n\n"
                "균형 잡힌 영양소를 제공하며,\n"
                "현재 상태를 유지하면 좋습니다."
            )

    else:

        st.warning(
            "일부 영양소가 부족할 가능성이 있습니다.\n\n"
            "추천 음식을 간식으로 섭취하면\n"
            "균형을 맞출 수 있습니다."
        )

# ============================================================
# PART 5 : 자율 식단 AI 분석 (수정 완성본)
# ============================================================


# 음식 영양 데이터베이스

food_db = {

    "라면":{
        "calorie":500,
        "탄수화물":70,
        "단백질":10,
        "지방":15
    },

    "불닭볶음면":{
        "calorie":550,
        "탄수화물":80,
        "단백질":12,
        "지방":18
    },

    "김밥":{
        "calorie":450,
        "탄수화물":65,
        "단백질":12,
        "지방":14
    },

    "참치김밥":{
        "calorie":520,
        "탄수화물":68,
        "단백질":18,
        "지방":18
    },

    "치킨":{
        "calorie":700,
        "탄수화물":20,
        "단백질":40,
        "지방":35
    },

    "계란":{
        "calorie":80,
        "탄수화물":1,
        "단백질":7,
        "지방":6
    },

    "우유":{
        "calorie":130,
        "탄수화물":10,
        "단백질":7,
        "지방":7
    },

    "사과":{
        "calorie":100,
        "탄수화물":25,
        "단백질":0,
        "지방":0
    },

    "콜라":{
        "calorie":150,
        "탄수화물":40,
        "단백질":0,
        "지방":0
    }

}



# ============================================================
# 자율 식단 분석
# ============================================================


if mode == "🏠 자율 식단":


    if analyze_btn:


        if user_food.strip() == "":


            st.warning(
                "음식을 입력해주세요."
            )


        else:


            foods = [

                f.strip()

                for f in user_food.split(",")

            ]


            total = {

                "calorie":0,

                "탄수화물":0,

                "단백질":0,

                "지방":0

            }


            not_found = []



            for food in foods:


                found = False


                for name, data in food_db.items():


                    if name in food:


                        total["calorie"] += data["calorie"]

                        total["탄수화물"] += data["탄수화물"]

                        total["단백질"] += data["단백질"]

                        total["지방"] += data["지방"]


                        found = True

                        break



                if found == False:

                    not_found.append(food)



            # -------------------------
            # Health Score 계산
            # -------------------------


            score = 100



            if total["단백질"] < 20:

                score -= 15



            if total["지방"] > 30:

                score -= 15



            if total["탄수화물"] > 150:

                score -= 10



            score = max(score,0)



            # ⭐ PART 6 전달용 저장

            st.session_state.diet_result = {


                "calorie": total["calorie"],


                "탄수화물": total["탄수화물"],


                "단백질": total["단백질"],


                "지방": total["지방"],


                "score": score

            }



            # -------------------------
            # 결과 출력
            # -------------------------


            st.markdown("---")


            st.header(
                "🤖 AI 식단 분석 결과"
            )


            col1, col2 = st.columns(2)



            with col1:


                st.metric(

                    "총 칼로리",

                    f"{total['calorie']} kcal"

                )


                st.metric(

                    "탄수화물",

                    f"{total['탄수화물']} g"

                )


                st.metric(

                    "단백질",

                    f"{total['단백질']} g"

                )


                st.metric(

                    "지방",

                    f"{total['지방']} g"

                )



            with col2:


                st.subheader(
                    "💯 Health Score"
                )


                st.metric(

                    "점수",

                    f"{score}점"

                )


                st.progress(

                    score / 100

                )



            st.markdown("---")



            st.subheader(
                "🥗 AI 추천"
            )



            if total["단백질"] < 20:


                st.info(
                    "🥚 단백질 보충 추천 : 계란, 두부, 닭가슴살"
                )



            if total["탄수화물"] > 150:


                st.warning(
                    "🍚 탄수화물이 많습니다. 채소를 추가해보세요."
                )



            if total["지방"] > 30:


                st.warning(
                    "🍗 지방 섭취가 높습니다. 튀김류를 줄이면 좋습니다."
                )



            if (
                total["단백질"] >= 20
                and total["지방"] <= 30
                and total["탄수화물"] <= 150
            ):


                st.success(
                    "🎉 균형 잡힌 식단입니다!"
                )



            if not_found:


                st.caption(

                    "⚠️ 데이터에 없는 음식 : "

                    + ", ".join(not_found)

                )
# ============================================================
# PART 6 : 식단 기록 저장 + 주간 건강 리포트 (최종 수정본)
# ============================================================


# 기록 저장 공간 생성

if "diet_history" not in st.session_state:

    st.session_state.diet_history = []



# ============================================================
# 자율 식단 결과 저장
# ============================================================


if (
    mode == "🏠 자율 식단"
    and "diet_result" in st.session_state
):

            result = st.session_state.diet_result
            today = str(datetime.date.today())
            new_record = {
                "날짜": today,
                "음식": user_food,
                "칼로리(kcal)": result["calorie"],
                "탄수화물(g)": result["탄수화물"],
                "단백질(g)": result["단백질"],
                "지방(g)": result["지방"],
                "Health Score": result["score"]
            }
            duplicate = False
            for item in st.session_state.diet_history:
                if (
                    item["날짜"] == today
                    and item["음식"] == user_food
                ):
                    duplicate = True
            if duplicate == False:
                st.session_state.diet_history.append(
                    new_record
                )
# ============================================================
# 기록 화면
# ============================================================
st.markdown("---")
st.header(
    "📅 나의 식단 기록 & 건강 리포트"
)
if len(st.session_state.diet_history) > 0:
    history_df = pd.DataFrame(
        st.session_state.diet_history
    )
    st.subheader(
        "📋 식단 기록"
    )
    st.dataframe(
        history_df,
        use_container_width=True
    )
    # 평균 계산
    avg_score = history_df["Health Score"].mean()
    avg_calorie = history_df["칼로리(kcal)"].mean()
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "평균 Health Score",
            f"{avg_score:.1f}점"
        )
    with col2:
        st.metric(
            "평균 칼로리",
            f"{avg_calorie:.0f} kcal"
        )
    # ========================================================
    # 점수 변화 그래프
    # ========================================================
    st.subheader(
        "📈 건강 점수 변화"
    )
    fig = px.line(
        history_df,
        x="날짜",
        y="Health Score",
        markers=True,
        title="Health Score 변화"
    )
    fig.update_layout(
        height=400
    )
    st.plotly_chart(
        fig,
        use_container_width=True

    )



    # ========================================================
    # AI 평가
    # ========================================================


    st.subheader(
        "🤖 AI 주간 평가"
    )



    if avg_score >= 90:


        st.success(

            """
🎉 매우 좋은 식습관입니다.

균형 잡힌 식단을 유지하고 있습니다.
"""

        )


    elif avg_score >= 75:


        st.info(

            """
👍 좋은 식단입니다.

부족한 영양소를 조금 보완하면 더 좋아집니다.
"""

        )


    else:


        st.warning(

            """
⚠️ 식단 개선이 필요합니다.

단백질과 채소 섭취를 늘려보세요.
"""

        )



else:


    st.info(

        "아직 저장된 식단 기록이 없습니다."

    )
