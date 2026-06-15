"""
SQL Optimizer Service
Analiza consultas SQL y detecta problemas, anti-patterns, y oportunidades de optimización.
"""

import re
from typing import List, Dict


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
        self.metrics: Dict[str, int] = {}
    
    def analyze(self) -> Dict:
        """Analiza la consulta y retorna resultados"""
        self.issues = []
        self.metrics = self._extract_metrics()
        
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
        self._check_distinct_usage()
        self._check_distinct_with_select_star()
        self._check_index_unfriendly_patterns()
        self._check_missing_table_alias()
        self._check_cartesian_product_risk()
        self._check_null_comparisons()
        self._check_implicit_type_conversion()
        self._check_order_by_without_limit()
        self._check_redundant_conditions()
        self._check_unsafe_dml_without_where()
        self._check_unnecessary_join_pattern()
        self._check_complex_query()
        
        # Ordenar por severidad
        severity_order = {'error': 0, 'warning': 1, 'info': 2}
        self.issues.sort(key=lambda issue: severity_order.get(issue.severity, 3))
        
        score = self._calculate_efficiency_score()
        performance_estimate = self._estimate_performance(score)
        complexity = self._describe_complexity()
        recommendations = self._compile_recommendations()

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
            'critical_count': sum(1 for issue in self.issues if issue.severity == 'error'),
            'warning_count': sum(1 for issue in self.issues if issue.severity == 'warning'),
            'info_count': sum(1 for issue in self.issues if issue.severity == 'info'),
            'efficiency_score': score,
            'performance_estimate': performance_estimate,
            'complexity': complexity,
            'recommendations': recommendations,
            'metrics': self.metrics,
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

    def _check_order_by_without_limit(self):
        """Detecta ORDER BY sin LIMIT"""
        if re.search(r'(?i)ORDER\s+BY', self.sql) and not re.search(r'(?i)LIMIT', self.sql):
            if not re.search(r'(?i)GROUP\s+BY', self.sql):
                self.issues.append(SQLOptimization(
                    'order_by_without_limit',
                    'warning',
                    '💡 ORDER BY sin LIMIT',
                    'ORDER BY sin LIMIT puede generar grandes costos de ordenamiento en memoria.',
                    'Agrega LIMIT y paginación: LIMIT 100 OFFSET 0',
                    example='// Mejor: SELECT id, name FROM users ORDER BY created_at DESC LIMIT 100',
                    impact='Ordenamiento costoso en grandes conjuntos'
                ))

    def _check_redundant_conditions(self):
        """Detecta condiciones redundantes"""
        if re.search(r'(?i)\bAND\s+1\s*=\s*1\b|\bOR\s+1\s*=\s*1\b', self.sql) or re.search(r'(?i)\b(\w+)\s*=\s*\1\b', self.sql):
            self.issues.append(SQLOptimization(
                'redundant_conditions',
                'info',
                '💡 Condiciones redundantes detectadas',
                'Algunas condiciones de filtro no aportan valor y saturan el plan de ejecución.',
                'Revisa la cláusula WHERE y elimina comparaciones redundantes.',
                example='// Malo: WHERE status = status AND 1 = 1\n// Mejor: WHERE status = "active"',
                impact='Podría complicar el optimizador de consultas'
            ))

    def _check_unsafe_dml_without_where(self):
        """Detecta UPDATE/DELETE sin WHERE"""
        sql_trimmed = self.sql.strip()
        if re.search(r'(?i)^(UPDATE|DELETE)\s+.+$', sql_trimmed) and not re.search(r'(?i)\bWHERE\b', sql_trimmed):
            self.issues.append(SQLOptimization(
                'unsafe_dml',
                'error',
                '❌ UPDATE/DELETE sin WHERE',
                'Actualizar o borrar sin WHERE puede modificar o eliminar todas las filas de la tabla.',
                'Agrega una condición WHERE clara antes de ejecutar operaciones destructivas.',
                example='// Malo: DELETE FROM users\n// Mejor: DELETE FROM users WHERE active = 0',
                impact='Puede causar pérdida de datos masiva'
            ))

    def _check_unnecessary_join_pattern(self):
        """Detecta JOINs difíciles de optimizar"""
        join_count = len(re.findall(r'(?i)JOIN', self.sql))
        if join_count >= 2 and not re.search(r'(?i)JOIN\s+\w+\s+ON', self.sql):
            self.issues.append(SQLOptimization(
                'join_without_on',
                'warning',
                '💡 JOIN sin ON detectado',
                'Algunos JOINs no tienen una condición ON clara, lo que puede indicar un producto cartesiano o ambigüedad.',
                'Asegura que cada JOIN incluya una condición ON específica.',
                example='// Malo: FROM users JOIN orders\n// Mejor: FROM users JOIN orders ON users.id = orders.user_id',
                impact='Puede causar combinaciones innecesarias de filas'
            ))

    def _check_complex_query(self):
        """Mide la complejidad de la consulta"""
        join_count = len(re.findall(r'(?i)JOIN', self.sql))
        subquery_count = len(re.findall(r'(?i)\(\s*SELECT', self.sql))
        if join_count >= 3 or subquery_count >= 2:
            self.issues.append(SQLOptimization(
                'complex_query',
                'info',
                '💡 Consulta compleja detectada',
                'Esta consulta contiene múltiples JOINs o subconsultas que aumentan su complejidad.',
                'Revisa si puedes dividir la consulta en pasos más simples o usar vistas.',
                example='// Consulta compleja con muchos JOINs y subconsultas',
                impact='Puede aumentar el tiempo de ejecución y dificultar mantenimiento'
            ))

    def _extract_metrics(self):
        """Extrae métricas clave para calificar la consulta"""
        query = self.sql.upper()
        join_count = len(re.findall(r'JOIN', query))
        subquery_count = len(re.findall(r'\(\s*SELECT', query))
        return {
            'length': len(self.sql),
            'join_count': join_count,
            'subquery_count': subquery_count,
            'has_where': bool(re.search(r'\bWHERE\b', query)),
            'has_limit': bool(re.search(r'\bLIMIT\b', query)),
            'has_order_by': bool(re.search(r'\bORDER\s+BY\b', query)),
            'has_distinct': bool(re.search(r'\bDISTINCT\b', query)),
            'has_group_by': bool(re.search(r'\bGROUP\s+BY\b', query)),
        }

    def _calculate_efficiency_score(self):
        """Calcula un puntaje de eficiencia basado en las detecciones"""
        score = 100
        for issue in self.issues:
            if issue.severity == 'error':
                score -= 25
            elif issue.severity == 'warning':
                score -= 12
            else:
                score -= 5
        score -= max(0, self.metrics.get('join_count', 0) - 1) * 3
        score -= max(0, self.metrics.get('subquery_count', 0) - 1) * 4
        score = max(15, min(100, score))
        return score

    def _estimate_performance(self, score: int) -> str:
        """Genera una estimación de rendimiento en lenguaje natural"""
        if score >= 85:
            return 'Alta eficiencia esperada'
        if score >= 70:
            return 'Buen rendimiento, revisar detalles menores'
        if score >= 50:
            return 'Rendimiento moderado, hay optimizaciones importantes'
        return 'Rendimiento crítico, requiere ajustes urgentes'

    def _describe_complexity(self) -> str:
        """Describe la complejidad de la consulta"""
        joins = self.metrics.get('join_count', 0)
        subqueries = self.metrics.get('subquery_count', 0)
        if joins >= 3 or subqueries >= 2:
            return 'Alta'
        if joins == 2 or subqueries == 1:
            return 'Media'
        return 'Baja'

    def _compile_recommendations(self) -> List[str]:
        """Genera recomendaciones clave en una lista legible"""
        recommendations = []
        if not self.metrics.get('has_where') and re.search(r'(?i)^SELECT', self.sql):
            recommendations.append('Agrega cláusulas WHERE específicas para evitar full table scans.')
        if self.metrics.get('has_order_by') and not self.metrics.get('has_limit'):
            recommendations.append('Aplica LIMIT/OFFSET cuando uses ORDER BY en consultas de listado.')
        if self.metrics.get('has_distinct') and not self.metrics.get('has_group_by'):
            recommendations.append('Revisa el uso de DISTINCT; puede ser más eficiente un GROUP BY o una subconsulta mejor definida.')
        if self.metrics.get('join_count', 0) >= 2:
            recommendations.append('Verifica que cada JOIN tenga ON correcto y que no traigas tablas innecesarias.')
        if self.metrics.get('subquery_count', 0) >= 1:
            recommendations.append('Evalúa si las subconsultas pueden reescribirse como JOINs o vistas materializadas.')
        if not recommendations:
            recommendations.append('La consulta parece sólida, pero revisa el plan de ejecución para confirmar.')
        return recommendations


def optimize_sql(sql: str) -> Dict:
    """API wrapper para optimizar SQL"""
    optimizer = SQLOptimizer(sql)
    return optimizer.analyze()
