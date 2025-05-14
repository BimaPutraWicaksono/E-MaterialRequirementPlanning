
from django.urls import path
from . import views
from . import views_view
from . import views_sparepart
from . import views_order
from . import views_auth


urlpatterns = [
    
    # login
    path('login/', views_auth.user_login, name='login'),
    path('logout/', views_auth.user_logout, name='logout'),
    
    #home
    path('home/', views_view.home, name='home'),
    
    # sparepart 
    path('applicator/', views_sparepart.applicator, name='applicator'),
    path('reset_applicator/', views_sparepart.reset_applicator, name='reset_applicator'),
    
    # tools
    path('carline/', views.carline_view, name='carline'), # carline
    path('carline/delete/<int:pk>/', views.delete_carline, name='delete_carline'),
    
    path('carlineSixProductionPlan/<str:name>/', views.sixProductionPlan, name='sixProductionPlan'),# import six production plan
    path('reset_sixProductionPlan/<str:name>/', views.reset_sixProductionPlan, name='reset_sixProductionPlan'),
    
    path('carlineMcl/<str:name>/', views.machineLoading, name='machineLoading'),# import machine loading
    path('reset_machineLoading/<str:name>/', views.reset_machineLoading, name='reset_machineLoading'),
    
    path('reset-carline/', views.reset_carline_all, name='reset_carline'),# reset all carline
    
    # calculation
    path('machineLoadingCalculate/<str:name>/', views.machineLoadingCalculate, name='machineLoadingCalculate'),
    path('requirementPartAllCarline/', views.requirementPartAllCarline, name='requirementPartAllCarline'),
    
    # stroke part
    path('strokePart/', views_sparepart.strokePart, name='strokePart'),    
    path('loadingPart/', views.loadingPart, name='loadingPart'),
    
    # about as
    path('about/', views_sparepart.about, name='about'),
    
    # crud account
    path('account', views_auth.daftar_akun, name='daftar_akun'),
    path('deleteAccount/', views_auth.hapus_akun, name='hapus_akun'),
     
    #home
    path('purchaseReq/', views_order.purchaseReq, name='purchaseReq'),
    path('purchaseOrd/', views_order.purchaseOrd, name='purchaseOrd'),
    path('scheduleConf/', views_order.scheduleConf, name='scheduleConf'),
    path('airwayBill/', views_order.airwayBill, name='airwayBill'),
    path('invoice/', views_order.invoice, name='invoice'),
    
]