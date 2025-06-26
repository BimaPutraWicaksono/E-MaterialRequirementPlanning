import openpyxl
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Invoice, PurchaseRequest
from django.core.exceptions import ObjectDoesNotExist

def import_invoice(request):
    invoices = Invoice.objects.select_related('registered_no').all()  # ambil semua invoice

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

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
                messages.error(request, f"Tidak ditemukan PurchaseRequest dengan ID {registered_no}")
                return redirect('import_invoice')

            Invoice.objects.create(
                invoice_no=invoice_no,
                registered_no=purchase_request,
                date=date,
                last_amount=last_amount or 0
            )
            messages.success(request, "Data Invoice berhasil diimport.")
            return redirect('import_invoice')

        except Exception as e:
            messages.error(request, f"Gagal mengimport file: {str(e)}")
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
