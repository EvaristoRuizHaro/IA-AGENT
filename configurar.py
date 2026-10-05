# Asistente para configurar el agente para una persona nueva.
# Uso: python configurar.py
import json
import os

print("=== Configuración del agente de LinkedIn ===\n")

presets = sorted(f[:-5] for f in os.listdir("presets") if f.endswith(".json"))
for i, p in enumerate(presets, start=1):
    print(f"  {i}. {p}")
eleccion = int(input("\n¿Sobre qué tema publicará? (número): ")) - 1
tema = presets[eleccion]

nombre = input("Nombre de la persona (como quiere que la llamen): ").strip()
print("\nDescribe en una frase quién es. Ejemplo:")
print('  "graduado en ADE interesado en finanzas y análisis de empresas, en Sevilla"')
perfil = input("Perfil: ").strip()

with open(f"presets/{tema}.json", encoding="utf-8") as f:
    texto = f.read()
texto = texto.replace("{NOMBRE}", nombre).replace("{PERFIL}", perfil)

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(json.loads(texto), f, ensure_ascii=False, indent=2)
print(f"\n✅ config.json creado con el tema '{tema}' para {nombre}.")

if input("\n¿Es una instalación nueva? Se vaciarán el historial y los posts programados (s/n): ").lower() == "s":
    with open("historial.json", "w", encoding="utf-8") as f:
        f.write("[]")
    with open("posts_programados.json", "w", encoding="utf-8") as f:
        f.write("{}")
    print("✅ Historial y posts programados vaciados.")

print("\nSiguiente paso: rellena el .env y prueba con  python redactor.py")
