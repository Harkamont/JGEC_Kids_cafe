import csv
import os
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import pytz
import time
import schedule
from threading import Thread
from send_csv_email import send_email_with_csv

app = Flask(__name__)

# CSV 파일 경로
CSV_FILE = "reservations.csv"

# 날짜 관련 설정
DAYS_TO_SHOW = 3  # 오늘 + 3일의 정보 표시
EXCLUDE_DAYS = [6, 0]  # 일요일(6)과 월요일(0)을 제외
KST = pytz.timezone("Asia/Seoul")  # 한국 시간대
schedule.every().day.at("07:00").do(
    send_email_with_csv, recipient_email="mares90@naver.com"
)
# 이미지 폴더 경로
IMAGE_FOLDER = "static/images"  # static 폴더 내 images 폴더 사용


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def translate_day_to_korean(day_name):
    day_translations = {
        "Monday": "월요일",
        "Tuesday": "화요일",
        "Wednesday": "수요일",
        "Thursday": "목요일",
        "Friday": "금요일",
        "Saturday": "토요일",
        "Sunday": "일요일",
    }
    return day_translations.get(day_name, day_name)


def read_reservations():
    reservations = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                reservations.append(row)
    return reservations


def write_reservation(reservation):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "예약 ID",
            "신청자명",
            "참석인원",
            "연락처",
            "주의사항",
            "타임 슬롯",
            "예약 날짜",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if os.path.getsize(CSV_FILE) == 0:
            writer.writeheader()
        writer.writerow(reservation)


@app.route("/admin")
def admin():
    reservations = read_reservations()
    today = datetime.now(KST).strftime(
        "%Y-%m-%d"
    )  # 한국 시간 기준으로 오늘 날짜 가져오기
    return render_template("admin.html", reservations=reservations, today=today)


@app.route("/cancel_reservation", methods=["POST"])
def cancel_reservation():
    reservation_id = request.form.get("reservation_id")

    reservations = read_reservations()
    updated_reservations = [r for r in reservations if r["예약 ID"] != reservation_id]

    # CSV 파일을 덮어쓰기 위해 기존 내용을 지우고 다시 작성
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "예약 ID",
            "신청자명",
            "참석인원",
            "연락처",
            "주의사항",
            "타임 슬롯",
            "예약 날짜",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_reservations)

    return redirect(url_for("admin"))  # 취소 후 관리자 페이지로 리다이렉트


@app.route("/submit_reservation", methods=["POST"])
def submit_reservation():
    reservations = read_reservations()
    reservation_id = len(reservations) + 1  # 예약 ID 자동 증가
    reservation_date = request.form.get("date")
    time_slot = request.form.get("time_slot")
    participants = int(request.form.get("participants"))  # 선택된 참석 인원 수

    # 예약된 인원 수 확인 및 업데이트
    current_reservations = [
        r
        for r in reservations
        if r["예약 날짜"] == reservation_date and r["타임 슬롯"] == time_slot
    ]
    total_current_participants = sum(int(r["참석인원"]) for r in current_reservations)

    if total_current_participants + participants <= 15:
        reservation = {
            "예약 ID": reservation_id,
            "신청자명": request.form.get("name"),
            "참석인원": participants,  # 전체 인원을 한 번에 추가
            "연락처": request.form.get("phone"),
            "주의사항": request.form.get("notice"),
            "타임 슬롯": time_slot,
            "예약 날짜": reservation_date,
        }
        write_reservation(reservation)
        return redirect(
            url_for(
                "confirmation",
                date=reservation_date,
                timeSlot=time_slot,
                participants=participants,
            )
        )
    else:
        return "예약 인원이 초과되었습니다.", 400


def get_next_days():
    today = datetime.now(KST)  # 한국 시간 기준으로 오늘 날짜 가져오기
    next_days = []
    added_days = 0

    while added_days < DAYS_TO_SHOW:
        if today.weekday() not in EXCLUDE_DAYS:
            next_days.append(today)
            added_days += 1
        today += timedelta(days=1)

    return next_days


@app.route("/reserve")
def reserve():
    time_slot = request.args.get("timeSlot")
    date = request.args.get("date")

    # 현재 타임 슬롯에 예약된 인원 수 계산
    reservations = read_reservations()
    current_reservations = [
        r
        for r in reservations
        if r["예약 날짜"] == date and r["타임 슬롯"] == time_slot
    ]
    current_participants = sum(int(r["참석인원"]) for r in current_reservations)

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

    # 현재 타임 슬롯에 예약된 인원 수 계산
    reservations = read_reservations()
    current_reservations = [
        r
        for r in reservations
        if r["예약 날짜"] == date and r["타임 슬롯"] == time_slot
    ]
    total_participants = sum(int(r["참석인원"]) for r in current_reservations)

    # 이름을 중간에 별표로 변환
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
    )


@app.route("/confirmation")
def confirmation():
    date = request.args.get("date")
    time_slot = request.args.get("timeSlot")
    participants = request.args.get("participants")
    return render_template(
        "confirmation.html", date=date, timeSlot=time_slot, participants=participants
    )


@app.route("/")
def main():
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(".jpg")]
    reservations = read_reservations()
    today = datetime.now(KST)
    next_days = get_next_days()
    formatted_days = [
        (day.strftime("%Y-%m-%d"), translate_day_to_korean(day.strftime("%A")))
        for day in next_days
    ]

    # 각 날짜와 타임 슬롯별로 예약 현황을 보여줄 수 있도록 데이터를 필터링합니다.
    filtered_reservations = {
        day: {"오전 (10~12시)": [], "오후 1부 (13~15시)": [], "오후 2부 (15~17시)": []}
        for day, _ in formatted_days
    }

    for reservation in reservations:
        reservation_date = reservation["예약 날짜"]
        time_slot = reservation["타임 슬롯"]

        # 날짜와 타임 슬롯이 filtered_reservations에 존재할 경우에만 추가
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

    return render_template(
        "main.html",
        days=formatted_days,
        reservations=filtered_reservations,
        image_files=image_files,
    )


if __name__ == "__main__":
    app.run(debug=True)
