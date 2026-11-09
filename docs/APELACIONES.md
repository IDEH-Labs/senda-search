# Senda — Procedimiento de Apelaciones y Rectificaciones

**Versión:** 1.0.0  
**Licencia:** GPL-3.0-or-later  
**Ámbito:** Apelaciones contra bloqueos técnicos duros y rectificaciones de metadatos/etiquetas de fuentes.  
**Contacto de gobernanza:** <governance@ideh.top>  

---

## 1. Objeto y Alcance

Este documento establece el mecanismo formal, transparente y auditable mediante el cual cualquier operador de un sitio web, investigador, periodista o usuario final puede:
1. **Apelar un bloqueo técnico duro** aplicado por el crawler o el despachador de Senda (por ejemplo, ante una sospecha de falso positivo en listas de malware o phishing).
2. **Solicitar la corrección o actualización de metadatos** exhibidos en el panel de evidencia "¿Por qué veo esto?" (por ejemplo, propiedad, política de correcciones, autoría, retractaciones).

---

## 2. Tipos de Solicitudes y Plazos de Respuesta (SLA)

| Tipo de Solicitud | Causal | Tiempo Máximo de Respuesta Inicial | Tiempo Máximo de Resolución |
| :--- | :--- | :--- | :--- |
| **Apelación de Bloqueo Duro (Urgente)** | Alegato de falso positivo en lista de amenazas (malware/phishing/fraude). | 24 horas hábiles | 72 horas hábiles |
| **Rectificación de Metadatos de Fuente** | Actualización de propiedad, autoría, política de correcciones o retractación subsanada. | 5 días hábiles | 10 días hábiles |
| **Solicitud de Desindexación por Privacidad** | Petición fundamentada en derechos ARCO / Ley 1581 de 2012 / RGPD respecto a datos sensibles indexados de la web pública. | 48 horas hábiles | 5 días hábiles |

---

## 3. Procedimiento para Apelar un Bloqueo Técnico Duro

Si un dominio ha sido excluido de los resultados debido a una coincidencia técnica en feeds de amenazas (URLhaus, feeds de anti-phishing, etc.) y el titular considera que se trata de un falso positivo o que el incidente de seguridad ha sido completamente remediado:

### Paso 1: Verificación Técnica Previa
Antes de someter la apelación, el operador del sitio debe:
- Verificar que el servidor no aloje binarios maliciosos, scripts ofuscados de inyección o pasarelas de pago no autenticadas.
- Comprobar el estado del dominio en los feeds de origen (ejemplo: si el reporte proviene de URLhaus de abuse.ch, verificar el estado en `https://urlhaus.abuse.ch/`).

### Paso 2: Envío de la Apelación
Remitir una solicitud por correo electrónico a `governance@ideh.top` o mediante un issue en el rastreador público del proyecto con el asunto:  
`[APELACIÓN-SEGURIDAD] Dominio: ejemplo.org`

La solicitud debe contener:
1. URL o dominio afectado.
2. Identificador del incidente o reporte previo (si fue notificado).
3. Informe técnico de remediación (medidas adoptadas para erradicar la vulnerabilidad).
4. Informe de escaneo limpio reciente (enlaces a análisis de herramientas de seguridad independientes).

### Paso 3: Revisión Técnica Independiente
El equipo de seguridad de Senda:
1. Realiza una comprobación en un entorno aislado sin ejecución de navegador cliente.
2. Si la remediación es verificada y el dominio ya no figura como activo en el feed de origen o se demostró un falso positivo, se retira la exclusión técnica y se actualiza la caché de seguridad.
3. Se publica la resolución en el registro público de auditoría de bloqueos y apelaciones.

---

## 4. Procedimiento para Rectificación de Metadatos de la Rúbrica

Si un medio o autor identifica que los datos presentados en el panel "¿Por qué veo esto?" contienen errores fácticos o están desactualizados:

1. Remitir solicitud a `governance@ideh.top` con el asunto:  
   `[RECTIFICACIÓN-RÚBRICA] Dominio: ejemplo.org`
2. Adjuntar la evidencia auditable exigida en [docs/RUBRICA_FUENTES.md](file:///home/Familia/Proyectos/senda-search/docs/RUBRICA_FUENTES.md) (enlace a sección de transparencia, marcado Schema.org actualizado, registro de retractación corregido, etc.).
3. El equipo técnico verificará la evidencia directamente en el dominio origen. Una vez validada, el extractor semántico refrescará los metadatos almacenados en la base de datos de fuentes.

---

## 5. Registro Público de Transparencia

Para evitar cualquier sospecha de acuerdos privados o favoritismos comerciales:
- Todas las resoluciones de apelación por bloqueo duro y rectificaciones de la rúbrica se consolidan en un registro de auditoría trimestral accesible en el repositorio del proyecto.
- Nunca se cobran tarifas, cargos administrativos ni contribuciones económicas por procesar apelaciones o rectificaciones. El proceso es 100% gratuito y de acceso público universal.
