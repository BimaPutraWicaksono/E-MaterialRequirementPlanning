# myapp/views_stock.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import PurchaseRequest, Stock, RequestItem

@login_required
def stockList(request):
    connected_requests = (
        PurchaseRequest.objects
        .filter(airwaybill__isnull=False)
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
    """
    Fitur:
    • Kolom input qty fleksibel (min 0, max qty asli).
    • Input '0' atau kosong ⇒ dianggap belum di‑input (stok dihapus jika ada).
    • Setelah Save, angka terakhir yang disimpan menjadi default.
    • Warna ANGKA: hijau (qty sama), merah (qty lebih kecil).
    • Tombol "Save" berubah jadi "Complete" jika semua qty sudah sesuai.
    """
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk)

    # Semua item di PR
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

            # Kosong / 0 ⇒ dianggap tidak diinput
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

            # Ambil Part terkait
            partdesk = getattr(item.loading_part_result, "partdesk", None)
            part = getattr(partdesk, "partName", None)
            if not part:
                continue  # Skip jika belum ada part definitif

            stock_obj = Stock.objects.filter(
                part=part,
                source_request_item=item.id
            ).first()

            if qty_input > 0:
                # Buat / update stok
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
                # qty 0 ⇒ hapus stok jika ada
                if stock_obj:
                    stock_obj.delete()

        if errors:
            messages.error(request, " ".join(errors))
        else:
            messages.success(request, "Stock Updated")

        return redirect(request.path)

    # Ambil semua stok yang tersimpan untuk PR ini
    stocks = Stock.objects.filter(
        source_request_item__in=[i.id for i in items]
    )
    saved_qty = {s.source_request_item_id: s.quantity for s in stocks}

    # Siapkan atribut bantu untuk template
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

    # Cek apakah semua qty sudah sesuai (untuk tombol "Complete")
    all_qty_complete = all(
        item.saved_qty == int(float(item.result_average_round))
        for item in items
        if item.saved_qty is not None
    )

    return render(
        request,
        'stock/request_item_detail_page.html',
        {
            'purchase_request': purchase_request,
            'request_items':    items,
            'all_qty_complete': all_qty_complete,  
        }
    )
