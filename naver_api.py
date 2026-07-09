import time
import bcrypt
import pybase64
import requests
import datetime

class NaverCommerceAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        
    def generate_token(self):
        timestamp = str(int(time.time() * 1000))
        password = f"{self.client_id}_{timestamp}"
        hashed = bcrypt.hashpw(password.encode("utf-8"), self.client_secret.encode("utf-8"))
        client_secret_sign = pybase64.standard_b64encode(hashed).decode("utf-8")
        
        url = "https://api.commerce.naver.com/external/v1/oauth2/token"
        data = {
            "client_id": self.client_id,
            "timestamp": timestamp,
            "client_secret_sign": client_secret_sign,
            "grant_type": "client_credentials",
            "type": "SELF"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            if "access_token" in token_data:
                self.access_token = token_data["access_token"]
                return True, "토큰 발급 성공"
        
        return False, f"인증 실패: {response.text}"

    def get_all_products(self):
        """네이버 커머스 API를 통해 모든 상품의 모델명을 가져옵니다."""
        if not self.access_token:
            success, msg = self.generate_token()
            if not success:
                return False, msg, [], {}

        url = "https://api.commerce.naver.com/external/v1/products/search"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        all_models = []
        page = 1
        size = 50
        last_data = {}
        
        # 네이버 API는 기간이 없으면 최근 1일만 조회할 가능성이 높습니다.
        # 따라서 등록일 기준으로 넉넉하게 기간을 설정합니다.
        today = datetime.date.today()
        # 일단 최근 10년으로 설정 (API 제한이 있다면 에러가 날 수 있음)
        try:
            start_date = today.replace(year=today.year - 10)
        except ValueError:
            start_date = today.replace(year=today.year - 10, day=today.day - 1)
            
        while True:
            payload = {
                "page": page,
                "size": size,
                "orderType": "NO",
                "periodType": "PROD_REG_DAY",
                "fromDate": start_date.strftime("%Y-%m-%d"),
                "toDate": today.strftime("%Y-%m-%d"),
                "productStatusTypes": ["SALE", "OUTOFSTOCK"]
            }
            
            retries = 3
            while retries > 0:
                response = requests.post(url, json=payload, headers=headers)
                
                if response.status_code == 429:
                    time.sleep(2)  # Rate limit hit, wait 2 seconds and retry
                    retries -= 1
                    continue
                    
                if response.status_code != 200:
                    return False, f"상품 조회 에러 ({response.status_code}): {response.text}", [], {}
                
                break
                
            if retries == 0:
                return False, "요청이 너무 많아 API 호출이 차단되었습니다. 잠시 후 다시 시도해주세요.", [], {}
                
            data = response.json()
            last_data = data
            contents = data.get("contents", [])
            
            if not contents:
                break
                
            for item in contents:
                # API 응답 구조에 맞게 channelProducts 배열에서 상품명을 추출
                channel_products = item.get("channelProducts", [])
                for cp in channel_products:
                    name = cp.get("name", "")
                    if name:
                        all_models.append(name)
                    
            if len(contents) < size:
                break
                
            page += 1
            time.sleep(0.3) # API Rate Limit 방지를 위한 지연
            
        return True, "상품 조회 성공", list(set(all_models)), last_data


    def upload_image(self, image_path):
        import mimetypes
        import os
        if not self.access_token:
            success, msg = self.generate_token()
            if not success:
                return False, f"토큰 발급 실패: {msg}", ""

        url = "https://api.commerce.naver.com/external/v1/product-images/upload"
        mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            with open(image_path, "rb") as f:
                files = [("imageFiles", (os.path.basename(image_path), f, mime))]
                r = requests.post(url, headers=headers, files=files, timeout=60)
            
            if r.status_code >= 400:
                return False, f"이미지 업로드 실패 {r.status_code}: {r.text}", ""
                
            data = r.json()
            if isinstance(data, dict):
                if "images" in data and data["images"]:
                    img = data["images"][0]
                    return True, "성공", img.get("url") or img.get("imageUrl")
                if "imageUrls" in data and data["imageUrls"]:
                    return True, "성공", data["imageUrls"][0]
                if "url" in data:
                    return True, "성공", data["url"]
            return False, f"이미지 업로드 URL 확인 실패: {data}", ""
        except Exception as e:
            return False, f"이미지 업로드 예외 발생: {str(e)}", ""

    def make_detail_html(self, p):
        return f"""
<div style="max-width:900px;margin:auto;font-family:'Malgun Gothic',sans-serif;color:#222;line-height:1.8;background:#fff;">
  <div style="background:#111;padding:38px 30px;border-radius:12px 12px 0 0;text-align:center;">
    <h1 style="color:#fff;font-size:30px;margin:0;">{p['상품명']}</h1>
    <p style="color:#ccc;font-size:15px;margin-top:10px;">Industrial Automation Components</p>
  </div>

  <div style="border:1px solid #ddd;border-top:none;padding:35px;background:#fafafa;">
    <h2 style="font-size:24px;border-left:6px solid #111;padding-left:14px;margin:0 0 22px 0;">상품 정보</h2>

    <table style="width:100%;border-collapse:collapse;font-size:17px;">
      <tr>
        <td style="width:180px;padding:16px;background:#eee;border:1px solid #ddd;font-weight:bold;">브랜드</td>
        <td style="padding:16px;border:1px solid #ddd;background:#fff;">{p['브랜드']}</td>
      </tr>
      <tr>
        <td style="padding:16px;background:#eee;border:1px solid #ddd;font-weight:bold;">모델명</td>
        <td style="padding:16px;border:1px solid #ddd;background:#fff;">{p['모델명']}</td>
      </tr>
      <tr>
        <td style="padding:16px;background:#eee;border:1px solid #ddd;font-weight:bold;">용도</td>
        <td style="padding:16px;border:1px solid #ddd;background:#fff;">{p.get('용도', '')}</td>
      </tr>
    </table>

    <div style="margin-top:38px;padding:34px 24px;background:#fff;border:3px solid #111;border-radius:14px;text-align:center;">
      <div style="font-size:27px;font-weight:900;color:#111;margin-bottom:14px;">제품견적 문의</div>
      <div style="font-size:38px;font-weight:900;color:#d60000;letter-spacing:1px;line-height:1.25;">010-2208-7194</div>
      <div style="font-size:27px;font-weight:800;color:#111;margin-top:14px;line-height:1.35;">kkm190412@naver.com</div>
      <div style="font-size:15px;color:#555;margin-top:18px;line-height:1.7;">
        필요하신 모델명과 수량을 문자로 남겨주시면<br>
        빠르게 확인 후 답변드리겠습니다.
      </div>
    </div>

    <h2 style="font-size:23px;border-left:6px solid #111;padding-left:14px;margin-top:45px;">구매 전 안내</h2>
    <p style="font-size:16px;color:#444;">본 상품은 산업 자동화 및 설비 유지보수용 부품입니다. 구매 전 모델명과 사양을 반드시 확인해 주세요.</p>
    <p style="font-size:16px;color:#444;">해외 재고 또는 구매대행 상품의 경우 발송 및 배송기간이 추가 소요될 수 있습니다.</p>
  </div>
</div>
"""

    def build_payload(self, p, config, image_url):
        leaf_category_id = config.get("default_category_id", "")
        if not leaf_category_id:
            raise ValueError("카테고리ID가 비어 있습니다.")

        as_tel = config.get("as_tel", "010-2208-7194")
        as_name = config.get("as_name", "대한종합상사")
        shipping_address_id = int(config.get("shipping_address_id", 0))
        return_address_id = int(config.get("return_address_id", 0))
        if not shipping_address_id or not return_address_id:
            raise ValueError("shipping_address_id, return_address_id가 설정되지 않았습니다.")

        base_fee = int(config.get("delivery_base_fee", 0))
        return_fee = int(config.get("return_delivery_fee", 50000))
        exchange_fee = int(config.get("exchange_delivery_fee", 100000))
        delivery_company = config.get("delivery_company", "CJGLS")
        
        detail_attribute = {
            "naverShoppingSearchInfo": {
                "modelName": p["모델명"],
                "manufacturerName": p["제조사"],
                "brandName": p["브랜드"],
                "manufactureDefineNo": p["모델명"]
            },
            "afterServiceInfo": {
                "afterServiceTelephoneNumber": as_tel,
                "afterServiceGuideContent": f"{as_name} / {as_tel}"
            },
            "originAreaInfo": {
                "originAreaCode": "03",
                "content": "기타",
                "plural": False
            },
            "taxType": "TAX",
            "minorPurchasable": True,
            "certificationTargetExcludeContent": {
                "kcCertifiedProductExclusionYn": "KC_EXEMPTION_OBJECT",
                "kcExemptionType": "OVERSEAS"
            },
            "purchaseReviewInfo": {
                "purchaseReviewExposure": True
            },
            "sellerCommentUsable": False,
            "itselfProductionProductYn": False,
            "productInfoProvidedNotice": {
                "productInfoProvidedNoticeType": "ETC",
                "etc": {
                    "itemName": p["모델명"],
                    "modelName": p["모델명"],
                    "manufacturer": p["제조사"] or p["브랜드"] or "상품상세참조",
                    "returnCostReason": "상품상세참조",
                    "noRefundReason": "상품상세참조",
                    "qualityAssuranceStandard": "상품상세참조",
                    "compensationProcedure": "상품상세참조",
                    "troubleShootingContents": "상품상세참조",
                    "customerServicePhoneNumber": as_tel
                }
            },
            "customMadeInfo": {
                "customMade": True
            }
        }

        delivery_info = {
            "deliveryType": "DELIVERY",
            "deliveryAttributeType": "NORMAL",
            "deliveryCompany": delivery_company,
            "deliveryBundleGroupUsable": False,
            "deliveryFee": {
                "deliveryFeeType": "FREE" if base_fee == 0 else "PAID",
                "baseFee": base_fee,
                "deliveryFeePayType": "PREPAID"
            },
            "claimDeliveryInfo": {
                "returnDeliveryCompanyPriorityType": "PRIMARY",
                "returnDeliveryFee": return_fee,
                "exchangeDeliveryFee": exchange_fee,
                "shippingAddressId": shipping_address_id,
                "returnAddressId": return_address_id,
                "freeReturnInsuranceYn": False
            },
            "installationFee": False,
            "customProductAfterOrderYn": True,
            "expectedDeliveryPeriodType": "FOURTEEN"
        }

        payload = {
            "originProduct": {
                "statusType": "SALE",
                "saleType": "NEW",
                "leafCategoryId": str(leaf_category_id),
                "name": p["상품명"],
                "detailContent": self.make_detail_html(p),
                "images": {
                    "representativeImage": {"url": image_url},
                    "optionalImages": []
                },
                "salePrice": p["판매가격"],
                "stockQuantity": p["재고"],
                "deliveryInfo": delivery_info,
                "detailAttribute": detail_attribute
            },
            "smartstoreChannelProduct": {
                "channelProductDisplayStatusType": "ON",
                "naverShoppingRegistration": True,
                "storeKeepExclusiveProduct": False
            }
        }

        return payload

    def register_product(self, payload):
        if not self.access_token:
            success, msg = self.generate_token()
            if not success:
                return False, f"토큰 발급 실패: {msg}", {}

        url = "https://api.commerce.naver.com/external/v2/products"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            trace_id = r.headers.get("GNCP-GW-Trace-ID", "")
            if r.status_code >= 400:
                return False, f"상품 등록 실패 {r.status_code}: {r.text} / TraceID: {trace_id}", {}
            
            data = r.json() if r.text else {}
            if trace_id:
                data["_trace_id"] = trace_id
            return True, "상품 등록 성공", data
        except Exception as e:
            return False, f"API 예외 발생: {str(e)}", {}
