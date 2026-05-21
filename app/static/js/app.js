async function formatSQL() {
    const sql = document.getElementById("sql-input").value;

    const response = await fetch("/api/format-sql", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ sql })
    });

    const data = await response.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    const result = document.getElementById("formatted-result");
    result.textContent = data.formatted_sql;
    Prism.highlightElement(result);
}

function showCsvError(message) {
    const error = document.getElementById("csv-error");
    if (!error) return;

    error.textContent = message;
    error.classList.toggle("form-error--visible", Boolean(message));
}

async function convertCSV() {
    const csvData = (document.getElementById("csv-input").value || "").trim();
    const table_name = (document.getElementById("table-name").value || "").trim();

    showCsvError("");

    if (!table_name || !csvData) {
        showCsvError("Datos incompletos: indica el nombre de la tabla y el contenido CSV antes de convertir.");
        return;
    }

    const response = await fetch("/api/csv-to-sql", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            table_name,
            csv_data: csvData
        })
    });

    const data = await response.json();

    if (data.error) {
        showCsvError(`Ocurrió un error: ${data.error}. Revisa el CSV y el nombre de la tabla.`);
        return;
    }

    const result = document.getElementById("csv-result");
    result.textContent = data.sql;
    Prism.highlightElement(result);
}

function showGeneratorError(message) {
    const error = document.getElementById("generator-error");
    if (!error) return;

    error.textContent = message;
    error.classList.toggle("form-error--visible", Boolean(message));
}

async function generateSQL() {
    const table = (document.getElementById("table").value || "").trim();
    const columns = (document.getElementById("columns").value || "")
        .split(",")
        .map(column => column.trim())
        .filter(Boolean);

    showGeneratorError("");

    if (!table || !columns.length) {
        showGeneratorError("Los datos enviados no son válidos. Asegúrate de indicar el nombre de la tabla y al menos una columna separada por comas.");
        return;
    }

    const response = await fetch("/api/generate-select", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            table,
            columns
        })
    });

    const data = await response.json();

    if (data.error) {
        showGeneratorError(`Ocurrió un error: ${data.error}. Revisa los nombres de tabla y columnas, y prueba de nuevo.`);
        return;
    }

    const result = document.getElementById("generator-result");
    result.textContent = data.query;
    Prism.highlightElement(result);
}

function createTableSizeRow({ name = "", type = "INT", size = "" } = {}) {
    const row = document.createElement("div");
    row.className = "table-size-row";
    row.innerHTML = `
        <div class="panel__field">
            <label class="field-label">Nombre de columna</label>
            <input class="input column-name" value="${name}" placeholder="ej. id" />
        </div>
        <div class="panel__field">
            <label class="field-label">Tipo</label>
            <select class="input column-type">
                <option value="INT">INT</option>
                <option value="BIGINT">BIGINT</option>
                <option value="SMALLINT">SMALLINT</option>
                <option value="VARCHAR">VARCHAR</option>
                <option value="CHAR">CHAR</option>
                <option value="TEXT">TEXT</option>
                <option value="DATE">DATE</option>
                <option value="DATETIME">DATETIME</option>
                <option value="BOOLEAN">BOOLEAN</option>
                <option value="FLOAT">FLOAT</option>
                <option value="DOUBLE">DOUBLE</option>
            </select>
        </div>
        <div class="panel__field">
            <label class="field-label">Tamaño opcional</label>
            <input class="input column-size" value="${size}" placeholder="Bytes o longitud" />
        </div>
        <div class="panel__field table-size-actions">
            <button type="button" class="button button--secondary" onclick="removeTableColumnRow(this)">Eliminar</button>
        </div>
    `;

    row.querySelector(".column-type").value = type;
    return row;
}

function addTableColumnRow() {
    const container = document.getElementById("columns-container");
    if (!container) return;

    container.appendChild(createTableSizeRow());
}

function removeTableColumnRow(button) {
    const container = document.getElementById("columns-container");
    if (!container) return;

    const row = button.closest(".table-size-row");
    if (!row) return;

    if (container.children.length > 1) {
        row.remove();
    } else {
        row.querySelectorAll("input").forEach(input => input.value = "");
        row.querySelector("select").value = "INT";
    }
}

function getTableSizePayload() {
    const rowsInput = document.getElementById("rows-count");
    const sqlInput = document.getElementById("sql-input");
    if (!rowsInput || !sqlInput) return null;

    return {
        rows: rowsInput.value,
        create_table_sql: sqlInput.value,
    };
}

function showTableSizeError(message) {
    const error = document.getElementById("table-size-error");
    if (!error) return;
    error.textContent = message;
    error.style.display = message ? "block" : "none";
    error.classList.toggle("form-error--visible", Boolean(message));
}

function renderTableSizeResult(data) {
    const output = document.getElementById("table-size-output");
    const breakdown = document.getElementById("table-size-breakdown");
    const rowsSummary = document.getElementById("summary-rows");
    const rowSizeSummary = document.getElementById("summary-row-size");
    const totalSizeSummary = document.getElementById("summary-total-size");

    if (!output || !breakdown || !rowsSummary || !rowSizeSummary || !totalSizeSummary) return;

    rowsSummary.textContent = `Registros: ${data.rows.toLocaleString()}`;
    rowSizeSummary.textContent = `Tamaño por fila: ${data.row_size.formatted}`;
    totalSizeSummary.textContent = `Tamaño total: ${data.total_size.formatted}`;

    breakdown.innerHTML = data.columns.map(col => `
        <div class="table-size-row-result">
            <div><strong>${col.name}</strong></div>
            <div>${col.type}</div>
            <div>${col.formatted_size}</div>
        </div>
    `).join("");

    output.hidden = false;
}

async function calculateTableSize() {
    showTableSizeError("");
    const payload = getTableSizePayload();
    if (!payload) return;

    const response = await fetch("/api/table-size", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (data.error) {
        showTableSizeError(data.error);
        return;
    }

    renderTableSizeResult(data.result);
}

function resetTableSize() {
    const rowsInput = document.getElementById("rows-count");
    const sqlInput = document.getElementById("sql-input");
    const output = document.getElementById("table-size-output");
    if (rowsInput) rowsInput.value = 1000;
    if (sqlInput) sqlInput.value = "";
    showTableSizeError("");
    if (output) output.hidden = true;
}

function loadTableSizeExample() {
    const sqlInput = document.getElementById("sql-input");
    const rowsInput = document.getElementById("rows-count");
    if (sqlInput) {
        sqlInput.value = `CREATE TABLE usuarios (
    id INT PRIMARY KEY,
    nombre VARCHAR(100),
    email VARCHAR(100),
    fecha_registro DATE,
    activo BOOLEAN
);`;
    }
    if (rowsInput) rowsInput.value = 5000;
}

async function copyTableSizeResult() {
    const output = document.getElementById("table-size-output");
    if (!output) return;

    const rowsText = document.getElementById("summary-rows")?.textContent || "";
    const rowSizeText = document.getElementById("summary-row-size")?.textContent || "";
    const totalSizeText = document.getElementById("summary-total-size")?.textContent || "";
    const breakdownText = Array.from(document.querySelectorAll(".table-size-row-result")).map(row => row.textContent.trim()).join("\n");

    const fullText = `${rowsText}\n${rowSizeText}\n${totalSizeText}\n\nDesglose:\n${breakdownText}`;
    await copyToClipboard(fullText, 'copy-table-btn');
}

function downloadTableSizeCSV() {
    const output = document.getElementById("table-size-output");
    if (!output) {
        showWarning('Advertencia', 'No hay datos para descargar');
        return;
    }

    const rowsText = document.getElementById("summary-rows")?.textContent || "";
    const rowSizeText = document.getElementById("summary-row-size")?.textContent || "";
    const totalSizeText = document.getElementById("summary-total-size")?.textContent || "";
    const breakdownRows = Array.from(document.querySelectorAll(".table-size-row-result")).map(row => {
        const cells = Array.from(row.querySelectorAll('div')).map(el => el.textContent.trim());
        return cells.join(',');
    }).join('\n');

    if (!breakdownRows) {
        showWarning('Advertencia', 'Ejecuta el cálculo primero');
        return;
    }

    const header = "Nombre,Tipo,Tamaño\n";
    const fullCSV = `${header}${breakdownRows}\n\nResumen:\n${rowsText}\n${rowSizeText}\n${totalSizeText}`;
    downloadFile(fullCSV, 'table_size_analysis.csv', 'text/csv');
}


function showNormalizationError(message) {
    const error = document.getElementById("norm-error");
    if (!error) return;

    error.textContent = message;
    error.style.display = message ? "block" : "none";
    error.classList.toggle("form-error--visible", Boolean(message));
}

function resetNormalization() {
    const sqlInput = document.getElementById("sql-input");
    const output = document.getElementById("norm-output");
    const results = document.getElementById("norm-results");

    if (sqlInput) sqlInput.value = "";
    if (results) results.innerHTML = "";
    if (output) output.hidden = true;

    showNormalizationError("");
}

function loadNormalizationExample() {
    const sqlInput = document.getElementById("sql-input");
    if (!sqlInput) return;

    sqlInput.value = `CREATE TABLE ordenes ( orden_id INT PRIMARY KEY, cliente_id INT, cliente_nombre VARCHAR(50), cliente_direccion VARCHAR(100), producto_id INT, producto_nombre VARCHAR(50) );`;
}

function parseNormalizationInput() {
    return {
        create_table_sql: (document.getElementById("sql-input")?.value || "").trim(),
    };
}

function analyzeNormalization() {
    const payload = parseNormalizationInput();
    if (!payload.create_table_sql) {
        showNormalizationError("Pega el script CREATE TABLE antes de analizar.");
        return;
    }

    fetch("/api/normalization", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
        .then(response => response.json())
        .then(data => {
            const resultsElement = document.getElementById("norm-results");
            const output = document.getElementById("norm-output");

            if (!resultsElement || !output) return;
            if (data.error) {
                showNormalizationError(data.error);
                return;
            }

            const result = data.result;
            resultsElement.innerHTML = [
                { title: '1FN', status: result['1fn'].status, detail: result['1fn'].detail },
                { title: '2FN', status: result['2fn'].status, detail: result['2fn'].detail },
                { title: '3FN', status: result['3fn'].status, detail: result['3fn'].detail }
            ].map(item => {
                const statusClass = item.status === 'CUMPLE' ? 'normalization-result-status--cumple' : 'normalization-result-status--no-cumple';
                return `
                    <div class="normalization-result-row">
                        <div class="normalization-result-status ${statusClass}">${item.status}</div>
                        <div class="normalization-result-detail"><strong>${item.title}</strong><br />${item.detail}</div>
                    </div>
                `;
            }).join('');
            output.hidden = false;
            showNormalizationError("");
        })
        .catch(() => {
            showNormalizationError('Error al comunicarse con el servidor. Intenta de nuevo.');
        });
}

function formatNormalizationOutput(evaluation) {
    return evaluation.results.map(item => {
        const statusClass = item.status === "Cumple" ? "normalization-result-status--cumple" : "normalization-result-status--no-cumple";
        return `
        <div class="normalization-result-row">
            <div class="normalization-result-status ${statusClass}">${item.status}</div>
            <div class="normalization-result-detail">
                <strong>${item.title}</strong><br />${item.detail}
            </div>
        </div>
    `;
    }).join("");
}

async function copyNormalizationResult() {
    const resultsElement = document.getElementById("norm-results");
    if (!resultsElement) return;

    const text = Array.from(resultsElement.querySelectorAll(".normalization-result-row")).map(row => row.textContent.trim()).join("\n\n");
    await copyToClipboard(text, 'copy-norm-btn');
}

function downloadNormalizationReport() {
    const resultsElement = document.getElementById("norm-results");
    if (!resultsElement || !resultsElement.innerHTML.trim()) {
        showWarning('Advertencia', 'Ejecuta el análisis primero');
        return;
    }

    const text = Array.from(resultsElement.querySelectorAll(".normalization-result-row")).map(row => row.textContent.trim()).join("\n\n");
    downloadFile(text, 'normalization_analysis.txt', 'text/plain');
}

function initTableSizeTool() {
    const container = document.getElementById("columns-container");
    if (!container) return;

    if (!container.children.length) {
        container.appendChild(createTableSizeRow());
    }
}

function updateThemeButton(theme) {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    const icon = toggle.querySelector('.theme-toggle__icon');
    const label = toggle.querySelector('.theme-toggle__label');

    if (theme === 'dark') {
        if (icon) icon.textContent = '☀️';
        if (label) label.textContent = 'Modo oscuro';
    } else {
        if (icon) icon.textContent = '🌙';
        if (label) label.textContent = 'Modo claro';
    }
}

function setTheme(theme) {
    document.body.classList.toggle('dark', theme === 'dark');
    updateThemeButton(theme);
    localStorage.setItem('ilovebd-theme', theme);
}

function getPreferredTheme() {
    const saved = localStorage.getItem('ilovebd-theme');
    if (saved === 'dark' || saved === 'light') {
        return saved;
    }

    const media = window.matchMedia('(prefers-color-scheme: dark)');
    return media.matches ? 'dark' : 'light';
}

function initThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    const preferredTheme = getPreferredTheme();
    setTheme(preferredTheme);

    toggle.addEventListener('click', () => {
        const nextTheme = document.body.classList.contains('dark') ? 'light' : 'dark';
        setTheme(nextTheme);
    });
}

function initializePage() {
    initThemeToggle();
    initTableSizeTool();
    initMobileMenu();
}

function initMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (!menuToggle || !navMenu) return;

    menuToggle.addEventListener('click', () => {
        const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true';
        menuToggle.setAttribute('aria-expanded', !isExpanded);
        navMenu.classList.toggle('active');
    });

    // Close menu when a link is clicked
    navMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            menuToggle.setAttribute('aria-expanded', 'false');
            navMenu.classList.remove('active');
        });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePage);
} else {
    initializePage();
}
