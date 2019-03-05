from django.contrib import admin
from parsing.models import *

# Register your models here.
class AssertionInline(admin.TabularInline):
    model = Assertion
    fields = ('key', 'value', 'status', 'enabled')
    extra = 0
    

class ParserInline(admin.TabularInline):
    model = Parser
    fields = ('field', 'priority', 'value', 'enabled')
    extra = 0
    
    
class SampleInline(admin.TabularInline):
    model = Sample
    fields = ('created', 'value', 'status')
    extra = 0
    
    
class FieldAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'validator', 'enabled')
    list_filter = ('enabled', 'created', 'updated')
    search_fields = ('key', 'description', 'tags')
    
    
class ParserAdmin(admin.ModelAdmin):
    list_display = ('service', 'field', 'priority', 'value', 'enabled')
    list_filter = ('enabled', 'created', 'updated', 'service__key', 'field')
    
  
class SampleAdmin(admin.ModelAdmin):
    list_display = ('service', 'value', 'status', 'enabled')
    list_filter = ('enabled', 'created', 'updated', 'status', 'service__key')
  
    inlines = [
        AssertionInline,  
    ]
    
  
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('token', 'key', 'enabled')
    
    inlines = [
        ParserInline,
        SampleInline,
    ]
    

admin.site.register(Service, ServiceAdmin)
admin.site.register(Parser, ParserAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(Field, FieldAdmin)