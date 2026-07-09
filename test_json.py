import json

json_data = """
{"contents":[{"originProductNo":11691446855,"channelProducts":[{"originProductNo":11691446855,"channelProductNo":11745910414,"channelServiceType":"STOREFARM","categoryId":"50003383","name":"FESTO 기관 호스 PUN-H-6x1-BL 9500M","statusType":"OUTOFSTOCK","channelProductDisplayStatusType":"ON","salePrice":5800000,"discountedPrice":5800000,"mobileDiscountedPrice":5800000,"stockQuantity":0,"knowledgeShoppingProductRegistration":true,"deliveryAttributeType":"NORMAL","deliveryFee":0,"returnFee":50000,"exchangeFee":100000,"managerPurchasePoint":1,"wholeCategoryName":"생활/건강>공구>에어공구>에어호스/게이지","wholeCategoryId":"50000008>50000165>50001025>50003383","representativeImage":{"url":"https://shop-phinf.pstatic.net/20250421_218/1745217987397jVxK1_PNG/42785239029895528_1016536894.png"},"sellerTags":[],"regDate":"2025-04-21T15:48:23.395+09:00","modifiedDate":"2025-11-25T09:55:34.303+09:00"}]}]}
"""
data = json.loads(json_data)
all_models = []

for item in data.get("contents", []):
    channel_products = item.get("channelProducts", [])
    for cp in channel_products:
        name = cp.get("name", "")
        if name:
            all_models.append(name)

print(f"Extracted {len(all_models)} models: {all_models}")
