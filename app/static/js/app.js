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
    const csv = (document.getElementById("csv-input").value || "").trim();
    const table_name = (document.getElementById("table-name").value || "").trim();

    showCsvError("");

    if (!table_name || !csv) {
        showCsvError("Datos incompletos: indica el nombre de la tabla y el contenido CSV antes de convertir.");
        return;
    }

    const response = await fetch("/api/csv-to-sql", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            csv,
            table_name
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
    const container = document.getElementById("columns-container");
    if (!rowsInput || !container) return null;

    const columns = Array.from(container.querySelectorAll(".table-size-row")).map(row => ({
        name: row.querySelector(".column-name").value,
        type: row.querySelector(".column-type").value,
        size: row.querySelector(".column-size").value.trim() || null,
    }));

    return {
        rows: rowsInput.value,
        columns,
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
    rowSizeSummary.textContent = `Tamaño por fila: ${data.row_size.bytes} (${data.row_size.kb})`;
    totalSizeSummary.textContent = `Tamaño total: ${data.total_size.mb} (${data.total_size.gb})`;

    breakdown.innerHTML = data.columns.map(col => `
        <div class="table-size-row-result">
            <div><strong>${col.name}</strong></div>
            <div>${col.type}</div>
            <div>${col.display_size}</div>
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
    const container = document.getElementById("columns-container");
    const output = document.getElementById("table-size-output");
    if (rowsInput) rowsInput.value = 1000;
    if (!container) return;

    container.innerHTML = "";
    container.appendChild(createTableSizeRow());
    showTableSizeError("");
    if (output) output.hidden = true;
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
    const rowsInput = document.getElementById("rows-count");
    const container = document.getElementById("columns-container");
    
    if (!rowsInput || !container) {
        showWarning('Advertencia', 'No hay datos para descargar');
        return;
    }

    const rows = Array.from(container.querySelectorAll(".table-size-row-result"));
    if (rows.length === 0) {
        showWarning('Advertencia', 'Ejecuta el cálculo primero');
        return;
    }

    const rowsCount = document.getElementById("summary-rows")?.textContent || "";
    const rowSize = document.getElementById("summary-row-size")?.textContent || "";
    const totalSize = document.getElementById("summary-total-size")?.textContent || "";

    const header = "Nombre,Tipo,Tamaño\n";
    const data = Array.from(container.querySelectorAll(".table-size-row-result")).map(row => {
        const cells = Array.from(row.querySelectorAll('div')).map(el => el.textContent.trim());
        return cells.join(',');
    }).join('\n');

    const fullCSV = `${header}${data}\n\nResumen:\n${rowsCount}\n${rowSize}\n${totalSize}`;
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
    const tableInput = document.getElementById("norm-table");
    const columnsInput = document.getElementById("norm-columns");
    const pkInput = document.getElementById("norm-pk");
    const fdsInput = document.getElementById("norm-fds");
    const output = document.getElementById("norm-output");
    const results = document.getElementById("norm-results");

    if (tableInput) tableInput.value = "";
    if (columnsInput) columnsInput.value = "";
    if (pkInput) pkInput.value = "";
    if (fdsInput) fdsInput.value = "";
    if (results) results.innerHTML = "";
    if (output) output.hidden = true;

    showNormalizationError("");
}

function parseNormalizationInput() {
    const table = document.getElementById("norm-table")?.value.trim() || "";
    const columns = (document.getElementById("norm-columns")?.value || "").split(",").map(col => col.trim()).filter(Boolean);
    const primaryKeys = (document.getElementById("norm-pk")?.value || "").split(",").map(col => col.trim()).filter(Boolean);
    const fds = (document.getElementById("norm-fds")?.value || "").split(/\r?\n/).map(line => line.trim()).filter(Boolean);

    return { table, columns, primaryKeys, fds };
}

function evaluateNormalization({ table, columns, primaryKeys, fds }) {
    const results = [];
    const validColumns = new Set(columns.map(col => col.toLowerCase()));
    const keySet = new Set(primaryKeys.map(col => col.toLowerCase()));
    const parsedFDs = [];

    for (const line of fds) {
        const match = line.match(/^(.+)->(.+)$/);
        if (!match) {
            continue;
        }

        const left = match[1].split(",").map(item => item.trim().toLowerCase()).filter(Boolean);
        const right = match[2].split(",").map(item => item.trim().toLowerCase()).filter(Boolean);
        if (!left.length || !right.length) continue;

        parsedFDs.push({ left, right });
    }

    const is1NF = table && columns.length > 0 && primaryKeys.length > 0;
    results.push({
        title: "1FN",
        status: is1NF ? "Cumple" : "No cumple",
        detail: is1NF
            ? "Tiene identificador y columnas definidas, por lo tanto cumple condiciones básicas de 1FN."
            : "Debes indicar nombre de tabla, columnas y claves primarias para evaluar correctamente 1FN."
    });

    let partialDependency = false;
    const compositeKey = primaryKeys.length > 1;

    if (parsedFDs.length) {
        for (const fd of parsedFDs) {
            const leftIsKeyPart = fd.left.every(attr => keySet.has(attr));
            const rightIsNonKey = fd.right.some(attr => !keySet.has(attr));
            if (compositeKey && leftIsKeyPart && rightIsNonKey && fd.left.length < primaryKeys.length) {
                partialDependency = true;
            }
        }
    }

    const is2NF = is1NF && !partialDependency;
    results.push({
        title: "2FN",
        status: is2NF ? "Cumple" : "No cumple",
        detail: is2NF
            ? "No se encontraron dependencias parciales sobre la clave primaria compuesta."
            : compositeKey
                ? "Se detectaron dependencias parciales en una clave primaria compuesta. Separar atributos en nuevas tablas mejorará 2FN."
                : "Con clave primaria simple, 2FN se satisface si no hay dependencias parciales."
    });

    let transitiveDependency = false;
    for (const fd of parsedFDs) {
        if (!fd.left.every(attr => keySet.has(attr))) {
            const rightNonKey = fd.right.some(attr => !keySet.has(attr));
            if (rightNonKey) {
                transitiveDependency = true;
                break;
            }
        }
    }

    const is3NF = is2NF && !transitiveDependency;
    results.push({
        title: "3FN",
        status: is3NF ? "Cumple" : "No cumple",
        detail: is3NF
            ? "No se encontraron dependencias transitivas relevantes."
            : "Hay dependencias transitivas o atributos no clave que dependen de otros atributos no clave. Revisar el diseño con más tablas."
    });

    return { results, parsedFDs };
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

function analyzeNormalization() {
    const payload = parseNormalizationInput();

    if (!payload.table || !payload.columns.length || !payload.primaryKeys.length) {
        showNormalizationError("Completa el nombre de tabla, las columnas y las claves primarias antes de analizar.");
        return;
    }

    const evaluation = evaluateNormalization(payload);
    const resultsElement = document.getElementById("norm-results");
    const output = document.getElementById("norm-output");

    if (!resultsElement || !output) return;

    resultsElement.innerHTML = formatNormalizationOutput(evaluation);
    output.hidden = false;
    showNormalizationError("");
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
