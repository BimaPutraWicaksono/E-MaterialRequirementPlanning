# myapp/views_schedule.py
import imaplib
import email
import os
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import FileResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

@login_required
def check_email(request):
    email_user = settings.EMAIL_HOST_USER
    email_pass = settings.EMAIL_HOST_PASSWORD
    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(email_user, email_pass)
    mail.select("inbox")

    status, messages = mail.search(None, 'ALL')
    email_ids = messages[0].split()
    downloaded_files = []

    for eid in reversed(email_ids):
        status, data = mail.fetch(eid, "(RFC822)")
        raw_email = data[0][1]

        msg = email.message_from_bytes(raw_email)
        subject = msg.get("subject", "")
        sender = msg.get("from", "")
        date = msg.get("date", "")

        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition") is None:
                continue

            filename = part.get_filename()
            if filename and filename.lower().endswith(".pdf") and "schedule confirmation" in filename.lower():
                download_dir = os.path.join(settings.MEDIA_ROOT, "email_files")
                os.makedirs(download_dir, exist_ok=True)
                filepath = os.path.join(download_dir, filename)

                if not os.path.exists(filepath):
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    downloaded_files.append({
                        "filename": filename,
                        "saved_path": filepath,
                        "subject": subject,
                        "sender": sender,
                        "date": date,
                    })

    mail.logout()
    request.session['downloaded_files'] = downloaded_files
    return redirect('scheduleConf')

@login_required()
def scheduleConf(request):
    files = request.session.pop('downloaded_files', [])

    email_files_dir = os.path.join(settings.MEDIA_ROOT, 'email_files')
    existing_files = []

    if os.path.exists(email_files_dir):
        for fname in os.listdir(email_files_dir):
            if fname.lower().endswith('.pdf'):
                existing_files.append(fname)

    return render(request, 'schedule_conf/scheduleConf.html', {
        'files': files,
        'existing_files': existing_files,
        'media_url': settings.MEDIA_URL,
    })

# Tambahkan view untuk delete file
from django.http import JsonResponse

@login_required
def delete_file(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'email_files', filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'File not found'}, status=404)
