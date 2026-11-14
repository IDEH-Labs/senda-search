# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Ethical Public Health Knowledge Engine.

Provides instant, transparent, and advertising-free public health cards
grounded in official international guidance from the World Health Organization (WHO/OMS)
and MedlinePlus (U.S. National Library of Medicine).

Zero tracking, zero pharmaceutical commercialization, strictly verified evidence.
"""

from __future__ import annotations

import unicodedata
from typing import Dict, List, Optional
from pydantic import BaseModel

from senda.ranking.suggestions import damerau_levenshtein_distance


class HealthCard(BaseModel):
    """Structured verifiable public health card."""
    title: str
    category: str
    summary: str
    symptoms: List[str]
    prevention: List[str]
    when_to_seek_care: str
    source: str
    source_url: str
    license: str = "Información pública de acceso libre y universal"
    disclaimer: str = (
        "Aviso ético de salud pública: Esta información proviene de organismos oficiales internacionales "
        "con fines educativos. No sustituye la consulta médica presencial ni el diagnóstico de un profesional de la salud."
    )


def _norm(s: str) -> str:
    """Normalize string removing accents, punctuation and excess whitespace."""
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s


# Authoritative Public Health Knowledge Base grounded in WHO/OMS & MedlinePlus
HEALTH_CONDITIONS: Dict[str, HealthCard] = {
    "dengue": HealthCard(
        title="Dengue",
        category="Enfermedad viral transmitida por mosquitos (Aedes aegypti)",
        summary=(
            "Infección vírica transmitida a las personas por la picadura de mosquitos hembra infectados. "
            "Es común en climas tropicales y subtropicales. La prevención principal radica en evitar la reproducción del mosquito vector."
        ),
        symptoms=[
            "Fiebre alta repentina (40 °C / 104 °F)",
            "Dolor de cabeza intenso y dolor detrás de los ojos",
            "Dolores musculares y articulares intensos («fiebre rompehuesos»)",
            "Náuseas, vómitos y sarpullido cutáneo",
        ],
        prevention=[
            "Eliminar recipientes con agua estancada (llantas, floreros, baldes)",
            "Uso de repelentes contra insectos autorizados",
            "Instalación de mosquiteros en ventanas y camas",
            "Vestir prendas de manga larga y colores claros",
        ],
        when_to_seek_care=(
            "Acudir urgentemente al centro de salud si se presentan signos de alarma: "
            "dolor abdominal intenso y continuo, vómitos persistentes, sangrado de encías o nariz, y fatiga extrema."
        ),
        source="Organización Mundial de la Salud (OMS)",
        source_url="https://www.who.int/es/news-room/fact-sheets/detail/dengue-and-severe-dengue",
    ),
    "diabetes": HealthCard(
        title="Diabetes Mellitus",
        category="Enfermedad metabólica crónica",
        summary=(
            "Afección crónica caracterizada por niveles elevados de glucosa en sangre debido a que el páncreas "
            "no produce suficiente insulina o el organismo no la utiliza eficazmente. La diabetes tipo 2 es la más común y prevenible."
        ),
        symptoms=[
            "Sed excesiva (polidipsia) y aumento de micción (poliuria)",
            "Hambre constante y pérdida de peso involuntaria",
            "Fatiga y visión borrosa",
            "Cicatrización lenta de heridas e infecciones recurrentes",
        ],
        prevention=[
            "Mantener un peso corporal saludable y alimentación equilibrada",
            "Realizar al menos 30 minutos de actividad física diaria moderada",
            "Reducir el consumo de azúcares libres y alimentos ultraprocesados",
            "Evitar el consumo de tabaco",
        ],
        when_to_seek_care=(
            "Consulte a su médico de atención primaria para un control glucémico periódico en ayunas. "
            "Buscar atención urgente ante confusión, dificultad para respirar o aliento con olor frutal (cetoacidosis)."
        ),
        source="Organización Mundial de la Salud (OMS)",
        source_url="https://www.who.int/es/news-room/fact-sheets/detail/diabetes",
    ),
    "hipertension": HealthCard(
        title="Hipertensión Arterial",
        category="Enfermedad cardiovascular crónica",
        summary=(
            "Trastorno en el que los vasos sanguíneos tienen una tensión persistentemente alta (≥ 140/90 mmHg). "
            "Se la denomina «asesina silenciosa» porque a menudo no causa síntomas tempranos, pero incrementa el riesgo de infarto y accidente cerebrovascular."
        ),
        symptoms=[
            "En la mayoría de casos es asintomática",
            "En fases avanzadas: cefaleas matutinas, hemorragias nasales",
            "Zumbido en los oídos (acúfenos) y palpitaciones",
            "Dificultad para respirar y mareos",
        ],
        prevention=[
            "Reducir el consumo de sal a menos de 5 gramos diarios",
            "Dieta rica en frutas, verduras y legumbres",
            "Evitar el sedentarismo y realizar ejercicio aeróbico regular",
            "Limitar el consumo de alcohol y abandonar el tabaco",
        ],
        when_to_seek_care=(
            "Medirse la presión arterial con regularidad en centros de salud autorizados. "
            "Buscar urgencias inmediatamente ante dolor torácico opresivo, dificultad respiratoria súbita o dolor de cabeza severo e inusual."
        ),
        source="Organización Mundial de la Salud (OMS)",
        source_url="https://www.who.int/es/news-room/fact-sheets/detail/hypertension",
    ),
    "asma": HealthCard(
        title="Asma Bronquial",
        category="Enfermedad respiratoria crónica",
        summary=(
            "Afección pulmonar no transmisible caracterizada por la inflamación y estrechamiento recurrente de las vías respiratorias. "
            "Afecta tanto a niños como a adultos y puede controlarse eficazmente con medicación inhalada adecuada."
        ),
        symptoms=[
            "Sibilancias o silbidos al exhalar el aire",
            "Tos recurrente, en particular de noche o temprano en la mañana",
            "Dificultad para respirar (disnea)",
            "Sensación de opresión en el pecho",
        ],
        prevention=[
            "Evitar desencadenantes conocidos: humo de tabaco, ácaros del polvo, polen y moho",
            "Uso regular y correcto del inhalador de control prescrito",
            "Vacunación anual contra la gripe y neumococo",
            "Mantener ventilados los espacios cerrados",
        ],
        when_to_seek_care=(
            "Acudir a urgencias inmediatamente ante un ataque de asma que no cede con el inhalador de rescate, "
            "dificultad severa para hablar o coloración azulada en labios o uñas."
        ),
        source="MedlinePlus / OMS",
        source_url="https://medlineplus.gov/spanish/asthma.html",
    ),
    "depresion": HealthCard(
        title="Trastorno Depresivo",
        category="Salud mental y bienestar psicológico",
        summary=(
            "Trastorno del estado de ánimo caracterizado por una tristeza persistente y pérdida de interés en las actividades cotidianas. "
            "No es un signo de debilidad y es tratable mediante apoyo psicológico, psicoterapia y atención médica especializada."
        ),
        symptoms=[
            "Sensación persistente de tristeza, vacío o desesperanza",
            "Pérdida de placer en actividades que antes disfrutaba",
            "Alteraciones del sueño (insomnio o exceso de sueño)",
            "Fatiga o falta constante de energía",
            "Dificultad para concentrarse o tomar decisiones",
        ],
        prevention=[
            "Mantener redes de apoyo social y comunicación con seres queridos",
            "Establecer rutinas de sueño regulares y ejercicio físico",
            "Evitar el aislamiento y el consumo de alcohol como automedicación",
            "Pedir ayuda profesional temprana sin estigma",
        ],
        when_to_seek_care=(
            "Consulte con un profesional de psicología o psiquiatría. "
            "Si usted o alguien conocido tiene pensamientos de autolesión o suicidio, comuníquese de inmediato con las líneas telefónicas gratuitas de apoyo emocional de su país o acuda a urgencias."
        ),
        source="Organización Mundial de la Salud (OMS)",
        source_url="https://www.who.int/es/news-room/fact-sheets/detail/depression",
    ),
    "malaria": HealthCard(
        title="Malaria (Paludismo)",
        category="Enfermedad parasitaria transmitida por mosquitos (Anopheles)",
        summary=(
            "Enfermedad potencialmente mortal causada por parásitos del género Plasmodium que se transmiten al ser humano "
            "a través de la picadura de mosquitos hembra infectados. Es prevenible y curable si se detecta a tiempo."
        ),
        symptoms=[
            "Fiebre alta, escalofríos intensos y temblores",
            "Dolor de cabeza intenso y sudores profusos",
            "Fatiga extrema, náuseas y vómitos",
            "Dolores musculares",
        ],
        prevention=[
            "Dormir bajo mosquiteros tratados con insecticida de acción prolongada",
            "Fumigación de interiores con insecticidas de acción residual",
            "Medicamentos profilácticos antes y durante viajes a zonas endémicas",
        ],
        when_to_seek_care=(
            "Buscar atención médica de inmediato para realizar una prueba de diagnóstico rápido o gota gruesa ante fiebre persistente tras viajar a zonas de riesgo."
        ),
        source="Organización Mundial de la Salud (OMS)",
        source_url="https://www.who.int/es/news-room/fact-sheets/detail/malaria",
    ),
    "tuberculosis": HealthCard(
        title="Tuberculosis (TB)",
        category="Enfermedad bacteriana infecciosa (Mycobacterium tuberculosis)",
        summary=(
            "Infección bacteriana que suele afectar a los pulmones y se transmite por el aire cuando una persona infectada tose o estornuda. "
            "Con un tratamiento antibiótico completo y supervisado, la gran mayoría de casos se curan."
        ),
        symptoms=[
            "Tos persistente que dura más de dos semanas (a veces con flema o sangre)",
            "Dolor en el pecho",
            "Pérdida de peso involuntaria y falta de apetito",
            "Fiebre y sudores nocturnos",
        ],
        prevention=[
            "Vacunación con BCG al nacer en zonas de riesgo",
            "Ventilación adecuada y luz solar en espacios cerrados",
            "Completar estrictamente todo el tratamiento antibiótico prescrito para evitar multirresistencia",
        ],
        when_to_seek_care=(
            "Acudir a un centro de salud para baciloscopia o prueba molecular ante tos con flema de más de 15 días."
        ),
        source="Organización Mundial de la Salud (OMS)",
        source_url="https://www.who.int/es/news-room/fact-sheets/detail/tuberculosis",
    ),
    "covid": HealthCard(
        title="COVID-19",
        category="Enfermedad respiratoria viral (SARS-CoV-2)",
        summary=(
            "Enfermedad respiratoria infecciosa causada por el coronavirus SARS-CoV-2. "
            "La mayoría de las personas infectadas experimentan síntomas leves a moderados, pero los adultos mayores y personas con comorbilidades tienen mayor riesgo de gravedad."
        ),
        symptoms=[
            "Fiebre, escalofríos y tos seca",
            "Fatiga general y dolores musculares",
            "Pérdida del gusto o del olfato",
            "Dolor de garganta, congestión nasal o dolor de cabeza",
        ],
        prevention=[
            "Esquemas de vacunación y dosis de refuerzo actualizadas",
            "Ventilación adecuada de espacios cerrados",
            "Lavado frecuente de manos con agua y jabón",
            "Uso de mascarilla ante síntomas respiratorios",
        ],
        when_to_seek_care=(
            "Buscar atención médica inmediata ante dificultad para respirar, dolor persistente o presión en el pecho, o confusión súbita."
        ),
        source="Organización Mundial de la Salud (OMS)",
        source_url="https://www.who.int/es/health-topics/coronavirus",
    ),
    "anemia": HealthCard(
        title="Anemia",
        category="Trastorno hematológico",
        summary=(
            "Afección en la que el número de glóbulos rojos o la concentración de hemoglobina en ellos es inferior a lo normal, "
            "disminuyendo la capacidad de la sangre para transportar oxígeno a los tejidos. La causa más frecuente es la deficiencia de hierro."
        ),
        symptoms=[
            "Fatiga extrema y debilidad continua",
            "Palidez en la piel, encías y lecho ungueal",
            "Mareos, aturdimiento y manos y pies fríos",
            "Dificultad para respirar al realizar esfuerzos leves",
        ],
        prevention=[
            "Consumo de alimentos ricos en hierro: legumbres, espinacas, carnes magras",
            "Acompañar fuentes de hierro vegetal con vitamina C (cítricos) para mejorar absorción",
            "Suplementación de hierro según prescripción médica en embarazadas y lactantes",
        ],
        when_to_seek_care=(
            "Consulte a su médico para un hemograma completo si experimenta cansancio inexplicable continuo o mareos frecuentes."
        ),
        source="MedlinePlus / OMS",
        source_url="https://medlineplus.gov/spanish/anemia.html",
    ),
    "gripe": HealthCard(
        title="Gripe (Influenza)",
        category="Infección respiratoria viral estacional",
        summary=(
            "Infección vírica aguda causada por virus de la influenza que se transmite con facilidad de persona a persona al toser o estornudar. "
            "A diferencia del resfriado común, el inicio de los síntomas suele ser súbito y con fiebre más alta."
        ),
        symptoms=[
            "Fiebre alta de inicio repentino",
            "Dolores musculares y articulares generalizados",
            "Dolor de cabeza intenso y dolor de garganta",
            "Tos seca y malestar general acusado",
        ],
        prevention=[
            "Vacunación antigripal anual, especialmente en grupos de riesgo",
            "Lavarse las manos frecuentemente con agua y jabón",
            "Cubrirse la boca y nariz con el codo flexionado al toser",
            "Evitar el contacto cercano con personas enfermas",
        ],
        when_to_seek_care=(
            "Consultar al médico ante dificultad para respirar, dolor torácico, fiebre que no baja tras tres días o empeoramiento súbito tras una mejoría."
        ),
        source="Organización Mundial de la Salud (OMS)",
        source_url="https://www.who.int/es/news-room/fact-sheets/detail/influenza-(seasonal)",
    ),
}

# Synonyms and alias mapping for query resolution
HEALTH_ALIASES: Dict[str, str] = {
    "dengue": "dengue",
    "fiebre del dengue": "dengue",
    "dengue hemorragico": "dengue",
    "diabetes": "diabetes",
    "diabetes mellitus": "diabetes",
    "diabetes tipo 2": "diabetes",
    "diabetes tipo 1": "diabetes",
    "azucar en sangre": "diabetes",
    "glucosa alta": "diabetes",
    "hipertension": "hipertension",
    "hipertension arterial": "hipertension",
    "presion alta": "hipertension",
    "tension alta": "hipertension",
    "presion arterial alta": "hipertension",
    "asma": "asma",
    "asma bronquial": "asma",
    "ataque de asma": "asma",
    "depresion": "depresion",
    "trastorno depresivo": "depresion",
    "depresion mayor": "depresion",
    "tristeza constante": "depresion",
    "malaria": "malaria",
    "paludismo": "malaria",
    "tuberculosis": "tuberculosis",
    "tisis": "tuberculosis",
    "tos con sangre": "tuberculosis",
    "covid": "covid",
    "covid 19": "covid",
    "covid-19": "covid",
    "coronavirus": "covid",
    "sars cov 2": "covid",
    "anemia": "anemia",
    "falta de hierro": "anemia",
    "deficiencia de hierro": "anemia",
    "gripe": "gripe",
    "influenza": "gripe",
    "gripe estacional": "gripe",
}


def evaluate_health_query(query: str) -> Optional[HealthCard]:
    """
    Evaluate if a user query corresponds to an authoritative public health condition.
    Supports exact matching, alias lookup, and typo-tolerance (edit distance <= 1 or 2).
    Deterministic, offline, zero-tracking.
    """
    clean_q = _norm(query)
    if not clean_q or len(clean_q) < 3:
        return None

    # 1. Exact alias match
    if clean_q in HEALTH_ALIASES:
        canonical_key = HEALTH_ALIASES[clean_q]
        return HEALTH_CONDITIONS.get(canonical_key)

    # 2. Check if query contains or matches key health terms
    for alias, canonical_key in HEALTH_ALIASES.items():
        if alias == clean_q or f" {alias} " in f" {clean_q} ":
            return HEALTH_CONDITIONS.get(canonical_key)

    # 3. Typo-tolerance check (Damerau-Levenshtein distance <= 1 or 2)
    max_d = 1 if len(clean_q) < 7 else 2
    best_match: Optional[str] = None
    best_dist = 999

    for alias, canonical_key in HEALTH_ALIASES.items():
        if abs(len(alias) - len(clean_q)) <= max_d:
            dist = damerau_levenshtein_distance(clean_q, alias)
            if dist <= max_d and dist < best_dist:
                best_dist = dist
                best_match = canonical_key
                if dist == 1:
                    break

    if best_match:
        return HEALTH_CONDITIONS.get(best_match)

    return None
