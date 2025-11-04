# 파일명: stock_app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# -----------------------------------------------------
# 💡 핵심 데이터 호출 및 분석 함수 (2단계 검증 완료)
# -----------------------------------------------------

def get_stock_data(code, days=90):
    """
    yfinance를 사용하여 주식 데이터를 가져와 기술적 지표 (MA, RSI)를 계산합니다.
    """
    # 날짜 포맷팅
    TODAY = datetime.date.today().strftime('%Y-%m-%d')
    START_DATE = (datetime.date.today() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    
    # 한국 종목일 경우 자동으로 .KS를 붙여주는 로직
    if code.isdigit() and len(code) == 6:
        code += '.KS'
        
    try:
        ticker_data = yf.Ticker(code)
        # 데이터 로딩
        df = ticker_data.history(start=START_DATE, end=TODAY)
        
        if df.empty:
            return pd.DataFrame(), '데이터 없음', code
            
        # 💡 분석 로직 (기술적 지표 계산)
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['MA_50'] = df['Close'].rolling(window=50).mean()
        
        # RSI 계산 (단순화된 방식)
        delta = df['Close'].diff(1)
        gain = delta.where(delta > 0, 0)
        loss = delta.where(delta < 0, 0).abs()
        avg_gain = gain.ewm(com=14 - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=14 - 1, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 가상 추천 신호 생성 (매수/매도 로직은 그대로)
        latest_row = df.iloc[-1]
        signal = '관망'
        
        if latest_row['RSI'] < 30 and latest_row['MA_20'] > latest_row['MA_50']:
            signal = '강력 매수' 
        elif latest_row['RSI'] > 70 and latest_row['MA_20'] < latest_row['MA_50']:
            signal = '강력 매도' 
        
        df['Signal'] = signal
        df = df.dropna()
        
        return df, signal, code
        
    except Exception:
        return pd.DataFrame(), '데이터 로딩 오류', code


# -----------------------------------------------------
# 💡 Streamlit UI (최종 문법 오류 수정 완료)
# -----------------------------------------------------

st.set_page_config(layout="wide")
st.title("📈 주식 기술적 분석 및 추천 시스템")
st.markdown("---")

# 사용자 입력
col1, col2 = st.columns([1, 2])
with col1:
    stock_code = st.text_input("분석할 종목 티커/코드 입력 (예: AAPL, 005930):", "005930").strip().upper()
    days_input = st.slider("조회 기간 (일):", min_value=90, max_value=365, value=200)

if st.button("분석 실행 및 추천 신호 확인"):
    
    with st.spinner(f"종목 {stock_code} 분석 중..."):
        df_analysis, current_signal, final_ticker = get_stock_data(stock_code, days_input)

    if not df_analysis.empty:
        st.success(f"✅ 분석 완료! 현재 종목: {final_ticker}")
        
        # 추천 신호 표시
        st.subheader("⭐ 추천 신호")
        if current_signal == '강력 매수':
            st.success(f"현재 신호: {current_signal} | 지표가 긍정적입니다!")
        elif current_signal == '강력 매도':
            st.error(f"현재 신호: {current_signal} | 지표가 부정적입니다!")
        else:
            st.info(f"현재 신호: {current_signal} | 시장 상황을 더 지켜봐야 합니다.")
        
        # 주가 및 MA 차트
        st.subheader("주가 및 이동평균선(MA) 추이")
        st.line_chart(df_analysis[['Close', 'MA_20', 'MA_50']])
        
        # 데이터프레임 표시 (문법 오류 수정 완료된 최종 포맷)
        max_price = df_analysis['Close'].max()
        min_price = df_analysis['Close'].min()
        
        st.metric(label="최근 종가", 
                  value=f"{df_analysis['Close'].iloc[-1]:,}", 
                  delta=f"{df_analysis['Signal'].iloc[-1]}") 
        
        st.info(f"기간 내 최고 종가: {max_price:,}원 | 최저 종가: {min_price:,}원")
        
    else:
        st.error(f"❌ 분석 실패: {current_signal} ({final_ticker}). 종목 코드를 다시 확인하거나 기간을 조정해 보세요.")