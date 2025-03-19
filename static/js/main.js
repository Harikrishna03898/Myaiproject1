let tables = new Map();
let tableCount = 0;
let toast;

document.addEventListener('DOMContentLoaded', async () => {
    await loadProjects();
    toast = new bootstrap.Toast(document.getElementById('notification'));
});

function showNotification(message, type = 'success') {
    const toastEl = document.getElementById('notification');
    toastEl.querySelector('.toast-body').textContent = message;
    toastEl.classList.toggle('bg-danger', type === 'error');
    toastEl.classList.toggle('text-white', type === 'error');
    toast.show();
}

async function loadProjects() {
    try {
        const response = await fetch('/get_projects_list');
        const data = await response.json();
        if (data.status === 'success') {
            const select = document.getElementById('projectSelector');
            data.projects.forEach(p => {
                const option = document.createElement('option');
                option.value = p.project_id;
                option.textContent = `${p.project_id} - ${p.name}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        showNotification('Error loading projects: ' + error.message, 'error');
    }
}

// Add after loadProjects function
async function loadProject(projectId) {
    if (!projectId) return;
    
    try {
        const response = await fetch(`/get_project/${projectId}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            // Load project details
            document.getElementById('projectId').value = data.data.project_id;
            document.getElementById('projectName').value = data.data.name;
            document.getElementById('projectDetails').value = data.data.details;
            
            // Clear existing tables
            document.getElementById('tablesContainer').innerHTML = '';
            tables.clear();
            tableCount = 0;
            
            // Load tables
            if (data.data.tables) {
                for (const table of data.data.tables) {
                    await addTable(table);
                }
            }
            
            showNotification('Project loaded successfully');
        } else {
            showNotification(data.message || 'Failed to load project', 'error');
        }
    } catch (error) {
        showNotification('Error loading project: ' + error.message, 'error');
    }
}

async function addTable(tableData = null) {
    try {
        const response = await fetch('/static/templates/table_template.html');
        let template = await response.text();
        
        // Replace {id} with actual tableCount
        template = template.replace(/{id}/g, tableCount);
        
        const container = document.getElementById('tablesContainer');
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = template;
        const tableElement = tempDiv.firstElementChild;
        container.appendChild(tableElement);

        // Initialize table data
        if (tableData) {
            const tableDiv = document.getElementById(`table-${tableCount}`);
            tableDiv.querySelector('.table-name').value = tableData.table_name || '';
            tableDiv.querySelector('.odata-url').value = tableData.odata_url || '';
            tables.set(tableCount, {
                ...tableData,
                table_id: tableCount
            });
            if (tableData.odata_url) {
                await previewTable(tableDiv.querySelector('button'));
            }
        } else {
            tables.set(tableCount, {
                table_id: tableCount,
                table_name: '',
                odata_url: '',
                modifications: {
                    renames: {},
                    dtypes: {},
                    drops: []
                }
            });
        }
        
        tableCount++;
    } catch (error) {
        showNotification('Error adding table: ' + error.message, 'error');
    }
}

// Add after addTable function
async function previewTable(btn) {
    try {
        const tableDiv = btn.closest('.table-config');
        const tableId = parseInt(tableDiv.id.split('-')[1]);
        const url = tableDiv.querySelector('.odata-url').value;
        const tableName = tableDiv.querySelector('.table-name').value;
        const previewContainer = tableDiv.querySelector('.preview-container');

        if (!tableName) {
            showNotification('Please enter table name first', 'error');
            return;
        }

        if (!url) {
            showNotification('Please enter OData URL', 'error');
            return;
        }

        previewContainer.innerHTML = '<div class="alert alert-info">Loading data...</div>';

        const response = await fetch('/preview_with_modifications', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                modifications: tables.get(tableId)?.modifications
            })
        });

        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }

        // Update table data
        const currentTable = tables.get(tableId);
        tables.set(tableId, {
            ...currentTable,
            table_id: tableId,
            table_name: tableName,
            odata_url: url,
            columns: data.columns,
            dtypes: data.dtypes,
            modifications: currentTable?.modifications || {
                renames: {},
                dtypes: {},
                drops: []
            }
        });

        // Generate preview table
        let html = `
            <div class="preview-table mt-3">
                <h6>Column Preview</h6>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Column</th>
                            <th>Type</th>
                            <th>New Name</th>
                            <th>New Type</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>`;

        data.columns.forEach(col => {
            const isDeleted = currentTable?.modifications?.drops?.includes(col);
            html += `
                <tr class="${isDeleted ? 'deleted-row' : ''}" data-column="${col}">
                    <td>${col}</td>
                    <td>${data.dtypes[col]}</td>
                    <td>
                        <input type="text" class="form-control" placeholder="${col}" 
                               onchange="handleColumnChange(this, ${tableId}, '${col}', 'rename')"
                               value="${currentTable?.modifications?.renames[col] || ''}">
                    </td>
                    <td>
                        <select class="form-control" onchange="handleColumnChange(this, ${tableId}, '${col}', 'dtype')">
                            <option value="string" ${data.dtypes[col] === 'object' ? 'selected' : ''}>string</option>
                            <option value="int64" ${data.dtypes[col] === 'int64' ? 'selected' : ''}>integer</option>
                            <option value="float64" ${data.dtypes[col] === 'float64' ? 'selected' : ''}>float</option>
                            <option value="datetime64" ${data.dtypes[col].includes('datetime') ? 'selected' : ''}>datetime</option>
                            <option value="boolean" ${data.dtypes[col] === 'bool' ? 'selected' : ''}>boolean</option>
                            <option value="convertedDate">convertedDate</option>
                        </select>
                    </td>
                    <td>
                        <button class="btn btn-sm ${isDeleted ? 'btn-danger' : 'btn-outline-danger'}" 
                                onclick="toggleDelete(this, ${tableId}, '${col}')">
                            ${isDeleted ? 'Deleted' : 'Delete'}
                        </button>
                    </td>
                </tr>`;
        });

        html += '</tbody></table></div>';
        previewContainer.innerHTML = html;

        // Generate initial schema
        updateSchema(tableId);

    } catch (error) {
        showNotification('Error previewing table: ' + error.message, 'error');
        if (previewContainer) {
            previewContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        }
    }
}

// Add after previewTable function
function handleColumnChange(element, tableId, column, type) {
    const table = tables.get(tableId);
    if (type === 'rename' && element.value) {
        table.modifications.renames[column] = element.value;
    } else if (type === 'dtype') {
        table.modifications.dtypes[column] = element.value;
    }
    updateSchema(tableId);
}

function toggleDelete(btn, tableId, column) {
    const table = tables.get(tableId);
    const row = btn.closest('tr');
    
    if (table.modifications.drops.includes(column)) {
        table.modifications.drops = table.modifications.drops.filter(c => c !== column);
        row.classList.remove('deleted-row');
        btn.classList.replace('btn-danger', 'btn-outline-danger');
        btn.textContent = 'Delete';
    } else {
        table.modifications.drops.push(column);
        row.classList.add('deleted-row');
        btn.classList.replace('btn-outline-danger', 'btn-danger');
        btn.textContent = 'Deleted';
    }
    updateSchema(tableId);
}

function updateSchema(tableId) {
    const table = tables.get(tableId);
    const tableDiv = document.getElementById(`table-${tableId}`);
    
    // Filter out dropped columns
    const activeColumns = table.columns.filter(col => !table.modifications.drops.includes(col));
    
    // Apply renames
    const renamedColumns = activeColumns.map(col => 
        table.modifications.renames[col] || col
    );
    
    // Apply dtypes
    const finalDtypes = {};
    activeColumns.forEach(col => {
        const renamed = table.modifications.renames[col] || col;
        finalDtypes[renamed] = table.modifications.dtypes[col] || table.dtypes[col];
    });
    
    // Generate schema
    fetch('/generate_schema', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            table_name: table.table_name,
            columns: renamedColumns,
            dtypes: finalDtypes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        table.sql_schema = data.schema;
        tableDiv.querySelector('.schema-display').textContent = data.schema;
    })
    .catch(error => {
        showNotification('Error generating schema: ' + error.message, 'error');
    });
}

async function saveProject() {
    try {
        const projectData = {
            project_id: document.getElementById('projectId').value,
            name: document.getElementById('projectName').value,
            details: document.getElementById('projectDetails').value,
            tables: Array.from(tables.values()).map(table => ({
                ...table,
                table_name: document.getElementById(`table-${table.table_id}`).querySelector('.table-name').value
            }))
        };

        const response = await fetch('/save_project', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData)
        });
        
        const result = await response.json();
        showNotification(result.message, result.status);
        
        if (result.status === 'success') {
            // Refresh projects list
            document.getElementById('projectSelector').innerHTML = '<option value="">Select Existing Project</option>';
            await loadProjects();
        }
    } catch (error) {
        showNotification('Error saving project: ' + error.message, 'error');
    }
}