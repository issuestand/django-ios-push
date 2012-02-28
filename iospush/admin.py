# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.actions import delete_selected
admin.site.add_action(delete_selected)

from iospush.models import *

class DeviceAdmin(admin.ModelAdmin):
    list_filter = ['failed', 'is_test_device']
    search_fields = ('',)
    pass

admin.site.register(Device, DeviceAdmin)