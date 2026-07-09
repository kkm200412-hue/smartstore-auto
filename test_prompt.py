import google.generativeai as genai
import json

genai.configure(api_key=json.load(open('api_config.json', encoding='utf-8')).get('gemini_api_key'))
model = genai.GenerativeModel('gemini-2.5-flash')

batch = [
    '한국 TPC 전자식 밸브 DS TVF3130 3230 3330 3430 61/5120 2120 53/5220',
    'SMC 정밀 압력 조절 밸브 IR2000-02 IR2010-02BG IR2020-02BG',
    'PLC Q64RD-G Q64TCTTBWN Q64TCRTBWN Q64TD V-GH QD62D QD62E QD63P6'
]

prompt = "다음은 공구/기계부품 등의 상품명 목록입니다. 각 상품명에서 진짜 '브랜드명', '모델명(부품 번호)', '핵심 품목명(예: 릴레이, 실린더, 센서 등)', 그리고 '상품 용도(Purpose)'를 찾아 JSON 배열로 반환하세요.\n"
prompt += "조건:\n1. 반환 형식은 [{\"brand\": \"...\", \"model\": \"...\", \"item\": \"...\", \"purpose\": \"...\"}] 이어야 합니다.\n2. 정보가 없으면 빈 문자열을 넣으세요.\n3. 입력 개수와 100% 동일한 길이의 배열을 반환해야 합니다.\n4. [중요] 만약 하나의 상품명 안에 모델명이 여러 개 존재할 경우, 가장 앞의 1개만 추출하지 말고 발견된 모든 모델명을 콤마(,)로 연결하여 모두 추출하세요.\n\n상품명 목록:\n"

for idx, name in enumerate(batch):
    prompt += f"{idx+1}. {name}\n"

res = model.generate_content(prompt, generation_config={'response_mime_type': 'application/json'})
print(res.text)
