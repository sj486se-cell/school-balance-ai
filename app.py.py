import networkx as nx

# 1. 그래프 생성 (지도 데이터 구조화)
G = nx.Graph()

# 2. 노드와 엣지 정의 (노드: 위치, 엣지: 연결 경로)
# weight: 거리, is_accessible: 계단/턱 유무 (True: 통행 가능, False: 장애물 있음)
edges = [
    ('입구', '광장', {'weight': 10, 'is_accessible': True}),
    ('광장', '카페', {'weight': 20, 'is_accessible': False}), # 카페 가는 길에 계단 존재
    ('광장', '우회로', {'weight': 15, 'is_accessible': True}),
    ('우회로', '카페', {'weight': 15, 'is_accessible': True})
]

for u, v, attr in edges:
    G.add_edge(u, v, **attr)

# 3. 교통약자용 최적 경로 탐색 함수
def get_accessible_path(graph, start, end):
    # 장애물이 있는 경로는 가중치를 매우 높게 설정 (피하도록 함)
    for u, v, data in graph.edges(data=True):
        if not data['is_accessible']:
            # 장애물이 있으면 가중치를 무한대(또는 매우 큰 값)로 변경
            graph[u][v]['weight'] = 999 
    
    # 다익스트라 알고리즘으로 최단 경로 탐색
    path = nx.shortest_path(graph, source=start, target=end, weight='weight')
    return path

# 실행
path = get_accessible_path(G, '입구', '카페')
print(f"교통약자를 위한 추천 경로: {' -> '.join(path)}")
