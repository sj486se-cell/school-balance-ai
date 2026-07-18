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
            url += f"&KEY={NEIS_API
