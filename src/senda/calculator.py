# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Senda Sovereign Instant Calculator
Zero-telemetry, sandboxed, deterministic mathematical evaluator.
Evaluates natural language arithmetic and expressions using Python's AST parser.
Strictly non-evaluating (never uses eval/exec) to guarantee zero security risk.
"""

from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel


class CalculatorResult(BaseModel):
    """Structured representation of an evaluated mathematical expression."""
    display_expr: str
    formatted_result: str
    raw_result: float | int | str
    is_error: bool = False


class SafeEvaluator(ast.NodeVisitor):
    """AST visitor executing only whitelisted arithmetic nodes."""

    MAX_POWER = 1000

    ALLOWED_FUNCS = {
        "sqrt": math.sqrt,
        "raiz": math.sqrt,
        "raíz": math.sqrt,
        "abs": abs,
        "round": round,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "ceil": math.ceil,
        "floor": math.floor,
    }

    ALLOWED_CONSTS = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
    }

    def visit(self, node: ast.AST) -> Any:
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Nodo no permitido: {type(node).__name__}")

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Solo se admiten valores numéricos")

    def visit_Name(self, node: ast.Name) -> Any:
        name = node.id.lower()
        if name in self.ALLOWED_CONSTS:
            return self.ALLOWED_CONSTS[name]
        raise ValueError(f"Constante desconocida: {node.id}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        val = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +val
        if isinstance(node.op, ast.USub):
            return -val
        raise ValueError("Operador unario no admitido")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("División por cero")
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise ZeroDivisionError("División entera por cero")
            return left // right
        if isinstance(node.op, ast.Mod):
            if right == 0:
                raise ZeroDivisionError("Módulo por cero")
            return left % right
        if isinstance(node.op, ast.Pow):
            if abs(right) > self.MAX_POWER:
                raise ValueError("Exponente excesivo para cálculo seguro")
            return left ** right

        raise ValueError("Operador binario no admitido")

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Llamada no válida")
        fname = node.func.id.lower()
        if fname not in self.ALLOWED_FUNCS:
            raise ValueError(f"Función no admitida: {fname}")
        args = [self.visit(arg) for arg in node.args]
        return self.ALLOWED_FUNCS[fname](*args)


def parse_number_str(s: str) -> Optional[float]:
    """Parse number strings handling currency symbols, spaces, and international decimal/thousands separators."""
    if not s:
        return None
    cleaned = s.strip()
    # Strip common currency symbols and codes
    cleaned = re.sub(r"^[\$€£¥₹₽\s]+|[\$€£¥₹₽\s]+$", "", cleaned).strip()
    cleaned = re.sub(r"^(?:cop|usd|eur|gbp|mxn|ars|clp)\s+|\s+(?:cop|usd|eur|gbp|mxn|ars|clp)$", "", cleaned, flags=re.I).strip()
    # Spaces as thousands separators: 22 000 000 -> 22000000
    cleaned = re.sub(r"(?<=\d)\s+(?=\d{3}\b)", "", cleaned)

    # Both dot and comma present:
    if "." in cleaned and "," in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            # Spanish / European: 1.234.567,89 -> remove dots, replace comma with dot
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # Anglo: 1,234,567.89 -> remove commas
            cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None

    # Multiple dots: definitely thousands separators (e.g. 22.000.000)
    if cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return None

    # Multiple commas: definitely thousands separators (e.g. 22,000,000)
    if cleaned.count(",") > 1:
        cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None

    # Single comma:
    if "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) != 3:
            # e.g. 2,5 or 0,05 or 12,34 -> decimal
            cleaned = cleaned.replace(",", ".")
        elif len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) <= 3:
            # e.g. 22,000 or 1,000 -> thousands
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    # Single dot:
    if "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) <= 3 and parts[1] == "000":
            # e.g. 22.000 or 1.000 (three zeros) -> thousands in Spanish
            cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def format_number(val: Any) -> str:
    """Format numeric result cleanly for human presentation."""
    if isinstance(val, (int, float)):
        if math.isinf(val):
            return "Infinito"
        if math.isnan(val):
            return "Indefinido"
        if abs(val) >= 1e14 or (0 < abs(val) < 1e-6):
            return f"{val:.6e}"
        if isinstance(val, float) and val.is_integer():
            return f"{int(val):,}"
        if isinstance(val, int):
            return f"{val:,}"
        rounded = round(val, 8)
        if rounded.is_integer():
            return f"{int(rounded):,}"
        return f"{rounded:g}"
    return str(val)


def evaluate_math_query(query: str) -> Optional[CalculatorResult]:
    """
    Examine search query for arithmetic or mathematical intent.
    Returns CalculatorResult if valid mathematical expression, or None.
    """
    if not query:
        return None
    raw = query.strip()
    if len(raw) > 128:
        return None

    # Strip conversational prefixes in Spanish and English
    expr = re.sub(
        r"^(cu[aá]nto\s+(?:es|ser[ií]a|da)|cu[aá]l\s+es|qu[eé]\s+es|calcular?|calcula|calcule|calculate|calc|resolver?|resuelve|solve|what\s+is|how\s+much\s+is)\s+",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip()
    # Strip optional leading article before percentages or numbers: e.g. "el 2.5% de..." -> "2.5% de..."
    expr = re.sub(r"^(?:el|la|the)\s+", "", expr, flags=re.IGNORECASE).strip()
    # Strip trailing punctuation
    expr = re.sub(r"[=?¿\s]+$", "", expr).strip()
    if not expr:
        return None

    # Normalize percentage wording: "por ciento", "porciento", "percent", "pct" -> "%"
    expr = re.sub(r"\s*(?:%|por\s*ciento|porciento|percent|pct)\b", "%", expr, flags=re.IGNORECASE)

    # Pattern: X% de Y / X% of Y
    pct_of = re.match(
        r"^([\d.,\s]+)%\s*(?:de|of)\s*([\$\€\£\¥\₹\₽\s]*[\d.,\s]+(?:cop|usd|eur|gbp|mxn|ars|clp)?)$",
        expr,
        flags=re.IGNORECASE,
    )
    if pct_of:
        p = parse_number_str(pct_of.group(1))
        b = parse_number_str(pct_of.group(2))
        if p is not None and b is not None:
            res = (p / 100.0) * b
            b_clean = pct_of.group(2).strip()
            p_clean = pct_of.group(1).strip()
            return CalculatorResult(
                display_expr=f"{p_clean}% de {b_clean}",
                formatted_result=format_number(res),
                raw_result=res,
            )

    # Pattern: Base + X% or Base - X% (including "mas", "menos", optional "iva")
    pct_add = re.match(
        r"^([\$\€\£\¥\₹\₽\s]*[\d.,\s]+(?:cop|usd|eur|gbp|mxn|ars|clp)?)\s*([+\-]|m[aá]s|menos)\s*([\d.,\s]+)%\s*(?:iva)?$",
        expr,
        flags=re.IGNORECASE,
    )
    if pct_add:
        base = parse_number_str(pct_add.group(1))
        raw_op = pct_add.group(2).lower()
        op = "+" if raw_op in ("+", "mas", "más") else "-"
        pct = parse_number_str(pct_add.group(3))
        if base is not None and pct is not None:
            diff = base * (pct / 100.0)
            res = base + diff if op == "+" else base - diff
            return CalculatorResult(
                display_expr=f"{pct_add.group(1).strip()} {op} {pct_add.group(3).strip()}%",
                formatted_result=format_number(res),
                raw_result=res,
            )

    # Pattern: "qué porcentaje es X de Y" / "what percentage is X of Y"
    pct_what = re.match(
        r"^(?:qu[eé]\s+porcentaje\s+es|what\s+(?:percentage|percent)\s+is)\s+([\d.,\s]+)\s+(?:de|of)\s+([\d.,\s]+)$",
        expr,
        flags=re.IGNORECASE,
    )
    if pct_what:
        part = parse_number_str(pct_what.group(1))
        whole = parse_number_str(pct_what.group(2))
        if part is not None and whole is not None:
            if whole == 0:
                return CalculatorResult(
                    display_expr=f"{pct_what.group(1).strip()} de {pct_what.group(2).strip()}",
                    formatted_result="Indefinido (división por cero)",
                    raw_result="ZeroDivisionError",
                    is_error=True,
                )
            res = (part / whole) * 100.0
            return CalculatorResult(
                display_expr=f"{pct_what.group(1).strip()} de {pct_what.group(2).strip()}",
                formatted_result=f"{format_number(res)}%",
                raw_result=res,
            )

    # Normalize mathematical symbols and numbers with thousands/decimals
    norm = expr
    norm = re.sub(r"[\$€£¥₹₽]", "", norm)
    # Spaces between digits (thousands): 22 000 000 -> 22000000
    norm = re.sub(r"(?<=\d)\s+(?=\d{3}\b)", "", norm)
    # Thousands dots: 22.000.000 -> 22000000
    norm = re.sub(r"\b(\d{1,3}(?:\.\d{3})+)\b", lambda m: m.group(1).replace(".", ""), norm)
    # Thousands commas: 22,000,000 -> 22000000
    norm = re.sub(r"\b(\d{1,3}(?:,\d{3})+)\b", lambda m: m.group(1).replace(",", ""), norm)
    # Decimal comma: 2,5 -> 2.5
    norm = re.sub(r"(?<=\d),(?=\d)", ".", norm)

    norm = norm.replace("×", "*").replace("·", "*").replace("÷", "/")
    norm = re.sub(r"(\d)\s*[xX]\s*(\d)", r"\1 * \2", norm)
    norm = norm.replace("^", "**")
    norm = norm.replace("π", "pi")
    norm = re.sub(r"\braiz\b|\braíz\b", "sqrt", norm, flags=re.IGNORECASE)

    # Ensure there is an operator or known math function
    has_operator = bool(
        re.search(
            r"[+\-*/%]|(\*\*)|\b(sqrt|raiz|raíz|abs|round|ceil|floor|sin|cos|tan|log|log10|log2|pi|e|tau)\b",
            norm,
        )
    )
    if not has_operator:
        return None

    # Whitelist characters allowed in normalized expression
    if not re.match(r"^[0-9\s.+\-*/%(),a-zA-Z_]+$", norm):
        return None

    # Disallow bare words that are not known functions/constants
    known_tokens = {"sqrt", "abs", "round", "sin", "cos", "tan", "log", "log10", "log2", "ceil", "floor", "pi", "e", "tau"}
    words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", norm)
    for w in words:
        if w.lower() not in known_tokens:
            return None

    try:
        tree = ast.parse(norm, mode="eval")
    except SyntaxError:
        return None

    try:
        evaluator = SafeEvaluator()
        result_val = evaluator.visit(tree)
        
        # Nicely styled expression for display
        display_str = (
            expr.replace("**", "^")
            .replace("*", " × ")
            .replace("/", " ÷ ")
            .replace("  ", " ")
        )
        return CalculatorResult(
            display_expr=display_str,
            formatted_result=format_number(result_val),
            raw_result=result_val,
        )
    except ZeroDivisionError:
        display_str = expr.replace("**", "^").replace("*", " × ").replace("/", " ÷ ")
        return CalculatorResult(
            display_expr=display_str,
            formatted_result="Indefinido (división por cero)",
            raw_result="ZeroDivisionError",
            is_error=True,
        )
    except ValueError as e:
        if "math domain error" in str(e).lower():
            return CalculatorResult(
                display_expr=expr,
                formatted_result="Indefinido (dominio matemático)",
                raw_result="DomainError",
                is_error=True,
            )
        return None
    except Exception:
        return None
