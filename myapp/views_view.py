from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from myapp.models import PurchaseRequest

@login_required()
def home(request):
    requests = PurchaseRequest.objects.all()

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
        }
    }
    return render(request, 'home.html', context)

from django.shortcuts import render
from .models import Stock

def stock_list(request):
    stocks = Stock.objects.select_related('part').all().order_by('-created_at')
    return render(request, 'home.html', {'stocks': stocks})
