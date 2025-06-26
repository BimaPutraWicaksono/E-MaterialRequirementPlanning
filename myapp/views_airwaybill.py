import openpyxl
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AirWayBill, PurchaseRequest, PurchaseOrder, RequestItem
from django.conf import settings
import imaplib
import email
from email.header import decode_header
from io import BytesIO

@login_required
def import_airwaybill(request):
    if request.method == 'POST':
        excel_file, error_message = get_excel_from_email()
        if not excel_file:
            messages.error(request, error_message or "Gagal mengambil file.")
            return redirect('import_airwaybill')

        wb = openpyxl.load_workbook(excel_file)
        sheet = wb.active

        airwaybill_no = str(sheet['D4'].value).strip()
        registered_no_str = str(sheet['D5'].value).strip()
        date = sheet['D6'].value
        weight = str(sheet['D7'].value).strip()
        shipping_cost = str(sheet['D8'].value).strip()

        try:
            purchase_request = PurchaseRequest.objects.get(registered_no=registered_no_str)
        except PurchaseRequest.DoesNotExist:
            messages.error(request, f"PurchaseRequest dengan PR No '{registered_no_str}' tidak ditemukan.")
            return redirect('import_airwaybill')

        if AirWayBill.objects.filter(airwaybill_no=airwaybill_no).exists():
            messages.warning(request, f"AirWayBill dengan nomor '{airwaybill_no}' sudah ada.")
        else:
            AirWayBill.objects.create(
                airwaybill_no=airwaybill_no,
                registered_no=purchase_request,
                date=date,
                weight=weight,
                shipping_cost=shipping_cost
            )
            messages.success(request, f"AirWayBill '{airwaybill_no}' berhasil disimpan.")

        return redirect('import_airwaybill')

    # Ambil semua data AirWayBill untuk ditampilkan
    air_waybills = AirWayBill.objects.select_related('registered_no').all()
    return render(request, 'airwaybill/airwaybill.html', {
        'air_waybills': air_waybills,
    })

def get_excel_from_email():
    import imaplib
    import email
    from email.header import decode_header
    from io import BytesIO

    try:
        mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, '(SUBJECT "AIRWAYBILL")')
        email_ids = messages[0].split()
        if not email_ids:
            return None, "Tidak ditemukan email dengan subject 'AIRWAYBILL'."

        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = msg_data[0][1]

        msg = email.message_from_bytes(raw_email)

        for part in msg.walk():
            content_disposition = part.get("Content-Disposition", "")
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename and filename.endswith(".xlsx"):
                    file_data = part.get_payload(decode=True)
                    return BytesIO(file_data), None

        return None, "Tidak ditemukan file Excel di attachment."
    except Exception as e:
        return None, f"Terjadi kesalahan saat mengambil email: {str(e)}"



@login_required
def airwaybill_detail(request, registered_no):
    purchase_request = get_object_or_404(PurchaseRequest, registered_no=registered_no)
    request_items = RequestItem.objects.filter(purchase_request=purchase_request)
    po = PurchaseOrder.objects.filter(registered_no=purchase_request).last()

    # Perbaikan penulisan nama model
    airwaybill = AirWayBill.objects.filter(registered_no=purchase_request).last()

    return render(request, 'airwaybill/airwaybill_detail.html', {
        'purchase_request': purchase_request,
        'request_items': request_items,
        'created_po': po,
        'airwaybill': airwaybill,
    })
