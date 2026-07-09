import pandas as pd

# 1. 새로 분석할 상품 목록
data_new = {
    "상품명": [
        "나이키 에어포스 1 '07",
        "아디다스 삼바 OG",
        "뉴발란스 993 그레이",
        "컨버스 척테일러 올스타 하이",
        "나이키 에어맥스 97",
        "반스 올드스쿨 블랙",
        "푸마 스웨이드 클래식"
    ],
    "가격": [139000, 139000, 259000, 69000, 199000, 79000, 89000]
}
df_new = pd.DataFrame(data_new)
df_new.to_excel("sample_new_products.xlsx", index=False)

# 2. 내 스토어에 이미 있는 상품 목록 (모델명만 있거나 상품명)
data_store = {
    "스토어상품명": [
        "나이키 에어포스 인기 신발",
        "뉴발란스 993 그레이 운동화",
        "컨버스 척테일러 올스타 하이"
    ],
    "등록모델명": [
        "에어포스 1 '07",
        "993 그레이",
        "척테일러 올스타 하이"
    ]
}
df_store = pd.DataFrame(data_store)
df_store.to_excel("sample_store_products.xlsx", index=False)

print("샘플 파일 생성 완료!")
