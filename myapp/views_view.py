from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from myapp.models import PurchaseRequest, Stock, PartName

@login_required()
def home(request):
    requests = PurchaseRequest.objects.all()

    # Agregasi stock per Part
    stock_summary = (
        Stock.objects.values('part__partName')
        .annotate(total_qty=Sum('quantity'))
        .order_by('part__partName')
    )

    count_not_processed = requests.filter(approve_spv__isnull=True).count()
    count_spv = requests.filter(approve_spv=True, approve_sspv__isnull=True).count()
    count_sspv = requests.filter(approve_sspv=True, approve_manager__isnull=True).count()
    count_manager = requests.filter(approve_manager=True, approve_factory_manager__isnull=True).count()
    count_factory_manager = requests.filter(approve_factory_manager=True).count()

    context = {
        'chart_data': {
            'labels': [
                'Belum Diproses',
                'SPV',
                'SSPV',
                'Manager',
                'Factory Manager',
            ],
            'counts': [
                count_not_processed,
                count_spv,
                count_sspv,
                count_manager,
                count_factory_manager,
            ]
        },
        'stock_summary': stock_summary,
    }
    return render(request, 'home.html', context)
