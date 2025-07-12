import os
import re
import imaplib
import email
from email.header import decode_header
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import EmailMessage
from django.http import (HttpResponse, JsonResponse, HttpResponseNotAllowed,)
from django.shortcuts import (render, redirect, get_object_or_404)
from django.template.loader import render_to_string, get_template
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa
# Forms
from .form import ( ShippedForm, PurchaseRequestForm, SupplierForm, PurchaseOrderForm)
# Models
from .models import ( Shipped, PurchaseRequest, RequestItem, LoadingPartResult, Section, Invoice, AirWayBill, PurchaseOrder, ScheduleConf, Supplier)


@login_required
def purchaseOrd(request):
    user_departement = request.user.departement

    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            selected_carlines = form.cleaned_data['part_order']
            budget_ref_no_list = request.POST.getlist('budget_ref_no')
            estimated_prices_list = request.POST.getlist('estimated_price')
            deadlines_list = request.POST.getlist('deadline')
            total_amount_hidden = request.POST.get('total_amount_hidden')

            try:
                total_amount = float(total_amount_hidden)
            except (TypeError, ValueError):
                total_amount = 0

            pr = form.save(commit=False)
            pr.departement = user_departement  # Set departemen sesuai user login
            pr.total_amount = total_amount
            pr.save()
            pr.part_order.set(selected_carlines)

            pr.items.all().delete()

            all_parts = []
            seen_partdesk_ids = set()

            for carline in selected_carlines:
                parts = LoadingPartResult.objects.filter(carline=carline).order_by('partdesk')
                for part in parts:
                    if part.partdesk_id and part.partdesk_id not in seen_partdesk_ids:
                        seen_partdesk_ids.add(part.partdesk_id)
                        all_parts.append(part)

            for i, part in enumerate(all_parts):
                try:
                    budget = budget_ref_no_list[i]
                    est_price = float(estimated_prices_list[i])
                    dl = deadlines_list[i] if deadlines_list[i] else None
                except (IndexError, ValueError):
                    budget = ""
                    est_price = 0
                    dl = None

                avg = part.average_round or 0
                amount = avg * est_price

                RequestItem.objects.create(
                    purchase_request=pr,
                    loading_part_result=part,
                    budget_ref_no=budget,
                    result_average_round=avg,
                    estimated_price=est_price,
                    amount=amount,
                    deadline=dl
                )

            messages.success(request, "Purchase Request berhasil disimpan.")
            return redirect('purchaseOrd')
    else:
        form = PurchaseRequestForm()

    # Ambil semua PurchaseRequest milik user
    all_requests = PurchaseRequest.objects.filter(departement=user_departement).order_by('-date')

    # PO registered_no yang sudah dibuat
    po_registered_nos = set(PurchaseOrder.objects.values_list('registered_no__registered_no', flat=True))

    # Hanya ambil PR yang sudah punya PO
    requests_with_po = all_requests.filter(registered_no__in=po_registered_nos)

    purchase_orders = {
        po.registered_no.registered_no: po
        for po in PurchaseOrder.objects.select_related('created_by').all()
    }

    # TAMBAHKAN INI: Ambil semua SC yang sudah dikirim
    sc_sent = {
        po.registered_no.registered_no: po
        for po in PurchaseOrder.objects.filter(sc_sent=True)
    }


    return render(request, 'order/purchaseOrd.html', {
        'form': form,
        'requests': requests_with_po,  # GUNAKAN YANG SUDAH DIFILTER
        'po_registered_nos': po_registered_nos,
        'purchase_orders': purchase_orders,
        'sc_sent': sc_sent,  # <-- tambahkan ini ke context
    })



@login_required
def purchase_order_detail(request, registered_no):
    purchase_request = get_object_or_404(PurchaseRequest, registered_no=registered_no)
    request_items = RequestItem.objects.filter(purchase_request=purchase_request)
    po = PurchaseOrder.objects.filter(registered_no=purchase_request).last()

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.registered_no = purchase_request
            po.created_by = request.user
            po.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    # Ambil deadline paling atas (terlama)
    earliest_deadline = request_items.exclude(deadline=None).order_by('deadline').first()
    initial_data = {}
    if earliest_deadline:
        initial_data['delivery'] = earliest_deadline.deadline

    form = PurchaseOrderForm(initial=initial_data)

    if 'delivery' in form.fields:
        form.fields['delivery'].widget.attrs['readonly'] = True

    html = render(request, 'order/partials/purchase_order_detail.html', {
        'purchase_request': purchase_request,
        'request_items': request_items,
        'po_form': form,
        'created_po': po,  # ← Nilai ini aman walaupun None
    }).content.decode('utf-8')

    return JsonResponse({'html': html})

from .models import PurchaseOrder, PurchaseRequest

def purchase_order_edit(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)
    po = get_object_or_404(PurchaseOrder, registered_no=pr)

    if request.method == "POST":
        form = PurchaseOrderForm(request.POST, instance=po)
        if form.is_valid():
            form.save()
            return redirect('purchaseOrd')
    else:
        form = PurchaseOrderForm(instance=po)

    return render(request, 'order/partials/purchase_order_edit.html', {
        'form': form,
        'po': po,
    })

def purchase_order_delete(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)
    po = get_object_or_404(PurchaseOrder, registered_no=pr)
    po.delete()
    return redirect('purchaseOrd')

@login_required
def approve_purchase_order(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Senior Supervisor
        if request.user.groups.filter(name='SeniorSupervisor').exists():
            if action == 'approve_sspv':
                pr.approve_sspv = True
                pr.reason_sspv = ''
            elif action == 'disapprove_sspv':
                reason = request.POST.get('reason_sspv', '').strip()
                if not reason:
                    messages.error(request, "Alasan penolakan harus diisi oleh Senior Supervisor.")
                    return redirect(request.META.get('HTTP_REFERER'))
                pr.approve_sspv = False
                pr.reason_sspv = reason
            pr.save()
            messages.success(request, "Senior Supervisor approval updated.")

        # Manager
        elif request.user.groups.filter(name='Manager').exists():
            if action == 'approve_manager':
                pr.approve_manager = True
                pr.reason_manager = ''
            elif action == 'disapprove_manager':
                reason = request.POST.get('reason_manager', '').strip()
                if not reason:
                    messages.error(request, "Alasan penolakan harus diisi oleh Manager.")
                    return redirect(request.META.get('HTTP_REFERER'))
                pr.approve_manager = False
                pr.reason_manager = reason
            pr.save()
            messages.success(request, "Manager approval updated.")

        # Factory Manager
        elif request.user.groups.filter(name='FactoryManager').exists():
            if action == 'approve_factory_manager':
                pr.approve_factory_manager = True
                pr.reason_factory_manager = ''
            elif action == 'disapprove_factory_manager':
                reason = request.POST.get('reason_factory_manager', '').strip()
                if not reason:
                    messages.error(request, "Alasan penolakan harus diisi oleh Factory Manager.")
                    return redirect(request.META.get('HTTP_REFERER'))
                pr.approve_factory_manager = False
                pr.reason_factory_manager = reason
            pr.save()
            messages.success(request, "Factory Manager approval updated.")

        return redirect('purchaseOrd')

from django.utils import timezone
from .models import ScheduleConf

def export_purchase_order_pdf(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)

    if not pr.approve_factory_manager:
        return HttpResponse("Unauthorized", status=403)

    template = get_template('order/partials/purchase_order_pdf.html')
    html = template.render({
        'purchase_request': pr,
        'created_po': pr.purchaseorder if hasattr(pr, 'purchaseorder') else None,
        'request_items': pr.items.all(),
        'po_form': None,
        'request': request,
        'is_pdf': True
    })

    # Path untuk menyimpan PDF
    directory = os.path.join(settings.MEDIA_ROOT, 'purchase_orders')
    os.makedirs(directory, exist_ok=True)
    filename = f"Purchase_Order_{registered_no}.pdf"
    filepath = os.path.join(directory, filename)

    with open(filepath, "wb") as f:
        pisa_status = pisa.CreatePDF(html, dest=f)

    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)

    # ✅ Update status sc_sent dan sc_sent_at
    schedule_conf = ScheduleConf.objects.filter(registered_no=pr).first()
    if schedule_conf:
        schedule_conf.sc_sent = True
        schedule_conf.sc_sent_at = timezone.now()
        schedule_conf.save()
    
    # 🔽 TAMBAHKAN INI: update juga sc_sent pada PurchaseOrder
    po = getattr(pr, 'purchaseorder', None)
    if po:
        po.sc_sent = True
        po.sc_sent_at = timezone.now()
        po.save()

    return redirect('list_exported_purchase_orders')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .models import PurchaseRequest, PurchaseOrder, ScheduleConf, Invoice, AirWayBill
import os, imaplib, email, re
from email.header import decode_header
from datetime import datetime

@login_required
def list_exported_purchase_orders(request):
    if request.method == "POST" and request.POST.get("action") == "search_email":
        today = datetime.now().date()

        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            mail.select("inbox")

            result, data = mail.search(None, f'(SINCE "{today.strftime("%d-%b-%Y")}")')

            if result == "OK":
                for num in data[0].split():
                    res, msg_data = mail.fetch(num, "(RFC822)")
                    if res != "OK":
                        continue

                    msg = email.message_from_bytes(msg_data[0][1])
                    subject, enc = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(enc or "utf-8")

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    body_lower = body.lower()
                    acc_rej = None
                    schedule_date = None

                    if "accept" in body_lower:
                        acc_rej = True
                        date_match = re.search(r"\d{4}-\d{2}-\d{2}", body)
                        if date_match:
                            schedule_date = datetime.strptime(date_match.group(), "%Y-%m-%d").date()
                    elif "reject" in body_lower:
                        acc_rej = False

                    if acc_rej is None:
                        continue

                    match = re.search(r"Purchase[_\s\-]?Order[_\-]?([\w\-]+)", subject, re.I)
                    if not match:
                        continue

                    registered_no = match.group(1)

                    try:
                        pr = PurchaseRequest.objects.get(registered_no=registered_no)
                    except PurchaseRequest.DoesNotExist:
                        continue

                    if ScheduleConf.objects.filter(registered_no=pr).exists():
                        continue

                    ScheduleConf.objects.create(
                        registered_no=pr,
                        acc_rej=acc_rej,
                        date=schedule_date,
                    )

                messages.success(request, "Email berhasil diproses.")
            else:
                messages.error(request, "Gagal mengakses inbox email.")
        except Exception as e:
            messages.error(request, f"Gagal memeriksa email: {e}")
        finally:
            try:
                mail.logout()
            except Exception:
                pass

        return redirect("list_exported_purchase_orders")

    folder_path = os.path.join(settings.MEDIA_ROOT, "purchase_orders")
    file_list = [
        f for f in os.listdir(folder_path) if f.endswith(".pdf")
    ] if os.path.exists(folder_path) else []

    file_urls = []
    for f in file_list:
        registered_no = f.replace("Purchase_Order_", "").replace(".pdf", "")
        supplier_name = "Unknown"
        acc_rej = None
        schedule_date = None
        schedule_exists = False
        po = None

        try:
            pr = PurchaseRequest.objects.get(registered_no=registered_no)
            po = PurchaseOrder.objects.get(registered_no=pr)
            supplier_name = po.supplier.name

            sc = ScheduleConf.objects.filter(registered_no=pr).first()
            if sc:
                acc_rej = sc.acc_rej
                schedule_date = sc.date
                schedule_exists = True
        except (PurchaseRequest.DoesNotExist, PurchaseOrder.DoesNotExist):
            pass

        file_urls.append({
            "name": f,
            "registered_no": registered_no,
            "url": os.path.join(settings.MEDIA_URL, "purchase_orders", f),
            "supplier_name": supplier_name,
            "email_sent": getattr(po, "email_sent", False) if po else False,
            "email_sent_at": po.email_sent_at if po else None,
            "acc_rej": acc_rej,
            "schedule_date": schedule_date,
            "schedule_exists": schedule_exists,  # ✅ Tambahkan ini agar form bisa tahu kapan edit
        })

    # Mapping invoice & airwaybill
    invoice_qs = Invoice.objects.all().select_related('registered_no')
    existing_invoices = {
        inv.registered_no.registered_no: inv.invoice_no
        for inv in invoice_qs
    }

    awb_qs = AirWayBill.objects.all().select_related('registered_no')
    existing_awb = {
        awb.registered_no.registered_no: awb.airwaybill_no
        for awb in awb_qs
    }

    return render(request, "order/list_exported_files.html", {
        "files": file_urls,
        "existing_invoices": existing_invoices,
        "existing_awb": existing_awb,
    })



@login_required
def manual_airwaybill(request):
    if request.method == "POST":
        reg_no = request.POST.get("registered_no").strip()
        airwaybill_no = request.POST.get("airwaybill_no")
        date = request.POST.get("date")
        weight = request.POST.get("weight")
        shipping_cost = request.POST.get("shipping_cost")

        try:
            pr = PurchaseRequest.objects.get(registered_no=reg_no)
        except PurchaseRequest.DoesNotExist:
            messages.error(request, f"Registered No '{reg_no}' tidak ditemukan.")
            return redirect("list_exported_purchase_orders")

        if AirWayBill.objects.filter(registered_no=pr).exists():
            messages.warning(request, "AirWay Bill sudah pernah dibuat.")
            return redirect("list_exported_purchase_orders")

        AirWayBill.objects.create(
            airwaybill_no=airwaybill_no,
            registered_no=pr,
            date=date,
            weight=weight,
            shipping_cost=shipping_cost
        )
        messages.success(request, "AirWay Bill berhasil disimpan.")

    return redirect('list_exported_purchase_orders')


@login_required
def manual_schedule_conf(request):
    if request.method == "POST":
        reg_no = request.POST.get("registered_no").strip()
        acc_rej = request.POST.get("acc_rej")
        schedule_date = request.POST.get("schedule_date")

        if acc_rej not in ["accept", "reject"]:
            messages.error(request, "Status tidak valid.")
            return redirect("list_exported_purchase_orders")

        try:
            pr = PurchaseRequest.objects.get(registered_no=reg_no)
        except PurchaseRequest.DoesNotExist:
            messages.error(request, f"Registered No '{reg_no}' tidak ditemukan.")
            return redirect("list_exported_purchase_orders")

        if ScheduleConf.objects.filter(registered_no=pr).exists():
            messages.error(request, "Data Schedule sudah ada, gunakan fitur Edit.")
            return redirect("list_exported_purchase_orders")

        ScheduleConf.objects.create(
            registered_no=pr,
            acc_rej=True if acc_rej == "accept" else False,
            date=schedule_date if acc_rej == "accept" and schedule_date else None
        )
        messages.success(request, "Schedule Confirmation berhasil ditambahkan.")
    
    return redirect("list_exported_purchase_orders")

@login_required
def manual_invoice_from_ordered(request):
    if request.method == 'POST':
        invoice_no = request.POST.get('invoice_no', '').strip()
        registered_no = request.POST.get('registered_no', '').strip()
        date = request.POST.get('date')
        last_amount_raw = request.POST.get('last_amount', '').replace('$', '').replace(',', '').strip()

        try:
            last_amount = float(last_amount_raw)
        except (ValueError, TypeError):
            last_amount = 0

        try:
            pr = PurchaseRequest.objects.get(registered_no=registered_no)
        except PurchaseRequest.DoesNotExist:
            messages.error(request, f"Registered No '{registered_no}' tidak ditemukan.")
            return redirect("list_exported_purchase_orders")

        if Invoice.objects.filter(invoice_no=invoice_no).exists():
            messages.warning(request, f"Invoice '{invoice_no}' sudah ada.")
        else:
            Invoice.objects.create(
                invoice_no=invoice_no,
                registered_no=pr,
                date=date,
                last_amount=last_amount
            )
            messages.success(request, f"Invoice '{invoice_no}' berhasil disimpan.")

    return redirect("list_exported_purchase_orders")

from datetime import datetime  # Pastikan sudah diimport
@login_required
def edit_schedule_conf(request, registered_no):
    if request.method == "POST":
        acc_rej = request.POST.get("acc_rej")
        schedule_date_raw = request.POST.get("schedule_date")

        try:
            pr = PurchaseRequest.objects.get(registered_no=registered_no)
            sc = ScheduleConf.objects.get(registered_no=pr)
        except (PurchaseRequest.DoesNotExist, ScheduleConf.DoesNotExist):
            messages.error(request, "Data tidak ditemukan.")
            return redirect("list_exported_purchase_orders")

        if acc_rej not in ["accept", "reject"]:
            messages.error(request, "Status tidak valid.")
            return redirect("list_exported_purchase_orders")

        sc.acc_rej = True if acc_rej == "accept" else False

        if acc_rej == "accept" and schedule_date_raw:
            try:
                sc.date = datetime.strptime(schedule_date_raw, "%Y-%m-%d").date()
            except ValueError:
                sc.date = None
        else:
            sc.date = None

        sc.save()
        messages.success(request, "Schedule Confirmation berhasil diperbarui.")

    return redirect("list_exported_purchase_orders")


@login_required
@require_POST
def delete_exported_file(request):
    filename = request.POST.get('filename')

    if not filename:
        return JsonResponse({'success': False, 'error': 'Filename not provided'})

    file_path = os.path.join(settings.MEDIA_ROOT, 'purchase_orders', filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)

            # Ambil registered_no dari nama file
            registered_no = filename.replace("Purchase_Order_", "").replace(".pdf", "")
            
            try:
                # Update field email_sent dan email_sent_at ke default
                pr = PurchaseRequest.objects.get(registered_no=registered_no)
                po = PurchaseOrder.objects.get(registered_no=pr)
                po.email_sent = False
                po.email_sent_at = None
                po.save()
            except PurchaseRequest.DoesNotExist:
                pass
            except PurchaseOrder.DoesNotExist:
                pass

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'File not found'})

# send email

@login_required
@require_POST
def send_exported_file_email(request):
    filename = request.POST.get('filename')

    if not filename:
        return JsonResponse({'success': False, 'error': 'Filename tidak disediakan.'})

    file_path = os.path.join(settings.MEDIA_ROOT, 'purchase_orders', filename)

    if not os.path.exists(file_path):
        return JsonResponse({'success': False, 'error': 'File tidak ditemukan.'})

    try:
        # Ekstrak nomor dari nama file (format: purchase_order_<registered_no>.pdf)
        registered_no = filename.replace("Purchase_Order_", "").replace(".pdf", "")
        pr = PurchaseRequest.objects.get(registered_no=registered_no)
        po = PurchaseOrder.objects.get(registered_no=pr)

        # Cek apakah email sudah dikirim sebelumnya
        if po.email_sent:
            return JsonResponse({'success': False, 'error': 'Email sudah pernah dikirim.'})

        recipient_email = po.supplier.email
        if not recipient_email:
            return JsonResponse({'success': False, 'error': 'Email supplier belum tersedia.'})
    except (PurchaseRequest.DoesNotExist, PurchaseOrder.DoesNotExist, AttributeError):
        return JsonResponse({'success': False, 'error': 'Data Purchase Order atau email supplier tidak ditemukan.'})

    try:
        filename_no_ext = os.path.splitext(filename)[0]
        subject = f'{filename_no_ext}'
        body = (
            "Dear Sir or Madam\n\n"
            f"We are pleased to attach the Purchase Order document: {filename}.\n"
            "Please proceed according to the applicable procedures. "
            "If you have any questions or need further clarification, feel free to reach out to us via this email or through the provided contact information.\n"
            "We truly appreciate your attention and cooperation.\n\n"
            "Best regards,\n"
            "[PT. XYZ Indonesia]"
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        email.attach_file(file_path)
        email.send()

        # Tandai email sudah dikirim
        po.email_sent = True
        po.email_sent_at = timezone.now()
        po.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

from django.http import JsonResponse

def supplier_list(request):
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        supplier_id = request.POST.get('id')
        form = SupplierForm(request.POST, instance=Supplier.objects.get(pk=supplier_id) if supplier_id else None)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')

    return render(request, 'order/supplier/supplier.html', {'suppliers': suppliers})


def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'order/supplier/supplier_form.html', {'form': form, 'title': 'Add Supplier'})

def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'order/supplier/supplier_form.html', {'form': form, 'title': 'Edit Supplier'})

def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        return redirect('supplier_list')
    return render(request, 'order/supplier/supplier_confirm_delete.html', {'supplier': supplier})

# shippedfrom django.shortcuts import render, redirect, get_object_or_404


def shipped_list(request):
    shippeds = Shipped.objects.all()
    return render(request, 'order/shipped/shipped.html', {'shippeds': shippeds})

def shipped_create(request):
    if request.method == 'POST':
        form = ShippedForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shipped_list')
    else:
        form = ShippedForm()
    return render(request, 'order/shipped/shipped_form.html', {'form': form})

def shipped_update(request, pk):
    shipped = get_object_or_404(Shipped, pk=pk)
    if request.method == 'POST':
        form = ShippedForm(request.POST, instance=shipped)
        if form.is_valid():
            form.save()
            return redirect('shipped_list')
    else:
        form = ShippedForm(instance=shipped)
    return render(request, 'order/shipped/shipped_form.html', {'form': form})

def shipped_delete(request, pk):
    shipped = get_object_or_404(Shipped, pk=pk)
    if request.method == 'POST':
        shipped.delete()
        return redirect('shipped_list')
    return render(request, 'order/shipped/shipped_confirm_delete.html', {'shipped': shipped})
