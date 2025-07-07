from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from myapp.models import (
    PurchaseRequest, Stock, PurchaseOrder,
    ScheduleConf, AirWayBill, Invoice
)

@login_required()
def home(request):
    # --- 1) Approval chart (kode Anda sebelumnya) -----------------------------
    requests = PurchaseRequest.objects.all()
    count_not_processed = requests.filter(approve_spv__isnull=True).count()
    count_spv           = requests.filter(approve_spv=True,  approve_sspv__isnull=True).count()
    count_sspv          = requests.filter(approve_sspv=True, approve_manager__isnull=True).count()
    count_manager       = requests.filter(approve_manager=True, approve_factory_manager__isnull=True).count()
    count_factory_mgr   = requests.filter(approve_factory_manager=True).count()

    # --- 2) Stock summary (kode Anda sebelumnya) ------------------------------
    stock_summary = (
        Stock.objects.values('part__partName')
        .annotate(total_qty=Sum('quantity'))
        .order_by('part__partName')
    )

    # --- 3) NEW – tahapan PR sampai dokumen terakhir -------------------------
    # id PurchaseRequest di tiap tabel
    invoice_ids = set(Invoice.objects.values_list('registered_no_id', flat=True))
    awb_ids     = set(AirWayBill.objects.values_list('registered_no_id', flat=True))
    sc_ids      = set(ScheduleConf.objects.values_list('registered_no_id', flat=True))
    po_ids      = set(PurchaseOrder.objects.values_list('registered_no_id', flat=True))

    # Hitung PR yg “mentok” di setiap level
    count_invoice = len(invoice_ids)                                         # sudah Invoice
    count_awb     = len(awb_ids     - invoice_ids)                           # AWB saja
    count_sc      = len(sc_ids      - awb_ids - invoice_ids)                 # SC saja
    count_po      = len(po_ids      - sc_ids - awb_ids - invoice_ids)        # PO saja

    # --- 4) Kirim data ke template -------------------------------------------
    context = {
        # Grafik approval (lama)
        'chart_data': {
            'labels': ['Belum Diproses', 'SPV', 'SSPV', 'Manager', 'Factory Manager'],
            'counts': [count_not_processed, count_spv, count_sspv, count_manager, count_factory_mgr],
        },
        # Grafik tahap dokumen (baru)
        'stage_data': {
            'labels': ['Purchase Order', 'Sent', 'Air Waybill', 'Invoice'],
            'counts': [count_po, count_sc, count_awb, count_invoice],
        },
        'stock_summary': stock_summary,
    }
    return render(request, 'home.html', context)
