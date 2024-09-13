import streamlit as st
import pandas as pd
from openai import OpenAI
import json
from datetime import datetime

st.title("Zotero CSV 기반 관련 연구 정리 도구")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["openai_api_key"])

# 사용자 가이드: Zotero에서 CSV 파일 내보내기
st.subheader("Zotero에서 CSV 파일 내보내는 방법")

col1, col2 = st.columns(2)
with col1:
    st.image("zotero_export_step1.png", caption="1단계: 컬렉션 내보내기")
with col2:
    st.image("zotero_export_step2.png", caption="2단계: CSV 형식 선택")

# CSV 파일 업로드 기능
uploaded_file = st.file_uploader("Zotero에서 내보낸 CSV 파일을 업로드하세요", type=["csv"])

# 사용자의 논문 아웃라인 입력란
user_outline = st.text_area("논문의 아웃라인을 입력하세요:")

# 제출 버튼
if st.button("제출"):
    if uploaded_file is None:
        st.info("CSV 파일을 업로드하세요.")
    elif not user_outline:
        st.info("논문의 아웃라인을 입력하세요.")
    else:
        # CSV 파일 읽기
        df = pd.read_csv(uploaded_file)

        # 필요한 열만 추출
        required_columns = ['Publication Year', 'Title', 'Author', 'Abstract Note']
        df_filtered = df[required_columns].dropna()

        # 출판 연도별로 정렬
        df_sorted = df_filtered.sort_values('Publication Year')

        # JSON 형식으로 변환
        literature_review = []
        for _, row in df_sorted.iterrows():
            paper = {
                'Publication_Year': str(row['Publication Year']),
                'Title': row['Title'],
                'Author': row['Author'],
                'Abstract_Note': row['Abstract Note']
            }
            literature_review.append(paper)

        json_string = json.dumps(literature_review, ensure_ascii=False, indent=2)

        # OpenAI API를 사용하여 주제별로 논문 분류
        prompt = f"""다음은 사용자의 논문 아웃라인입니다:

{user_outline}

아래의 JSON 형식으로 정리된 문헌 정보를 분석하고, 사용자의 논문 아웃라인과의 연관성을 고려하여 주요 주제별로 논문을 정리하세요. 결과는 마크다운 형식으로 출력해주세요. 각 주제 아래에 관련된 논문을 다음 형식으로 나열하세요:

## 주제
#### {{논문 제목}}
- 논문 요약: {{논문 요약}}
- 관련성: {{사용자의 논문 아웃라인과의 관련성 설명}}

#### {{논문 제목}}
- 논문 요약: {{논문 요약}}
- 관련성: {{사용자의 논문 아웃라인과의 관련성 설명}}

## 주제 2
- ...

JSON 문헌 정보:

{json_string}"""
        
        # OpenAI 입력 표시
        input_display = st.empty()
        input_display.text_area("OpenAI API 입력:", value=prompt, height=300)
        
        # 로딩 중 표시
        with st.spinner('OpenAI API를 통해 관련 연구를 정리 중입니다. 잠시만 기다려 주세요...'):
            # 스트리밍 출력을 위한 빈 컨테이너 생성
            output_container = st.empty()
            full_response = ""
            
            # 스트리밍 응답 생성
            for chunk in client.chat.completions.create(
                model="chatgpt-4o-latest",
                messages=[
                    {"role": "system", "content": "당신은 문헌 리뷰를 정리하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
            ):
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    output_container.markdown(full_response)
            
            # 최종 응답 표시
            output_container.markdown(full_response)
        
        # 데이터 미리보기 표시
        st.subheader("업로드된 데이터 미리보기")
        st.dataframe(df_sorted)
        
        # 기본 데이터 정보 표시
        st.subheader("기본 데이터 정보")
        st.write(f"논문 총 개수: {len(df_sorted)}")
        st.write(f"출판 연도 범위: {df_sorted['Publication Year'].min()} - {df_sorted['Publication Year'].max()}")