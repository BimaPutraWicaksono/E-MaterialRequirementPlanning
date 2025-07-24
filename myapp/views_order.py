from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string

from .form import PurchaseRequestForm, PurchaseRequestEditForm, PurchaseOrderForm
from .models import PurchaseRequest, RequestItem, LoadingPartResult, Carline, Section, PurchaseOrder
from myapp.models import Departement

@login_required()
def master_departement_section(request):
    departements = Departement.objects.all()
    sections = Section.objects.select_related('departement').all()
    return render(request, 'departement/departement.html', {
        'departements': departements,
        'sections': sections,
    })

@login_required()
def create_departement(request): 
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Departement.objects.create(name=name)
            messages.success(request, 'Departement berhasil ditambahkan.')
        else:
            messages.error(request, 'Nama Departement tidak boleh kosong.')
    return redirect('master_departement_section')

@login_required()
def update_departement(request, id):
    departement = get_object_or_404(Departement, id=id)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            departement.name = name
            departement.save()
            messages.success(request, 'Departement berhasil diperbarui.')
        else:
            messages.error(request, 'Nama tidak boleh kosong.')
        return redirect('master_departement_section')
    return render(request, 'departement/edit_departement.html', {'departement': departement})


@login_required()
def delete_departement(request, id):
    departement = get_object_or_404(Departement, id=id)
    departement.delete()
    messages.success(request, 'Departement berhasil dihapus.')
    return redirect('master_departement_section')

@login_required()
def create_section(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        departement_id = request.POST.get('departement')
        if name and departement_id:
            departement = Departement.objects.get(id=departement_id)
            Section.objects.create(name=name, departement=departement)
            messages.success(request, 'Section berhasil ditambahkan.')
        else:
            messages.error(request, 'Semua field Section harus diisi.')
    return redirect('master_departement_section')


@login_required()
def update_section(request, id):
    section = get_object_or_404(Section, id=id)
    departements = Departement.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        departement_id = request.POST.get('departement')
        if name and departement_id:
            section.name = name
            section.departement_id = departement_id
            section.save()
            messages.success(request, 'Section berhasil diperbarui.')
        else:
            messages.error(request, 'Semua field harus diisi.')
        return redirect('master_departement_section')
    return render(request, 'departement/edit_section.html', {'section': section, 'departements': departements})

@login_required()
def delete_section(request, id):
    section = get_object_or_404(Section, id=id)
    section.delete()
    messages.success(request, 'Section berhasil dihapus.')
    return redirect('master_departement_section')

@login_required
def purchaseReq(request):
    user_departement = request.user.departement
    show_duplicate_modal = False  # default
    status_filter = request.GET.get('status')
    
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        registered_no = request.POST.get('registered_no')
        
        # Cek apakah registered_no sudah ada di database
        if PurchaseRequest.objects.filter(registered_no=registered_no).exists():
            show_duplicate_modal = True  # Trigger modal
        elif form.is_valid():
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
            pr.departement = user_departement
            pr.total_amount = total_amount
            pr.created_by = request.user
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
            return redirect('purchaseReq')
    else:
        form = PurchaseRequestForm()
        form.fields['section'].queryset = Section.objects.filter(departement=user_departement)

    if request.user.groups.filter(name='Admin').exists():
        requests = PurchaseRequest.objects.all()
    else:
        requests = PurchaseRequest.objects.filter(departement=user_departement)

    # 🟨 Tambahkan filter berdasarkan status
    if status_filter == "approved":
        requests = requests.filter(approve_spv=True)
    elif status_filter == "rejected":
        requests = requests.filter(approve_spv=False)
    elif status_filter == "pending":
        requests = requests.filter(requested=True, approve_spv__isnull=True)

    requests = requests.order_by('-date')

    return render(request, 'order/purchaseReq.html', {
        'form': form,
        'requests': requests,
        'user_departement': user_departement,
        'show_duplicate_modal': show_duplicate_modal,
        'status_filter': status_filter,
    })

 
@login_required
def ajax_get_loading_parts(request):
    if request.method == 'POST':
        carline_ids = request.POST.getlist('carline_ids[]')
        parts = LoadingPartResult.objects.filter(carline__id__in=carline_ids).order_by('partdesk')

        unique_parts = {}
        for part in parts:
            if part.partdesk_id not in unique_parts:
                unique_parts[part.partdesk_id] = part
        
        parts_list = unique_parts.values()
        
        # Tambahkan tanggal default
        deadline_default = (date.today() + timedelta(days=30)).isoformat()

        table_html = render_to_string('order/partials/loading_parts_table.html', {
            'parts': parts_list,
            'deadline_default': deadline_default,
        })
        return JsonResponse({'table': table_html})


@login_required
def ajax_load_sections(request):
    departement_id = request.GET.get('departement_id')
    sections = Section.objects.filter(departement_id=departement_id).order_by('name')
    html = render_to_string('order/partials/section_dropdown_list_options.html', {'sections': sections})
    return JsonResponse(html, safe=False)


@login_required
def purchase_request_detail(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)
    items = RequestItem.objects.filter(purchase_request=pr)

    context = {
        'purchase_request': pr,
        'request_items': items,
    }

    # Render template ke string
    html = render_to_string('order/partials/purchase_request_detail.html', context, request=request)
    return JsonResponse({'html': html})


@login_required
def approve_purchase_request(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Supervisor
        if request.user.groups.filter(name='Supervisor').exists():
            if action == 'approve_spv':
                pr.approve_spv = True
                pr.reason_spv = ''
            elif action == 'disapprove_spv':
                reason = request.POST.get('reason_spv', '').strip()
                if not reason:
                    messages.error(request, "Alasan penolakan harus diisi oleh Supervisor.")
                    return redirect(request.META.get('HTTP_REFERER'))
                pr.approve_spv = False
                pr.reason_spv = reason
            pr.save()
            messages.success(request, "Supervisor approval updated.")
        return redirect('purchaseReq')

def delete_purchase_request(request, registered_no):
    if request.method == "POST":
        pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)
        pr.delete()
        messages.success(request, f"Purchase Request {registered_no} berhasil dihapus.")
    return redirect('purchaseReq')  # ganti sesuai nama path untuk halaman PR utama

@login_required
def purchase_request_edit(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no, created_by=request.user)

    if not request.user.groups.filter(name='Karyawan').exists():
        return HttpResponseForbidden("Tidak memiliki izin untuk mengedit")

    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST, instance=pr)
        if form.is_valid():
            selected_carlines = form.cleaned_data['part_order']
            budget_ref_no_list = request.POST.getlist('budget_ref_no')
            estimated_prices_list = request.POST.getlist('estimated_price')
            deadlines_list = request.POST.getlist('deadline')

            # Simpan form PR (tanpa menyimpan total_amount dulu)
            pr = form.save(commit=False)
            pr.save()
            pr.part_order.set(selected_carlines)

            # Hapus item lama
            pr.items.all().delete()

            # Persiapan data item baru
            all_parts = []
            seen_partdesk_ids = set()

            for carline in selected_carlines:
                parts = LoadingPartResult.objects.filter(carline=carline).order_by('partdesk')
                for part in parts:
                    if part.partdesk_id and part.partdesk_id not in seen_partdesk_ids:
                        seen_partdesk_ids.add(part.partdesk_id)
                        all_parts.append(part)

            total_amount = 0  # Inisialisasi total amount

            # Simpan item baru
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
                total_amount += amount  # Akumulasi total

                RequestItem.objects.create(
                    purchase_request=pr,
                    loading_part_result=part,
                    budget_ref_no=budget,
                    result_average_round=avg,
                    estimated_price=est_price,
                    amount=amount,
                    deadline=dl
                )

            # Update total_amount di PR
            pr.total_amount = total_amount
            pr.save()

            messages.success(request, "Purchase Request berhasil diperbarui.")
            return redirect('purchaseReq')
    else:
        form = PurchaseRequestForm(instance=pr)
        form.fields['section'].queryset = Section.objects.filter(departement=pr.departement)

    items = pr.items.all()
    selected_carline_ids = pr.part_order.values_list('id', flat=True)
    deadline_default = (date.today() + timedelta(days=30)).isoformat()

    table_html = render_to_string('order/partials/loading_parts_table.html', {
        'parts': [item.loading_part_result for item in items],
        'deadline_default': deadline_default,
        'items': items,
    })

    html = render_to_string('order/partials/purchase_request_edit_modal.html', {
        'form': form,
        'pr': pr,
        'user_departement': pr.departement,
        'table_html': table_html,
    }, request=request)

    return JsonResponse({'html': html})


@login_required
def ajax_get_loading_parts_edit(request):
    if request.method == 'POST':
        carline_ids = request.POST.getlist('carline_ids')
        purchase_request_id = request.POST.get('purchase_request_id')
        parts = LoadingPartResult.objects.filter(carline__id__in=carline_ids).order_by('partdesk')

        unique_parts = {}
        for part in parts:
            if part.partdesk_id not in unique_parts:
                unique_parts[part.partdesk_id] = part
        
        parts_list = unique_parts.values()

        existing_details = {}
        if purchase_request_id:
            details_qs = RequestItem.objects.filter(purchase_request_id=purchase_request_id)
            for d in details_qs:
                existing_details[d.loading_part_result.partdesk_id] = d

        table_html = render_to_string('order/partials/loading_parts_table_edit.html', {
            'parts': parts_list,
            'existing_details': existing_details
        })
        return JsonResponse({'table': table_html})


@login_required
def create_purchase_order(request, registered_no):
    purchase_request = get_object_or_404(PurchaseRequest, registered_no=registered_no)

    if not purchase_request.approve_spv:
        messages.error(request, "Purchase Request belum disetujui oleh SPV.")
        return redirect('purchaseReq')

    if PurchaseOrder.objects.filter(registered_no=purchase_request).exists():
        messages.warning(request, "Purchase Order sudah dibuat untuk registered_no ini.")
        return redirect('purchaseReq')

    request_items = RequestItem.objects.filter(purchase_request=purchase_request)
    earliest_deadline = request_items.exclude(deadline=None).order_by('deadline').first()
    initial_delivery = earliest_deadline.deadline if earliest_deadline else None

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.registered_no = purchase_request
            po.created_by = request.user
            if not po.delivery:
                po.delivery = initial_delivery
            po.save()
            # messages.success(request, f"Purchase Order untuk {registered_no} berhasil dibuat.")
            return redirect('purchaseReq')
        else:
            messages.error(request, "Terdapat kesalahan pada form.")
    else:
        form = PurchaseOrderForm(initial={'delivery': initial_delivery})

    return render(request, 'order/create_po_form.html', {
        'form': form,
        'purchase_request': purchase_request,
    })

@login_required
def ajax_load_po_form(request, registered_no):
    purchase_request = get_object_or_404(PurchaseRequest, registered_no=registered_no)

    if not purchase_request.approve_spv:
        return JsonResponse({'error': 'Purchase Request belum disetujui oleh SPV.'}, status=400)

    created_po = PurchaseOrder.objects.filter(registered_no=purchase_request).first()
    request_items = RequestItem.objects.filter(purchase_request=purchase_request)

    earliest_deadline = request_items.exclude(deadline=None).order_by('deadline').first()
    initial_delivery = earliest_deadline.deadline if earliest_deadline else None

    if created_po:
        po_form = None
    else:
        po_form = PurchaseOrderForm(initial={'delivery': initial_delivery})

    html = render_to_string('order/partials/purchase_order_detail.html', {
        'purchase_request': purchase_request,
        'request_items': request_items,
        'created_po': created_po,
        'po_form': po_form,
        'request': request,
    })
    return JsonResponse({'html': html})
