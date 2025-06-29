from django.shortcuts import render
from .models import Stock

def stock_list(request):
    stocks = Stock.objects.select_related('part').all().order_by('-created_at')
    return render(request, 'stock/stock.html', {'stocks': stocks})
