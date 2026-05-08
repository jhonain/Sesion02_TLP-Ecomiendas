# envios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

from .models import Encomienda, Empleado, HistorialEstado
from .forms import EncomiendaCrearForm, EncomiendaEditarForm
from config.choices import EstadoEnvio


# ── Helper interno ────────────────────────────────────────────────────────────
def _get_empleado(request):
    """
    Devuelve el Empleado vinculado al usuario autenticado.
    Primero intenta buscar por OneToOne (user), luego como fallback por email.
    Lanza Empleado.DoesNotExist si no hay ninguna coincidencia.
    """
    # Intentar por relación directa user (si existe en el futuro)
    if hasattr(Empleado, 'user'):
        return Empleado.objects.get(user=request.user)
    # Fallback actual: buscar por email
    return Empleado.objects.get(email=request.user.email)


# ── Dashboard ─────────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    """Vista principal del sistema con estadísticas"""
    hoy = timezone.now().date()
    context = {
        'total_activas':  Encomienda.objects.activas().count(),
        'en_transito':    Encomienda.objects.en_transito().count(),
        'con_retraso':    Encomienda.objects.con_retraso().count(),
        'entregadas_hoy': Encomienda.objects.filter(
                              estado=EstadoEnvio.ENTREGADO,
                              fecha_entrega_real=hoy
                          ).count(),
        'ultimas':        Encomienda.objects.con_relaciones()[:5],
    }
    return render(request, 'envios/dashboard.html', context)


# ── Lista con búsqueda, filtro y paginación ───────────────────────────────────
@login_required
def encomienda_lista(request):
    """Lista de encomiendas con filtros GET y paginación"""
    estado_activo = request.GET.get('estado', '')
    q             = request.GET.get('q', '')

    qs = Encomienda.objects.con_relaciones()

    if estado_activo:
        qs = qs.filter(estado=estado_activo)

    if q:
        qs = qs.filter(
            Q(codigo__icontains=q) |
            Q(remitente__apellidos__icontains=q) |
            Q(destinatario__apellidos__icontains=q)
        )

    paginator   = Paginator(qs, 15)
    page_number = request.GET.get('page', 1)
    encomiendas = paginator.get_page(page_number)

    context = {
        'encomiendas':   encomiendas,
        'estados':       EstadoEnvio.choices,
        'estado_activo': estado_activo,
        'q':             q,
    }
    return render(request, 'envios/lista.html', context)


# ── Detalle ───────────────────────────────────────────────────────────────────
@login_required
def encomienda_detalle(request, pk):
    """Detalle de una encomienda con su historial de estados"""
    enc = get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)
    context = {
        'encomienda': enc,
        'historial':  enc.historial.select_related('empleado').all(),
        'estados':    EstadoEnvio.choices,
    }
    return render(request, 'envios/detalle.html', context)


# ── Crear ─────────────────────────────────────────────────────────────────────
@login_required
def encomienda_crear(request):
    """
    GET  → muestra formulario vacío (sin campos auto-generados)
    POST → valida, genera código y costo automáticamente, guarda (patrón PRG)
    """
    if request.method == 'POST':
        form = EncomiendaCrearForm(request.POST)
        if form.is_valid():
            try:
                empleado = _get_empleado(request)
            except Empleado.DoesNotExist:
                messages.error(request, 'No se encontró un empleado asociado a tu usuario.')
                return render(request, 'envios/form.html', {'form': form, 'titulo': 'Nueva Encomienda'})

            enc = Encomienda.crear_con_costo_calculado(
                remitente    = form.cleaned_data['remitente'],
                destinatario = form.cleaned_data['destinatario'],
                ruta         = form.cleaned_data['ruta'],
                empleado     = empleado,
                descripcion  = form.cleaned_data['descripcion'],
                peso_kg      = form.cleaned_data['peso_kg'],
                volumen_cm3  = form.cleaned_data.get('volumen_cm3'),
                observaciones= form.cleaned_data.get('observaciones'),
            )
            messages.success(request, f'Encomienda {enc.codigo} registrada correctamente.')
            return redirect('encomienda_detalle', pk=enc.pk)
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = EncomiendaCrearForm()

    return render(request, 'envios/form.html', {
        'form':   form,
        'titulo': 'Nueva Encomienda',
    })


# ── Editar ────────────────────────────────────────────────────────────────────
@login_required
def encomienda_editar(request, pk):
    """Editar una encomienda — solo si está en estado Pendiente"""
    enc = get_object_or_404(Encomienda, pk=pk)

    if enc.estado != EstadoEnvio.PENDIENTE:
        raise PermissionDenied

    if request.method == 'POST':
        form = EncomiendaEditarForm(request.POST, instance=enc)
        if form.is_valid():
            form.save()
            messages.success(request, f'Encomienda {enc.codigo} actualizada.')
            return redirect('encomienda_detalle', pk=enc.pk)
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = EncomiendaEditarForm(instance=enc)

    return render(request, 'envios/form.html', {
        'form':   form,
        'titulo': f'Editar {enc.codigo}',
    })


# ── Cambiar estado ────────────────────────────────────────────────────────────
@login_required
@require_POST
def encomienda_cambiar_estado(request, pk):
    """Cambia el estado de una encomienda y registra en el historial"""
    enc          = get_object_or_404(Encomienda, pk=pk)
    nuevo_estado = request.POST.get('estado')
    observacion  = request.POST.get('observacion', '')

    try:
        empleado = _get_empleado(request)
        enc.cambiar_estado(nuevo_estado, empleado, observacion)
        messages.success(request, f'Estado actualizado a "{enc.get_estado_display()}" correctamente.')
    except Empleado.DoesNotExist:
        messages.error(request, 'No se encontró el empleado asociado a tu usuario.')
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error al cambiar estado: {e}')

    return redirect('encomienda_detalle', pk=pk)


# ── API JSON ──────────────────────────────────────────────────────────────────
@login_required
def encomienda_estado_json(request, pk):
    """Endpoint JSON con el estado actual de una encomienda"""
    enc = get_object_or_404(Encomienda, pk=pk)
    return JsonResponse({
        'codigo':  enc.codigo,
        'estado':  enc.estado,
        'display': enc.get_estado_display(),
        'retraso': enc.tiene_retraso,
        'dias':    enc.dias_en_transito,
    })
