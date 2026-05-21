import argostranslate.package
import argostranslate.translate

def instalar_modelos_necesarios():
    """
    IMPORTANTE: Ejecuta esta función UNA SOLA VEZ con conexión a internet.
    Descarga los modelos de IA para traducir entre Inglés y Español.
    """
    print("Actualizando índice de paquetes de traducción...")
    argostranslate.package.update_package_index()
    paquetes_disponibles = argostranslate.package.get_available_packages()

    print("Buscando paquetes ES <-> EN...")
    modelos_instalados = 0
    for paquete in paquetes_disponibles:
        if (paquete.from_code == 'en' and paquete.to_code == 'es') or \
           (paquete.from_code == 'es' and paquete.to_code == 'en'):
            print(f"Descargando e instalando: {paquete.from_code} -> {paquete.to_code}...")
            argostranslate.package.install_from_path(paquete.download())
            modelos_instalados += 1
    
    if modelos_instalados > 0:
        print("¡Instalación completada! Ya puedes usar el sistema 100% offline.")
    else:
        print("Los modelos ya estaban instalados o hubo un problema al encontrarlos.")

class TraductorOffline:
    def procesar_texto(self, texto, idioma_destino):
        """
        Traduce el texto al idioma destino ('en' o 'es') de forma local.
        """
        # Si el texto está vacío, devolvemos vacío
        if not texto or not texto.strip():
            return ""
            
        try:
            if idioma_destino == 'en':
                # Traduce de Español a Inglés
                return argostranslate.translate.translate(texto, 'es', 'en')
                
            elif idioma_destino == 'es':
                # Traduce de Inglés a Español
                return argostranslate.translate.translate(texto, 'en', 'es')
                
            else:
                # Si le pasas un idioma no soportado, devuelve el texto original
                return texto 
                
        except Exception as e:
            # Si hay un error (ej. modelos no instalados), no rompe la app, solo devuelve el texto original
            print(f"Error en traducción: {e}")
            return texto

# ==========================================
# BLOQUE DE CONFIGURACIÓN INICIAL
# ==========================================
# Al ejecutar este archivo directamente desde la terminal, se descargarán los modelos.
if __name__ == "__main__":
    print("Iniciando configuración inicial de idiomas...")
    instalar_modelos_necesarios()