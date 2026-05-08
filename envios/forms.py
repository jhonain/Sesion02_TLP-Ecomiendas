# envios/forms.py
from django import forms
from .models import Encomienda
from clientes.models import Cliente
from rutas.models import Ruta


class EncomiendaCrearForm(forms.ModelForm):
    """
    Formulario para REGISTRAR una nueva encomienda.
    No incluye 'codigo' ni 'costo_envio' porque se generan
    automáticamente en Encomienda.crear_con_costo_calculado().
    """

    class Meta:
        model  = Encomienda
        fields = [
            'descripcion', 'peso_kg', 'volumen_cm3',
            'remitente', 'destinatario', 'ruta',
            'observaciones',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Describe el contenido del paquete…',
            }),
            'peso_kg': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0.01',
            }),
            'volumen_cm3': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01',
            }),
            'remitente':    forms.Select(attrs={'class': 'form-select'}),
            'destinatario': forms.Select(attrs={'class': 'form-select'}),
            'ruta':         forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Indicaciones especiales, fragilidad, etc.',
            }),
        }
        labels = {
            'peso_kg':     'Peso (kg)',
            'volumen_cm3': 'Volumen (cm³)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['remitente'].queryset    = Cliente.objects.activos().order_by('apellidos')
        self.fields['destinatario'].queryset = Cliente.objects.activos().order_by('apellidos')
        self.fields['ruta'].queryset         = Ruta.objects.activas().order_by('origen')
        self.fields['volumen_cm3'].required  = False
        self.fields['observaciones'].required = False

    def clean(self):
        """Validación a nivel de formulario: remitente ≠ destinatario"""
        cleaned      = super().clean()
        remitente    = cleaned.get('remitente')
        destinatario = cleaned.get('destinatario')
        if remitente and destinatario and remitente == destinatario:
            raise forms.ValidationError(
                'El remitente y el destinatario no pueden ser la misma persona.'
            )
        return cleaned


class EncomiendaEditarForm(forms.ModelForm):
    """
    Formulario para EDITAR una encomienda existente (solo estado Pendiente).
    Muestra código y costo como campos de solo lectura para referencia visual,
    pero no permite modificarlos.
    """

    class Meta:
        model  = Encomienda
        fields = [
            'descripcion', 'peso_kg', 'volumen_cm3',
            'remitente', 'destinatario', 'ruta',
            'fecha_entrega_est', 'observaciones',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
            }),
            'peso_kg': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0.01',
            }),
            'volumen_cm3': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01',
            }),
            'remitente':    forms.Select(attrs={'class': 'form-select'}),
            'destinatario': forms.Select(attrs={'class': 'form-select'}),
            'ruta':         forms.Select(attrs={'class': 'form-select'}),
            'fecha_entrega_est': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
            }),
        }
        labels = {
            'peso_kg':          'Peso (kg)',
            'volumen_cm3':      'Volumen (cm³)',
            'fecha_entrega_est': 'Fecha estimada de entrega',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['remitente'].queryset    = Cliente.objects.activos().order_by('apellidos')
        self.fields['destinatario'].queryset = Cliente.objects.activos().order_by('apellidos')
        self.fields['ruta'].queryset         = Ruta.objects.activas().order_by('origen')
        self.fields['volumen_cm3'].required  = False
        self.fields['observaciones'].required = False

    def clean(self):
        """Validación a nivel de formulario: remitente ≠ destinatario"""
        cleaned      = super().clean()
        remitente    = cleaned.get('remitente')
        destinatario = cleaned.get('destinatario')
        if remitente and destinatario and remitente == destinatario:
            raise forms.ValidationError(
                'El remitente y el destinatario no pueden ser la misma persona.'
            )
        return cleaned


# Alias de compatibilidad — las vistas que aún usen EncomiendaForm seguirán
# funcionando sin cambios hasta que se actualicen explícitamente.
EncomiendaForm = EncomiendaCrearForm
