from django.contrib import admin
from .models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'completed', 'assigned_to')  
    list_filter = ('completed', 'assigned_to')            
    search_fields = ('title', 'description')            

admin.site.register(Task, TaskAdmin)
