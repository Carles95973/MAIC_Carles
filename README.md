# MAIC · Materiales de clase 🎓

¡Hola! 👋 Este repositorio reúne el código y los ejemplos de mis módulos del
**Máster en Inteligencia Artificial para la Construcción (MAIC) de Zigurat**.

La idea es sencilla: que tengáis a mano proyectos **reales y ejecutables** para
trastear, romper y aprender. Nada de teoría suelta — aquí todo se puede abrir,
correr y modificar.

> 💡 Cada carpeta es autocontenida y tiene su propio `README` con instrucciones.
> Empieza siempre por ahí.

---

## 📚 Contenido

| Módulo | Qué encontrarás | Estado |
|--------|-----------------|--------|
| [`M8T1`](./M8T1) · Gestión de Tecnología y Estrategias Digitales | Asistente documental para una constructora: un **PoC** (mockup navegable) y un **PoT** (RAG real con Docling + pgvector + LangGraph) | ✅ Disponible |
| _Próximos módulos_ | Más material en camino | 🚧 Por subir |

### M8T1 de un vistazo

- **[PoC](./M8T1/PoC)** — Prueba de concepto. Un mockup web (`index.html`) que
  se abre en el navegador sin instalar nada. Sirve para validar si la idea
  *merece la pena* antes de programar.
  👉 [Versión online](https://carles95973.github.io/MAIC_Carles/)
- **[PoT](./M8T1/PoT)** — Prueba de tecnología. Aquí ya hay código de verdad:
  parseo de documentos, embeddings, recuperación y generación con detección de
  contradicciones. Incluye notebooks para seguir las fases paso a paso.

---

## 🚀 Cómo empezar

1. Clona el repo.
2. Entra en la carpeta del módulo que te interese.
3. Lee su `README` y sigue el setup.

Para el **PoC** no necesitas nada (solo un navegador). Para el **PoT** necesitas
Python 3.11+, Poetry y una API key de OpenAI — todo está explicado en su
[`SETUP.md`](./M8T1/PoT/SETUP.md).

---

## ⚠️ Aviso

Es material **didáctico**: prioriza la claridad sobre la robustez de producción.
Si algo no funciona, no os agobiéis — forma parte del aprendizaje. Cualquier duda
o mejora, abrid un *issue* o comentádmelo en clase.

¡Que lo disfrutéis! 🍌
