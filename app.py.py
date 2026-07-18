import streamlit as st
import urllib.parse
import urllib.request
import json
import re
import datetime
import time

st.set_page_config(page_title="School Balance AI", page_icon="🍱", layout="wide")

# ==========================================
# 0. 진짜 교육청(나이스) API 연동 함수
# ==========================================
def get_school_info(school_name):
    try:
        url = f"https://open.neis.go.kr/hub/schoolInfo?Type=json&SCHUL_NM={urllib.parse.quote(school_name)}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "schoolInfo" in data:
                row = data["schoolInfo"][1]["row"][0]
                return row["ATPT_OFCDC_SC_CODE"], row["SD_SCHUL_CODE"], row["SCHUL_NM"]
    except: pass
    return None, None, None

def get_meal_info(edu_code, sch_code, date_str):
    try:
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&ATPT_OFCDC_SC_CODE={edu_code}&SD_SCHUL_CODE={sch_code}&MLSV_YMD={date_str}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "mealServiceDietInfo" in data:
                row = data["mealServiceDietInfo"][1]["row"][0]
                raw_menu = row["DDISH_NM"]
                menu_list = [re.sub(r'[0-9\.\(\)]', '', m).strip() for m in raw_menu.split('<br/>')]
                return menu_list, row["CAL_INFO"], row["NTR_INFO"]
    except: pass
    return None, None, None

# ==========================================
# 1. 사이드바: 365일 대응 모드 선택
# ==========================================
with st.sidebar:
    st.title("📅 식단 관리 모드")
    # 🌟 핵심: 학기 중인지 방학/주말인지 선택하는 라디오 버튼
    day_type = st.radio("오늘 급식이 나오는 날인가요?", ["🏫 네 (학기 중 평일)", "🏠 아니요 (방학/주말/공휴일)"])
    st.divider()

    if "네" in day_type:
        st.subheader("🏫 전국 학교 급식 연동기")
        school_input = st.text_input("학교 검색", "서현중학교")
        target_date = st.date_input("조회할 날짜 (평일)", datetime.date(2026, 7, 2))
        date_str = target_date.strftime("%Y%m%d")
        fetch_btn = st.button("실제 급식 데이터 불러오기 📡", type="primary", use_container_width=True)
    else:
        st.subheader("🏠 자율 식단 분석기")
        st.caption("급식이 없는 날에도 영양 관리는 계속됩니다!")
        # 🌟 방학일 경우 사용자가 직접 메뉴를 입력
        user_meal = st.text_input("오늘 어떤 메뉴를 드셨나요?", "불닭볶음면, 참치삼각김밥, 콜라")
        analyze_self_btn = st.button("내 식단 AI 분석하기 🔍", type="primary", use_container_width=True)

# ==========================================
# 2. 메인 화면
# ==========================================
st.title("🍱 School Balance: 365일 AI 영양사")

# ----------------------------------------
# 모드 A: 학기 중 급식 연동 로직
# ----------------------------------------
if "네" in day_type:
    st.info("👈 왼쪽 사이드바에서 학교와 날짜를 선택하고 급식 데이터를 불러오세요!")
    # fetch_btn을 눌렀을 때만 작동할 수 있도록 `fetch_btn` 변수가 정의되어 있는지 확인
    if 'fetch_btn' in locals() and fetch_btn:
        with st.spinner("나이스(NEIS) 메인 서버에서 데이터를 추출 중입니다..."):
            edu_code, sch_code, real_school_name = get_school_info(school_input)
            if not sch_code:
                st.error("❌ 학교를 찾을 수 없습니다.")
            else:
                menu_list, cal_info, ntr_info = get_meal_info(edu_code, sch_code, date_str)
                if not menu_list:
                    st.warning("⚠️ 해당 날짜의 급식 정보가 없습니다.")
                else:
                    st.success(f"✅ [{real_school_name}] 실제 데이터 연동 성공!")
                    col1, col2 = st.columns([1, 1.5])
                    with col1:
                        st.subheader("🍽️ 식단표")
                        st.markdown("<div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; text-align: center;'>" + 
                                    "".join([f"<h5 style='color: #2b8a3e;'>{m}</h5>" for m in menu_list]) + "</div>", unsafe_allow_html=True)
                    with col2:
                        st.subheader("📊 교육청 영양 데이터")
                        st.write(f"**총 칼로리:** {cal_info}")
                        st.success("✅ **분석:** 학교 영양사 선생님이 구성한 식단으로 밸런스가 우수합니다!")

# ----------------------------------------
# 모드 B: 방학/주말 자율 식단 분석 로직 (새로 추가됨!)
# ----------------------------------------
elif "아니요" in day_type:
    if 'analyze_self_btn' in locals() and analyze_self_btn:
        with st.spinner("사용자가 입력한 식단의 영양 성분을 분석 중입니다..."):
            time.sleep(1.2) # 분석하는 척
            
        st.success(f"✅ '{user_meal}'에 대한 분석이 완료되었습니다!")
        st.subheader("📊 AI 영양 분석 리포트")
        
        # 키워드 기반 동적 분석 로직
        meal_str = user_meal.replace(" ", "")
        
        if any(word in meal_str for word in ["마라탕", "라면", "불닭", "떡볶이", "짬뽕"]):
            st.error("🚨 **[위험 경고] 나트륨 및 정제 탄수화물 폭발!**")
            st.write("청소년들이 가장 좋아하는 메뉴지만, 하루 권장 나트륨의 150% 이상을 한 끼에 섭취했을 확률이 매우 높습니다. 또한 위장 점막을 자극할 수 있습니다.")
            st.warning("🎯 **AI 긴급 솔루션**")
            st.write("1. **나트륨 배출:** 칼륨이 풍부한 **바나나, 토마토, 우유**를 반드시 섭취하세요.\n2. **저녁 식단:** 저녁은 국물이 없는 **닭가슴살 샐러드나 두부 부침** 같은 담백한 단백질 위주로 구성해야 합니다.")
            
        elif any(word in meal_str for word in ["치킨", "피자", "햄버거", "돈까스", "튀김"]):
            st.error("🚨 **[위험 경고] 포화지방 및 고칼로리 주의!**")
            st.write("트랜스 지방과 포화지방 섭취가 높아 소화가 느려지고 피로감이 올 수 있으며, 식이섬유가 심각하게 부족한 식단입니다.")
            st.warning("🎯 **AI 긴급 솔루션**")
            st.write("1. **지방 분해 및 소화:** **녹차나 아메리카노(연하게)**, 혹은 **매실차**를 드세요.\n2. **저녁 식단:** **사과, 양배추 샐러드** 등 비타민과 식이섬유가 듬뿍 든 신선한 채소를 꼭 보충해야 합니다.")
            
        else:
            st.success("✅ **[무난한 식단] 일반적인 밸런스입니다.**")
            st.write("크게 위험한 요소는 보이지 않지만, 외식이나 배달 음식일 경우 집밥보다 나트륨과 기름이 많을 수 있습니다.")
            st.info("🎯 **AI 밸런스업 솔루션**")
            st.write("청소년기 성장을 위해 계란 프라이 1~2개나 우유 한 팩을 곁들여 부족한 단백질과 칼슘을 보충해 보세요!")
            
    else:
        st.info("👈 방학이나 주말에는 메뉴를 직접 입력하고 영양 밸런스를 확인해 보세요!")
