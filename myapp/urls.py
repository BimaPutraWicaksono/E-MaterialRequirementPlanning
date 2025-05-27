
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
    
    # departement
    path('master/departement-section/', views_order.master_departement_section, name='master_departement_section'),
    path('master/departement/create/', views_order.create_departement, name='create_departement'),
    path('master/section/create/', views_order.create_section, name='create_section'),
     
    #order
    path('purchase-request/', views_order.purchaseReq, name='purchaseReq'),
    path('ajax/get-loading-parts/', views_order.ajax_get_loading_parts, name='ajax_get_loading_parts'),
    path('ajax/load-sections/', views_order.ajax_load_sections, name='ajax_load_sections'),

    path('purchase-request/detail/<str:registered_no>/', views_order.purchase_request_detail, name='purchase_request_detail'),
    path('purchase-request/approve/<str:registered_no>/', views_order.approve_purchase_request, name='approve_purchase_request'),
    
    path('purchase-request/delete/<str:registered_no>/', views_order.delete_purchase_request, name='delete_purchase_request'),
    path('purchase-request/edit/<str:registered_no>/', views_order.purchase_request_edit, name='purchase_request_edit'),
    path('ajax/get-loading-parts-edit/', views_order.ajax_get_loading_parts_edit, name='ajax_get_loading_parts_edit'),
    
    path('purchaseOrd/', views_order.purchaseOrd, name='purchaseOrd'),
    path('scheduleConf/', views_order.scheduleConf, name='scheduleConf'),
    path('airwayBill/', views_order.airwayBill, name='airwayBill'),
    path('invoice/', views_order.invoice, name='invoice'),
     
    
    
]