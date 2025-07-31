# myapp/views_stock.py 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Exists, OuterRef
from .models import PurchaseRequest, Stock, RequestItem, Invoice

@login_required
def stockList(request):
    # Subquery: cek apakah ada Invoice terkait untuk PurchaseRequest tertentu
    has_invoice = Invoice.objects.filter(registered_no=OuterRef('pk'))

    connected_requests = (
        PurchaseRequest.objects
        .filter(
            airwaybill__isnull=False,  # Sudah ada airwaybill
        )
        .annotate(has_invoice=Exists(has_invoice))  # Tambahkan flag
        .filter(has_invoice=True)  # Filter yang punya invoice saja
        .select_related('departement', 'section')
        .prefetch_related('items')
    )

    for pr in connected_requests:
        item_ids = pr.items.values_list('id', flat=True)
        stocks = Stock.objects.filter(source_request_item__in=item_ids)
        stock_map = {s.source_request_item_id: s for s in stocks}

        total_items = pr.items.count()
        complete = True
        exact_match = True
        for item in pr.items.all():
            expected = int(float(item.result_average_round))
            stock = stock_map.get(item.id)

            if not stock:
                complete = False
                exact_match = False
                break

            total_input = stock.quantity_real + stock.quantity_defect + stock.quantity_missing
            if total_input != expected:
                complete = False
                exact_match = False
                break
            elif stock.quantity_missing > 0:
                exact_match = False

        if not complete:
            pr.stock_status = 'pending'
        elif exact_match:
            pr.stock_status = 'done_exact'
        else:
            pr.stock_status = 'done_less'


    return render(
        request,
        'stock/stock.html',
        {'connected_requests': connected_requests}
    )


@login_required
def requestItemDetail(request, pk):
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk)

    items = purchase_request.items.select_related(
        'loading_part_result',
        'loading_part_result__partdesk',
        'loading_part_result__partdesk__partName'
    )

    if request.method == "POST":
        errors = []

        for item in items:
            id = item.id
            original_qty = int(float(item.result_average_round))

            qty_real = int(request.POST.get(f"input_qty_real_{id}", 0))
            qty_defect = int(request.POST.get(f"input_qty_defect_{id}", 0))
            qty_missing = int(request.POST.get(f"input_qty_missing_{id}", 0))

            total_input = qty_real + qty_defect + qty_missing

            if total_input != original_qty:
                errors.append(f"Total input untuk item {item.budget_ref_no} harus sama dengan {original_qty}.")
                continue

            partdesk = getattr(item.loading_part_result, "partdesk", None)
            part = getattr(partdesk, "partName", None)
            if not part:
                continue

            stock_obj, _ = Stock.objects.get_or_create(part=part, source_request_item=item)
            stock_obj.quantity_real = qty_real
            stock_obj.quantity_defect = qty_defect
            stock_obj.quantity_missing = qty_missing
            stock_obj.save()

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            messages.success(request, "Stock Updated")

        return redirect('request_item_detail', pk=pk)  # ← POST redirect handled

    stocks = Stock.objects.filter(source_request_item__in=[i.id for i in items])
    saved_map = {s.source_request_item_id: s for s in stocks}

    for item in items:
        stock = saved_map.get(item.id)
        original_qty = int(float(item.result_average_round))

        if stock:
            item.saved_qty_real = stock.quantity_real
            item.saved_qty_defect = stock.quantity_defect
            item.saved_qty_missing = stock.quantity_missing
        else:
            item.saved_qty_real = 0
            item.saved_qty_defect = 0
            item.saved_qty_missing = 0

        total = item.saved_qty_real + item.saved_qty_defect + item.saved_qty_missing
        item.qty_color = "text-success fw-bold" if total == original_qty else "text-danger fw-bold"

    all_qty_complete = all(
        i.saved_qty_real == int(float(i.result_average_round)) and
        i.saved_qty_defect == 0 and
        i.saved_qty_missing == 0
        for i in items
    )




    return render(
        request,
        'stock/request_item_detail_page.html',
        {
            'purchase_request': purchase_request,
            'request_items': items,
            'all_qty_complete': all_qty_complete,
        }
    )
