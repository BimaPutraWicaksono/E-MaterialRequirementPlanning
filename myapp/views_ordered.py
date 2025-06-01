from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import PurchaseRequest, RequestItem, LoadingPartResult, Section
from .form import PurchaseRequestForm

@login_required
def purchaseReq(request):
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
    return render(request, 'order/purchaseOrd.html', {
        'form': form,
        'requests': requests,
    })

@login_required
def purchase_order_detail(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)
    items = RequestItem.objects.filter(purchase_request=pr)

    context = {
        'purchase_request': pr,
        'request_items': items,
    }

    # Render template ke string
    html = render_to_string('partials/purchase_order_detail.html', context, request=request)
    return JsonResponse({'html': html})