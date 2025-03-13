
from django.urls import path
from . import views
from . import views_sparepart
from . import views_auth


urlpatterns = [
    
    # login
    path('login/', views_auth.user_login, name='login'),
    path('logout/', views_auth.user_logout, name='logout'),
    
    # dashboard 
    path('dashboard/', views_sparepart.dashboard, name='dashboard'),
    # export dashboard
    path('export-dashboard/', views.export_dashboard, name='export_dashboard'),
    
    # sparepart 
    path('applicator/', views_sparepart.applicator, name='applicator'),
    path('reset_applicator/', views_sparepart.reset_applicator, name='reset_applicator'),
    path('machine/', views_sparepart.machine, name='machine'),
    path('reset_machine/', views_sparepart.reset_machine, name='reset_machine'),
    path('sealUnit/', views_sparepart.sealUnit, name='sealUnit'),
    path('reset_sealUnit/', views_sparepart.reset_sealUnit, name='reset_sealUnit'),
    
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
    
    
    path('about/', views_sparepart.about, name='about'),
    
    # crud account
    path('account', views_auth.daftar_akun, name='daftar_akun'),
    path('deleteAccount/', views_auth.hapus_akun, name='hapus_akun'),
    path('delete-all/', views.delete_all_data, name='delete_all_data'), #menghapus semua database (WARNING!)
]

