import re
from typing import List, Optional

import sqlparse

SQL_TYPE_KEYWORDS = [
    "INT",
    "INTEGER",
    "BIGINT",
    "SMALLINT",
    "TINYINT",
    "VARCHAR",
    "CHAR",
    "TEXT",
    "DATE",
    "DATETIME",
    "TIMESTAMP",
    "TIME",
    "BOOLEAN",
    "FLOAT",
    "DOUBLE",
    "DECIMAL",
    "NUMERIC",
    "REAL",
    "SERIAL",
    "BLOB",
    "JSON",
    "UUID",
    "ENUM",
]

SQL_CONSTRAINT_KEYWORDS = [
    "PRIMARY KEY",
    "FOREIGN KEY",
    "REFERENCES",
    "NOT NULL",
    "NULL",
    "DEFAULT",
    "UNIQUE",
    "AUTO_INCREMENT",
    "AUTO INCREMENT",
    "CHECK",
    "CONSTRAINT",
    "CASCADE",
    "ON DELETE",
    "ON UPDATE",
]

SQL_FORMAT_KEYWORDS = SQL_CONSTRAINT_KEYWORDS + SQL_TYPE_KEYWORDS


def format_sql_query(sql: str) -> str:
    sql_text = (sql or "").strip()
    if not sql_text:
        return ""

    formatted_sql = sqlparse.format(
        sql_text,
        reindent=True,
        indent_width=4,
        keyword_case="upper",
        strip_comments=False,
        strip_whitespace=True,
        use_space_around_operators=True,
    )

    formatted_sql = _force_uppercase_types_and_constraints(formatted_sql)
    formatted_sql = _format_create_table_blocks(formatted_sql)
    formatted_sql = _format_insert_statements(formatted_sql)
    formatted_sql = _remove_redundant_blank_lines(formatted_sql)
    formatted_sql = _normalize_whitespace(formatted_sql)

    return formatted_sql.strip()


def _force_uppercase_types_and_constraints(sql: str) -> str:
    sorted_keywords = sorted(SQL_FORMAT_KEYWORDS, key=len, reverse=True)
    pattern = re.compile(
        r"\b(" + r"|".join(re.escape(token) for token in sorted_keywords) + r")\b",
        flags=re.IGNORECASE,
    )
    return pattern.sub(lambda match: match.group(1).upper(), sql)


def _remove_redundant_blank_lines(sql: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", sql)


def _normalize_whitespace(sql: str) -> str:
    cleaned = re.sub(r"[ \t]+$", "", sql, flags=re.MULTILINE)
    cleaned = re.sub(r"\s+;", ";", cleaned)
    cleaned = re.sub(r"\n\s+\n", "\n\n", cleaned)
    return cleaned


def _split_top_level_comma_separated(value: str) -> List[str]:
    parts: List[str] = []
    current: List[str] = []
    depth = 0
    in_single_quote = False
    in_double_quote = False
    escape = False

    for char in value:
        if escape:
            current.append(char)
            escape = False
            continue

        if char == "\\":
            current.append(char)
            escape = True
            continue

        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(depth - 1, 0)
            elif char == "," and depth == 0:
                parts.append("".join(current))
                current = []
                continue

        current.append(char)

    if current:
        parts.append("".join(current))

    return parts


def _find_matching_parenthesis(text: str, open_index: int) -> Optional[int]:
    depth = 0
    in_single_quote = False
    in_double_quote = False
    escape = False

    for idx in range(open_index, len(text)):
        char = text[idx]

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return idx

    return None


def _format_create_table_blocks(sql: str) -> str:
    output: List[str] = []
    cursor = 0
    pattern = re.compile(r"CREATE\s+TABLE\s+[^(]*\(", flags=re.IGNORECASE)

    while True:
        match = pattern.search(sql, cursor)
        if not match:
            break

        start = match.start()
        open_paren_index = sql.find("(", match.end() - 1)
        if open_paren_index == -1:
            break

        close_paren_index = _find_matching_parenthesis(sql, open_paren_index)
        if close_paren_index is None:
            break

        output.append(sql[cursor:start])
        block = sql[start : close_paren_index + 1]
        output.append(_format_create_table_block(block))
        cursor = close_paren_index + 1

    output.append(sql[cursor:])
    return "".join(output)


def _format_create_table_block(block: str) -> str:
    open_paren = block.index("(")
    header = block[: open_paren + 1].strip()
    body = block[open_paren + 1 : -1].strip()

    if not body:
        return f"{header}\n)"

    parts = _split_top_level_comma_separated(body)
    formatted_body = ",\n".join(" " * 4 + part.strip() for part in parts if part.strip())

    return f"{header}\n{formatted_body}\n)"


def _format_insert_statements(sql: str) -> str:
    sql = _format_insert_column_lists(sql)
    sql = _format_insert_values(sql)
    return sql


def _format_insert_column_lists(sql: str) -> str:
    output: List[str] = []
    cursor = 0
    pattern = re.compile(r"INSERT\s+INTO\s+[^\(]*\(", flags=re.IGNORECASE)

    while True:
        match = pattern.search(sql, cursor)
        if not match:
            break

        start = match.start()
        open_paren_index = sql.find("(", match.end() - 1)
        if open_paren_index == -1:
            break

        close_paren_index = _find_matching_parenthesis(sql, open_paren_index)
        if close_paren_index is None:
            break

        output.append(sql[cursor:start])
        block = sql[start : close_paren_index + 1]
        output.append(_format_insert_column_block(block))
        cursor = close_paren_index + 1

    output.append(sql[cursor:])
    return "".join(output)


def _format_insert_column_block(block: str) -> str:
    open_paren = block.index("(")
    header = block[: open_paren + 1].strip()
    body = block[open_paren + 1 : -1].strip()

    if not body:
        return f"{header}\n)"

    columns = _split_top_level_comma_separated(body)
    formatted_columns = ",\n".join(" " * 4 + column.strip() for column in columns if column.strip())

    return f"{header}\n{formatted_columns}\n)"


def _format_insert_values(sql: str) -> str:
    output: List[str] = []
    cursor = 0
    pattern = re.compile(r"VALUES\s*\(", flags=re.IGNORECASE)

    while True:
        match = pattern.search(sql, cursor)
        if not match:
            break

        start = match.start()
        open_paren_index = sql.find("(", match.end() - 1)
        if open_paren_index == -1:
            break

        close_paren_index = _find_matching_parenthesis(sql, open_paren_index)
        if close_paren_index is None:
            break

        output.append(sql[cursor:start])
        block = sql[start : close_paren_index + 1]
        output.append(_format_values_block(block))
        cursor = close_paren_index + 1

    output.append(sql[cursor:])
    return "".join(output)


def _format_values_block(block: str) -> str:
    open_paren = block.index("(")
    prefix = block[:open_paren].strip()
    body = block[open_paren + 1 : -1].strip()

    if not body:
        return f"{prefix}()"

    tuples = _split_top_level_comma_separated(body)
    formatted_items = []

    for item in tuples:
        item_str = item.strip()
        if item_str.startswith("(") and item_str.endswith(")"):
            inner = item_str[1:-1].strip()
            values = _split_top_level_comma_separated(inner)
            if len(values) > 1:
                formatted_values = ",\n".join(" " * 8 + value.strip() for value in values if value.strip())
                formatted_items.append(" " * 4 + "(\n" + formatted_values + "\n" + " " * 4 + ")")
            else:
                formatted_items.append(" " * 4 + item_str)
        else:
            formatted_items.append(" " * 4 + item_str)

    return f"{prefix}\n" + ",\n".join(formatted_items)
