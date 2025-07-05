from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from . import views_auth
from . import views_view
from . import views_sparepart
from . import views_order
from . import views_ordered
from . import views_airwaybill
from . import views_invoice
from . import views_stock



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
    
    path('carlineSixProductionPlan/<str:name>/', views.sixProductionPlan, name='sixProductionPlan'),
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
    

    path('departement/edit/<int:id>/', views_order.update_departement, name='update_departement'),
    path('departement/delete/<int:id>/', views_order.delete_departement, name='delete_departement'),
    path('section/edit/<int:id>/', views_order.update_section, name='update_section'),
    path('section/delete/<int:id>/', views_order.delete_section, name='delete_section'),
     
    #purchase request
    path('purchase-request/', views_order.purchaseReq, name='purchaseReq'),
    path('ajax/get-loading-parts/', views_order.ajax_get_loading_parts, name='ajax_get_loading_parts'),
    path('ajax/load-sections/', views_order.ajax_load_sections, name='ajax_load_sections'),

    path('purchase-request/detail/<str:registered_no>/', views_order.purchase_request_detail, name='purchase_request_detail'),
    path('purchase-request/approve/<str:registered_no>/', views_order.approve_purchase_request, name='approve_purchase_request'),
    
    path('purchase-request/delete/<str:registered_no>/', views_order.delete_purchase_request, name='delete_purchase_request'),
    path('purchase-request/edit/<str:registered_no>/', views_order.purchase_request_edit, name='purchase_request_edit'),
    path('ajax/get-loading-parts-edit/', views_order.ajax_get_loading_parts_edit, name='ajax_get_loading_parts_edit'),
    
    # purchase order
    path('purchase-order/', views_ordered.purchaseOrd, name='purchaseOrd'),
    path('purchase-order/detail/<str:registered_no>/', views_ordered.purchase_order_detail, name='purchase_order_detail'),
    
    path('purchase-order/edit/<str:registered_no>/', views_ordered.purchase_order_edit, name='purchase_order_edit'),
    path('purchase-order/delete/<str:registered_no>/', views_ordered.purchase_order_delete, name='purchase_order_delete'),
    path('purchase-order/approve/<str:registered_no>/', views_ordered.approve_purchase_order, name='approve_purchase_order'),
    
    # supplier
    path('supplier/', views_ordered.supplier_list, name='supplier_list'),
    path('supplier/add/', views_ordered.supplier_create, name='supplier_create'),
    path('supplier/edit/<int:pk>/', views_ordered.supplier_update, name='supplier_update'),
    path('supplier/delete/<int:pk>/', views_ordered.supplier_delete, name='supplier_delete'),
    
    # shipped
    path('shipped/', views_ordered.shipped_list, name='shipped_list'),
    path('shipped/add/', views_ordered.shipped_create, name='shipped_create'),
    path('shipped/<int:pk>/edit/', views_ordered.shipped_update, name='shipped_update'),
    path('shipped/<int:pk>/delete/', views_ordered.shipped_delete, name='shipped_delete'),
    
    # eksport
    path('purchase-order/export/<str:registered_no>/', views_ordered.export_purchase_order_pdf, name='export_purchase_order_pdf'),
    path('exported-files/', views_ordered.list_exported_purchase_orders, name='list_exported_files'),
    path('exported-files/delete/', views_ordered.delete_exported_file, name='delete_exported_file'),
    
    # send email
    path('send-exported-file-email/', views_ordered.send_exported_file_email, name='send_exported_file_email'),
    path('e-mrp/exported-files/', views_ordered.list_exported_purchase_orders, name='list_exported_purchase_orders'),
    
    # airwaybil
    path('airwaybill/import/', views_airwaybill.import_airwaybill, name='import_airwaybill'),
    path('airwaybill-detail/<str:registered_no>/', views_airwaybill.airwaybill_detail, name='airwaybill_detail'),
    
    # invoice
    path('invoice/import/', views_invoice.import_invoice, name='import_invoice'),
    path('invoice/detail/<str:registered_no>/', views_invoice.invoice_detail, name='invoice_detail'),

    # stock
    path('add-stock/', views_stock.stockList, name='add_stock'),
    path('stock/request-item-detail/<int:pk>/', views_stock.requestItemDetail, name='request_item_detail'),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)