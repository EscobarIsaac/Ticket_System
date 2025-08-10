% -*- mode: prolog -*-
:- encoding(utf8).

% ===== Conocimiento: soluciones y si se resuelven automáticamente =====
solucion(problema_sin_senal,       'Revisa que el módem/ONT esté encendido y los cables firmes. Apaga y enciende el router 30s. Prueba otro dispositivo o puerto LAN.').
resuelve(problema_sin_senal,       auto).

solucion(problema_conexion_lenta,  'Reinicia el router, cierra descargas/streaming, prueba con cable de red y verifica la velocidad con un test.').
resuelve(problema_conexion_lenta,  auto).

solucion(problema_wifi_no_conecta, 'Olvida la red Wi-Fi y vuelve a conectarte, verifica la contraseña, acércate al router y reinicia ambos equipos.').
resuelve(problema_wifi_no_conecta, auto).

solucion(problema_caida_red,       'Parece una caída del servicio en tu zona o tu línea. Necesita revisión de un técnico.').
resuelve(problema_caida_red,       escalar).

solucion(problema_otro,            'No puedo identificar el problema con precisión ahora.').
resuelve(problema_otro,            escalar).

% ===== Clasificación simple por palabras clave (case-insensitive) =====
clase(T, problema_sin_senal)       :- contiene(T, 'sin señal'); contiene(T,'no tengo señal'); contiene(T,'sin senal').
clase(T, problema_conexion_lenta)  :- contiene(T, 'lenta'); contiene(T,'conexión lenta'); contiene(T,'conexion lenta'); contiene(T,'se cae internet').
clase(T, problema_wifi_no_conecta) :- contiene(T, 'wifi no conecta'); contiene(T,'no conecta'); contiene(T,'contraseña wifi'); contiene(T,'clave wifi').
clase(T, problema_caida_red)       :- contiene(T, 'caída de red'); contiene(T,'caida de red'); contiene(T,'sin servicio'); contiene(T,'se cayó la red').
clase(_, problema_otro).

contiene(Texto, Patron) :-
    downcase_atom(Texto, T),
    downcase_atom(Patron, P),
    sub_string(T, _, _, _, P).

% ===== API principal =====
% responder(+Texto,-Estado,-Respuesta).
% Estado = auto | escalar
responder(Texto, Estado, Respuesta) :-
    clase(Texto, Clase),
    solucion(Clase, Respuesta),
    resuelve(Clase, Estado).
