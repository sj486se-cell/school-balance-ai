import streamlit as st  # streamlit 라이브러리 추가
import networkx as nx

st.title("교통약자를 위한 배리어 프리 경로 안내") # 웹 화면 제목

# 1. 그래프 생성
G = nx.Graph()

# 2. 노드와 엣지 정의
edges = [
    ('입구', '광장', {'weight': 10, 'is_accessible': True}),
    ('광장', '카페', {'weight': 20, 'is_accessible': False}),
    ('광장', '우회로', {'weight': 15, 'is_accessible': True}),
    ('우회로', '카페', {'weight': 15, 'is_accessible': True})
]

for u, v, attr in edges:
    G.add_edge(u, v, **attr)

# 3. 경로 탐색 함수
def get_accessible_path(graph, start, end):
    for u, v, data in graph.edges(data=True):
        if not data['is_accessible']:
            graph[u][v]['weight'] = 999 
    path = nx.shortest_path(graph, source=start, target=end, weight='weight')
    return path

# 4. 실행 및 결과 출력
path = get_accessible_path(G, '입구', '카페')
st.write(f"교통약자를 위한 추천 경로: {' -> '.join(path)}") # print 대신 st.write 사용
