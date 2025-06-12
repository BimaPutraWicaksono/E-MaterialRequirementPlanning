from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import PurchaseRequest, RequestItem, LoadingPartResult, Section
from .form import PurchaseRequestForm

@login_required
def purchaseOrd(request):
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
            pr.total_amount = total_amount
            pr.save()
            pr.part_order.set(selected_carlines)

            pr.items.all().delete()

            # Kumpulkan semua part unik dari seluruh carline
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
    
    requests = PurchaseRequest.objects.all().order_by('-date')
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

@login_required
def purchase_order_detail(request, registered_no):
    purchase_request = get_object_or_404(PurchaseRequest, registered_no=registered_no)
    request_items = RequestItem.objects.filter(purchase_request=purchase_request)  # Perbaikan di sini
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

    form = PurchaseOrderForm()
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

from django.shortcuts import get_object_or_404, redirect
from .models import PurchaseRequest


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
