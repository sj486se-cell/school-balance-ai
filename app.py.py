import streamlit as st
import urllib.parse
import urllib.request
import json
import re
import datetime

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
                cal_info = row["CAL_INFO"] 
                ntr_info = row["NTR_INFO"] 
                
                return menu_list, cal_info, ntr_info
    except: pass
    return None, None, None

# ==========================================
# 1. 사이드바: 검색기 (학기 중 날짜로 기본 세팅)
# ==========================================
with st.sidebar:
    st.title("🏫 전국 학교 급식 연동기")
    st.caption("나이스(NEIS) 교육행정 정보시스템 실시간 연동")
    
    school_input = st.text_input("학교 검색 (예: 서현중학교)", "서현중학교")
    
    # 🌟 핵심 수정: 기본 날짜를 방학 전인 '7월 2일(목)'로 고정하여 무조건 데이터가 나오게 함!
    demo_date = datetime.date(2026, 7, 2)
    target_date = st.date_input("조회할 날짜 (학기 중 평일)", demo_date)
    date_str = target_date.strftime("%Y%m%d")
    
    fetch_btn = st.button("실제 급식 데이터 불러오기 📡", type="primary", use_container_width=True)
    
    st.info("💡 **Demo Tip:** 현재는 방학 기간이므로, 실제 데이터가 있는 학기 중 날짜(예: 7월 초)로 조회합니다.")

# ==========================================
# 2. 메인 화면: 리얼 메뉴판 및 분석
# ==========================================
st.title("🍱 School Balance: 공공데이터 기반 AI 영양사")

if fetch_btn:
    with st.spinner("나이스(NEIS) 메인 서버에서 실제 데이터를 추출하고 있습니다..."):
        edu_code, sch_code, real_school_name = get_school_info(school_input)
        
        if not sch_code:
            st.error("❌ 학교를 찾을 수 없습니다. 정확한 학교명을 입력해주세요.")
        else:
            menu_list, cal_info, ntr_info = get_meal_info(edu_code, sch_code, date_str)
            
            # 🌟 방학/주말 예외 처리 (데이터가 없을 때 당황하지 않고 스마트하게 안내)
            if not menu_list:
                st.warning(f"⚠️ {target_date.strftime('%Y년 %m월 %d일')}에는 등록된 급식 정보가 없습니다.")
                st.error("💡 **AI 안내:** 선택하신 날짜는 **방학, 주말, 또는 공휴일**일 가능성이 높습니다. 왼쪽 달력에서 **'학기 중 평일(예: 7월 2일)'**을 선택하여 다시 시도해 주세요!")
            else:
                st.success(f"✅ 나이스(NEIS) 연동 성공! [{real_school_name}]의 실제 데이터입니다.")
                
                col1, col2 = st.columns([1, 1.5])
                
                with col1:
                    st.subheader("🍽️ 오늘의 실제 식단표")
                    menu_html = "<div style='background-color: #f8f9fa; padding: 20px; border-radius: 15px; border: 2px solid #e9ecef; text-align: center;'>"
                    for menu in menu_list:
                        menu_html += f"<h4 style='color: #2b8a3e; margin: 10px;'>{menu}</h4>"
                    menu_html += "</div>"
                    st.markdown(menu_html, unsafe_allow_html=True)
                    
                with col2:
                    st.subheader("📊 교육청 공식 영양 데이터")
                    st.metric(label="제공 총 칼로리", value=cal_info)
                    
                    st.markdown("**[상세 영양 성분 분석]**")
                    ntr_dict = {}
                    for item in ntr_info.split('<br/>'):
                        if ":" in item:
                            k, v = item.split(':')
                            ntr_dict[k.strip()] = v.strip()
                            
                    df_ntr = pd.DataFrame(list(ntr_dict.items()), columns=['영양소', '함유량(g/mg)'])
                    st.dataframe(df_ntr, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("💡 AI 맞춤형 밸런스 리포트")
                
                if "나트륨(mg)" in ntr_dict and float(ntr_dict["나트륨(mg)"]) > 1000:
                    st.error("🚨 **나트륨 초과 경고:** 오늘 급식의 나트륨 함량이 다소 높습니다. 하교 후 나트륨 배출을 돕는 **'바나나'나 '토마토'** 섭취를 강력히 권장합니다.")
                else:
                    st.success("✅ **영양 밸런스 우수:** 전반적으로 영양소가 고르게 분포된 건강한 식단입니다.")
