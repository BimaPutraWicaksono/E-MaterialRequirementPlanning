from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Item
from .resources import ItemResource

@admin.register(Item)
class ItemAdmin(ImportExportModelAdmin):
    resource_class = ItemResource
