# myapp/views_schedule.py
import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from .models import ScheduleConf
from django.contrib import messages

def scheduleConf(request):
    if request.method == 'POST':
        today = datetime.now().date()

        # Login ke IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")  # sesuaikan server jika bukan Gmail
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select("inbox")

        # Cari email hari ini saja
        result, data = mail.search(None, f'(SINCE "{today.strftime("%d-%b-%Y")}")')

        if result == "OK":
            for num in data[0].split():
                res, msg_data = mail.fetch(num, "(RFC822)")
                if res != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                if "purchase order" in subject.lower():
                    # Ekstrak hanya bagian 2w dari format "Purchase Order (purchase_order_2w)"
                    match = re.search(r"purchase_order_(\w+)", subject.lower())
                    if match:
                        registered_no = match.group(1)  # "2w"
                    else:
                        continue  # Jika format tidak sesuai, skip

                    if not ScheduleConf.objects.filter(registered_no=registered_no).exists():
                        acc_rej = None
                        date_found = None

                        # Ambil isi pesan
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    try:
                                        body = part.get_payload(decode=True).decode()
                                        break
                                    except:
                                        continue
                        else:
                            body = msg.get_payload(decode=True).decode()

                        body_lower = body.lower()

                        if "accept" in body_lower:
                            acc_rej = True
                            date_match = re.search(r"\d{4}-\d{2}-\d{2}", body)
                            if date_match:
                                date_found = datetime.strptime(date_match.group(), "%Y-%m-%d").date()
                        elif "reject" in body_lower:
                            acc_rej = False

                        ScheduleConf.objects.create(
                            registered_no=registered_no,
                            acc_rej=acc_rej,
                            date=date_found
                        )

            messages.success(request, "Email berhasil diproses.")
        else:
            messages.error(request, "Tidak dapat mengambil email.")

        mail.logout()
        return redirect('scheduleConf')

    all_data = ScheduleConf.objects.all()
    return render(request, 'schedule_conf/scheduleConf.html', {'data': all_data})
