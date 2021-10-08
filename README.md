# monitoreogrid
ManagEV app for monitoring electric vehicles operation.

This repository contains the source code for the app, IoT monitoring devices, and research

Como inicializar el servidor en PUTTY:
    En la pestaña "Session" configurar la IP: "104.236.94.94" en el puerto 22.
    Por otra parte guardar la sesión para que se llame ManagEV
    Irse a la pestaña Data (dentro de connections) y en Auto-login username poner "root"
    Seleccionar ManagEV y presionar OPEN. La contraseña del servidor es "2021.ManagEV"

Comandos necesarios dentro del servidor:
    con el comando "tmux attach" lo que hace es correrse el programa como un threat. Cuando se cierra la consola no se para el proceso
    Con git pull se baja el respositorio con los cambios hechos
    con flask db upgrade se actualiza la base de datos en caso de que se hayan agregado nuevas columnas y campos en las tablas
    con el comando "gunicorn --worker-class gevent -b localhost:8080 app:app" se corre el servidor


