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
        excel_files, error_message = get_excel_from_email()
        if not excel_files:
            messages.error(request, error_message or "No files retrieved.")
            return redirect('import_airwaybill')

        for excel_file in excel_files:
            try:
                wb = openpyxl.load_workbook(excel_file)
                sheet = wb.active

                airwaybill_no = str(sheet['D4'].value).strip()
                registered_no_str = str(sheet['D5'].value).strip()
                date = sheet['D6'].value
                weight = str(sheet['D7'].value).strip()
                shipping_cost_raw = str(sheet['D8'].value).strip()
                shipping_cost = shipping_cost_raw.replace('$', '').replace(',', '').strip()


                try:
                    purchase_request = PurchaseRequest.objects.get(registered_no=registered_no_str)
                except PurchaseRequest.DoesNotExist:
                    messages.error(request, f"PR No '{registered_no_str}' not found.")
                    continue

                if AirWayBill.objects.filter(airwaybill_no=airwaybill_no).exists():
                    messages.warning(request, f"AirWayBill '{airwaybill_no}' already exists.")
                else:
                    AirWayBill.objects.create(
                        airwaybill_no=airwaybill_no,
                        registered_no=purchase_request,
                        date=date,
                        weight=weight,
                        shipping_cost=shipping_cost
                    )
                    messages.success(request, f"AirWayBill '{airwaybill_no}' saved.")

            except Exception as e:
                messages.error(request, f"Failed to process a file: {str(e)}")

        return redirect('import_airwaybill')

    air_waybills = AirWayBill.objects.select_related('registered_no').all()
    return render(request, 'airwaybill/airwaybill.html', {
        'air_waybills': air_waybills,
    })

from datetime import datetime
import email.utils

def get_excel_from_email():
    try:
        mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST)
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select("inbox")

        # Cari semua email dengan SUBJECT 'AIRWAYBILL'
        status, messages = mail.search(None, '(SUBJECT "AIRWAYBILL")')
        email_ids = messages[0].split()
        if not email_ids:
            return [], "Subject 'AIRWAYBILL' not found."

        today = datetime.now().date()
        excel_files = []

        for email_id in reversed(email_ids):  # cek dari terbaru ke terlama
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Ambil tanggal email dan cocokan dengan hari ini
            msg_date_tuple = email.utils.parsedate_tz(msg["Date"])
            if msg_date_tuple is None:
                continue
            msg_date = datetime.fromtimestamp(email.utils.mktime_tz(msg_date_tuple)).date()
            if msg_date != today:
                continue  # Skip jika bukan email hari ini

            # Cek semua attachment dan ambil file .xlsx
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
 
@login_required
def manual_airwaybill(request):
    if request.method == 'POST':
        airwaybill_no = request.POST.get('airwaybill_no').strip()
        registered_no_str = request.POST.get('registered_no').strip()
        date = request.POST.get('date')
        weight = request.POST.get('weight').strip()
        shipping_cost = request.POST.get('shipping_cost').replace('$', '').replace(',', '').strip()

        try:
            purchase_request = PurchaseRequest.objects.get(registered_no=registered_no_str)
        except PurchaseRequest.DoesNotExist:
            messages.error(request, f"PR No '{registered_no_str}' not found.")
            return redirect('import_airwaybill')

        if AirWayBill.objects.filter(airwaybill_no=airwaybill_no).exists():
            messages.warning(request, f"AirWayBill '{airwaybill_no}' already exists.")
        else:
            AirWayBill.objects.create(
                airwaybill_no=airwaybill_no,
                registered_no=purchase_request,
                date=date,
                weight=weight,
                shipping_cost=shipping_cost
            )
            messages.success(request, f"AirWayBill '{airwaybill_no}' saved successfully.")
    
    return redirect('import_airwaybill')

@login_required
def edit_airwaybill(request, airwaybill_id):
    awb = get_object_or_404(AirWayBill, id=airwaybill_id)
    
    if request.method == 'POST':
        airwaybill_no = request.POST.get('airwaybill_no').strip()
        date = request.POST.get('date')
        weight = request.POST.get('weight').strip()
        shipping_cost = request.POST.get('shipping_cost').replace('$', '').replace(',', '').strip()

        # Cek jika AirWayBill No berubah dan tidak duplikat
        if awb.airwaybill_no != airwaybill_no and AirWayBill.objects.filter(airwaybill_no=airwaybill_no).exists():
            messages.error(request, f"AirWayBill '{airwaybill_no}' already exists.")
        else:
            awb.airwaybill_no = airwaybill_no
            awb.date = date
            awb.weight = weight
            awb.shipping_cost = shipping_cost
            awb.save()
            messages.success(request, "AirWayBill updated successfully.")
    
    return redirect('import_airwaybill')

@login_required
def delete_airwaybill(request, airwaybill_id):
    awb = get_object_or_404(AirWayBill, id=airwaybill_id)

    if request.method == 'POST':
        awb.delete()
        messages.success(request, "AirWayBill deleted successfully.")
    
    return redirect('import_airwaybill')
