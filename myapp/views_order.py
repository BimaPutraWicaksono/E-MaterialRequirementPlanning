from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .form import PurchaseReqForm

# purchase request
@login_required()
def purchaseReq(request):
    if request.method == 'POST':
        form = PurchaseReqForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('purchaseReq')  # redirect ke form lagi setelah submit
    else:
        form = PurchaseReqForm()
    
    return render(request, 'order/purchaseReq.html', {'form': form})


# purchase order
@login_required()
def purchaseOrd(request):
    return render(request, 'order/purchaseOrd.html')

# schedule confirmation
@login_required()
def scheduleConf(request):
    return render(request, 'order/scheduleConf.html')

# Airway bill
@login_required()
def airwayBill(request):
    return render(request, 'order/airwayBill.html')

# invoice
@login_required()
def invoice(request):
    return render(request, 'order/invoice.html')