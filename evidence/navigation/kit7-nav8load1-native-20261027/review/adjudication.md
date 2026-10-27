# Bloqueador corregido antes del lanzamiento

Fable encontró un capturador que no parseaba. Se conserva el archivo rechazado:14erroresPowerShell. Causa aislada: String.replace deJavaScript expandía el token dólar-apóstrofe dentro del texto de reemplazo; no era .NET. Reescritura literal sinreplace.

7escenarios ejecutan PowerShell real con logs sintéticos yPID/creación del proceso de prueba: captura607,END0 conservado,configobsoleto,logobsoleto,creaciónincorrecta,configparcial,salidayaexistente. Todos pasan; los5negativos devuelven1 y no creanbinding. El primer harness falló por ErrorActionPreferenceStop en un negativo esperado; v2 conserva código de salida yassert explícita. Ningún intentoDayZ consumido.

Selladorparsea de nuevo, exigehashdelcapturador probado, superconjunto defuentesrevisadas y dependenciastransitivasdeloráculo607. La aprobacióncondicionada de Fable se satisface con estas correcciones; RAM sigue fuera deestealcance.
