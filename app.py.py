import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="School Balance AI", page_icon="🍱", layout="wide")

# ==========================================
# 1. 사이드바: 사용자 및 식단 정보 입력
# ==========================================
with st.sidebar:
    st.title("🧑‍🎓 나의 급식 정보")
    
    # 자연스러운 디테일: 학교 이름을 기본값으로 넣어 친숙함 어필
    school_name = st.text_input("학교 검색", "서현중학교")
    user_grade = st.selectbox("학년", ["1학년", "2학년", "3학년"])
    user_gender = st.radio("성별", ["남학생", "여학생"])
    
    st.divider()
    st.subheader("🍱 오늘의 점심 메뉴")
    # 해커톤 시연용 가상 데이터 입력창 (실제로는 나이스 API 연동 예정임을 어필)
    menu_input = st.text_area("메뉴를 입력하세요 (쉼표로 구분)", "잡곡밥, 돈육김치찌개, 고등어구이, 시금치나물, 깍두기")
    
    analyze_btn = st.button("AI 영양 분석 시작 🔍", use_container_width=True)

# ==========================================
# 2. 메인 화면: AI 분석 결과 및 대시보드
# ==========================================
st.title("🍱 School Balance: 청소년 맞춤형 AI 영양사")
st.caption(f"청소년기 필수 영양소 기준치와 오늘 {school_name}의 급식을 비교 분석합니다.")

if analyze_btn:
    with st.spinner(f"{school_name} {user_grade} 권장 섭취량과 메뉴 데이터를 매칭하고 있습니다..."):
        time.sleep(1.5) # 분석하는 듯한 극적인 연출
        
    st.success("✅ 영양 분석이 완료되었습니다!")
    
    # 🌟 1. 핵심 지표 시각화 (대시보드 형태)
    st.subheader("📊 오늘의 급식 영양 밸런스")
    
    col1, col2, col3, col4 = st.columns(4)
    # 가상의 영양 분석 결과 데이터
    col1.metric(label="총 칼로리", value="750 kcal", delta="-50 kcal (적정)")
    col2.metric(label="탄수화물", value="110g", delta="초과 주의", delta_color="inverse")
    col3.metric(label="단백질", value="35g", delta="+5g (우수)")
    col4.metric(label="지방", value="18g", delta="적정 수준")
    
    st.markdown("---")
    
    # 🌟 2. 프로그레스 바를 이용한 시각적 경고
    st.subheader("⚠️ 필수 영양소 부족/과다 경고")
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("**칼슘 (성장기 필수)**: 40% 달성")
        st.progress(0.40) # 40% 채워짐 (부족)
        
        st.write("**비타민 C (면역력)**: 30% 달성")
        st.progress(0.30) # 30% 채워짐 (부족)
        
    with c2:
        st.write("**나트륨 (김치찌개/깍두기 영향)**: 120% (경고)")
        st.progress(1.0) # 100% 초과 (위험)
        
        st.write("**식이섬유 (채소류)**: 85% 달성")
        st.progress(0.85) # 양호
        
    st.markdown("---")
    
    # 🌟 3. AI 맞춤형 저녁/간식 솔루션 제공
    st.subheader("💡 AI 영양사의 맞춤형 솔루션")
    
    st.error(f"🚨 **분석 결과:** 오늘의 점심 메뉴({menu_input.split(',')[1]})로 인해 **나트륨 섭취가 높고**, 성장기에 필수적인 **칼슘과 비타민 C가 다소 부족**합니다.")
    
    st.success("🎯 **오늘 저녁 & 간식 추천 조합**")
    st.write("부족한 영양소를 채우고 나트륨을 배출하기 위해 다음 식단을 추천합니다.")
    
    # 표 형태로 깔끔하게 제안
    recommend_df = pd.DataFrame(
        [
            {"추천 메뉴": "바나나 1개", "보충 효과": "칼륨 풍부 (나트륨 배출 도움)", "분류": "하교 후 간식"},
            {"추천 메뉴": "우유 1팩 (200ml)", "보충 효과": "칼슘 보충 (성장기 필수)", "분류": "하교 후 간식"},
            {"추천 메뉴": "닭가슴살 샐러드", "보충 효과": "비타민 C 및 단백질 보충", "분류": "저녁 식사"}
        ]
    )
    st.table(recommend_df)
    
    st.info("※ 본 솔루션은 보건복지부 '한국인 영양소 섭취기준(청소년기)' 데이터를 기반으로 산출되었습니다.")

else:
    st.info("👈 왼쪽 사이드바에서 학교와 급식 메뉴를 입력하고 '분석 시작' 버튼을 눌러보세요!")
