# legacy/

Código que la aplicación **ya no importa**, conservado sólo como referencia.

- `calculadora_mundial.py`: calculadora del Mundial de la que nació la calculadora
  argentina. Compartía 163 de sus 170 funciones con `calculadora_futbol_argentino.py`,
  por lo que mantener las dos copias garantizaba que las correcciones se aplicaran
  a una sola. Se archivó en la versión 3.8.0. Si alguna vez se necesita, conviene
  extraer el núcleo común (posiciones, escenarios, situación) a un módulo compartido
  que ambas calculadoras importen, en lugar de reactivar la copia.
