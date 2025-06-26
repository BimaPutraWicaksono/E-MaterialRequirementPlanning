from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Invoice, PurchaseRequest
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from io import BytesIO
import openpyxl
import imaplib
import email
from datetime import datetime
import email.utils

def get_invoice_excel_from_email():
    try:
        mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select("inbox")

        # Cari semua email dengan SUBJECT 'INVOICE'
        status, messages_data = mail.search(None, '(SUBJECT "INVOICE")')
        email_ids = messages_data[0].split()
        if not email_ids:
            return [], "Subject 'INVOICE' not found."

        today = datetime.now().date()
        excel_files = []

        for email_id in reversed(email_ids):  # dari terbaru ke terlama
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            msg_date_tuple = email.utils.parsedate_tz(msg["Date"])
            if msg_date_tuple is None:
                continue
            msg_date = datetime.fromtimestamp(email.utils.mktime_tz(msg_date_tuple)).date()
            if msg_date != today:
                continue  # Skip jika bukan email hari ini

            for part in msg.walk():
                content_disposition = part.get("Content-Disposition", "")
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename and filename.endswith(".xlsx"):
                        file_data = part.get_payload(decode=True)
                        excel_files.append(BytesIO(file_data))

        if not excel_files:
            return [], "No Excel attachments found for today."

        return excel_files, None
    except Exception as e:
        return [], f"An error occurred while retrieving emails: {str(e)}"


@login_required
def import_invoice(request):
    invoices = Invoice.objects.select_related('registered_no').all()

    if request.method == 'POST':
        excel_files, error_message = get_invoice_excel_from_email()
        if not excel_files:
            messages.error(request, error_message or "No files found.")
            return redirect('import_invoice')

        for excel_file in excel_files:
            try:
                wb = openpyxl.load_workbook(excel_file)
                sheet = wb.active

                invoice_no = sheet['D4'].value
                registered_no = sheet['D5'].value
                date = sheet['D6'].value
                raw_last_amount = sheet['H19'].value

                if isinstance(raw_last_amount, str):
                    cleaned_amount = raw_last_amount.replace('$', '').replace(',', '').strip()
                else:
                    cleaned_amount = raw_last_amount

                try:
                    last_amount = float(cleaned_amount)
                except (ValueError, TypeError):
                    last_amount = 0

                try:
                    purchase_request = PurchaseRequest.objects.get(registered_no=registered_no)
                except ObjectDoesNotExist:
                    messages.error(request, f"PurchaseRequest dengan ID {registered_no} tidak ditemukan.")
                    continue

                if Invoice.objects.filter(invoice_no=invoice_no).exists():
                    messages.warning(request, f"Invoice '{invoice_no}' sudah ada.")
                else:
                    Invoice.objects.create(
                        invoice_no=invoice_no,
                        registered_no=purchase_request,
                        date=date,
                        last_amount=last_amount or 0
                    )
                    messages.success(request, f"Invoice '{invoice_no}' berhasil diimport.")

            except Exception as e:
                messages.error(request, f"Gagal memproses file: {str(e)}")

        return redirect('import_invoice')

    return render(request, 'invoice/invoice.html', {'invoices': invoices})


from .models import PurchaseOrder, RequestItem

@login_required
def invoice_detail(request, registered_no):
    purchase_request = get_object_or_404(PurchaseRequest, registered_no=registered_no)
    request_items = RequestItem.objects.filter(purchase_request=purchase_request)
    po = PurchaseOrder.objects.filter(registered_no=purchase_request).last()
    invoice = Invoice.objects.filter(registered_no=purchase_request).last()

    return render(request, 'invoice/invoice_detail.html', {
        'purchase_request': purchase_request,
        'request_items': request_items,
        'created_po': po,
        'invoice': invoice,
    })
