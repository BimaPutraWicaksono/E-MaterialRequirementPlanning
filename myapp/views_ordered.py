from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import PurchaseRequest, RequestItem, LoadingPartResult, Section
from .form import PurchaseRequestForm
@login_required
def purchaseOrd(request):
    user_departement = request.user.departement  # Ambil departemen dari user yang login

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

    # ❗ Filter berdasarkan departemen user login
    requests = PurchaseRequest.objects.filter(departement=user_departement).order_by('-date')

    # PO registered_no yang sudah dibuat
    po_registered_nos = set(PurchaseOrder.objects.values_list('registered_no__registered_no', flat=True))

    return render(request, 'order/purchaseOrd.html', {
        'form': form,
        'requests': requests,
        'po_registered_nos': po_registered_nos,
    })


from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from .models import PurchaseRequest, RequestItem, PurchaseOrder
from .form import PurchaseOrderForm
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from .models import PurchaseRequest, RequestItem, PurchaseOrder
from .form import PurchaseOrderForm
from django.contrib.auth.decorators import login_required

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
        form.fields['delivery'].disabled = True
        
    html = render(request, 'order/partials/purchase_order_detail.html', {
        'purchase_request': purchase_request,
        'request_items': request_items,
        'po_form': form,
        'created_po': po,
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
    
import os
from django.conf import settings
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import PurchaseRequest

from django.shortcuts import redirect

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
    filename = f"purchase_order_{registered_no}.pdf"
    filepath = os.path.join(directory, filename)

    with open(filepath, "wb") as f:
        pisa_status = pisa.CreatePDF(html, dest=f)

    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)

    # Redirect ke halaman list setelah sukses
    return redirect('list_exported_files')

import os
from django.conf import settings
from django.shortcuts import render
from .models import PurchaseRequest, PurchaseOrder

def list_exported_purchase_orders(request):
    folder_path = os.path.join(settings.MEDIA_ROOT, 'purchase_orders')
    file_list = []

    if os.path.exists(folder_path):
        file_list = [
            f for f in os.listdir(folder_path)
            if f.endswith('.pdf')
        ]

    file_urls = []
    for f in file_list:
        try:
            registered_no = f.replace("purchase_order_", "").replace(".pdf", "")
            pr = PurchaseRequest.objects.get(registered_no=registered_no)
            po = PurchaseOrder.objects.get(registered_no=pr)
            supplier_name = po.supplier.name
        except:
            supplier_name = 'Unknown'

        file_urls.append({
            'name': f,
            'url': os.path.join(settings.MEDIA_URL, 'purchase_orders', f),
            'supplier_name': supplier_name,
            'email_sent': getattr(po, 'email_sent', False),
            'email_sent_at': po.email_sent_at if po else None
        })


    return render(request, 'order/list_exported_files.html', {'files': file_urls})


import os
from django.conf import settings
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test

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
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'File not found'})

# send email
import os
from django.conf import settings
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import PurchaseRequest, PurchaseOrder  # pastikan import model
from django.utils import timezone


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
        registered_no = filename.replace("purchase_order_", "").replace(".pdf", "")
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
        subject = f'Purchase Order ({filename_no_ext})'
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



from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Supplier
from .form import SupplierForm

def supplier_list(request):
    suppliers = Supplier.objects.all()
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
from .models import Shipped
from .form import ShippedForm

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
