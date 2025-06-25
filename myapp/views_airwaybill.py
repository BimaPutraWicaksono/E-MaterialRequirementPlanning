import openpyxl
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AirWayBill, PurchaseRequest, PurchaseOrder, RequestItem


@login_required
def import_airwaybill(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
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
