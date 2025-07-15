# myapp/views_stock.py 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import PurchaseRequest, Stock, RequestItem

from django.db.models import Exists, OuterRef
from .models import PurchaseRequest, Stock, RequestItem, Invoice  # pastikan Invoice diimpor

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
        stock_map = {s.source_request_item_id: s.quantity for s in stocks}

        total_items = pr.items.count()
        complete = True
        exact_match = True
        for item in pr.items.all():
            expected = int(float(item.result_average_round))
            actual = stock_map.get(item.id)

            if actual is None:
                complete = False
                exact_match = False
                break
            elif actual < expected:
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
            field_key = f"input_qty_{item.id}"
            raw_val = request.POST.get(field_key, "").strip()

            if raw_val in ("", "0"):
                qty_input = 0
            else:
                try:
                    qty_input = int(raw_val)
                except ValueError:
                    qty_input = 0

            original_qty = int(float(item.result_average_round))
            if qty_input > original_qty:
                errors.append(
                    f"Qty untuk item {item.budget_ref_no} tidak boleh "
                    f"melebihi {original_qty}."
                )
                continue

            partdesk = getattr(item.loading_part_result, "partdesk", None)
            part = getattr(partdesk, "partName", None)
            if not part:
                continue

            stock_obj = Stock.objects.filter(
                part=part,
                source_request_item=item.id
            ).first()

            if qty_input > 0:
                if stock_obj:
                    stock_obj.quantity = qty_input
                    stock_obj.save()
                else:
                    Stock.objects.create(
                        part=part,
                        quantity=qty_input,
                        source_request_item_id=item.id
                    )
            else:
                if stock_obj:
                    stock_obj.delete()

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            messages.success(request, "Stock Updated")

        return redirect('request_item_detail', pk=pk)  # ← POST redirect handled

    # ====== GET request handler starts here =======
    stocks = Stock.objects.filter(
        source_request_item__in=[i.id for i in items]
    )
    saved_qty = {s.source_request_item_id: s.quantity for s in stocks}

    for item in items:
        item.saved_qty = saved_qty.get(item.id)
        original_qty = int(float(item.result_average_round))

        if item.saved_qty is None:
            item.input_value = original_qty
            item.qty_color   = ""
        else:
            item.input_value = item.saved_qty
            if item.saved_qty == original_qty:
                item.qty_color = "text-success fw-bold"
            elif item.saved_qty < original_qty:
                item.qty_color = "text-danger fw-bold"
            else:
                item.qty_color = ""

    all_qty_complete = all(
        saved_qty.get(item.id) == int(float(item.result_average_round))
        for item in items
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
