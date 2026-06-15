import re
from typing import List, Optional
import sqlparse
from abc import ABC, abstractmethod

SQL_TYPE_KEYWORDS = ["INT", "INTEGER", "VARCHAR", "TEXT", "DATE", "TIMESTAMP", "BOOLEAN", "FLOAT"]
SQL_CONSTRAINT_KEYWORDS = ["PRIMARY KEY", "FOREIGN KEY", "REFERENCES", "NOT NULL", "NULL", "UNIQUE"]
SQL_FORMAT_KEYWORDS = SQL_CONSTRAINT_KEYWORDS + SQL_TYPE_KEYWORDS

# ==========================================
# MOTOR DE REGLAS (PATRÓN STRATEGY)
# ==========================================

class SqlRule(ABC):
    @abstractmethod
    def analyze(self, statement, sql_text: str) -> Optional[dict]:
        pass

class SelectStarRule(SqlRule):
    def analyze(self, statement, sql_text: str):
        if statement.get_type() == 'SELECT' and re.search(r'SELECT\s+\*', sql_text, re.IGNORECASE):
            return {
                "type": "warning",
                "title": "Sobrecarga de I/O (SELECT *)",
                "message": "El uso de SELECT * transfiere datos innecesarios a través de la red y el disco.",
                "recommendation": "Especifica únicamente las columnas requeridas para reducir el consumo de memoria.",
                "example": "SELECT id, nombre, fecha_registro FROM tabla;"
            }
        return None

class MissingWhereRule(SqlRule):
    def analyze(self, statement, sql_text: str):
        statement_type = statement.get_type()
        if statement_type in ['UPDATE', 'DELETE']:
            has_where = any(isinstance(token, sqlparse.sql.Where) for token in statement.tokens)
            if not has_where:
                return {
                    "type": "danger",
                    "title": f"Operación Destructiva ({statement_type} sin WHERE)",
                    "message": f"Se detectó un {statement_type} sin filtros. Esto afectará a TODOS los registros de la tabla.",
                    "recommendation": "Agrega siempre una cláusula WHERE usando una clave primaria o índice único.",
                    "example": f"{statement_type} tabla SET columna = valor WHERE id = 123;" if statement_type == 'UPDATE' else f"DELETE FROM tabla WHERE id = 123;"
                }
        return None

class UnfilteredSelectRule(SqlRule):
    def analyze(self, statement, sql_text: str):
        if statement.get_type() == 'SELECT':
            has_where = any(isinstance(token, sqlparse.sql.Where) for token in statement.tokens)
            has_limit = re.search(r'\bLIMIT\b', sql_text, re.IGNORECASE)
            
            if not has_where and not has_limit:
                return {
                    "type": "info",
                    "title": "Escaneo de tabla completa (Full Table Scan)",
                    "message": "Consulta sin filtros ni límites. En producción con tablas masivas, degradará el rendimiento.",
                    "recommendation": "Agrega una cláusula WHERE indexada o un LIMIT para paginar resultados.",
                    "example": "SELECT columnas FROM tabla WHERE estado = 'activo' LIMIT 100;"
                }
        return None

class ImplicitJoinRule(SqlRule):
    def analyze(self, statement, sql_text: str):
        if statement.get_type() == 'SELECT' and re.search(r'FROM\s+\w+\s*,\s*\w+', sql_text, re.IGNORECASE):
            return {
                "type": "warning",
                "title": "Sintaxis JOIN Antigua (Implícita)",
                "message": "Estás usando JOINs implícitos (separados por comas). Esto es propenso a errores lógicos y productos cartesianos.",
                "recommendation": "Utiliza la sintaxis explícita estándar ANSI SQL (INNER JOIN, LEFT JOIN).",
                "example": "SELECT a.col, b.col FROM tabla_a a INNER JOIN tabla_b b ON a.id = b.a_id;"
            }
        return None

# ==========================================
# FUNCIONES PRINCIPALES
# ==========================================

def format_sql_query(sql: str) -> str:
    sql_text = (sql or "").strip()
    if not sql_text: return ""
    formatted_sql = sqlparse.format(
        sql_text, reindent=True, indent_width=4, keyword_case="upper",
        strip_comments=False, strip_whitespace=True, use_space_around_operators=True,
    )
    return formatted_sql.strip()

def analyze_sql_query(sql: str) -> dict:
    warnings = []
    statements = sqlparse.parse(sql)
    rules = [SelectStarRule(), MissingWhereRule(), UnfilteredSelectRule(), ImplicitJoinRule()]
    
    score = 100
    complexity_points = 0
    
    for statement in statements:
        sql_text = str(statement)
        complexity_points += sql_text.upper().count("JOIN")
        complexity_points += sql_text.upper().count("SELECT") - 1 
        
        for rule in rules:
            result = rule.analyze(statement, sql_text)
            if result:
                warnings.append(result)
                if result['type'] == 'danger': score -= 30
                elif result['type'] == 'warning': score -= 15
                elif result['type'] == 'info': score -= 5

    score = max(0, min(100, score))
    level = "Optimizado" if score > 85 else "Requiere Revisión" if score > 60 else "Crítico"

    return {
        "score": score,
        "level": level,
        "stats": {
            "statements": len(statements),
            "complexity": "Alta" if complexity_points > 3 else "Media" if complexity_points > 0 else "Baja"
        },
        "warnings": warnings
    }
