# =====================================================================
#  TP02 - Programacion I
#  Controlador de misiones
#
#  ESTE ES EL ARCHIVO DONDE ESCRIBIS TU PROGRAMA.
#
#  Antes de ejecutarlo:
#    1. Abri INICIAR_SIMULADOR (elegi G1 o Go2)
#    2. Espera a que aparezca la ventana con el robot
#    3. Recien ahi ejecuta este archivo
#
#  Nombre y apellido:  .....................................
#  Comision:           .....................................
# =====================================================================

from robot import ErrorDeSeguridad, Robot

from misiones import MISION_BASICA, MISION_CON_ERRORES, MISION_CUADRADO, MISION_LARGA


def motivo_comando_invalido(comando):
    """Devuelve el motivo del rechazo, o un texto vacio si el formato es valido."""
    if type(comando) != tuple:
        return "El comando debe ser una tupla."
    if len(comando) == 0:
        return "La tupla del comando esta vacia."

    nombre = comando[0]
    if nombre not in ("avanzar", "girar", "detenerse", "saludar"):
        return f"Comando desconocido: {nombre}."

    if nombre in ("detenerse", "saludar"):
        if len(comando) != 1:
            return f"{nombre} no lleva velocidad ni tiempo."
    else:
        if len(comando) != 3:
            return f"{nombre} necesita velocidad y tiempo."
        if type(comando[1]) not in (int, float):
            return "La velocidad debe ser un numero entero o decimal."
        if type(comando[2]) not in (int, float):
            return "El tiempo debe ser un numero entero o decimal."
        if comando[2] < 0:
            return "El tiempo no puede ser negativo."

    return ""


# =====================================================================
#  PARTE 1 - Validar un comando
# =====================================================================
def comando_es_valido(comando):
    """Decide si un comando se puede ejecutar. Devuelve True o False.

    Un comando es una tupla. El primer elemento dice que hacer:

        ("avanzar", velocidad, tiempo)    velocidad en m/s, tiempo en s
        ("girar", velocidad, tiempo)      velocidad en rad/s, tiempo en s
        ("detenerse",)
        ("saludar",)

    Cosas que conviene revisar:
      - que la tupla no este vacia
      - que el nombre del comando sea uno de los cuatro validos
      - que tenga la cantidad de datos que corresponde
        (avanzar y girar llevan dos; detenerse y saludar, ninguno)
      - que velocidad y tiempo sean numeros de verdad, no textos
      - que el tiempo no sea negativo
    """
    return motivo_comando_invalido(comando) == ""


# =====================================================================
#  PARTE 2 - Ejecutar un comando
# =====================================================================
def ejecutar_comando(robot, comando):
    """Ejecuta UN comando en el robot. Devuelve un texto con lo que paso.

    Ordenes que podes usar:

        robot.avanzar(velocidad=..., tiempo=...)
        robot.girar(velocidad=..., tiempo=...)
        robot.detenerse()
        robot.saludar()

    Ojo: aunque el comando parezca valido, el robot puede rechazarlo
    igual (por ejemplo, si la velocidad supera el limite de la materia).
    Eso llega como un ErrorDeSeguridad y conviene atraparlo.
    """
    motivo = motivo_comando_invalido(comando)
    if motivo != "":
        return f"Rechazado: {motivo}"

    nombre = comando[0]
    try:
        if nombre == "avanzar":
            robot.avanzar(velocidad=comando[1], tiempo=comando[2])
        elif nombre == "girar":
            robot.girar(velocidad=comando[1], tiempo=comando[2])
        elif nombre == "detenerse":
            robot.detenerse()
        elif nombre == "saludar":
            robot.saludar()
    except ErrorDeSeguridad as error:
        robot.detenerse()
        return f"Rechazado: {error}"

    return f"Ejecutado: {nombre}."


# =====================================================================
#  PARTE 3 - Recorrer la mision entera
# =====================================================================
def ejecutar_mision(robot, mision, historial):
    """Recorre la lista de comandos, uno por uno.

    Por cada comando:
      - si NO es valido, lo rechaza y sigue con el siguiente
      - si es valido, lo ejecuta
      - en los dos casos, guarda en 'historial' que fue lo que paso

    Un comando invalido NO tiene que cortar la mision.
    """
    for comando in mision:
        if comando_es_valido(comando):
            resultado = ejecutar_comando(robot, comando)
        else:
            resultado = f"Rechazado: {motivo_comando_invalido(comando)}"

        historial.append({"comando": comando, "resultado": resultado})
        print(f"{comando} -> {resultado}")


# =====================================================================
#  PARTE 4 - El reporte final
# =====================================================================
def generar_reporte(historial):
    """Muestra por pantalla un resumen de la mision.

    Tiene que decir, como minimo:
      - cuantos comandos se ejecutaron bien
      - cuantos se rechazaron
      - cual fue el motivo de cada rechazo
    """
    ejecutados = 0
    rechazados = 0

    for registro in historial:
        if registro["resultado"].startswith("Ejecutado:"):
            ejecutados = ejecutados + 1
        else:
            rechazados = rechazados + 1

    print("\nReporte de la mision")
    print("Total de comandos:", len(historial))
    print("Ejecutados:", ejecutados)
    print("Rechazados:", rechazados)

    for registro in historial:
        if registro["resultado"].startswith("Rechazado:"):
            print(f"{registro['comando']} -> {registro['resultado']}")


# =====================================================================
#  PROGRAMA PRINCIPAL
# =====================================================================
def main():
    # Cambia esta variable por MISION_CUADRADO, MISION_CON_ERRORES o MISION_LARGA.
    mision = MISION_BASICA

    robot = Robot()
    robot.conectar()

    historial = []

    try:
        ejecutar_mision(robot, mision, historial)
        generar_reporte(historial)
    finally:
        try:
            robot.detenerse()
        finally:
            robot.desconectar()


if __name__ == "__main__":
    main()
