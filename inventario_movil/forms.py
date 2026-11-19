"""Formularios con las validaciones de entrada del módulo móvil."""
import re
from datetime import date

from django import forms

from inventario_movil.models import Articulo, Bodega, GRADOS

# Texto permitido en categoría y referencia: letras (con tildes y ñ), números,
# espacios y los signos . - /  Se rechazan <, >, ;, comillas, etc.
PATRON_TEXTO = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .\-/]*$")
CANTIDAD_MAXIMA = 100000


def _validar_texto_limpio(valor, etiqueta):
    """Rechaza vacíos y caracteres especiales no permitidos."""
    valor = ' '.join(valor.split())  # colapsa espacios repetidos
    if not PATRON_TEXTO.match(valor):
        raise forms.ValidationError(
            f"{etiqueta} solo admite letras, números, espacios y . - /")
    return valor


class ArticuloForm(forms.ModelForm):
    """HU-05: crear un artículo nuevo."""

    class Meta:
        model = Articulo
        fields = ['categoria', 'referencia', 'grado', 'stock_minimo']

    def clean_categoria(self):
        return _validar_texto_limpio(self.cleaned_data['categoria'], "La categoría")

    def clean_referencia(self):
        return _validar_texto_limpio(self.cleaned_data['referencia'], "La referencia")

    def clean_stock_minimo(self):
        minimo = self.cleaned_data['stock_minimo']
        if minimo > CANTIDAD_MAXIMA:
            raise forms.ValidationError(
                f"El stock mínimo no puede superar {CANTIDAD_MAXIMA}.")
        return minimo


class MovimientoForm(forms.Form):
    """HU-02 y HU-03: datos comunes de una entrada o una salida."""

    articulo = forms.ModelChoiceField(
        queryset=Articulo.objects.filter(activo=True), label="Artículo",
        error_messages={'required': "Selecciona un artículo.",
                        'invalid_choice': "El artículo no existe."})
    bodega = forms.ModelChoiceField(
        queryset=Bodega.objects.filter(activa=True), label="Bodega",
        error_messages={'required': "Selecciona una bodega.",
                        'invalid_choice': "La bodega no existe o está inactiva."})
    cantidad = forms.IntegerField(
        label="Cantidad", min_value=1, max_value=CANTIDAD_MAXIMA,
        error_messages={
            'required': "Escribe la cantidad.",
            'invalid': "La cantidad debe ser un número entero.",
            'min_value': "La cantidad debe ser mayor que cero.",
            'max_value': f"La cantidad no puede superar {CANTIDAD_MAXIMA}."})
    fecha = forms.DateField(
        label="Fecha", widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={'required': "Indica la fecha.",
                        'invalid': "La fecha no es válida."})
    observaciones = forms.CharField(
        label="Observaciones", required=False, max_length=200,
        widget=forms.Textarea(attrs={'rows': 2}),
        error_messages={'max_length': "Las observaciones admiten máximo 200 caracteres."})

    def clean_fecha(self):
        """No se aceptan fechas futuras (el movimiento ya ocurrió)."""
        fecha = self.cleaned_data['fecha']
        if fecha > date.today():
            raise forms.ValidationError("La fecha no puede ser futura.")
        return fecha

    def clean_observaciones(self):
        """Quita espacios sobrantes y rechaza caracteres de control."""
        texto = self.cleaned_data['observaciones'].strip()
        if any(ord(caracter) < 32 and caracter not in '\n\r\t' for caracter in texto):
            raise forms.ValidationError("Las observaciones tienen caracteres no permitidos.")
        return texto
