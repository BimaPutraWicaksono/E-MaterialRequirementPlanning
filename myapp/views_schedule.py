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

    try:
        mail.login(email_user, email_pass)
        mail.select("inbox")

        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        latest_email_ids = email_ids[-10:]  # Ambil hanya 10 email terbaru

        downloaded_files = []
        download_dir = os.path.join(settings.MEDIA_ROOT, "email_files")
        os.makedirs(download_dir, exist_ok=True)

        for eid in reversed(latest_email_ids):
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

        request.session['downloaded_files'] = downloaded_files

    except Exception as e:
        messages.error(request, f"Gagal memeriksa email: {str(e)}")

    finally:
        mail.logout()

    return redirect('scheduleConf')

@login_required()
def scheduleConf(request):
    # Ambil file baru dari session
    new_files = request.session.pop('downloaded_files', [])

    # Ambil file lama dari folder
    email_files_dir = os.path.join(settings.MEDIA_ROOT, 'email_files')
    existing_files = []

    if os.path.exists(email_files_dir):
        for fname in os.listdir(email_files_dir):
            if fname.lower().endswith('.pdf'):
                # Hindari duplikasi jika file sudah ada di new_files
                if not any(f['filename'] == fname for f in new_files):
                    existing_files.append({
                        "filename": fname,
                        "subject": "",
                        "sender": "",
                        "date": "",
                        "source": "Folder"
                    })

    # Tandai source untuk file baru
    for f in new_files:
        f['source'] = 'Email'

    all_files = new_files + existing_files

    return render(request, 'schedule_conf/scheduleConf.html', {
        'files': all_files,
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
