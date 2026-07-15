import streamlit as st
import pandas as pd
import io
import json
from naver_api import NaverCommerceAPI
import scraper
import importlib
importlib.reload(scraper)

st.set_page_config(page_title="스마트스토어 상품 분석기", layout="wide")

import streamlit.components.v1 as components
components.html("""
<script>
try {
    const parentDoc = window.parent.document;
    if (!parentDoc.getElementById('shortcut-blocker-installed')) {
        const marker = parentDoc.createElement('div');
        marker.id = 'shortcut-blocker-installed';
        marker.style.display = 'none';
        parentDoc.body.appendChild(marker);
        
        parentDoc.addEventListener('keydown', function(e) {
            if (e.key === 'c' || e.key === 'C') {
                const target = e.target;
                const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;
                if (!isInput) {
                    e.stopPropagation();
                    e.preventDefault();
                }
            }
        }, { capture: true });
    }
} catch (err) {}
</script>
""", height=0, width=0)

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
                    st.session_state.store_models = [str(m).lower() for m in models]
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
    import os
    if "df_scraped" not in st.session_state and os.path.exists("scraped_data.pkl"):
        try:
            st.session_state.df_scraped = pd.read_pickle("scraped_data.pkl")
        except:
            pass
            
    st.subheader("1. 스마트스토어 카테고리 URL 수집")
    st.markdown("수집할 카테고리 URL을 한 줄에 하나씩 입력하세요. 첫 페이지만 수집합니다.")
    
    url_input = st.text_area("스마트스토어 URL", height=200, placeholder="https://smartstore.naver.com/...\\nhttps://smartstore.naver.com/...")
    
    c1, c2 = st.columns(2)
    use_best = c1.checkbox("BEST 상품 수집", value=True)
    use_review = c2.checkbox("리뷰 많은순 + 리뷰 있는 상품만 수집", value=True)
    
    st.markdown("---")
    st.markdown("🔑 **네이버 자동 로그인 (선택)** - 수집 시 로그인 화면이 뜨면 자동으로 입력합니다.")
    
    saved_id, saved_pw = "", ""
    if os.path.exists("settings.json"):
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                saved_id = settings.get("naver_id", "")
                saved_pw = settings.get("naver_pw", "")
        except:
            pass
            
    login_c1, login_c2 = st.columns(2)
    naver_id = login_c1.text_input("네이버 아이디", value=saved_id, placeholder="아이디를 입력하세요")
    naver_pw = login_c2.text_input("네이버 비밀번호", value=saved_pw, type="password", placeholder="비밀번호를 입력하세요")
    
    headless = False # 백그라운드 수집을 기본값으로 고정하여 UI에서 숨김
    
    if st.button("수집 시작", type="primary", use_container_width=True):
        if naver_id or naver_pw:
            try:
                with open("settings.json", "w", encoding="utf-8") as f:
                    json.dump({"naver_id": naver_id, "naver_pw": naver_pw}, f)
            except:
                pass
                
        import re
        raw_urls = re.split(r'[\n\s,]+', url_input)
        urls = [u.strip() for u in raw_urls if u.strip().startswith('http')]
        has_individual = any("/product" in u for u in urls)
        
        if not urls or not any(u.strip() for u in urls):
            st.warning("URL을 입력해주세요.")
        elif not use_best and not use_review and not has_individual:
            st.warning("스토어 URL인 경우 수집 방식을 하나 이상 선택해주세요.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            realtime_df_placeholder = st.empty()
            
            def update_progress(idx, total, store_name, current_results=None):
                progress_bar.progress(idx / total)
                status_text.text(f"{idx}/{total} 수집 중: {store_name}")
                if current_results:
                    # 실시간으로 수집된 데이터를 보여줍니다
                    realtime_df_placeholder.dataframe(pd.DataFrame(current_results), use_container_width=True)
                
            with st.spinner("상품 정보를 수집하고 있습니다. 완료될 때까지 기다려주세요..."):
                success, msg, df, fail_list = scraper.run_collection(
                    urls, use_best, use_review, headless, update_progress, naver_id, naver_pw
                )
                
            if success:
                import datetime
                now = datetime.datetime.now()
                timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
                file_timestamp = now.strftime("%Y%m%d_%H%M%S")
                
                status_text.text("수집 완료!")
                st.success(f"총 {len(df)}개의 상품 정보 수집을 완료했습니다! (수집 일시: {timestamp_str})")
                if fail_list:
                    st.warning(f"일부 URL은 수집에 실패했거나 0개 수집됨:\n" + "\n".join(fail_list[:10]))
                    
                st.session_state.df_scraped = df
                df.to_pickle("scraped_data.pkl")
                
                # 히스토리 자동 저장
                if not os.path.exists("history"):
                    os.makedirs("history")
                history_file = f"history/scraped_{file_timestamp}.pkl"
                df.to_pickle(history_file)
                
                hist_meta = []
                if os.path.exists("history/meta.json"):
                    try:
                        with open("history/meta.json", "r", encoding="utf-8") as meta_f:
                            hist_meta = json.load(meta_f)
                    except: pass
                
                hist_meta.insert(0, {
                    "file": history_file,
                    "date": timestamp_str,
                    "count": len(df)
                })
                with open("history/meta.json", "w", encoding="utf-8") as meta_f:
                    json.dump(hist_meta, meta_f, ensure_ascii=False)
            else:
                st.error(msg)
                
    if 'df_scraped' in st.session_state and not st.session_state.df_scraped.empty:
        st.markdown("---")
        st.success("🎉 방금 수집한 데이터가 준비되어 있습니다! [2단계: 상품 분석] 탭으로 이동해서 파일 업로드 없이 바로 분석을 시작할 수 있습니다.")
        
        st.dataframe(st.session_state.df_scraped, use_container_width=True)
        
        col_down, col_clear = st.columns(2)
        with col_down:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                st.session_state.df_scraped.to_excel(writer, index=False)
            st.download_button(
                label="📥 수집된 원본 엑셀 다운로드",
                data=buffer.getvalue(),
                file_name="scraped_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col_clear:
            if st.button("🗑️ 수집 결과 삭제 (초기화)", type="secondary", use_container_width=True):
                if os.path.exists("scraped_data.pkl"):
                    os.remove("scraped_data.pkl")
                del st.session_state.df_scraped
                st.rerun()

    st.markdown("---")
    st.subheader("📂 과거 수집 히스토리")
    if os.path.exists("history/meta.json"):
        try:
            with open("history/meta.json", "r", encoding="utf-8") as f:
                hist_meta = json.load(f)
            
            if hist_meta:
                for h in hist_meta:
                    h_col1, h_col2, h_col3 = st.columns([3, 2, 2])
                    h_col1.write(f"📅 **{h['date']}**")
                    h_col2.write(f"📦 {h['count']}개 상품")
                    if h_col3.button("이 데이터 불러오기", key=f"load_{h['file']}"):
                        if os.path.exists(h['file']):
                            st.session_state.df_scraped = pd.read_pickle(h['file'])
                            st.session_state.df_scraped.to_pickle("scraped_data.pkl")
                            st.success(f"{h['date']}의 수집 데이터를 성공적으로 불러왔습니다!")
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("해당 파일을 찾을 수 없습니다.")
            else:
                st.info("저장된 과거 수집 내역이 없습니다.")
        except Exception as e:
            st.error("히스토리를 불러오는 중 오류가 발생했습니다.")
    else:
        st.info("저장된 과거 수집 내역이 없습니다.")
        
with tab2:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("1. 분석할 상품 목록 선택")
        source_option = st.radio("데이터 소스 선택:", ["과거 수집 히스토리 불러오기", "새 엑셀 파일 업로드"])
        
        df_new = None
        if source_option == "과거 수집 히스토리 불러오기":
            hist_options = []
            hist_map = {}
            if os.path.exists("history/meta.json"):
                try:
                    with open("history/meta.json", "r", encoding="utf-8") as f:
                        hist_meta = json.load(f)
                    for h in hist_meta:
                        label = f"{h['date']} 수집본 ({h['count']}개)"
                        hist_options.append(label)
                        hist_map[label] = h['file']
                except: pass
            
            if hist_options:
                selected_hist = st.selectbox("불러올 수집 내역을 선택하세요:", hist_options)
                if selected_hist:
                    try:
                        df_new = pd.read_pickle(hist_map[selected_hist])
                        st.success("✅ 수집 데이터를 성공적으로 불러왔습니다.")
                    except:
                        st.error("데이터를 불러오는데 실패했습니다.")
            else:
                st.warning("⚠️ 저장된 과거 수집 내역이 없습니다. 먼저 1단계에서 상품을 수집해주세요.")
        else:
            new_products_file = st.file_uploader("새 상품 엑셀 파일 선택", type=["xlsx", "xls"], key="new")
            if new_products_file is not None:
                try:
                    df_new = pd.read_excel(new_products_file, dtype=str)
                    st.success("✅ 엑셀 파일을 성공적으로 불러왔습니다.")
                except Exception as e:
                    st.error(f"엑셀 파일 읽기 오류: {e}")

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
                    ["[최강 AI] Gemini 실시간 완벽 추출 (가장 정확하지만 오류 잦음, API Key 필수)",
                     "🌟 [추천] 영문/숫자 조합 스마트 추출 (에러 없음, 즉시 추출, API 불필요)"]
                )
                
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
                                brand_list, model_list, item_list, purpose_list, seo_name_list = [], [], [], [], []
                                batch_size = 40
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                for i in range(0, len(product_names), batch_size):
                                    batch = product_names[i:i+batch_size]
                                    status_text.text(f"Gemini AI가 상품명을 분석 중입니다... ({min(i+batch_size, len(product_names))}/{len(product_names)} 개 완료)")
                                    prompt = "다음은 공구/기계부품 등의 상품명 또는 브랜드+모델명 목록입니다. 각 항목에서 진짜 '브랜드명', '모델명(부품 번호)', '핵심 품목명', 그리고 '상품 용도(카테고리)'를 찾아 JSON 배열로 반환하세요.\n"
                                    prompt += "조건:\n1. 반환 형식은 [{\"brand\": \"...\", \"model\": \"...\", \"item\": \"...\", \"purpose\": \"...\", \"seo_name\": \"...\"}] 이어야 합니다.\n2. 정보가 없으면 빈 문자열을 넣으세요.\n3. 입력 개수와 100% 동일한 길이의 배열을 반환해야 합니다.\n4. [아주 중요] 상품명에 포함된 영문/숫자 부품 번호(모델명)들을 하나도 빠짐없이 찾아 콤마(,)로 연결하세요.\n5. 모델명을 바탕으로 실제 제조사(브랜드명)를 유추할 수 있다면 AI의 지식을 활용해 반드시 채워주세요.\n6. [핵심] 네이버 스마트스토어 SEO 가이드에 맞춘 최적화된 상품명을 'seo_name'에 생성해주세요. \n   - 규칙: [브랜드] + [모델명] + [핵심 품목 및 연관 검색어(동의어, 한글/영문 병기 추가)]\n   - 예시: '와이엠릴레이 EVR100A-24S' -> '와이엠릴레이 EVR100A-24S 고전압 DC EV 릴레이 콘택터'\n   - [주의] '정품' 이라는 단어는 절대 포함하지 마세요.\n7. 'purpose'(용도)는 엑셀 필터링 및 카테고리 매칭을 위해 '산업용 제어 부품', '공압 제어 부품', '산업용 센서' 처럼 아주 짧고 포괄적인 대분류 명칭으로 적어주세요.\n\n상품명 목록:\n"
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
                                        while len(batch_result) < len(batch): batch_result.append({"brand": "AI 실패", "model": "AI 실패", "item": "AI 실패", "purpose": "AI 실패", "seo_name": "AI 실패"})
                                        for r in batch_result[:len(batch)]:
                                            brand_val = r.get("brand")
                                            model_val = r.get("model")
                                            item_val = r.get("item")
                                            purpose_val = r.get("purpose")
                                            seo_val = r.get("seo_name")
                                            
                                            if isinstance(model_val, list): model_val = ", ".join(str(m) for m in model_val)
                                            
                                            brand_list.append(str(brand_val or "").strip())
                                            model_list.append(str(model_val or "").strip())
                                            item_list.append(str(item_val or "").strip())
                                            purpose_list.append(str(purpose_val or "").strip())
                                            seo_name_list.append(str(seo_val or "").strip())
                                    except Exception as e:
                                        st.error(f"AI API 통신 중 에러 발생 (배치 {i}~): {e}")
                                        for _ in batch:
                                            brand_list.append("AI Error")
                                            model_list.append("AI Error")
                                            item_list.append("AI Error")
                                            purpose_list.append("AI Error")
                                            seo_name_list.append("AI Error")
                                            
                                    progress_bar.progress(min((i + batch_size) / len(product_names), 1.0))
                                    time.sleep(3)
                                    
                                status_text.text("AI 분석이 성공적으로 완료되었습니다!")
                                df_result['추출_브랜드'] = brand_list[:len(df_result)]
                                df_result['추출_모델명'] = model_list[:len(df_result)]
                                df_result['추출_품목'] = item_list[:len(df_result)]
                                df_result['용도'] = purpose_list[:len(df_result)]
                                df_result['AI_추천상품명'] = seo_name_list[:len(df_result)]
                                
                            elif "[추천]" in split_rule:
                                import re
                                def smart_extract(text):
                                    text = str(text)
                                    words = text.split()
                                    if not words: return pd.Series(["", ""])
                                    
                                    brand = words[0]
                                    
                                    # Strip non-alphanumeric (except hyphens, slashes, dots) for model candidates
                                    clean_words = [re.sub(r'[^A-Za-z0-9\-\/\.]', '', w) for w in words[1:]]
                                    # 영문이나 숫자가 포함된 2글자 이상의 단어들을 모두 모델명 후보로 추출
                                    candidates = [w for w in clean_words if len(w) >= 2 and re.search(r'[A-Za-z0-9]', w)]
                                    
                                    if candidates:
                                        model = ", ".join(candidates)
                                    else:
                                        # Fallback: the first non-empty clean word
                                        fallback = [w for w in clean_words if w]
                                        model = ", ".join(fallback) if fallback else ""
                                        
                                    return pd.Series([brand, model])
                                df_result[['추출_브랜드', '추출_모델명']] = df_result[col_name_new].apply(smart_extract)
                        
                        df_result['추출_브랜드'] = df_result['추출_브랜드'].fillna("").str.strip()
                        df_result['추출_모델명'] = df_result['추출_모델명'].fillna("").str.strip()
                        
                        import re
                        # 고객 요청사항: 모델명은 영어와 숫자로만 구성되어 있으며 한글 단어는 포함되지 않음.
                        if model_col_new == "(자동 추출 사용)":
                            df_result['추출_모델명'] = df_result['추출_모델명'].astype(str).str.strip()
                            # 고객 요청사항: 모델명에 콤마(,)가 포함된 경우 각각 다른 상품(행)으로 분리
                            df_result['추출_모델명'] = df_result['추출_모델명'].apply(lambda x: [m.strip() for m in x.split(',')] if ',' in x else x)
                            df_result = df_result.explode('추출_모델명', ignore_index=True)
                            df_result['추출_모델명'] = df_result['추출_모델명'].astype(str).str.strip()
                        
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
                        
                        def build_seo_name(row):
                            if 'AI_추천상품명' in row:
                                ai_name = str(row['AI_추천상품명']).strip()
                                if ai_name and ai_name not in ["AI 실패", "AI Error", "nan", "None"]:
                                    return ai_name
                                    
                            parts = []
                            for col in ['추출_브랜드', '추출_모델명', '추출_품목', '용도']:
                                val = str(row.get(col, "")).strip()
                                if val and val.lower() not in ['nan', 'none']:
                                    # 네이버 SEO 가이드: 불필요한 특수문자 제거, 괄호 제거
                                    import re
                                    val = re.sub(r'[\[\]\(\)\{\}\<\>\!]', '', val)
                                    parts.append(val)
                            
                            # 중복 단어 제거 (순서 유지, 어뷰징 방지)
                            seen = set()
                            final_words = []
                            for part in parts:
                                for word in part.split():
                                    word_clean = word.strip()
                                    if word_clean.lower() not in seen:
                                        seen.add(word_clean.lower())
                                        final_words.append(word_clean)
                            
                            return " ".join(final_words).strip()
                            
                        df_result['추천_스토어상품명'] = df_result.apply(build_seo_name, axis=1)
                        
                        df_result['타오바오_단가'] = None
                        df_result['최종_판매가'] = ""
                        import urllib.parse
                        df_result['이미지_검색'] = df_result.apply(
                            lambda x: f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(str(x['추출_브랜드']) + ' ' + str(x['추출_모델명']))}", axis=1
                        )
                        df_result['이미지_확보'] = False

                        
                        def check_registration(model_name):
                            clean_model = str(model_name).strip().lower()
                            if not clean_model: return "확인 불가 (모델명 없음)"
                            
                            import re
                            has_eng_or_num = bool(re.search(r'[a-z0-9]', clean_model))
                            
                            if len(clean_model) <= 2 or not has_eng_or_num:
                                for store_model in st.session_state.store_models:
                                    if clean_model == store_model.strip(): return "✅ 기등록"
                                return "❌ 미등록 (신규)"
                                
                            # 정규식을 사용하여, 영문/숫자가 연속되지 않는(독립된 단어인) 경우만 매칭합니다.
                            # 예: "gth-22"가 "gth-224"에 매칭되는 오탐지를 방지
                            pattern = re.compile(rf'(?<![a-z0-9]){re.escape(clean_model)}(?![a-z0-9])')
                            
                            for store_model in st.session_state.store_models:
                                if not store_model:
                                    continue
                                if pattern.search(store_model):
                                    return "✅ 기등록"
                            return "❌ 미등록 (신규)"
                                
                        df_result['스토어_등록여부'] = df_result['추출_모델명'].apply(check_registration)
                        
                        # 기등록 제외 없이 전체 데이터 저장
                        total_cnt = len(df_result)
                        
                        import os
                        # 기존 데이터가 있으면 아래에 추가(Append)
                        if os.path.exists("last_analysis.pkl"):
                            try:
                                existing_df = pd.read_pickle("last_analysis.pkl")
                                df_result = pd.concat([existing_df, df_result], ignore_index=True)
                            except:
                                pass # 파일이 손상되었거나 읽을 수 없으면 그냥 덮어씀
                                
                        df_result.to_pickle("last_analysis.pkl")
                        st.session_state.df_result = df_result
                        st.session_state.analysis_done = True
                        st.session_state.filtered_cnt = len(df_result[df_result['스토어_등록여부'] == "✅ 기등록"])
            except Exception as e:
                st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")
                        
            if st.session_state.get("analysis_done", False):
                st.success(f"🎉 분석이 완료되었습니다! 총 {st.session_state.get('filtered_cnt', 0)}개의 기등록 상품이 확인되었습니다.\\n\\n**이제 화면 상단의 [✍️ 3단계: 상품 등록 작업] 탭을 클릭하여 결과를 확인하세요.**")

with tab3:
    import os
    df_result = None
    
    if "df_result" in st.session_state:
        df_result = st.session_state.df_result
    elif os.path.exists("last_analysis.pkl"):
        try:
            df_result = pd.read_pickle("last_analysis.pkl")
            st.session_state.df_result = df_result
        except:
            pass
            
    if df_result is not None and not df_result.empty:
        try:
            st.subheader("🧮 타오바오 연동 판매가 일괄 계산기")
            
            with st.container():
                c1, c2, c3 = st.columns(3)
                ex_rate = c1.number_input("적용 환율 (원/위안)", value=230.0, step=1.0)
                margin_rate = c2.number_input("목표 마진율 (%)", value=35.0, step=1.0)
                shipping_fee = c3.number_input("기본 배송비 (원)", value=10000, step=100)
                
                if st.button("🔄 '타오바오_단가' 입력값 기준으로 최종 판매가 일괄 계산", type="primary", use_container_width=True):
                    import math
                    # Use edited_df's state if possible, otherwise df_result
                    try:
                        current_df = st.session_state.get("main_data_editor_fixed", {}).get("edited_rows", {})
                        for row_idx_str, edits in current_df.items():
                            row_idx = df_result.index[int(row_idx_str)]
                            if "타오바오_단가" in edits:
                                df_result.at[row_idx, "타오바오_단가"] = edits["타오바오_단가"]
                    except: pass
                    
                    for idx, row in df_result.iterrows():
                        try:
                            tb_price = float(row['타오바오_단가'])
                            if not pd.isna(tb_price):
                                final_price = (tb_price * ex_rate) * (1 + margin_rate / 100) + shipping_fee
                                final_price = math.ceil(final_price / 100) * 100
                                df_result.at[idx, '최종_판매가'] = str(int(final_price))
                        except:
                            pass
                    st.session_state.df_result = df_result
                    df_result.to_pickle("last_analysis.pkl")
                    if "main_data_editor_fixed" in st.session_state:
                        del st.session_state["main_data_editor_fixed"]
                    st.success("판매가 계산이 완료되었습니다!")
                    import time
                    time.sleep(0.5)
                    st.rerun()
                    
            st.markdown("---")
            
            # --- 선택 기능 및 액션 버튼 ---
            if "선택" not in df_result.columns:
                df_result["선택"] = False
                df_result.to_pickle("last_analysis.pkl")
                
            if "이미지_확보" not in df_result.columns:
                df_result["이미지_확보"] = False
                df_result.to_pickle("last_analysis.pkl")
            # 열 순서 설정 기능 (저장 가능)
            import json, os
            col_order_file = "column_order.json"
            saved_col_order = []
            if os.path.exists(col_order_file):
                try:
                    with open(col_order_file, "r", encoding="utf-8") as f:
                        saved_col_order = json.load(f)
                except: pass

            default_cols = [c for c in df_result.columns if c != "선택"]
            
            if not saved_col_order:
                # 초기 기본값 설정: '이미지_검색', '이미지_확보'를 '추출_모델명' 바로 뒤로 위치
                if "추출_모델명" in default_cols:
                    if "이미지_검색" in default_cols: default_cols.remove("이미지_검색")
                    if "이미지_확보" in default_cols: default_cols.remove("이미지_확보")
                    idx = default_cols.index("추출_모델명")
                    if "이미지_검색" in df_result.columns: default_cols.insert(idx + 1, "이미지_검색")
                    if "이미지_확보" in df_result.columns: default_cols.insert(idx + 2, "이미지_확보")
                saved_col_order = default_cols
            else:
                # 삭제된 열 제거 및 새로운 열을 맨 뒤에 추가
                saved_col_order = [c for c in saved_col_order if c in default_cols]
                for c in default_cols:
                    if c not in saved_col_order:
                        saved_col_order.append(c)

            st.write("🔄 **표 열(Column) 순서 설정** (순서를 바꾸시려면 X를 눌러 지우고 맨 뒤에 다시 추가하세요)")
            selected_col_order = st.multiselect(
                "표에 표시될 열과 순서를 지정하세요", 
                options=default_cols, 
                default=saved_col_order,
                label_visibility="collapsed"
            )
            
            if selected_col_order != saved_col_order:
                with open(col_order_file, "w", encoding="utf-8") as f:
                    json.dump(selected_col_order, f, ensure_ascii=False)
            
            top_action_col1, top_action_col2 = st.columns([1.5, 4])
            with top_action_col2:
                view_filter = st.radio(
                    "🔎 상품 보기 옵션",
                    ["등록되지 않은 상품만 보기 (신규)", "이미 등록된 상품만 보기", "모든 상품 보기"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
            del_btn_place = top_action_col1.empty()
            
            # Ensure boolean columns are strictly bool before displaying
            if '선택' in df_result.columns:
                df_result['선택'] = df_result['선택'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False}).fillna(False).astype(bool)
            if '이미지_확보' in df_result.columns:
                df_result['이미지_확보'] = df_result['이미지_확보'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False}).fillna(False).astype(bool)

            if view_filter == "등록되지 않은 상품만 보기 (신규)":
                filtered_df = df_result[df_result['스토어_등록여부'] != "✅ 기등록"].copy()
            elif view_filter == "이미 등록된 상품만 보기":
                filtered_df = df_result[df_result['스토어_등록여부'] == "✅ 기등록"].copy()
            else:
                filtered_df = df_result.copy()
            st.markdown("---")
            use_realtime_calc = st.checkbox("⚡ 단가 입력 시 실시간으로 최종 판매가 자동 계산 (끄면 스크롤이 위로 튀지 않아 연속 입력이 매우 편해집니다)", value=False)
            
            # --- 선택 기능 및 액션 버튼 ---
            sel_col1, sel_col2, sel_col3, sel_col4, sel_col5 = st.columns([1.2, 1.2, 1, 1, 1.5])
            with sel_col1:
                if st.button("☑️ 현재 목록 전체 선택", use_container_width=True):
                    df_result.loc[filtered_df.index, "선택"] = True
                    st.session_state.df_result = df_result
                    df_result.to_pickle("last_analysis.pkl")
                    if "main_data_editor_fixed" in st.session_state: del st.session_state["main_data_editor_fixed"]
                    st.rerun()
            with sel_col2:
                if st.button("⬜ 현재 목록 전체 해제", use_container_width=True):
                    df_result.loc[filtered_df.index, "선택"] = False
                    st.session_state.df_result = df_result
                    df_result.to_pickle("last_analysis.pkl")
                    if "main_data_editor_fixed" in st.session_state: del st.session_state["main_data_editor_fixed"]
                    st.rerun()
            with sel_col3:
                start_idx = st.number_input("시작번호", min_value=1, value=1, step=1, label_visibility="collapsed")
            with sel_col4:
                end_idx = st.number_input("끝번호", min_value=1, value=10, step=1, label_visibility="collapsed")
            with sel_col5:
                if st.button("✅ 순번 범위 체크", use_container_width=True):
                    if not filtered_df.empty:
                        actual_start = max(0, start_idx - 1)
                        actual_end = min(len(filtered_df), end_idx)
                        if actual_start < actual_end:
                            target_indices = filtered_df.index[actual_start:actual_end]
                            df_result.loc[target_indices, "선택"] = True
                            st.session_state.df_result = df_result
                            df_result.to_pickle("last_analysis.pkl")
                            if "main_data_editor_fixed" in st.session_state: del st.session_state["main_data_editor_fixed"]
                            st.rerun()
            
            # --- 실시간 타오바오 단가 계산 (스크롤 유지) ---
            if use_realtime_calc:
                editor_state = st.session_state.get("main_data_editor_fixed", {})
                if "edited_rows" in editor_state:
                    import math
                    for row_idx_str, edits in editor_state["edited_rows"].items():
                        if "타오바오_단가" in edits:
                            try:
                                disp_idx = int(row_idx_str)
                                if disp_idx < len(filtered_df):
                                    real_idx = filtered_df.index[disp_idx]
                                    tb_price_str = str(edits["타오바오_단가"]).strip()
                                    if tb_price_str and tb_price_str.lower() not in ['nan', 'none']:
                                        tb_price = float(tb_price_str)
                                        if tb_price > 0:
                                            final_price = (tb_price * ex_rate) * (1 + margin_rate / 100) + shipping_fee
                                            final_price = math.ceil(final_price / 100) * 100
                                            filtered_df.at[real_idx, '최종_판매가'] = str(int(final_price))
                                            # df_result에도 반영 (메모리상에만)
                                            df_result.at[real_idx, '최종_판매가'] = str(int(final_price))
                                            
                                            # 🚨 추가: 에디터가 리셋될 경우를 대비해, 방금 수정한 타오바오 단가도 df_display의 원본에 반영해줍니다!
                                            filtered_df.at[real_idx, '타오바오_단가'] = edits["타오바오_단가"]
                                            df_result.at[real_idx, '타오바오_단가'] = edits["타오바오_단가"]
                            except:
                                pass
            # ----------------------------------------------
                
            display_cols = ["선택"] + [c for c in selected_col_order if c in filtered_df.columns]
            df_display = filtered_df[display_cols].copy()
            if "순번" in df_display.columns:
                df_display = df_display.drop(columns=["순번"])
            df_display.insert(0, "순번", range(1, len(df_display) + 1))

            def render_editor_and_save():
                global df_result
                # Fixed key ensures the scroll position is maintained even when data is updated.
                edited_df = st.data_editor(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    key="main_data_editor_fixed",
                    column_config={
                        "선택": st.column_config.CheckboxColumn(
                            "선택",
                            help="삭제하거나 다룰 상품을 선택하세요",
                            default=False
                        ),
                        "순번": st.column_config.NumberColumn(
                            "순번",
                            disabled=True
                        ),
                        "이미지_검색": st.column_config.LinkColumn(
                            "구글 이미지 검색",
                            display_text="🔍 구글에서 찾기"
                        ),
                        "이미지_확보": st.column_config.CheckboxColumn(
                            "이미지 확보", 
                            help="이미지를 찾았으면 체크하세요"
                        )
                    }
                )
                
                # --- Removed automatic df_result update to prevent data_editor from resetting ---
                
                if st.button("💾 위 표에서 수정한 내용 모두 저장하기 (필수)", type="primary", use_container_width=True):
                    update_cols = [c for c in edited_df.columns if c != "순번"]
                    df_result.loc[edited_df.index, update_cols] = edited_df[update_cols]
                    st.session_state.df_result = df_result
                    df_result.to_pickle("last_analysis.pkl")
                    # Clear editor state so it cleanly reloads the saved data
                    if "main_data_editor_fixed" in st.session_state:
                        del st.session_state["main_data_editor_fixed"]
                    st.success("✅ 모든 수정사항이 영구적으로 저장되었습니다!")
                    import time
                    time.sleep(0.5)
                    st.rerun()

                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    export_df = edited_df.copy()
                    export_df.insert(0, 'ID (수정금지)', export_df.index)
                    export_df.to_excel(writer, index=False, sheet_name='분석결과')
                
                st.download_button(
                    label="📥 수정한 최종 결과 엑셀로 다운로드 (스마트스토어 등록용)",
                    data=buffer.getvalue(),
                    file_name="최종_상품등록작업_결과.xlsx",
                    mime="application/vnd.ms-excel",
                    type="primary",
                    use_container_width=True
                )
                
                uploaded_file = st.file_uploader("📤 수정한 엑셀 파일 다시 불러오기 (수정 후 업로드)", type=['xlsx', 'xls'])
                if uploaded_file is not None:
                    try:
                        uploaded_df = pd.read_excel(uploaded_file)
                        if 'ID (수정금지)' in uploaded_df.columns:
                            # 엑셀에서 문자열이나 실수로 읽히는 것을 방지하고 무조건 정수로 변환
                            uploaded_df['ID (수정금지)'] = pd.to_numeric(uploaded_df['ID (수정금지)'], errors='coerce')
                            uploaded_df = uploaded_df.dropna(subset=['ID (수정금지)'])
                            uploaded_df['ID (수정금지)'] = uploaded_df['ID (수정금지)'].astype(int)
                            uploaded_df = uploaded_df.set_index('ID (수정금지)')
                            
                            valid_idx = uploaded_df.index.intersection(df_result.index)
                            if len(valid_idx) == 0:
                                st.warning("⚠️ 업로드한 엑셀 파일의 상품 ID가 현재 목록과 하나도 일치하지 않습니다. (초기화되었거나 예전 파일입니다). 기존 작업 내역을 살리기 위해 현재 목록 맨 아래에 새 항목으로 모두 추가했습니다!")
                                uploaded_df = uploaded_df.reset_index(drop=True)
                                df_result = pd.concat([df_result, uploaded_df], ignore_index=True)
                                if '선택' in df_result.columns:
                                    df_result['선택'] = df_result['선택'].fillna(False).astype(bool)
                                if '이미지_확보' in df_result.columns:
                                    df_result['이미지_확보'] = df_result['이미지_확보'].fillna(False).astype(bool)
                                st.session_state.df_result = df_result
                                df_result.to_pickle("last_analysis.pkl")
                                if "main_data_editor_fixed" in st.session_state:
                                    del st.session_state["main_data_editor_fixed"]
                                import time
                                time.sleep(2.0)
                                st.rerun()
                            else:
                                uploaded_df = uploaded_df.loc[valid_idx]
                                common_cols = [c for c in uploaded_df.columns if c in df_result.columns and c != '선택']
                                for col in common_cols:
                                    orig_dtype = str(df_result[col].dtype).lower()
                                    if "string" in orig_dtype or "str" in orig_dtype or "object" in orig_dtype:
                                        series = uploaded_df[col].fillna("")
                                        # Convert to string and remove trailing .0 from Excel float parsing
                                        series = series.astype(str).str.replace(r'\.0$', '', regex=True)
                                        df_result.loc[valid_idx, col] = series
                                    else:
                                        df_result.loc[valid_idx, col] = uploaded_df[col]
                                
                                st.session_state.df_result = df_result
                                df_result.to_pickle("last_analysis.pkl")
                                if "main_data_editor_fixed" in st.session_state:
                                    del st.session_state["main_data_editor_fixed"]
                                st.success(f"✅ 총 {len(valid_idx)}개의 엑셀 수정사항이 성공적으로 반영되었습니다!")
                                import time
                                time.sleep(1.0)
                                st.rerun()
                        else:
                            st.error("❌ 'ID (수정금지)' 열이 없습니다. 이 프로그램에서 다운로드한 엑셀 파일을 그대로 사용해주세요.")
                    except Exception as e:
                        st.error(f"엑셀 파일 읽기 오류: {e}")
                
                return edited_df
                    
            edited_df = render_editor_and_save()
            action_col1, action_col2 = st.columns(2)
            
            with del_btn_place:
                if st.button("🗑️ 선택 상품 삭제", type="secondary", use_container_width=True):
                    is_selected = edited_df["선택"].fillna(False).astype(bool)
                    if is_selected.any():
                        selected_indices = edited_df[is_selected].index
                        df_result = df_result.drop(index=selected_indices).copy()
                        st.session_state.df_result = df_result
                        df_result.to_pickle("last_analysis.pkl")
                        if "main_data_editor_fixed" in st.session_state:
                            del st.session_state["main_data_editor_fixed"]
                        st.success("선택한 행이 삭제되었습니다.")
                        import time
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.warning("선택된 항목이 없습니다.")

            with action_col1:
                if st.button("🚀 선택 항목 자동 업로드", type="primary", use_container_width=True):
                        is_selected = edited_df["선택"].fillna(False).astype(bool)
                        if is_selected.any():
                            selected_indices = edited_df[is_selected].index
                            selected_items = edited_df.loc[selected_indices].copy()

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
                                        import re
                                        def sanitize_filename(name):
                                            return re.sub(r'[<>:"/\\|?*]', '_', name)
                                            
                                        img_dir = conf.get("image_dir", r"C:\Images")
                                        img_path = None
                                        
                                        safe_model = sanitize_filename(model)
                                        
                                        for s_name in [model, safe_model]:
                                            for ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
                                                p = os.path.join(img_dir, s_name + ext)
                                                if os.path.exists(p):
                                                    img_path = p
                                                    break
                                            if img_path: break
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

                                        brand_str = safe_str(row.get("추출_브랜드", ""))

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
                                    st.session_state.df_result = df_result
                                    df_result.to_pickle("last_analysis.pkl")
                                    if "main_data_editor_fixed" in st.session_state:
                                        del st.session_state["main_data_editor_fixed"]

                                if fail_count > 0:
                                    st.error(f"✅ 성공: {success_count}개 | ❌ 실패: {fail_count}개")
                                    with st.expander("실패 사유 보기 (클릭)"):
                                        for err in errors:
                                            st.write(err)
                                else:
                                    st.success(f"✅ {success_count}개 상품 자동 업로드 완료! 4단계 탭으로 이동되었습니다.")
                                    import time
                                    time.sleep(1.5)
                                    st.rerun()

                        else:
                            st.warning("선택된 항목이 없습니다.")

                with action_col2:
                    if st.button("📦 스토어 업로드 없이 4단계로 이동", type="secondary", use_container_width=True):
                        is_selected = edited_df["선택"].fillna(False).astype(bool)
                        if is_selected.any():
                            selected_indices = edited_df[is_selected].index
                            selected_items = edited_df.loc[selected_indices].copy()
                            selected_items["선택"] = False
                            if os.path.exists("completed_analysis.pkl"):
                                completed_df = pd.read_pickle("completed_analysis.pkl")
                                completed_df = pd.concat([completed_df, selected_items], ignore_index=True)
                            else:
                                completed_df = selected_items
                            completed_df.to_pickle("completed_analysis.pkl")
                            
                            df_result = df_result.drop(index=selected_indices).copy()
                            st.session_state.df_result = df_result
                            df_result.to_pickle("last_analysis.pkl")
                            if "main_data_editor_fixed" in st.session_state:
                                del st.session_state["main_data_editor_fixed"]
                            st.success(f"성공적으로 {len(selected_items)}개의 항목이 3단계로 이동되었습니다!")
                            import time
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.warning("선택된 항목이 없습니다.")

                st.markdown("---")

                # 사용자 편의를 위해 중요한 열을 맨 앞으로 이동시킵니다 (가로 스크롤 방지)
                important_cols_requested = ['선택', '추출_브랜드', '추출_모델명', '용도', '타오바오_단가', '최종_판매가', '가격', '추천_스토어상품명', '이미지_검색']
                important_cols = [c for c in important_cols_requested if c in df_result.columns]
                other_cols = [c for c in df_result.columns if c not in important_cols]
                df_result = df_result[important_cols + other_cols]

                # 열 숨기기 적용
                # 상품 필터 라디오 버튼

        except Exception as e:
            import traceback
            err_trace = traceback.format_exc()
            st.error(f"엑셀 파일 생성 중 에러가 발생했습니다: {e}")
            with st.expander("에러 상세 내용 보기"):
                st.code(err_trace)
            if st.button("작업 내역 초기화"):
                if os.path.exists("last_analysis.pkl"):
                    os.remove("last_analysis.pkl")
                if "analysis_done" in st.session_state:
                    del st.session_state.analysis_done
                if "df_result" in st.session_state:
                    del st.session_state.df_result
                st.rerun()
    else:
        st.warning("먼저 [📊 2단계: 상품 분석] 탭에서 데이터를 준비하고 분석을 완료해주세요!")

with tab4:
    import os
    if os.path.exists("completed_analysis.pkl"):
        try:
            completed_df = pd.read_pickle("completed_analysis.pkl")
            st.subheader("✅ 4단계: 등록 완료 관리")
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
        st.info("아직 등록 완료 처리된 상품이 없습니다. 3단계 탭에서 항목을 선택하고 완료 처리해 주세요.")
