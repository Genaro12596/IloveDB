"""
SQL Optimizer Service
Analiza consultas SQL y detecta problemas, anti-patterns, y oportunidades de optimización.
"""

import re
from typing import List, Dict, Tuple


class SQLOptimization:
    """Análisis de optimización SQL"""
    
    def __init__(self, issue_type: str, severity: str, title: str, description: str, suggestion: str, 
                 example: str = '', impact: str = ''):
        self.issue_type = issue_type  # full_scan, select_star, subquery, etc.
        self.severity = severity  # error, warning, info
        self.title = title
        self.description = description
        self.suggestion = suggestion
        self.example = example  # Ejemplo de código optimizado
        self.impact = impact  # Impacto estimado


class SQLOptimizer:
    """Analizador de consultas SQL - Detecciones expandidas"""
    
    PATTERNS = {
        'full_scan': r'(?i)^SELECT\s+.+\s+FROM\s+\w+\s*(?:;)?$',  # SELECT sin WHERE
        'select_star': r'(?i)SELECT\s+\*',
        'like_percent': r"(?i)LIKE\s+'%.*%'",
        'not_in_null': r"(?i)NOT\s+IN\s*\(\s*NULL",
        'or_conditions': r"(?i)WHERE\s+.+\s+OR\s+.+",
        'function_in_where': r"(?i)WHERE\s+(?:UPPER|LOWER|SUBSTRING|LEFT|RIGHT)\s*\(",
        'select_without_where': r"(?i)^SELECT\s+.+FROM\s+\w+\s*$(?!WHERE)",
        'no_limit': r"(?i)^SELECT\s+.+\s+FROM\s+",
        'multiple_joins': r"(?i)JOIN\s+.+JOIN\s+.+JOIN",
    }
    
    def __init__(self, sql: str):
        self.sql = sql.strip()
        self.issues: List[SQLOptimization] = []
    
    def analyze(self) -> Dict:
        """Analiza la consulta y retorna resultados"""
        self.issues = []
        
        if not self.sql:
            return {
                'success': False,
                'error': 'Por favor, ingresa una consulta SQL válida.'
            }
        
        # ANÁLISIS EXPANDIDO - 15+ detecciones
        self._check_full_table_scan()
        self._check_select_star()
        self._check_like_with_percent()
        self._check_not_in_null()
        self._check_or_conditions()
        self._check_function_in_where()
        self._check_missing_limit()
        self._check_multiple_joins()
        self._check_correlated_subqueries()
        self._check_distinct_usage()  # NUEVA
        self._check_distinct_with_select_star()  # NUEVA
        self._check_index_unfriendly_patterns()  # NUEVA
        self._check_missing_table_alias()  # NUEVA
        self._check_cartesian_product_risk()  # NUEVA
        self._check_null_comparisons()  # NUEVA
        self._check_implicit_type_conversion()  # NUEVA
        
        # Ordenar por severidad
        severity_order = {'error': 0, 'warning': 1, 'info': 2}
        self.issues.sort(key=lambda x: severity_order.get(x.severity, 3))
        
        return {
            'success': True,
            'query': self.sql,
            'issues': [
                {
                    'type': issue.issue_type,
                    'severity': issue.severity,
                    'title': issue.title,
                    'description': issue.description,
                    'suggestion': issue.suggestion,
                    'example': issue.example,
                    'impact': issue.impact
                }
                for issue in self.issues
            ],
            'total_issues': len(self.issues),
            'critical_count': sum(1 for i in self.issues if i.severity == 'error'),
            'warning_count': sum(1 for i in self.issues if i.severity == 'warning'),
            'info_count': sum(1 for i in self.issues if i.severity == 'info'),
        }
    
    def _check_full_table_scan(self):
        """Detecta SELECT sin WHERE (full table scan)"""
        # Buscar SELECT ... FROM ... sin WHERE
        if not re.search(r'(?i)WHERE', self.sql):
            if re.search(r'(?i)FROM', self.sql):
                self.issues.append(SQLOptimization(
                    'full_scan',
                    'error',
                    '⚠️ Full Table Scan Detectado',
                    'Esta consulta no tiene cláusula WHERE, lo que significa que examinará todas las filas de la tabla.',
                    'Agrega una cláusula WHERE para filtrar solo los registros necesarios. Ejemplo: WHERE id = 1',
                    example='// Malo: SELECT * FROM users\n// Mejor: SELECT * FROM users WHERE status = "active"',
                    impact='Lee toda la tabla, muy lento con muchos datos'
                ))
    
    def _check_select_star(self):
        """Detecta SELECT *"""
        if re.search(r'(?i)SELECT\s+\*', self.sql):
            self.issues.append(SQLOptimization(
                'select_star',
                'warning',
                '⚠️ SELECT * Detectado',
                'Usar SELECT * trae todas las columnas, lo que puede impactar rendimiento y transferencia de datos.',
                'Especifica solo las columnas que necesitas: SELECT id, name, email FROM tabla WHERE ...',
                example='// Malo: SELECT * FROM users\n// Mejor: SELECT id, name, email FROM users',
                impact='Transferencia de datos innecesaria'
            ))
    
    def _check_like_with_percent(self):
        """Detecta LIKE '%...%' que no usa índices"""
        if re.search(r"(?i)LIKE\s+'%", self.sql):
            self.issues.append(SQLOptimization(
                'like_percent',
                'warning',
                '💡 LIKE con % al Inicio Detectado',
                'LIKE con % al inicio no puede usar índices de base de datos, haciendo la búsqueda lenta.',
                'Si es posible, usa LIKE "value%" en vez de "% value %". O considera usar full-text search.',
                example='// Lento: WHERE name LIKE "%john%"\n// Mejor: WHERE name LIKE "john%"',
                impact='No usa índices, búsqueda completa de tabla'
            ))
    
    def _check_not_in_null(self):
        """Detecta NOT IN con NULL"""
        if re.search(r"(?i)NOT\s+IN\s*\(", self.sql) and 'NULL' in self.sql.upper():
            self.issues.append(SQLOptimization(
                'not_in_null',
                'error',
                '❌ NOT IN con NULL Detectado',
                'Si hay NULL en la lista de NOT IN, la condición siempre devuelve false (UNKNOWN en SQL).',
                'Usa NOT EXISTS con una subconsulta o filtra NULLs: NOT IN (...) AND columna IS NOT NULL',
                example='// Malo: WHERE id NOT IN (SELECT id FROM ...)\n// Mejor: WHERE id NOT IN (SELECT id FROM ... WHERE id IS NOT NULL)',
                impact='Condición nunca se cumple'
            ))
    
    def _check_or_conditions(self):
        """Detecta múltiples OR que podrían optimizarse"""
        or_count = self.sql.upper().count(' OR ')
        if or_count >= 3:
            self.issues.append(SQLOptimization(
                'or_conditions',
                'info',
                '💡 Múltiples Condiciones OR Detectadas',
                f'Se encontraron {or_count} condiciones OR. Muchas ORs pueden reducir la eficiencia.',
                'Considera usar IN() para igualdades: WHERE columna IN (val1, val2, val3) en lugar de OR',
                example='// Lento: WHERE status = "active" OR status = "pending" OR status = "pending"\n// Mejor: WHERE status IN ("active", "pending")',
                impact='Optimizador puede no elegir mejores índices'
            ))
    
    def _check_function_in_where(self):
        """Detecta funciones en WHERE que no usan índices"""
        if re.search(r"(?i)WHERE\s+(?:UPPER|LOWER|SUBSTRING|LEFT|RIGHT|CAST|CONVERT)\s*\(", self.sql):
            self.issues.append(SQLOptimization(
                'function_in_where',
                'warning',
                '💡 Función en WHERE Detectada',
                'Usar funciones en WHERE evita usar índices de la base de datos.',
                'Reorganiza la lógica: WHERE UPPER(nombre) = "JUAN" → WHERE nombre = "juan" (si BD distingue mayúsculas)',
                example='// Malo: WHERE UPPER(email) = "USER@EXAMPLE.COM"\n// Mejor: almacena en BD normalizado o usa búsqueda case-insensitive',
                impact='No usa índices'
            ))
    
    def _check_missing_limit(self):
        """Detecta SELECT sin LIMIT (potencial problema)"""
        if re.search(r'(?i)SELECT\s+.+FROM', self.sql):
            if not re.search(r'(?i)LIMIT', self.sql):
                # Solo si no es un aggregation
                if not re.search(r'(?i)COUNT\s*\(|SUM\s*\(|AVG\s*\(|MAX\s*\(|MIN\s*\(|GROUP\s+BY', self.sql):
                    self.issues.append(SQLOptimization(
                        'no_limit',
                        'info',
                        '💡 Sin LIMIT',
                        'Esta consulta no tiene LIMIT, podría traer muchos registros.',
                        'Considera agregar LIMIT para paginar: LIMIT 100 OFFSET 0',
                        example='// Mejor práctica: SELECT * FROM users LIMIT 100 OFFSET 0',
                        impact='Puede devolver demasiados datos'
                    ))
    
    def _check_multiple_joins(self):
        """Detecta múltiples JOINs"""
        join_count = len(re.findall(r'(?i)JOIN', self.sql))
        if join_count >= 4:
            self.issues.append(SQLOptimization(
                'multiple_joins',
                'info',
                '💡 Múltiples JOINs Detectados',
                f'Se encontraron {join_count} JOINs. Muchos JOINs pueden afectar rendimiento.',
                'Revisa si todos los JOINs son necesarios. Considera denormalización o vistas si es necesario.',
                example='// Considera usar vistas si necesitas muchos JOINs',
                impact='Rendimiento puede degradarse'
            ))
    
    def _check_correlated_subqueries(self):
        """Detecta subconsultas correlacionadas"""
        # Patrón simple: WHERE xxx IN (SELECT ... WHERE referencias tabla externa)
        if re.search(r'(?i)WHERE\s+.+\s+IN\s*\(\s*SELECT', self.sql):
            self.issues.append(SQLOptimization(
                'subquery',
                'info',
                '💡 Subconsulta Detectada',
                'Las subconsultas en WHERE pueden ser lentas si están correlacionadas.',
                'Considera usar JOIN en lugar de subconsulta cuando sea posible.',
                example='SELECT * FROM orders o WHERE o.user_id IN (SELECT id FROM users WHERE active = 1)',
                impact='Lento si hay muchos registros'
            ))
    
    def _check_distinct_usage(self):
        """Detecta DISTINCT innecesario"""
        if re.search(r'(?i)SELECT\s+DISTINCT', self.sql):
            # Verificar si hay GROUP BY
            if not re.search(r'(?i)GROUP\s+BY', self.sql):
                self.issues.append(SQLOptimization(
                    'distinct_abuse',
                    'warning',
                    '⚠️ DISTINCT sin GROUP BY',
                    'DISTINCT puede ser lento porque requiere ordenar todos los registros para eliminar duplicados.',
                    'Revisa si realmente necesitas DISTINCT. Si hay duplicados, mejor optimiza la consulta.',
                    example='// Malo: SELECT DISTINCT user_id FROM orders\n// Mejor: SELECT user_id FROM orders GROUP BY user_id',
                    impact='Rendimiento degradado con muchos datos'
                ))
    
    def _check_distinct_with_select_star(self):
        """Detecta DISTINCT * que es ineficiente"""
        if re.search(r'(?i)SELECT\s+DISTINCT\s+\*', self.sql):
            self.issues.append(SQLOptimization(
                'distinct_star',
                'error',
                '❌ DISTINCT * Detectado',
                'Usar DISTINCT * es muy ineficiente y generalmente innecesario.',
                'Especifica solo las columnas: SELECT DISTINCT user_id, name FROM usuarios',
                example='// Malo: SELECT DISTINCT * FROM orders\n// Mejor: SELECT DISTINCT order_id FROM orders',
                impact='Muy lento, consume muchos recursos'
            ))
    
    def _check_index_unfriendly_patterns(self):
        """Detecta patrones que evitan uso de índices"""
        # CAST en WHERE
        if re.search(r"(?i)WHERE\s+CAST\s*\(", self.sql):
            self.issues.append(SQLOptimization(
                'cast_in_where',
                'warning',
                '💡 CAST en WHERE',
                'CAST en la cláusula WHERE evita usar índices.',
                'Almacena la columna en el tipo correcto en la BD o ajusta la query.',
                example='// Malo: WHERE CAST(id AS VARCHAR) = "123"\n// Mejor: WHERE id = 123',
                impact='No usa índices'
            ))
    
    def _check_missing_table_alias(self):
        """Detecta JOINs sin alias que pueden causar ambigüedad"""
        join_count = len(re.findall(r'(?i)JOIN', self.sql))
        if join_count >= 2:
            # Verificar si hay ambigüedad potencial
            if not re.search(r'(?i)JOIN\s+\w+\s+[A-Za-z]+\s+ON', self.sql):
                self.issues.append(SQLOptimization(
                    'missing_alias',
                    'info',
                    '💡 JOINs sin Alias Claros',
                    'Los JOINs sin alias pueden causar ambigüedad en columnas.',
                    'Usa alias: JOIN users u ON u.id = orders.user_id',
                    example='SELECT o.id, u.name FROM orders o JOIN users u ON o.user_id = u.id',
                    impact='Mejora legibilidad y evita errores'
                ))
    
    def _check_cartesian_product_risk(self):
        """Detecta riesgo de producto cartesiano"""
        if re.search(r'(?i)FROM\s+\w+\s*,\s*\w+', self.sql) and not re.search(r'(?i)WHERE', self.sql):
            self.issues.append(SQLOptimization(
                'cartesian_product',
                'error',
                '❌ Producto Cartesiano Potencial',
                'Esta consulta usa FROM con múltiples tablas pero sin WHERE. Esto crea un producto cartesiano.',
                'Agrega JOIN y ON: FROM tabla1 JOIN tabla2 ON tabla1.id = tabla2.id',
                example='// Malo: SELECT * FROM users, orders\n// Mejor: SELECT * FROM users JOIN orders ON users.id = orders.user_id',
                impact='Resultado exponencial de registros'
            ))
    
    def _check_null_comparisons(self):
        """Detecta comparaciones incorrectas con NULL"""
        if re.search(r'(?i)WHERE\s+.+\s*=\s*NULL', self.sql):
            self.issues.append(SQLOptimization(
                'null_comparison',
                'error',
                '❌ Comparación con NULL Incorrecta',
                'En SQL, NULL != NULL. Usar = NULL siempre devuelve false.',
                'Usa IS NULL o IS NOT NULL en lugar de = NULL',
                example='// Malo: WHERE email = NULL\n// Correcto: WHERE email IS NULL',
                impact='La condición nunca se cumple'
            ))
    
    def _check_implicit_type_conversion(self):
        """Detecta conversiones implícitas de tipos que evitan índices"""
        # Strings vs números en comparaciones
        if re.search(r"(?i)WHERE\s+\w+\s*=\s*['\"]", self.sql):
            # Podría ser comparación de tipos implícita
            self.issues.append(SQLOptimization(
                'type_conversion',
                'info',
                '💡 Posible Conversión Implícita de Tipos',
                'Si la columna es numérica pero se compara con string, se hace conversión implícita.',
                'Asegúrate que los tipos coincidan: WHERE user_id = 123 (no "123")',
                example='// Cuidado: WHERE id = "123" (si id es INT)\n// Mejor: WHERE id = 123',
                impact='Puede evitar índices'
            ))


def optimize_sql(sql: str) -> Dict:
    """API wrapper para optimizar SQL"""
    optimizer = SQLOptimizer(sql)
    return optimizer.analyze()
