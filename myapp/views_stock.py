from django.shortcuts import render
from .models import PurchaseRequest, AirWayBill
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def stockList(request):
    connected_requests = PurchaseRequest.objects.filter(airwaybill__isnull=False).select_related('departement', 'section')
    context = {
        'connected_requests': connected_requests
    }
    return render(request, 'stock/stock.html', context)


@login_required
def requestItemDetail(request, pk):
    purchase_request = PurchaseRequest.objects.get(pk=pk)
    items = purchase_request.items.select_related('loading_part_result').all()

    context = {
        'purchase_request': purchase_request,
        'request_items': items,
    }
    return render(request, 'stock/request_item_detail_page.html', context)

