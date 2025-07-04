from django.shortcuts import render
from .models import PurchaseRequest, AirWayBill
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404


from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def stockList(request):
    connected_requests = PurchaseRequest.objects.filter(airwaybill__isnull=False).select_related('departement', 'section')
    context = {
        'connected_requests': connected_requests
    }
    return render(request, 'stock/stock.html', context)


from .models import Stock, PartName

@login_required
def requestItemDetail(request, pk):
    purchase_request = PurchaseRequest.objects.get(pk=pk)
    items = purchase_request.items.select_related(
        'loading_part_result',
        'loading_part_result__partdesk',
        'loading_part_result__partdesk__partName'
    ).all()

    if request.method == 'POST':
        selected = request.POST.getlist('selected_items')
        
        for item_id in selected:
            part_id = request.POST.get(f'part_id_{item_id}')
            qty = request.POST.get(f'qty_{item_id}')

            if part_id and qty:
                part = PartName.objects.filter(id=part_id).first()
                if part:
                    # Cek apakah sudah ada Stock berdasarkan part + source_request_item
                    stock_obj = Stock.objects.filter(part=part, source_request_item=item_id).first()

                    if stock_obj:
                        stock_obj.quantity += int(float(qty))
                        stock_obj.save()
                    else:
                        Stock.objects.create(
                            part=part,
                            quantity=int(float(qty)),
                            source_request_item_id=item_id
                        )

        messages.success(request, "Stock berhasil disimpan.")
        return redirect('request_item_detail', pk=purchase_request.id)

    # Ambil semua item.id yang sudah pernah masuk Stock
    existing_item_ids = set(Stock.objects.filter(source_request_item__isnull=False).values_list('source_request_item', flat=True))

    context = {
        'purchase_request': purchase_request,
        'request_items': items,
        'existing_item_ids': existing_item_ids,
    }
    return render(request, 'stock/request_item_detail_page.html', context)
