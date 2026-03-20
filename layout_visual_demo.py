"""
Visual demo de la estructura de botones
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║         PANTALLA DE VALIDACIÓN BIOMÉTRICA - LAYOUT DE BOTONES             ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│                          BARRA SUPERIOR (Header)                         │
│  Logo                    SISTEMA DE CONTROL BIOMÉTRICO            ES|EN ☀ │
│  ▌                                                                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      POR FAVOR NO SE MUEVA                               │
│                     ESCANEANDO ROSTRO...                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│                    ┌─────────────────────────┐                           │
│                    │    CAPTURA DE CÁMARA    │                           │
│                    │   (Video en tiempo real)│                           │
│                    │    [ROSTRO DETECTADO]   │                           │
│                    │  ▢ ▭▭▭ ▭▭ ▭▭▭ ▭▭▭ ▢    │                           │
│                    └─────────────────────────┘                           │
│                                                                           │
│      Estado: ✓ 1 rostro(s) detectado(s)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│          LADO IZQUIERDO       │       CENTRO       │    LADO DERECHO     │
│  ┌──────────────────────────┐ │ ┌──────────────┐  │ ┌──────────────────┐│
│  │  ← VOLVER  📋 VERIFICAR  │ │ │ 🔒 CAPTURAR  │  │ │  ⚙ CONFIG        ││
│  └──────────────────────────┘ │ └──────────────┘  │ └──────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════════════════════╗
║                         FUNCIONALIDADES                                    ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ← VOLVER                                                                  ║
║  └─ Regresa a la pantalla anterior / cierra la aplicación                ║
║                                                                            ║
║  📋 VERIFICAR                                                              ║
║  └─ Verifica la identidad usando los vectores capturados                 ║
║  └─ Requiere haber presionado CAPTURAR primero                           ║
║  └─ TODO: Redirige a otra pantalla cuando se implemente                  ║
║                                                                            ║
║  🔒 CAPTURAR                                                               ║
║  └─ Extrae vectores/encodings del rostro detectado                       ║
║  └─ Guarda características faciales en memoria                           ║
║  └─ Mostrará confirmación con cantidad de vectores extraídos             ║
║                                                                            ║
║  ⚙ CONFIG                                                                  ║
║  └─ Botón de configuración (SIN FUNCIONALIDAD POR AHORA)                ║
║  └─ TODO: Implementar pantalla de configuración                          ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════════════════╗
║                    EXTRACCIÓN DE VECTORES FACIALES                         ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  MÉTODO: _extraer_vectores_rostro()                                       ║
║                                                                            ║
║  DATOS EXTRAÍDOS POR ROSTRO:                                              ║
║  ├─ Posición: {"x": int, "y": int, "ancho": int, "alto": int}           ║
║  ├─ Histograma: lista de 256 valores de intensidad                       ║
║  ├─ Media de intensidad: valor promedio (0-255)                          ║
║  ├─ Desviación estándar: variación de intensidad                         ║
║  └─ Hash único: identificador del rostro para comparación                ║
║                                                                            ║
║  ALMACENAMIENTO:                                                          ║
║  └─ self.vectores_rostros: lista de vectores capturados                  ║
║  └─ Se llena cuando presionas: 🔒 CAPTURAR                               ║
║  └─ Se usa cuando presionas: 📋 VERIFICAR                                ║
║                                                                            ║
║  FALLBACK:                                                                ║
║  ├─ Si face_recognition está disponible → usa face encodings (128 dims)  ║
║  └─ Si no → usa características de OpenCV (histogramas + stats)          ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
