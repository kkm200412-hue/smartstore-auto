import streamlit as st
import pandas as pd
import io
import json
from naver_api import NaverCommerceAPI
import scraper

st.set_page_config(page_title="스마트스토어 상품 분석기", layout="wide")

st.title("🛍️ 스마트스토어 상품명 분석 및 등록 확인 (API 연동 버전)")
st.markdown("엑셀에 등록된 상품명을 분석하고, **네이버 커머스 API**를 통해 내 스토어에 이미 등록되어 있는지 실시간으로 확인합니다.")

# Initialize session state for store models
if "store_models" not in st.session_state:
    import os, json
    st.session_state.store_models = []
    if os.path.exists("store_models_cache.json"):
        try:
            with open("store_models_cache.json", "r", encoding="utf-8") as f:
                st.session_state.store_models = json.load(f)
        except: pass

# Sidebar for instructions and API setup
with st.sidebar:
    st.header("⚙️ 네이버 커머스 API 설정")
    st.markdown("""
    [네이버 커머스 API 센터](https://apicenter.commerce.naver.com/)에서 발급받은 애플리케이션 정보를 입력해주세요.
    **(입력하신 정보는 내 PC에 안전하게 자동 저장되어 새로고침해도 유지됩니다.)**
    """)
    
    import os
    config_file = "api_config.json"
    api_config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                api_config = json.load(f)
        except: pass

    client_id = st.text_input("Client ID", value=api_config.get("client_id", ""), type="password")
    client_secret = st.text_input("Client Secret", value=api_config.get("client_secret", ""), type="password")
    st.markdown("---")
    gemini_api_key = st.text_input("Gemini API Key (선택, AI 자동분리용)", value=api_config.get("gemini_api_key", ""), type="password")
    
    with st.expander("📦 자동 업로드 필수 설정", expanded=False):
        st.caption("스마트스토어 API 업로드를 위한 필수 설정입니다.")
        new_cat = st.text_input("기본 카테고리 ID (예: 50000001)", value=api_config.get("default_category_id", ""))
        new_ship = st.text_input("출고지 주소록 번호 (숫자)", value=api_config.get("shipping_address_id", ""))
        new_ret = st.text_input("반품지 주소록 번호 (숫자)", value=api_config.get("return_address_id", ""))
        new_as_tel = st.text_input("A/S 전화번호", value=api_config.get("as_tel", "010-2208-7194"))
        new_as_name = st.text_input("A/S 상호명", value=api_config.get("as_name", "대한종합상사"))
        new_img_dir = st.text_input("PC 이미지 폴더 경로", value=api_config.get("image_dir", r"C:\\Images"))
        
        if st.button("설정 저장", key="save_upload_settings"):
            api_config.update({
                "client_id": client_id,
                "client_secret": client_secret,
                "gemini_api_key": gemini_api_key,
                "default_category_id": new_cat,
                "shipping_address_id": new_ship,
                "return_address_id": new_ret,
                "as_tel": new_as_tel,
                "as_name": new_as_name,
                "image_dir": new_img_dir
            })
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(api_config, f, ensure_ascii=False, indent=2)
            st.success("설정이 저장되었습니다.")

    if st.button("내 스토어 상품 동기화", type="primary"):
        if not client_id or not client_secret:
            st.error("Client ID와 Client Secret을 모두 입력해주세요.")
        else:
            api_config["client_id"] = client_id
            api_config["client_secret"] = client_secret
            api_config["gemini_api_key"] = gemini_api_key
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(api_config, f, ensure_ascii=False, indent=2)
            with st.spinner("네이버 스토어에서 상품 목록을 불러오는 중..."):
                api = NaverCommerceAPI(client_id, client_secret)
                success, msg, models, raw_data = api.get_all_products()
                
                if success:
                    st.session_state.store_models = [str(m).replace(" ", "").lower() for m in models]
                    try:
                        with open("store_models_cache.json", "w", encoding="utf-8") as f:
                            json.dump(st.session_state.store_models, f)
                    except: pass
                    
                    if len(models) == 0:
                        st.warning("API 통신은 성공했지만, 상품이 0개 검색되었습니다.")
                        with st.expander("원인 파악을 위한 API 응답 데이터 보기"):
                            st.json(raw_data)
                    else:
                        st.success(f"성공적으로 상품 {len(models)}개를 불러왔습니다!")
                else:
                    st.error(f"동기화 실패: {msg}")
                    st.session_state.store_models = []

    st.divider()
    st.header("사용 방법")
    st.markdown("""
    1. 왼쪽 메뉴에서 API 키를 입력하고 **내 스토어 상품 동기화**를 누르세요.
    2. 분석할 **새 상품 엑셀 파일**을 업로드하세요.
    3. 엑셀에서 분석할 열과 분리 규칙을 선택하세요.
    4. 분석 시작 버튼을 누르고 결과를 확인하세요.
    """)

# Main Layout
tab1, tab2, tab3, tab4 = st.tabs(["🔍 1단계: 상품 수집", "📊 2단계: 상품 분석", "✍️ 3단계: 상품 등록 작업", "✅ 4단계: 등록 완료"])


with tab1:
    st.subheader("1. 스마트스토어 카테고리 URL 수집")
    st.markdown("수집할 카테고리 URL을 한 줄에 하나씩 입력하세요. 첫 페이지만 수집합니다.")
    
    url_input = st.text_area("스마트스토어 URL", height=200, placeholder="https://smartstore.naver.com/...\nhttps://smartstore.naver.com/...")
    
    c1, c2 = st.columns(2)
    use_best = c1.checkbox("BEST 상품 수집", value=True)
    use_review = c2.checkbox("리뷰 많은순 + 리뷰 있는 상품만 수집", value=True)
    headless = st.checkbox("백그라운드에서 조용히 수집 (화면에 브라우저 안 띄움)", value=True)
    
    if st.button("수집 시작", type="primary", use_container_width=True):
        urls = url_input.splitlines()
        if not urls or not any(u.strip() for u in urls):
            st.warning("URL을 입력해주세요.")
        elif not use_best and not use_review:
            st.warning("수집 방식을 하나 이상 선택해주세요.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(idx, total, store_name):
                progress_bar.progress(idx / total)
                status_text.text(f"{idx}/{total} 수집 중: {store_name}")
                
            with st.spinner("상품 정보를 수집하고 있습니다. 완료될 때까지 기다려주세요..."):
                success, msg, df, fail_list = scraper.run_collection(
                    urls, use_best, use_review, headless, update_progress
                )
                
            if success:
                status_text.text("수집 완료!")
                st.success(f"총 {len(df)}개의 상품 정보 수집을 완료했습니다!")
                if fail_list:
                    st.warning(f"일부 URL은 수집에 실패했거나 0개 수집됨:\n" + "\n".join(fail_list[:10]))
                    
                st.session_state.df_scraped = df
                st.dataframe(df)
            else:
                st.error(msg)
                
    if 'df_scraped' in st.session_state and not st.session_state.df_scraped.empty:
        st.markdown("---")
        st.success("🎉 방금 수집한 데이터가 준비되어 있습니다! [2단계: 상품 분석] 탭으로 이동해서 파일 업로드 없이 바로 분석을 시작할 수 있습니다.")
        
        # Download button for scraped data
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            st.session_state.df_scraped.to_excel(writer, index=False)
        st.download_button(
            label="수집된 원본 엑셀 다운로드",
            data=buffer.getvalue(),
            file_name="scraped_result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with tab2:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("1. 분석할 상품 목록 선택")
        source_option = st.radio("데이터 소스 선택:", ["방금 수집한 데이터 사용", "새 엑셀 파일 업로드"])
        
        df_new = None
        if source_option == "방금 수집한 데이터 사용":
            if 'df_scraped' in st.session_state and not st.session_state.df_scraped.empty:
                df_new = st.session_state.df_scraped.copy()
                st.success("✅ 수집된 데이터를 불러왔습니다.")
            else:
                st.warning("⚠️ 1단계에서 수집한 데이터가 없습니다. 1단계로 가서 먼저 수집을 진행하거나 엑셀 파일을 업로드하세요.")
        else:
            new_products_file = st.file_uploader("새 상품 엑셀 파일 선택", type=["xlsx", "xls"], key="new")
            if new_products_file is not None:
                df_new = pd.read_excel(new_products_file)
                st.success("✅ 엑셀 파일을 성공적으로 불러왔습니다.")

    with col2:
        st.subheader("2. 내 스토어 연동 상태")
        if len(st.session_state.store_models) > 0:
            st.success(f"✅ **{len(st.session_state.store_models)}개**의 스토어 상품 정보가 동기화되어 있습니다.")
            st.info("비교 준비 완료! 이제 엑셀 파일을 업로드하고 분석을 시작하세요.")
        elif st.session_state.get('store_models') == []:
            st.warning("⚠️ 스토어 상품이 동기화되지 않았거나 0개입니다. 좌측 메뉴에서 동기화를 진행해주세요.")

    if df_new is not None:
        if len(st.session_state.store_models) == 0:
            st.error("스토어 상품이 0개이거나 동기화되지 않았습니다. 동기화를 성공적으로 마친 후 진행해주세요.")
        else:
            try:
                st.subheader("3. 열(Column) 및 규칙 설정")
                col_name_new = st.selectbox("분석할 상품 목록에서 '상품명'이 있는 열을 선택하세요:", df_new.columns)
                model_col_options = ["(자동 추출 사용)"] + list(df_new.columns)
                model_col_new = st.selectbox("이미 '모델명'이 분리된 열이 있다면 선택하세요 (없으면 '자동 추출' 유지):", model_col_options)
                
                split_rule = st.radio("상품명 자동 분리 규칙 ('자동 추출'을 선택한 경우 작동):", 
                    ["[최강 AI] Gemini 실시간 완벽 추출 (가장 정확, 좌측에 API Key 필요)",
                     "[추천] 영문/숫자 조합 스마트 추출 (예: 'Banner 스위치 OTBVN6' -> 모델명: OTBVN6)",
                     "첫 번째 띄어쓰기를 기준으로 분리 (예: '나이키 에어포스' -> 브랜드: 나이키, 모델명: 에어포스)", 
                     "직접 분리 기호 입력"]
                )
                
                custom_delimiter = ""
                if "직접 분리 기호" in split_rule:
                    custom_delimiter = st.text_input("분리 기호 (예: -, _, 또는 공백):", value=" ")
                    
                if st.button("분석 시작", type="primary", use_container_width=True):
                    with st.spinner("스토어 상품과 비교하는 중..."):
                        df_result = df_new.copy()
                        
                        if model_col_new != "(자동 추출 사용)":
                            df_result['추출_모델명'] = df_result[model_col_new].astype(str)
                            if '브랜드' in df_new.columns: df_result['추출_브랜드'] = df_result['브랜드'].astype(str)
                            else: df_result['추출_브랜드'] = ""
                        else:
                            if "[최강 AI]" in split_rule:
                                if not gemini_api_key:
                                    st.error("이 기능을 사용하려면 좌측 설정 메뉴에 Gemini API Key를 입력해야 합니다!")
                                    st.stop()
                                import google.generativeai as genai
                                import time
                                genai.configure(api_key=gemini_api_key)
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                
                                product_names = df_result[col_name_new].astype(str).tolist()
                                brand_list, model_list, item_list, purpose_list = [], [], [], []
                                batch_size = 40
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                for i in range(0, len(product_names), batch_size):
                                    batch = product_names[i:i+batch_size]
                                    status_text.text(f"Gemini AI가 상품명을 분석 중입니다... ({min(i+batch_size, len(product_names))}/{len(product_names)} 개 완료)")
                                    prompt = "다음은 공구/기계부품 등의 상품명 목록입니다. 각 상품명에서 진짜 '브랜드명', '모델명(부품 번호)', '핵심 품목명(예: 릴레이, 실린더, 센서 등)', 그리고 '상품 용도(Purpose)'를 찾아 JSON 배열로 반환하세요.\n"
                                    prompt += "조건:\n1. 반환 형식은 [{\"brand\": \"...\", \"model\": \"...\", \"item\": \"...\", \"purpose\": \"...\"}] 이어야 합니다.\n2. 정보가 없으면 빈 문자열을 넣으세요.\n3. 입력 개수와 100% 동일한 길이의 배열을 반환해야 합니다.\n\n상품명 목록:\n"
                                    for idx, name in enumerate(batch):
                                        if str(name).lower() == 'nan' or not str(name).strip(): name = "Unknown"
                                        prompt += f"{idx+1}. {name}\n"
                                        
                                    try:
                                        res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                                        text = res.text.strip()
                                        if text.startswith("```json"): text = text[7:]
                                        if text.startswith("```"): text = text[3:]
                                        if text.endswith("```"): text = text[:-3]
                                        batch_result = json.loads(text.strip())
                                        while len(batch_result) < len(batch): batch_result.append({"brand": "", "model": "", "item": "", "purpose": ""})
                                        for r in batch_result[:len(batch)]:
                                            brand_list.append(str(r.get("brand", "")))
                                            model_list.append(str(r.get("model", "")))
                                            item_list.append(str(r.get("item", "")))
                                            purpose_list.append(str(r.get("purpose", "")))
                                    except Exception as e:
                                        st.error(f"AI API 통신 중 에러 발생 (배치 {i}~): {e}")
                                        for _ in batch:
                                            brand_list.append("AI Error")
                                            model_list.append("AI Error")
                                            item_list.append("AI Error")
                                            purpose_list.append("AI Error")
                                            
                                    progress_bar.progress(min((i + batch_size) / len(product_names), 1.0))
                                    time.sleep(3)
                                    
                                status_text.text("AI 분석이 성공적으로 완료되었습니다!")
                                df_result['추출_브랜드'] = brand_list[:len(df_result)]
                                df_result['추출_모델명'] = model_list[:len(df_result)]
                                df_result['추출_품목'] = item_list[:len(df_result)]
                                df_result['용도'] = purpose_list[:len(df_result)]
                                
                            elif "[추천]" in split_rule:
                                import re
                                def smart_extract(text):
                                    text = str(text)
                                    words = text.split()
                                    if not words: return "", ""
                                    brand = words[0]
                                    candidates = []
                                    for w in words[1:]:
                                        if bool(re.search(r'[A-Za-z]', w)) and bool(re.search(r'[0-9]', w)): candidates.append(w)
                                    if not candidates:
                                        for w in words[1:]:
                                            if bool(re.search(r'[A-Za-z]', w)) and bool(re.search(r'[\-\/]', w)): candidates.append(w)
                                    if candidates: model = max(candidates, key=len)
                                    else: model = " ".join(words[1:]) if len(words) > 1 else ""
                                    return pd.Series([brand, model])
                                df_result[['추출_브랜드', '추출_모델명']] = df_result[col_name_new].apply(smart_extract)
                                
                            elif "첫 번째 띄어쓰기" in split_rule:
                                split_data = df_result[col_name_new].astype(str).str.split(' ', n=1, expand=True)
                                df_result['추출_브랜드'] = split_data[0] if split_data.shape[1] > 0 else ""
                                df_result['추출_모델명'] = split_data[1] if split_data.shape[1] > 1 else ""
                            else:
                                split_data = df_result[col_name_new].astype(str).str.split(custom_delimiter, n=1, expand=True)
                                df_result['추출_브랜드'] = split_data[0] if split_data.shape[1] > 0 else ""
                                df_result['추출_모델명'] = split_data[1] if split_data.shape[1] > 1 else ""
                        
                        df_result['추출_브랜드'] = df_result['추출_브랜드'].fillna("").str.strip()
                        df_result['추출_모델명'] = df_result['추출_모델명'].fillna("").str.strip()
                        
                        if '추출_품목' not in df_result.columns:
                            items = []
                            for idx, row in df_result.iterrows():
                                nm = str(row[col_name_new])
                                br = str(row['추출_브랜드'])
                                mo = str(row['추출_모델명'])
                                if br and br in nm: nm = nm.replace(br, "", 1)
                                if mo and mo in nm: nm = nm.replace(mo, "", 1)
                                items.append(" ".join(nm.split()))
                            df_result['추출_품목'] = items
                            
                        df_result['추출_품목'] = df_result['추출_품목'].fillna("").str.strip()
                        
                        df_result['추천_스토어상품명'] = df_result.apply(
                            lambda x: f"{x['추출_브랜드']} {x['추출_모델명']} {x['추출_품목']}".strip().replace("  ", " ").replace("  ", " "), axis=1
                        )
                        
                        df_result['타오바오_단가'] = None
                        df_result['최종_판매가'] = ""
                        import urllib.parse
                        df_result['이미지_검색'] = df_result.apply(
                            lambda x: f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(str(x['추출_브랜드']) + ' ' + str(x['추출_모델명']))}", axis=1
                        )
                        
                        def check_registration(model_name):
                            clean_model = str(model_name).replace(" ", "").lower()
                            if not clean_model: return "확인 불가 (모델명 없음)"
                            for store_model in st.session_state.store_models:
                                if clean_model in store_model or store_model in clean_model: return "✅ 기등록"
                            return "❌ 미등록 (신규)"
                                
                        df_result['스토어_등록여부'] = df_result['추출_모델명'].apply(check_registration)
                        
                        # 기등록 제외 필터링 (미등록만 남기기)
                        total_cnt = len(df_result)
                        df_unregistered = df_result[df_result['스토어_등록여부'] == "❌ 미등록 (신규)"].copy()
                        
                        import os
                        df_unregistered.to_pickle("last_analysis.pkl")
                        st.session_state.analysis_done = True
                        st.session_state.filtered_cnt = total_cnt - len(df_unregistered)
            except Exception as e:
                st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")
                        
            if st.session_state.get("analysis_done", False):
                st.success(f"🎉 분석이 완료되었습니다! 이미 등록된 {st.session_state.get('filtered_cnt', 0)}개의 상품을 제외하고 저장했습니다.\n\n**이제 화면 상단의 [✍️ 3단계: 상품 등록 작업] 탭을 클릭하여 가격을 입력하세요.**")

with tab3:
    import os
    if os.path.exists("last_analysis.pkl"):
        try:
            df_result = pd.read_pickle("last_analysis.pkl")
            
            st.subheader("🧮 타오바오 연동 판매가 일괄 계산기")
            
            with st.container():
                c1, c2, c3 = st.columns(3)
                ex_rate = c1.number_input("적용 환율 (원/위안)", value=230.0, step=1.0)
                margin_rate = c2.number_input("목표 마진율 (%)", value=35.0, step=1.0)
                shipping_fee = c3.number_input("기본 배송비 (원)", value=10000, step=100)
                
                if st.button("🔄 '타오바오_단가' 입력값 기준으로 최종 판매가 일괄 계산", type="primary", use_container_width=True):
                    import math
                    for idx, row in df_result.iterrows():
                        try:
                            tb_price = float(row['타오바오_단가'])
                            if not pd.isna(tb_price):
                                final_price = (tb_price * ex_rate) * (1 + margin_rate / 100) + shipping_fee
                                final_price = math.ceil(final_price / 100) * 100
                                df_result.at[idx, '최종_판매가'] = str(int(final_price))
                        except:
                            pass
                    df_result.to_pickle("last_analysis.pkl")
                    st.success("판매가 계산이 갱신되었습니다!")
                    import time
                    time.sleep(0.5)
                    st.rerun()
                    
            st.markdown("---")
            
            # --- 선택 기능 및 액션 버튼 ---
            if "선택" not in df_result.columns:
                df_result["선택"] = False
                df_result.to_pickle("last_analysis.pkl")
            
            st.info("💡 드래그나 엑셀 방식 조작이 불편하시다면 아래 **범위 선택기**를 사용해 지정된 번호(인덱스)만큼 한 번에 체크하세요!")
            
            sel_col1, sel_col2, sel_col3, sel_col4 = st.columns(4)
            with sel_col1:
                if st.button("☑️ 전체 선택", use_container_width=True):
                    df_result["선택"] = True
                    df_result.to_pickle("last_analysis.pkl")
                    st.rerun()
            with sel_col2:
                if st.button("⬜ 전체 해제", use_container_width=True):
                    df_result["선택"] = False
                    df_result.to_pickle("last_analysis.pkl")
                    st.rerun()
            with sel_col3:
                start_idx = st.number_input("시작 번호", min_value=0, max_value=max(0, len(df_result)-1), value=0, step=1, label_visibility="collapsed")
            with sel_col4:
                end_idx = st.number_input("종료 번호", min_value=0, max_value=max(0, len(df_result)-1), value=min(4, max(0, len(df_result)-1)), step=1, label_visibility="collapsed")
            
            if st.button(f"🎯 선택한 {start_idx}번부터 {end_idx}번까지 한번에 체크 켜기", use_container_width=True):
                s = min(start_idx, end_idx)
                e = max(start_idx, end_idx)
                # Ensure we use positional indexing since user sees sequential numbers
                df_result.iloc[s:e+1, df_result.columns.get_loc("선택")] = True
                df_result.to_pickle("last_analysis.pkl")
                st.rerun()
            
            # 숨길 열 선택
            col_opts = [c for c in df_result.columns if c != "선택"]
            hide_cols = st.multiselect("👀 표에서 숨길 열(Column)을 선택하세요", options=col_opts, default=[])
            
            # 버튼 영역
            action_col1, action_col2, action_col3 = st.columns([1, 1.5, 1.5])
            with action_col1:
                if st.button("🗑️ 선택한 행 삭제", type="secondary", use_container_width=True):
                    if df_result["선택"].any():
                        df_result = df_result[~df_result["선택"]].copy()
                        df_result.to_pickle("last_analysis.pkl")
                        st.success("선택한 행이 삭제되었습니다.")
                        import time
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.warning("선택된 항목이 없습니다.")
                        
            with action_col2:
                if st.button("🚀 선택 항목 자동 업로드", type="primary", use_container_width=True):
                    if df_result["선택"].any():
                        selected_items = df_result[df_result["선택"]].copy()
                        
                        # Load Config
                        conf = {}
                        if os.path.exists("api_config.json"):
                            with open("api_config.json", "r", encoding="utf-8") as f:
                                conf = json.load(f)
                        
                        cid = conf.get("client_id")
                        csec = conf.get("client_secret")
                        if not cid or not csec:
                            st.error("좌측 사이드바에서 API 키를 입력해주세요.")
                        else:
                            api = NaverCommerceAPI(cid, csec)
                            success_count = 0
                            fail_count = 0
                            errors = []
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            successful_indices = []
                            
                            for i, (idx, row) in enumerate(selected_items.iterrows()):
                                progress = (i + 1) / len(selected_items)
                                status_text.text(f"업로드 진행 중... ({i+1}/{len(selected_items)}) - {row.get('추출_모델명', '')}")
                                
                                try:
                                    model = str(row.get("추출_모델명", "")).strip()
                                    if not model:
                                        raise ValueError("추출_모델명이 비어있습니다.")
                                        
                                    # Find Image
                                    img_dir = conf.get("image_dir", r"C:\Images")
                                    img_path = None
                                    for ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
                                        p = os.path.join(img_dir, model + ext)
                                        if os.path.exists(p):
                                            img_path = p
                                            break
                                    if not img_path:
                                        default_p = os.path.join(img_dir, "default.jpg")
                                        if os.path.exists(default_p):
                                            img_path = default_p
                                        else:
                                            raise FileNotFoundError(f"'{img_dir}' 폴더 내에 '{model}.jpg' 또는 'default.jpg' 파일이 없습니다.")
                                            
                                    # 1. Upload Image
                                    success, msg, img_url = api.upload_image(img_path)
                                    if not success:
                                        raise RuntimeError(f"이미지 업로드 실패: {msg}")
                                        
                                    # 2. Build Payload
                                    def safe_str(val):
                                        s = str(val).strip()
                                        return "" if s.lower() in ["nan", "none", "nat"] else s

                                    price_str = safe_str(row.get("최종_판매가", "0")).replace(",", "")
                                    price_val = int(float(price_str)) if price_str else 0

                                    brand_str = safe_str(row.get("브랜드", ""))
                                    
                                    p_dict = {
                                        "모델명": model,
                                        "상품명": safe_str(row.get("추천_스토어상품명", model)),
                                        "판매가격": price_val,
                                        "브랜드": brand_str,
                                        "제조사": safe_str(row.get("제조사", brand_str)),
                                        "용도": safe_str(row.get("용도", "")),
                                        "재고": 999
                                    }
                                    
                                    if p_dict["판매가격"] <= 0:
                                        raise ValueError("최종_판매가가 올바르지 않습니다. (타오바오 단가를 입력했는지 확인하세요)")
                                        
                                    payload = api.build_payload(p_dict, conf, img_url)
                                    
                                    # 3. Register Product
                                    r_success, r_msg, r_data = api.register_product(payload)
                                    if not r_success:
                                        raise RuntimeError(f"상품 등록 실패: {r_msg}")
                                        
                                    success_count += 1
                                    successful_indices.append(idx)
                                    
                                    # 네이버 API 제한(Rate Limit)을 피하기 위한 지연 시간
                                    import time
                                    time.sleep(60)
                                    
                                except Exception as e:
                                    fail_count += 1
                                    errors.append(f"[{model}] {str(e)}")
                                
                                progress_bar.progress(progress)
                                
                            status_text.empty()
                            progress_bar.empty()
                            
                            if success_count > 0:
                                # Move successful items to Tab 3
                                success_items = df_result.loc[successful_indices].copy()
                                success_items["선택"] = False
                                if os.path.exists("completed_analysis.pkl"):
                                    completed_df = pd.read_pickle("completed_analysis.pkl")
                                    completed_df = pd.concat([completed_df, success_items], ignore_index=True)
                                else:
                                    completed_df = success_items
                                completed_df.to_pickle("completed_analysis.pkl")
                                
                                # Remove from current df
                                df_result = df_result.drop(index=successful_indices)
                                df_result.to_pickle("last_analysis.pkl")
                                
                            if fail_count > 0:
                                st.error(f"✅ 성공: {success_count}개 | ❌ 실패: {fail_count}개")
                                with st.expander("실패 사유 보기 (클릭)"):
                                    for err in errors:
                                        st.write(err)
                            else:
                                st.success(f"✅ {success_count}개 상품 자동 업로드 완료! 3단계 탭으로 이동되었습니다.")
                                import time
                                time.sleep(1.5)
                                st.rerun()
                                
                    else:
                        st.warning("선택된 항목이 없습니다.")

            with action_col3:
                if st.button("📦 스토어 업로드 없이 3단계로 이동", type="secondary", use_container_width=True):
                    if df_result["선택"].any():
                        selected_items = df_result[df_result["선택"]].copy()
                        selected_items["선택"] = False
                        if os.path.exists("completed_analysis.pkl"):
                            completed_df = pd.read_pickle("completed_analysis.pkl")
                            completed_df = pd.concat([completed_df, selected_items], ignore_index=True)
                        else:
                            completed_df = selected_items
                        completed_df.to_pickle("completed_analysis.pkl")
                        df_result = df_result[~df_result["선택"]].copy()
                        df_result.to_pickle("last_analysis.pkl")
                        st.success(f"성공적으로 {len(selected_items)}개의 항목이 3단계로 이동되었습니다!")
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.warning("선택된 항목이 없습니다.")
            
            st.markdown("---")

            # 사용자 편의를 위해 중요한 열을 맨 앞으로 이동시킵니다 (가로 스크롤 방지)
            important_cols_requested = ['선택', '브랜드', '추출_모델명', '용도', '타오바오_단가', '최종_판매가', '추천_스토어상품명', '이미지_검색']
            important_cols = [c for c in important_cols_requested if c in df_result.columns]
            other_cols = [c for c in df_result.columns if c not in important_cols]
            df_result = df_result[important_cols + other_cols]
            
            # 열 숨기기 적용
            df_display = df_result.drop(columns=[c for c in hide_cols if c in df_result.columns])

            # Fixed key ensures the scroll position is maintained even when data is updated.
            edited_df = st.data_editor(
                df_display,
                use_container_width=True,
                key="main_data_editor_fixed",
                column_config={
                    "이미지_검색": st.column_config.LinkColumn(
                        "구글 이미지 검색",
                        display_text="🔍 구글에서 찾기"
                    )
                }
            )
            
            if not edited_df.equals(df_display):
                changed_for_auto_calc = False
                import math
                if '타오바오_단가' in edited_df.columns and '최종_판매가' in edited_df.columns:
                    for idx in df_display.index:
                        old_tb = str(df_display.at[idx, '타오바오_단가']).strip()
                        new_tb = str(edited_df.at[idx, '타오바오_단가']).strip()
                        
                        if old_tb.lower() in ['nan', 'none']: old_tb = ''
                        if new_tb.lower() in ['nan', 'none']: new_tb = ''
                        
                        if old_tb != new_tb and new_tb:
                            try:
                                tb_price = float(new_tb)
                                final_price = (tb_price * ex_rate) * (1 + margin_rate / 100) + shipping_fee
                                final_price = math.ceil(final_price / 100) * 100
                                edited_df.at[idx, '최종_판매가'] = str(int(final_price))
                                changed_for_auto_calc = True
                            except Exception as e:
                                print(f"[DEBUG] auto calc error: {e}")
                                pass
                
                # Update original df_result with edits from edited_df
                for c in edited_df.columns:
                    df_result[c] = edited_df[c]
                df_result.to_pickle("last_analysis.pkl")
                if changed_for_auto_calc:
                    st.rerun()
            else:
                # If they just clicked checkbox or edited something but auto calc wasn't triggered
                for c in edited_df.columns:
                    df_result[c] = edited_df[c]
                df_result.to_pickle("last_analysis.pkl")
            
            
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # 엑셀 다운로드는 화면에 보이는 대로(숨김열 제외) 다운로드
                edited_df.to_excel(writer, index=False, sheet_name='분석결과')
            
            st.download_button(
                label="📥 수정한 최종 결과 엑셀로 다운로드 (스마트스토어 등록용)",
                data=buffer.getvalue(),
                file_name="최종_상품등록작업_결과.xlsx",
                mime="application/vnd.ms-excel",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"저장된 분석 결과를 불러오는 데 실패했습니다: {e}")
            if st.button("작업 내역 초기화"):
                os.remove("last_analysis.pkl")
                if "analysis_done" in st.session_state:
                    del st.session_state.analysis_done
                st.rerun()
    else:
        st.warning("먼저 [📊 1단계: 상품 분석] 탭에서 엑셀 파일을 업로드하고 분석을 완료해주세요!")

with tab3:
    import os
    if os.path.exists("completed_analysis.pkl"):
        try:
            completed_df = pd.read_pickle("completed_analysis.pkl")
            st.subheader("✅ 상품 등록이 완료된 항목들")
            st.info(f"총 {len(completed_df)}개의 등록 완료 상품이 보관되어 있습니다.")
            
            st.dataframe(completed_df, use_container_width=True)
            
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                completed_df.to_excel(writer, index=False, sheet_name='등록완료')
            
            st.download_button(
                label="📥 등록 완료 항목 엑셀로 다운로드",
                data=buffer.getvalue(),
                file_name="최종_등록완료_결과.xlsx",
                mime="application/vnd.ms-excel",
                type="primary",
                use_container_width=True
            )
            
            if st.button("🚨 완료 내역 전체 삭제 (초기화)", type="secondary"):
                os.remove("completed_analysis.pkl")
                st.rerun()
                
        except Exception as e:
            st.error(f"저장된 완료 결과를 불러오는 데 실패했습니다: {e}")
    else:
        st.info("아직 등록 완료 처리된 상품이 없습니다. 2단계 탭에서 항목을 선택하고 완료 처리해 주세요.")
