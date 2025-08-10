:- encoding(utf8).

/* ============================================================
   SISTEMA EXPERTO – SOPORTE (reglas simples con palabras clave)
   responder(Texto, Respuesta).
   ============================================================ */

% --- Soluciones por tipo de problema ---
solucion(conexion_lenta,
"Pasos sugeridos para CONEXIÓN LENTA:
1) Reinicia el router y espera 30–60 segundos.
2) Prueba con cable de red directo al router.
3) Cierra descargas/streaming pesados y prueba de nuevo.
4) Ejecuta 'ipconfig /flushdns' (Windows) o 'sudo dscacheutil -flushcache' (macOS).
Si persiste, indícanos el resultado y lo escalamos a un técnico.").

solucion(sin_senal,
"Pasos sugeridos para SIN SEÑAL:
1) Verifica que el router esté encendido y con LEDs normales.
2) Revisa que el proveedor de Internet no tenga incidencia en tu zona.
3) Apaga/enciende el router (30–60 segundos).
4) Prueba otra red (hotspot) para descartar tu equipo.
Si sigue igual, lo escalaremos a un técnico.").

solucion(caida_de_red,
"Pasos sugeridos para CAÍDA DE RED:
1) Revisa si otros dispositivos también pierden conexión.
2) Revisa cables y ONT (fibra) o módem (coaxial).
3) Reinicia el router/ONT.
4) Si la caída es intermitente, toma hora aproximada de ocurrencias.
Si continúa, lo escalaremos con prioridad.").

solucion(wifi_no_conecta,
"Pasos sugeridos para WIFI NO CONECTA:
1) Olvida la red y vuelve a ingresar la contraseña.
2) Cambia la banda: prueba 2.4 GHz y 5 GHz.
3) Verifica que el filtro MAC no esté activo.
4) Acércate al router y prueba otro dispositivo.
Si no conecta, lo escalaremos a un técnico.").

solucion(login,
"Pasos sugeridos para LOGIN:
1) Comprueba usuario/contraseña (bloq mayús).
2) Intenta restablecer clave desde 'Olvidé mi contraseña'.
3) Verifica hora/fecha del sistema.
4) Limpia caché/cookies o navega en modo incógnito.").

solucion(email,
"Pasos sugeridos para CORREO:
1) Verifica conexión y credenciales.
2) Revisa cuota de buzón y carpeta SPAM.
3) Revisa puertos/SSL del cliente (IMAP/SMTP).
4) Prueba desde la web del proveedor (webmail).").

solucion(impresora,
"Pasos sugeridos para IMPRESORA:
1) Asegúrate de que la impresora esté encendida y conectada.
2) Instala/actualiza drivers.
3) Configura como impresora predeterminada.
4) Revisa papel/atascos y nivel de tinta/toner.").

solucion(desconocido,
"No tengo una solución inmediata. Escalaré tu caso a un técnico.").

% --- Clasificación por palabras clave (búsqueda en minúsculas) ---
tiene(Palabra, Texto) :- sub_string(Texto, _, _, _, Palabra).

clasificar(Texto, conexion_lenta)  :- tiene("lenta", Texto);  tiene("conexión lenta", Texto).
clasificar(Texto, sin_senal)       :- tiene("sin señal", Texto); tiene("no hay señal", Texto).
clasificar(Texto, caida_de_red)    :- tiene("caída de red", Texto); tiene("se cae", Texto); tiene("se corta", Texto).
clasificar(Texto, wifi_no_conecta) :- tiene("wifi no conecta", Texto); tiene("no conecta", Texto), tiene("wifi", Texto).
clasificar(Texto, login)           :- tiene("login", Texto); tiene("iniciar sesión", Texto); tiene("contraseña", Texto).
clasificar(Texto, email)           :- tiene("correo", Texto); tiene("email", Texto); tiene("imap", Texto); tiene("smtp", Texto).
clasificar(Texto, impresora)       :- tiene("impresora", Texto); tiene("printer", Texto).

% --- Mensaje de cierre detectado ---
mensaje_resuelto(Texto) :-
    tiene("ya funciona", Texto);
    tiene("solucionado", Texto);
    tiene("se soluciono", Texto);
    tiene("se solucionó", Texto);
    tiene("listo", Texto);
    tiene("gracias, ya", Texto).

/* API principal
   - Si detecta que el usuario dice que ya funciona → mensaje de cierre.
   - Si detecta categoría → devuelve solución.
   - Caso contrario → escalar.
*/
responder(Texto, R) :-
    string_lower(Texto, T),
    (   mensaje_resuelto(T)
    ->  R = "¡Excelente! Me alegra que se haya solucionado. Procederé a cerrar el ticket."
    ;   (   clasificar(T, Tipo) -> solucion(Tipo, R)
        ;   solucion(desconocido, R)
        )
    ).
