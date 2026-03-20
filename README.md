SRFC_Project/
├── assets/              # Recursos visuales estáticos
│   ├── fonts/           # Tipografías personalizadas
│   └── img/             # Logos institucionales e iconos
├── core/                # Lógica de Negocio (Backend)
│   ├── camera.py        # Procesamiento con OpenCV
│   └── biometrics.py    # Reconocimiento facial (dlib/face_recognition)
├── data/                # Persistencia y archivos locales
│   ├── profiles/        # Fotos de referencia de los alumnos
│   └── SRFC.db          # Base de datos SQLite
├── src/                 # Utilidades y soporte técnico
├── ui/                  # Interfaz de Usuario (Frontend)
│   ├── components/      # Widgets reutilizables (Botones, Inputs)
│   ├── screens/         # Ventanas (Login, Registro, Dashboard)
│   └── styles.py        # Definición de temas y colores (CustomTkinter)
├── .gitignore           # Archivos ignorados por Git (ej. .venv, __pycache__)
├── LICENSE              # Licencia del software
├── main.py              # Punto de entrada de la aplicación
├── README.md            # Documentación general del proyecto
└── requirements.txt     # Dependencias del sistema