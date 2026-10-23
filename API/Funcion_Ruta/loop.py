
import importlib.util
import os
import sys


def registrar_rutas_desde_directorio(router, directorio):
    for nombre_archivo in os.listdir(directorio):
        ruta_completa = os.path.join(directorio, nombre_archivo)

        if os.path.isdir(ruta_completa):
            registrar_rutas_desde_directorio(
                router,
                ruta_completa
            )

        elif (
            nombre_archivo.endswith(".py")
            and nombre_archivo != "__init__.py"
        ):
            nombre_modulo = nombre_archivo[:-3]

            # Crear un nombre unico para evitar colisiones
            ruta_absoluta = os.path.abspath(ruta_completa)
            nombre_unico = (
                "API_dinamico_"
                + str(abs(hash(ruta_absoluta)))
                + "_"
                + nombre_modulo
            )

            spec = importlib.util.spec_from_file_location(
                nombre_unico,
                ruta_completa
            )

            if spec is None or spec.loader is None:
                continue

            modulo = importlib.util.module_from_spec(spec)

            # IMPORTANTE: registrar antes de ejecutar el modulo
            sys.modules[nombre_unico] = modulo

            try:
                spec.loader.exec_module(modulo)

                if hasattr(modulo, "router"):
                    router.include_router(modulo.router)

            except Exception:
                # Retirar el modulo si su importacion falla
                sys.modules.pop(nombre_unico, None)
                raise
