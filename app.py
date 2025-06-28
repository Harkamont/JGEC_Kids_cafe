import csv
import os
import time
from datetime import datetime, timedelta
from threading import Thread

import pytz
import schedule
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
)


from send_csv_email import send_email_with_csv

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 세션을 위한 비밀키 설정

# Constants
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "3762211"

# Constants
CSV_FILE = "reservations.csv"
CONTENT_FILE = "site_content.csv"  # 사이트 콘텐츠를 저장할 파일
DAYS_TO_SHOW = 3
EXCLUDE_DAYS = [6, 0]  # Sunday(6) and Monday(0)
KST = pytz.timezone("Asia/Seoul")
IMAGE_FOLDER = "static/images"


# Helper functions
def read_reservations():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))

def get_next_reservation_id():
    """예약 ID를 생성하는 함수입니다. 기존 ID의 최대값 + 1로 생성하여 중복을 방지합니다."""
    reservations = read_reservations()
    if not reservations:
        return 1
    try:
        # 모든 예약에서 예약 ID를 정수로 변환하여 최대값 찾기
        max_id = max(int(r["예약 ID"]) for r in reservations)
        return max_id + 1
    except (ValueError, KeyError):
        # ID 변환 중 오류가 발생하면 기본 방식으로 생성
        return len(reservations) + 1


def write_reservation(reservation):
    fieldnames = [
        "예약 ID",
        "신청자명",
        "참석인원",
        "연락처",
        "주의사항",
        "타임 슬롯",
        "예약 날짜",
        "제출 시간",
    ]

    # Check for duplicates
    reservations = read_reservations()
    for r in reservations:
        if (
            r["연락처"] == reservation["연락처"]
            and r["예약 날짜"] == reservation["예약 날짜"]
            and r["타임 슬롯"] == reservation["타임 슬롯"]
        ):
            return False  # Duplicate found

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if os.path.getsize(CSV_FILE) == 0:
            writer.writeheader()
        writer.writerow(reservation)
    return True


def translate_day_to_korean(day_name):
    translations = {
        "Monday": "월요일",
        "Tuesday": "화요일",
        "Wednesday": "수요일",
        "Thursday": "목요일",
        "Friday": "금요일",
        "Saturday": "토요일",
        "Sunday": "일요일",
    }
    return translations.get(day_name, day_name)


def get_next_days():
    today = datetime.now(KST)
    next_days = []
    added_days = 0
    current_day = today

    while added_days < DAYS_TO_SHOW:
        if current_day.weekday() not in EXCLUDE_DAYS:
            next_days.append(current_day)
            added_days += 1
        current_day += timedelta(days=1)
    return next_days


def get_current_participants(date, time_slot):
    reservations = read_reservations()
    current_reservations = [
        r
        for r in reservations
        if r["예약 날짜"] == date and r["타임 슬롯"] == time_slot
    ]
    return sum(int(r["참석인원"]) for r in current_reservations)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def read_site_content():
    """사이트 콘텐츠를 읽는 함수"""
    if not os.path.exists(CONTENT_FILE):
        # 기본 콘텐츠 설정
        default_content = {
            "location": "증가교회(서대문구 거북골로 162) 지하 2층 벧엘홀",
            "notice1": "원활한 이용을 위해 이용 수칙을 꼭 준수해 주시기 부탁드립니다.",
            "notice2": "7월과 8월은 교회 행사로 증가교회 교인외 이용이 불가합니다.",
            "notice3": "당일 예약 및 이용은 불가합니다.",
            "contact": "교인의 경우 김재환 목사(010-6721-2400)를 통해 문의 부탁드립니다."
        }
        # 기본 콘텐츠를 CSV 파일에 저장
        with open(CONTENT_FILE, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["key", "value"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for key, value in default_content.items():
                writer.writerow({"key": key, "value": value})
        return default_content
    
    # CSV 파일에서 콘텐츠 읽기
    content = {}
    with open(CONTENT_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            content[row["key"]] = row["value"]
    return content


def write_site_content(content):
    """사이트 콘텐츠를 저장하는 함수"""
    with open(CONTENT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["key", "value"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for key, value in content.items():
            writer.writerow({"key": key, "value": value})
    return True


# Routes
@app.route("/")
def main():
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(".jpg")]
    reservations = read_reservations()
    next_days = get_next_days()
    formatted_days = [
        (day.strftime("%Y-%m-%d"), translate_day_to_korean(day.strftime("%A")))
        for day in next_days
    ]

    filtered_reservations = {
        day: {"오전 (10~12시)": [], "오후 1부 (13~15시)": [], "오후 2부 (15~17시)": []}
        for day, _ in formatted_days
    }

    for reservation in reservations:
        reservation_date = reservation["예약 날짜"]
        time_slot = reservation["타임 슬롯"]
        if (
            reservation_date in filtered_reservations
            and time_slot in filtered_reservations[reservation_date]
        ):
            filtered_reservations[reservation_date][time_slot].append(
                {
                    "참석인원": int(reservation["참석인원"]),
                    "신청자명": reservation["신청자명"],
                }
            )
    
    # 사이트 콘텐츠 가져오기
    site_content = read_site_content()

    return render_template(
        "main.html",
        days=formatted_days,
        reservations=filtered_reservations,
        image_files=image_files,
        content=site_content,  # 콘텐츠 전달
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            flash("잘못된 아이디 또는 비밀번호입니다.")
            return redirect(url_for("login"))
    return render_template("login.html")


# Logout route
@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/admin")
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    reservations = read_reservations()
    today = datetime.now(KST).strftime("%Y-%m-%d")
    
    # 사이트 콘텐츠 가져오기
    site_content = read_site_content()

    # 예약 데이터를 FullCalendar 형식으로 변환
    events = []
    time_slot_mapping = {
        "오전 (10~12시)": "10:00:00",
        "오후 1부 (13~15시)": "13:00:00",
        "오후 2부 (15~17시)": "15:00:00",
    }

    for reservation in reservations:
        time_slot = time_slot_mapping.get(reservation["타임 슬롯"], "00:00:00")
        start_time = f"{reservation['예약 날짜']}T{time_slot}"

        event = {
            "id": reservation["예약 ID"],
            "title": f"{reservation['신청자명']} ({reservation['참석인원']}명)",
            "start": start_time,
            "extendedProps": {
                "contact": reservation["연락처"],
                "notice": reservation.get("주의사항", ""),
                "submit_time": reservation.get("제출 시간", ""),
            },
        }
        events.append(event)

    return render_template(
        "admin.html", 
        reservations=reservations, 
        today=today, 
        events=events,
        content=site_content
    )


@app.route("/cancel_reservation", methods=["POST"])
def cancel_reservation():
    data = request.get_json()
    reservation_id = data.get("reservation_id")

    reservations = read_reservations()
    updated_reservations = [r for r in reservations if r["예약 ID"] != reservation_id]

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "예약 ID",
            "신청자명",
            "참석인원",
            "연락처",
            "주의사항",
            "타임 슬롯",
            "예약 날짜",
            "제출 시간",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_reservations)

    return "", 204  # 성공 응답으로 204 No Content 반환


@app.route("/submit_reservation", methods=["POST"])
def submit_reservation():
    # 안전한 방식으로 예약 ID 생성
    reservation_id = get_next_reservation_id()
    reservation_date = request.form.get("date")
    time_slot = request.form.get("time_slot")
    participants = int(request.form.get("participants"))

    # 날짜 검증 - 당일 예약 방지
    today = datetime.now(KST).strftime("%Y-%m-%d")
    if reservation_date == today:
        return "당일 예약은 불가능합니다. 다음 날부터 예약 가능합니다.", 400

    # 전화번호 검증
    phone = request.form.get("phone")
    if not phone.isdigit():
        return "전화번호는 숫자만 입력 가능합니다. 다시 시도해주세요.", 400

    current_participants = get_current_participants(reservation_date, time_slot)

    if current_participants + participants <= 15:
        # 현재 시간 기록
        current_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

        reservation = {
            "예약 ID": reservation_id,
            "신청자명": request.form.get("name"),
            "참석인원": participants,
            "연락처": phone,
            "주의사항": request.form.get("notice"),
            "타임 슬롯": time_slot,
            "예약 날짜": reservation_date,
            "제출 시간": current_time,
        }
        if write_reservation(reservation):
            return redirect(
                url_for(
                    "confirmation",
                    date=reservation_date,
                    timeSlot=time_slot,
                    participants=participants,
                )
            )
        else:
            return redirect(url_for("duplicate"))  # 중복 발생 시 이동
    else:
        return "예약 인원이 초과되었습니다.", 400


@app.route("/duplicate")
def duplicate():
    return render_template("duplicate.html")


@app.route("/reserve")
def reserve():
    time_slot = request.args.get("timeSlot")
    date = request.args.get("date")
    current_participants = get_current_participants(date, time_slot)
    return render_template(
        "reserve.html",
        time_slot=time_slot,
        date=date,
        current_participants=current_participants,
    )


@app.route("/popup")
def popup():
    time_slot = request.args.get("timeSlot")
    date = request.args.get("date")
    reservations = read_reservations()
    current_reservations = [
        r
        for r in reservations
        if r["예약 날짜"] == date and r["타임 슬롯"] == time_slot
    ]
    total_participants = sum(int(r["참석인원"]) for r in current_reservations)

    for reservation in current_reservations:
        name = reservation["신청자명"]
        if len(name) > 1:
            reservation["신청자명"] = name[0] + "•" + name[-1]

    return render_template(
        "popup.html",
        time_slot=time_slot,
        date=date,
        reservations=current_reservations,
        total_participants=total_participants,
        now=datetime.now,  # 현재 시간 함수를 템플릿에 전달
    )


@app.route("/confirmation")
def confirmation():
    date = request.args.get("date")
    time_slot = request.args.get("timeSlot")
    participants = request.args.get("participants")
    return render_template(
        "confirmation.html", date=date, timeSlot=time_slot, participants=participants
    )


@app.route("/admin_add_reservation", methods=["POST"])
def admin_add_reservation():
    data = request.get_json()
    reservation_date = data.get("date")
    time_slot = data.get("time_slot")
    name = data.get("name")
    participants = int(data.get("participants"))
    phone = data.get("phone")
    notice = data.get("notice")

    # 전화번호 검증
    if not phone.isdigit():
        return "전화번호는 숫자만 입력 가능합니다.", 400

    # 현재 참여자 수 확인 (인원 초과 여부)
    current_participants = get_current_participants(reservation_date, time_slot)
    if current_participants + participants > 15:
        return "예약 인원이 초과되었습니다.", 400

    # 안전한 방식으로 예약 ID 생성
    reservation_id = str(get_next_reservation_id())

    # 현재 시간 기록
    current_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    # 새 예약 생성
    reservation = {
        "예약 ID": reservation_id,
        "신청자명": name,
        "참석인원": participants,
        "연락처": phone,
        "주의사항": notice,
        "타임 슬롯": time_slot,
        "예약 날짜": reservation_date,
        "제출 시간": current_time,
    }

    # 예약 추가
    if write_reservation(reservation):
        return "", 204  # 성공 응답
    else:
        return "동일한 시간대에 이미 같은 전화번호로 예약이 존재합니다.", 400


@app.route("/edit_reservation", methods=["POST"])
def edit_reservation():
    data = request.get_json()
    reservation_id = data.get("reservation_id")

    # 새로운 데이터 가져오기
    new_name = data.get("name")
    new_participants = data.get("participants")
    new_phone = data.get("phone")
    new_notice = data.get("notice")

    reservations = read_reservations()

    # 해당 예약 찾기 및 수정
    for reservation in reservations:
        if reservation["예약 ID"] == reservation_id:
            reservation["신청자명"] = new_name
            reservation["참석인원"] = new_participants
            reservation["연락처"] = new_phone
            reservation["주의사항"] = new_notice
            break

    # CSV 파일에 수정된 예약 정보 저장
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "예약 ID",
            "신청자명",
            "참석인원",
            "연락처",
            "주의사항",
            "타임 슬롯",
            "예약 날짜",
            "제출 시간",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reservations)

    return "", 204  # 성공 응답으로 204 No Content 반환


@app.route("/view_reservations")
def view_reservations():
    reservations = read_reservations()
    return render_template("view_reservations.html", reservations=reservations)


@app.route("/download_reservations")
def download_reservations():
    return send_file(CSV_FILE, as_attachment=True, download_name="reservations.csv")


@app.route("/update_site_content", methods=["POST"])
def update_site_content():
    """사이트 콘텐츠를 업데이트하는 API"""
    if not session.get("logged_in"):
        return "권한이 없습니다.", 403
        
    data = request.get_json()
    if not data:
        return "데이터가 없습니다.", 400
        
    # 기존 콘텐츠 불러오기
    content = read_site_content()
    
    # 전달받은 내용으로 업데이트
    for key, value in data.items():
        content[key] = value
    
    # 저장
    if write_site_content(content):
        return "", 204  # 성공
    else:
        return "콘텐츠 저장 중 오류가 발생했습니다.", 500


@app.route("/cancel_reservation_by_user", methods=["GET"])
def cancel_reservation_by_user():
    reservation_id = request.args.get("reservationId")
    return render_template("cancel.html", reservation_id=reservation_id)


@app.route("/process_cancel_reservation_by_user", methods=["POST"])
def process_cancel_reservation_by_user():
    reservation_id = request.form["reservation_id"]
    phone = request.form["phone"]

    reservations = read_reservations()

    reservation_to_delete = None
    for reservation in reservations:
        if reservation["예약 ID"] == reservation_id and reservation["연락처"] == phone:
            reservation_to_delete = reservation
            break

    if reservation_to_delete:
        reservations.remove(reservation_to_delete)
        with open(CSV_FILE, "w", newline="") as file:
            fieldnames = (
                reservations[0].keys()
                if reservations
                else [
                    "예약 ID",
                    "신청자명",
                    "참석인원",
                    "연락처",
                    "주의사항",
                    "타임 슬롯",
                    "예약 날짜",
                    "제출 시간",
                ]
            )
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(reservations)

        # 예약 취소 후 부모 창(메인)과 예약 현황 창을 모두 리프레시
        return """
            <script>
                alert("예약이 취소되었습니다.");
                if (window.opener) {
                    if (window.opener.opener) {
                        window.opener.opener.location.reload();  // 메인 페이지 리프레시
                    }
                    window.opener.location.reload();  // 부모 창(예약 현황) 리프레시
                }
                window.close();  // 팝업 창 닫기
            </script>
        """
    else:
        return """
            <script>
                alert("연락처가 일치하지 않습니다.");
                window.history.back();  // 이전 페이지로 돌아가기
            </script>
        """


if __name__ == "__main__":
    schedule.every().day.at("07:00").do(
        send_email_with_csv, recipient_email="mares90@naver.com"
    )
    Thread(target=run_scheduler).start()
    app.run(debug=True)
