from django.contrib.auth.decorators import login_required
from myapp.models import (
    PurchaseRequest, PurchaseOrder, ScheduleConf,
    AirWayBill, Invoice, RequestItem, Stock
)
from django.db.models import Sum
from django.shortcuts import render
from django.utils.timezone import datetime
from collections import OrderedDict
from django.db.models import Q

MONTH_NAMES = OrderedDict([
    ("01", "January"), ("02", "February"), ("03", "March"),
    ("04", "April"), ("05", "May"), ("06", "June"),
    ("07", "July"), ("08", "August"), ("09", "September"),
    ("10", "October"), ("11", "November"), ("12", "December"),
])

@login_required
def home(request):
    selected_month = request.GET.get('month')
    now = datetime.now()

    # Convert to int if selected
    month_int = int(selected_month) if selected_month else None

    # Data approval (berdasarkan tanggal PR)
    pr_qs = PurchaseRequest.objects.all()
    if month_int:
        pr_qs = pr_qs.filter(date__month=month_int)

    count_not_processed = pr_qs.filter(approve_spv__isnull=True).count()
    count_spv = pr_qs.filter(approve_spv=True, approve_sspv__isnull=True).count()
    count_sspv = pr_qs.filter(approve_sspv=True, approve_manager__isnull=True).count()
    count_manager = pr_qs.filter(approve_manager=True, approve_factory_manager__isnull=True).count()
    count_factory_mgr = pr_qs.filter(approve_factory_manager=True).count()

    # Semua registered_no dari PR (untuk awal tahap dokumen)
    all_ids = set(pr_qs.values_list('id', flat=True))

    # Stock: created_at
    stock_ids = set()
    if month_int:
        stock_ids = set(
            Stock.objects.filter(created_at__month=month_int)
            .values_list('source_request_item__purchase_request_id', flat=True)
        )
    else:
        stock_ids = set(
            Stock.objects.all()
            .values_list('source_request_item__purchase_request_id', flat=True)
        )

    # Invoice: date
    invoice_ids = set()
    if month_int:
        invoice_ids = set(
            Invoice.objects.filter(date__month=month_int)
            .exclude(registered_no_id__in=stock_ids)
            .values_list('registered_no_id', flat=True)
        )
    else:
        invoice_ids = set(
            Invoice.objects.exclude(registered_no_id__in=stock_ids)
            .values_list('registered_no_id', flat=True)
        )

    # AWB: date
    awb_ids = set()
    if month_int:
        awb_ids = set(
            AirWayBill.objects.filter(date__month=month_int)
            .exclude(registered_no_id__in=stock_ids | invoice_ids)
            .values_list('registered_no_id', flat=True)
        )
    else:
        awb_ids = set(
            AirWayBill.objects.exclude(registered_no_id__in=stock_ids | invoice_ids)
            .values_list('registered_no_id', flat=True)
        )

    # ScheduleConf: date
    sc_ids = set()
    if month_int:
        sc_ids = set(
            ScheduleConf.objects.filter(date__month=month_int, acc_rej=True)
            .exclude(registered_no_id__in=stock_ids | invoice_ids | awb_ids)
            .values_list('registered_no_id', flat=True)
        )
    else:
        sc_ids = set(
            ScheduleConf.objects.filter(acc_rej=True)
            .exclude(registered_no_id__in=stock_ids | invoice_ids | awb_ids)
            .values_list('registered_no_id', flat=True)
        )

    # PurchaseOrder: pisahkan filter sesuai email_sent
    po_sent_ids = set()
    po_not_sent_ids = set()

    if month_int:
        po_sent_ids = set(
            PurchaseOrder.objects.filter(email_sent=True, email_sent_at__month=month_int)
            .exclude(registered_no_id__in=stock_ids | invoice_ids | awb_ids | sc_ids)
            .values_list('registered_no_id', flat=True)
        )
        po_not_sent_ids = set(
            PurchaseOrder.objects.filter(email_sent=False, date__month=month_int)
            .exclude(registered_no_id__in=stock_ids | invoice_ids | awb_ids | sc_ids | po_sent_ids)
            .values_list('registered_no_id', flat=True)
        )
    else:
        po_sent_ids = set(
            PurchaseOrder.objects.filter(email_sent=True)
            .exclude(registered_no_id__in=stock_ids | invoice_ids | awb_ids | sc_ids)
            .values_list('registered_no_id', flat=True)
        )
        po_not_sent_ids = set(
            PurchaseOrder.objects.filter(email_sent=False)
            .exclude(registered_no_id__in=stock_ids | invoice_ids | awb_ids | sc_ids | po_sent_ids)
            .values_list('registered_no_id', flat=True)
        )

    # PR yang belum masuk tahapan apa pun
    used_ids = stock_ids | invoice_ids | awb_ids | sc_ids | po_sent_ids | po_not_sent_ids
    new_pr_ids = all_ids - used_ids

    stage_labels = [
        "Purchase Order",
        "Purchase Order Sent",
        "Delivery Confirmed",
        "Airway Bill",
        "Invoice",
        "Delivery Completed",
    ]
    stage_counts = [
        len(po_not_sent_ids),
        len(po_sent_ids),
        len(sc_ids),
        len(awb_ids),
        len(invoice_ids),
        len(stock_ids),
    ]

    stock_summary = (
        Stock.objects.values('part__partName')
        .annotate(total_qty=Sum('quantity'))
        .order_by('part__partName')
    )

    context = {
        'chart_data': {
            'labels': ['Pending', 'SPV', 'SSPV', 'Manager', 'Factory Manager'],
            'counts': [count_not_processed, count_spv, count_sspv, count_manager, count_factory_mgr],
        },
        'stage_data': {
            'labels': stage_labels,
            'counts': stage_counts,
        },
        'stock_summary': stock_summary,
        'month_names': MONTH_NAMES,
        'selected_month': selected_month,
    }
    return render(request, 'home.html', context)

