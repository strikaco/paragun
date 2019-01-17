from django.contrib import admin
from common.models import *

# Register your models here.
class TokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created', 'expires', 'enabled')
    list_filter = ('enabled', 'created', 'updated', 'expires')

class PulseAdmin(admin.ModelAdmin):
    list_display = ('token', 'host', 'app', 'count', 'bytes', 'created')
    list_filter = ('created', 'app')

admin.site.register(Token, TokenAdmin)
admin.site.register(Pulse, PulseAdmin)
admin.site.register(User)