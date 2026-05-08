# envios/admin.py 
from django.contrib import admin 
from .models import Empleado, Encomienda, HistorialEstado 
@admin.register(Encomienda) 
class EncomiendaAdmin(admin.ModelAdmin): 
    list_display  = ('codigo', 'remitente', 'destinatario', 'ruta', 'estado', 'fecha_registro') 
    list_filter   = ('estado', 'ruta') 
    readonly_fields = ('fecha_registro',) 
@admin.register(Empleado) 
class EmpleadoAdmin(admin.ModelAdmin): 
    list_display  = ('codigo', 'apellidos', 'nombres', 'cargo', 'estado') 
search_fields = ('codigo', 'apellidos', 'nombres') 
@admin.register(HistorialEstado) 
class HistorialEstadoAdmin(admin.ModelAdmin): 
    list_display  = ('encomienda', 'estado_anterior', 'estado_nuevo', 'empleado', 'fecha_cambio') 
    readonly_fields = ('fecha_cambio',)