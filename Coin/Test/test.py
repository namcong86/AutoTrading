import matplotlib.font_manager as fm

# 시스템에 설치된 폰트 중 한글 폰트 목록을 출력합니다.
print("--- 사용 가능한 한글 폰트 목록 ---")
for font in fm.fontManager.ttflist:
    # 'Gothic', 'Malgun', 'Apple', 'Nanum', '명조' 등이 포함된 폰트 이름을 찾습니다.
    if any(keyword in font.name for keyword in ['Gothic', 'Malgun', 'Apple', 'Nanum', '명조']):
        print(f"폰트 이름: {font.name}, 경로: {font.fname}")
print("---------------------------------")