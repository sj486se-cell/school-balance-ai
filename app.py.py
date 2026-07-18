import streamlit as st
import urllib.parse
import urllib.request
import json
import re
import datetime
import pandas as pd
import google.generativeai as genai

# ==========================================
# 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="School Balance AI", page_icon="🍱", layout="wide")

# ==========================================
# Gemini API 설정 (클라우드 Secrets 또는 secrets.toml 확인)
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    model = None # API 키가 없을 경우를 대비한 안전 장치

# ==========================================
# 교육청(나이스) API 연동 함수
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
# 1. 사이드바 (UI 메뉴 설정)
# ==========================================
# 버튼 클릭 에러를 방지하기 위해 변수를 미리 선언합니다.
fetch_btn = False
analyze_self_btn = False

with st.sidebar:
    st.title("📅 식단 관리 모드")
    day_type = st.radio("오늘 급식이 나오는 날인가요?", ["🏫 네 (학기 중 평일)", "🏠 아니요 (방학/주말/공휴일)"])
    st.divider()

    if "네" in day_type:
        st.subheader("🏫 전국 학교 급식 연동기")
        school_input = st.text_input("학교 검색", "서현중학교")
        target_date = st.date_input("조회할 날짜 (평일)", datetime.date.today())
        date_str = target_date.strftime("%Y%m%d")
        fetch_btn = st.button("실제 급식 데이터 불러오기 📡", type="primary", use_container_width=True)
    else:
        st.subheader("🏠 자율 식단 분석기")
        st.caption("급식이 없는 날에도 영양 관리는 계속됩니다!")
        user_meal = st.text_input("오늘 어떤 메뉴를 드셨나요?", "마라탕, 탕후루")
        analyze_self_btn = st.button("내 식단 AI 분석하기 🔍", type="primary", use_container_width=True)

# ==========================================
# 2. 메인 화면 출력 로직
# ==========================================
st.title("🍱 School Balance: 365일 AI 영양사")

# ----------------------------------------
# [모드 A] 평일 - 학교 급식 연동
# ----------------------------------------
if "네" in day_type:
    st.info("👈 왼쪽 사이드바에서 학교와 날짜를 선택하고 급식 데이터를 불러오세요!")
    
    if fetch_btn:
        with st.spinner("교육청 메인 서버에서 식단 데이터를 추출 중입니다..."):
            edu_code, sch_code, real_school_name = get_school_info(school_input)
            
            if not sch_code:
                st.error("❌ 학교를 찾을 수 없습니다. 학교명을 정확히 입력해 주세요.")
            else:
                menu_list, cal_info, ntr_info = get_meal_info(edu_code, sch_code, date_str)
                
                if not menu_list:
                    st.warning("⚠️ 선택하신 날짜의 급식 정보가 없습니다. (주말이거나 방학일 수 있습니다.)")
                else:
                    st.success(f"✅ [{real_school_name}] 실제 데이터 연동 성공!")
                    
                    col1, col2 = st.columns([1, 1.5])
                    with col1:
                        st.subheader("🍽️ 식단표")
                        menus_html = "".join([f"<h5 style='color: #2b8a3e;'>{m}</h5>" for m in menu_list])
                        st.markdown(f"<div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; text-align: center;'>{menus_html}</div>", unsafe_allow_html=True)
                    with col2:
                        st.subheader("📊 교육청 영양 데이터")
                        st.write(f"**총 칼로리:** {cal_info}")
                        st.write(f"**영양 정보:** {ntr_info}")
                        st.success("✅ **분석:** 학교 영양사 선생님이 구성한 식단으로 밸런스가 매우 우수합니다!")

# ----------------------------------------
# [모드 B] 주말/방학 - 생성형 AI 식단 분석
# ----------------------------------------
elif "아니요" in day_type:
    st.info("👈 왼쪽에서 방학이나 주말에 드신 메뉴를 자유롭게 입력하고 분석 버튼을 눌러주세요!")
    
    if analyze_self_btn:
        if model is None:
            st.error("🚨 API 키가 설정되지 않았습니다. Streamlit Cloud의 Settings -> Secrets에 API 키를 입력했는지 확인해 주세요.")
        else:
            with st.spinner("AI가 입력된 식단을 분석하여 분자 단위 맞춤형 영양 처방전을 작성하고 있습니다..."):
                
                # 💡 LLM 프롬프트: JSON 형태로 답변을 강제합니다.
                prompt = f"""
                당신은 10대 청소년을 위한 전문 AI 영양사입니다. 
                사용자가 방금 먹은 식단을 분석하고, 반드시 아래의 JSON 형식으로만 답변해 주세요. 
                다른 설명은 절대 추가하지 마세요.
                
                분석할 식단: {user_meal}

                {{
                    "status": "DANGER" 또는 "WARNING" 또는 "SAFE" 중 하나,
                    "summary": "영양 상태에 대한 핵심 한 줄 요약",
                    "risk_scores": {{
                        "sodium": 0.0부터 1.0 사이의 숫자 (나트륨 위험도, 1에 가까울수록 높음),
                        "sugar_fat": 0.0부터 1.0 사이의 숫자 (당/포화지방 위험도)
                    }},
                    "analysis_text": "왜 이 식단이 청소년 건강에 좋거나 위험한지 과학적이고 친절하게 설명 (3문장 이내)",
                    "solution_title": "솔루션의 멋진 제목 (예: 붓기 쫙 빼는 나트륨 디톡스 처방전)",
                    "prescriptions": [
                        {{"food": "추천 식품 1", "nutrient": "핵심 성분명", "effect": "기대 효과"}},
                        {{"food": "추천 식품 2", "nutrient": "핵심 성분명", "effect": "기대 효과"}}
                    ]
                }}
                """
                
                try:
                    # AI 호출
                    response = model.generate_content(prompt)
                    
                    # 마크다운 찌꺼기(```json) 제거
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    result = json.loads(clean_text)

                    # --- 화면 출력 ---
                    st.success(f"✅ '{user_meal}'에 대한 초정밀 영양 분석이 완료되었습니다!")
                    st.markdown("---")
                    st.header("📊 AI 심층 영양 분석 리포트")
                    
                    # 1. 상태에 따른 경고 메시지
                    if result["status"] == "DANGER":
                        st.error(f"🚨 **[위험] {result['summary']}**")
                    elif result["status"] == "WARNING":
                        st.warning(f"⚠️ **[경고] {result['summary']}**")
                    else:
                        st.success(f"✅ **[안전] {result['summary']}**")
                        
                    # 2. 프로그래스 바 (위험도 게이지)
                    st.subheader("⚠️ 주요 위험 지표")
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        st.write("**나트륨(염분) 과다 지수**")
                        st.progress(float(result["risk_scores"]["sodium"]))
                    with col_g2:
                        st.write("**정제 탄수화물/당/지방 과다 지수**")
                        st.progress(float(result["risk_scores"]["sugar_fat"]))
                        
                    # 3. AI 상세 코멘트
                    st.write(result["analysis_text"])
                    st.markdown("---")
                    
                    # 4. 맞춤형 솔루션 데이터 표
                    st.subheader(f"💡 {result['solution_title']}")
                    prescription_df = pd.DataFrame(result["prescriptions"])
                    prescription_df.columns = ["처방 식품", "핵심 성분", "기대 효과"] 
                    st.dataframe(prescription_df, use_container_width=True, hide_index=True)

                except Exception as e:
                    st.error("AI 응답을 분석하는 중 문제가 발생했습니다. 식단을 약간 다르게 적어서 다시 시도해 주세요.")
                    st.write(f"(시스템 에러 내용: {e})")
