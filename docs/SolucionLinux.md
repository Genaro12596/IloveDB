1. Cambiar a la shell Bash para asegurar compatibilidad con el script de activación
```bash
bash
```

2. Eliminar el entorno virtual anterior que causaba problemas
```bash
rm -rf venv
```
3. Recrear el entorno virtual utilizando el módulo venv de Python 3
```bash
python3 -m venv venv
```
4. Activar el entorno virtual (ahora ejecutado correctamente bajo Bash)
```bash
source venv/bin/activate
```

Regresar al readme: [Click aqui](../README.md)