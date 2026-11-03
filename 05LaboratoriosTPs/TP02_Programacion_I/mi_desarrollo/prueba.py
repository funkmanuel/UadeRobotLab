from robot import Robot

robot = Robot()
robot.conectar()

try:
    robot.avanzar(velocidad=0.2, tiempo=2.0)
    robot.girar(velocidad=-0.5, tiempo=3.14)
    robot.avanzar(velocidad=0.2, tiempo=2.0)
finally:
    robot.detenerse()
    robot.desconectar()