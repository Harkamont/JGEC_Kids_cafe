# 베이스 이미지로 Python 3.9 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치를 위한 requirements.txt 복사
COPY requirements.txt .

# 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 코드를 컨테이너에 복사
COPY . .

# Flask 환경 변수 설정
ENV FLASK_APP=app.py

# Flask 서버 실행
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--no-debugger", "--no-reload"]