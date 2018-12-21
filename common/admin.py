from django.contrib import admin
from common.models import *

# Register your models here.
class TokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'expires', 'enabled')
    list_filter = ('enabled', 'created', 'updated', 'expires')
    
class HostAdmin(admin.ModelAdmin):
    list_display = ('fqdn', 'hostname', 'domain', 'created', 'enabled')
    list_filter = ('enabled', 'created', 'updated')
    
class PulseAdmin(admin.ModelAdmin):
    list_display = ('token', 'app', 'count', 'bytes', 'created')
    list_filter = ('created', 'app')

admin.site.register(Token, TokenAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Pulse, PulseAdmin)
admin.site.register(User)