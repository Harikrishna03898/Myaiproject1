let toast;
let currentProjectToDelete;

document.addEventListener('DOMContentLoaded', () => {
    toast = new bootstrap.Toast(document.getElementById('notification'));
    loadProjects();
    loadUsers();
    loadPolicies();
});

function showNotification(message, type = 'success') {
    const toastEl = document.getElementById('notification');
    toastEl.querySelector('.toast-body').textContent = message;
    toastEl.classList.toggle('bg-danger', type === 'error');
    toast.show();
}

// Projects Management
async function loadProjects() {
    try {
        const response = await fetch('/get_projects_list');
        const data = await response.json();
        
        const tbody = document.getElementById('projectsList');
        tbody.innerHTML = data.projects.map(p => `
            <tr>
                <td>${p.project_id}</td>
                <td>${p.name}</td>
                <td>${p.details || ''}</td>
                <td>
                    <button class="btn btn-info btn-sm" onclick="showProjectInfo('${p.project_id}')">Info</button>
                    <button class="btn btn-danger btn-sm" onclick="showDeleteConfirm('${p.project_id}')">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        showNotification('Error loading projects: ' + error.message, 'error');
    }
}

function showProjectInfo(projectId) {
    fetch(`/get_project/${projectId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('projectInfo').textContent = JSON.stringify(data.data, null, 2);
            document.getElementById('projectInfoModal').style.display = 'block';
        })
        .catch(error => showNotification('Error loading project info: ' + error.message, 'error'));
}

function showDeleteConfirm(projectId) {
    currentProjectToDelete = projectId;
    document.getElementById('deleteConfirmModal').style.display = 'block';
}

async function confirmDelete() {
    try {
        const response = await fetch(`/delete_project/${currentProjectToDelete}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Project deleted successfully');
            loadProjects();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        showNotification('Error deleting project: ' + error.message, 'error');
    } finally {
        closeModal('deleteConfirmModal');
    }
}

// Users Management
async function loadUsers() {
    try {
        const response = await fetch('/get_users');
        const data = await response.json();
        
        if (data.status === 'success') {
            const tbody = document.getElementById('usersList');
            tbody.innerHTML = (data.users || []).map(u => `
                <tr>
                    <td>${u.user_id}</td>
                    <td>${u.user_name}</td>
                    <td>${u.user_details || ''}</td>
                    <td>${u.access_id}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" 
                                onclick="deleteUser('${u.user_id}')">
                            Delete
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        showNotification('Error loading users: ' + error.message, 'error');
    }
}

// Access Policies Management
async function loadPolicies() {
    try {
        const response = await fetch('/get_access_policies');
        const data = await response.json();
        
        if (data.status === 'success') {
            const tbody = document.getElementById('policiesList');
            tbody.innerHTML = (data.policies || []).map(p => `
                <tr>
                    <td>${p.access_id}</td>
                    <td>${p.projects?.join(', ') || ''}</td>
                    <td>${p.tables?.map(t => t.table_name).join(', ') || ''}</td>
                    <td>${p.access_details || ''}</td>
                    <td>
                        <button class="btn btn-info btn-sm me-2" 
                                onclick="viewPolicyInfo('${p.access_id}')">
                            View
                        </button>
                        <button class="btn btn-danger btn-sm"
                                onclick="deleteAccessPolicy('${p.access_id}')">
                            Delete
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        showNotification('Error loading policies: ' + error.message, 'error');
    }
}

// Add new function for deleting access policy
async function deleteAccessPolicy(accessId) {
    if (!confirm(`Are you sure you want to delete access policy ${accessId}?`)) {
        return;
    }

    try {
        const response = await fetch(`/delete_access_policy/${accessId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Access policy deleted successfully');
            loadPolicies();  // Refresh the list
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        showNotification('Error deleting access policy: ' + error.message, 'error');
    }
}

async function loadPolicyTables() {
    const selectedProjects = Array.from(document.getElementById('policyProjects').selectedOptions)
        .map(option => option.value);
    
    try {
        const tablesDiv = document.getElementById('policyTables');
        tablesDiv.innerHTML = '';
        
        for (const projectId of selectedProjects) {
            const response = await fetch('/get_project_tables', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: projectId })
            });
            const data = await response.json();
            
            const projectTables = document.createElement('div');
            projectTables.innerHTML = `
                <h6 class="mt-2">Project ${projectId} Tables:</h6>
                ${data.tables.map(table => `
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" 
                               value="${table.table_id}" 
                               data-project="${projectId}"
                               onchange="loadTableColumns(this)">
                        <label class="form-check-label">
                            ${table.table_name}
                        </label>
                    </div>
                `).join('')}
            `;
            tablesDiv.appendChild(projectTables);
        }
    } catch (error) {
        showNotification('Error loading tables: ' + error.message, 'error');
    }
}

// Update loadTableColumns function to use safe IDs
async function loadTableColumns(checkbox) {
    const projectId = checkbox.dataset.project;
    const tableId = checkbox.value;
    const columnsDiv = document.getElementById('policyColumns');
    
    // Create safe ID
    const safeId = `columns-${projectId.replace(/[^a-zA-Z0-9]/g, '_')}-${tableId}`;
    
    if (!checkbox.checked) {
        const existingColumns = document.getElementById(safeId);
        if (existingColumns) existingColumns.remove();
        return;
    }
    
    try {
        const response = await fetch('/get_table_columns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: projectId, table_id: parseInt(tableId) })
        });
        const data = await response.json();
        
        const columnSection = document.createElement('div');
        columnSection.id = safeId;
        columnSection.innerHTML = `
            <h6 class="mt-3">Columns for Table ${tableId}:</h6>
            ${data.columns.map(col => `
                <div class="mb-2">
                    <div class="form-check d-inline-block">
                        <input class="form-check-input" type="checkbox" 
                               value="${col}" name="columns[]">
                        <label class="form-check-label">${col}</label>
                    </div>
                    <div class="value-filter d-inline-block">
                        <input type="text" class="form-control form-control-sm" 
                               placeholder="Value filter" 
                               data-column="${col}">
                    </div>
                </div>
            `).join('')}
        `;
        columnsDiv.appendChild(columnSection);
    } catch (error) {
        showNotification('Error loading columns: ' + error.message, 'error');
    }
}

function showAddUserModal() {
    document.getElementById('addUserForm').reset();
    document.getElementById('addUserModal').style.display = 'block';
}

function showAddPolicyModal() {
    document.getElementById('addPolicyForm').reset();
    loadProjectsForPolicy();
    document.getElementById('addPolicyModal').style.display = 'block';
}

async function loadProjectsForPolicy() {
    try {
        const response = await fetch('/get_projects_list');
        const data = await response.json();
        
        const select = document.getElementById('policyProjects');
        select.innerHTML = data.projects.map(p => `
            <option value="${p.project_id}">${p.project_id} - ${p.name}</option>
        `).join('');
    } catch (error) {
        showNotification('Error loading projects: ' + error.message, 'error');
    }
}

// Form submission handlers
document.getElementById('addUserForm').onsubmit = async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const userData = {
        user_id: formData.get('user_id'),
        user_name: formData.get('user_name'),
        user_details: formData.get('user_details'),
        access_id: parseInt(formData.get('access_id'))
    };
    
    try {
        const response = await fetch('/add_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            showNotification('User added successfully');
            loadUsers();
            closeModal('addUserModal');
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        showNotification('Error adding user: ' + error.message, 'error');
    }
};

// Update the addPolicyForm submit handler
document.getElementById('addPolicyForm').onsubmit = async (e) => {
    e.preventDefault();
    
    try {
        const selectedProjects = Array.from(document.getElementById('policyProjects').selectedOptions)
            .map(option => option.value);
        
        const tables = [];
        document.querySelectorAll('#policyTables input:checked').forEach(checkbox => {
            const projectId = checkbox.dataset.project;
            const tableId = parseInt(checkbox.value);
            
            // Create a safe ID for querying
            const safeId = `columns-${projectId.replace(/[^a-zA-Z0-9]/g, '_')}-${tableId}`;
            const columnsDiv = document.getElementById(safeId);
            
            if (columnsDiv) {
                const columns = {};
                columnsDiv.querySelectorAll('input[type="checkbox"]:checked').forEach(colCheckbox => {
                    const colName = colCheckbox.value;
                    const filterInput = columnsDiv.querySelector(`input[data-column="${colName}"]`);
                    const filterValue = filterInput ? filterInput.value : null;
                    columns[colName] = filterValue || null;
                });
                
                if (Object.keys(columns).length > 0) {
                    tables.push({
                        project_id: projectId,
                        table_id: tableId,
                        columns: columns
                    });
                }
            }
        });
        
        const formData = new FormData(e.target);
        const policyData = {
            access_id: formData.get('access_id'),
            projects: selectedProjects,
            tables: tables,
            updated_at: new Date().toISOString()
        };
        
        const response = await fetch('/add_access_policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(policyData)
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            showNotification('Access policy updated successfully');
            loadPolicies();
            closeModal('addPolicyModal');
            e.target.reset();
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        showNotification('Error updating access policy: ' + error.message, 'error');
        console.error('Error:', error);
    }
};

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Add/Update these functions

function toggleAllProjects() {
    const select = document.getElementById('policyProjects');
    const options = select.options;
    const allSelected = Array.from(options).every(opt => opt.selected);
    
    for (let opt of options) {
        opt.selected = !allSelected;
    }
    loadPolicyTables();
}

function toggleAllTables() {
    const checkboxes = document.querySelectorAll('#policyTables input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    
    checkboxes.forEach(cb => {
        cb.checked = !allChecked;
        if (!allChecked) loadTableColumns(cb);
    });
}

function toggleAllColumns(projectId, tableId) {
    const container = tableId ? 
        document.querySelector(`#columns-${projectId}-${tableId}`) : 
        document.getElementById('policyColumns');
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    
    checkboxes.forEach(cb => cb.checked = !allChecked);
}

function viewPolicyInfo(accessId) {
    fetch(`/get_access_policy/${accessId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.data) {
                // Format the JSON data for display
                const formattedJson = JSON.stringify(data.data, null, 2);
                document.getElementById('projectInfo').textContent = formattedJson;
                document.getElementById('projectInfoModal').style.display = 'block';
            } else {
                showNotification('No policy data found', 'error');
            }
        })
        .catch(error => showNotification('Error loading policy info: ' + error.message, 'error'));
}

// Add these new functions

async function deleteUser(userId) {
    if (!confirm(`Are you sure you want to delete user ${userId}?`)) {
        return;
    }

    try {
        const response = await fetch(`/delete_user/${userId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('User deleted successfully');
            loadUsers();  // Refresh the list
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        showNotification('Error deleting user: ' + error.message, 'error');
    }
}

async function deleteAccessPolicy(accessId) {
    if (!confirm(`Are you sure you want to delete access policy ${accessId}?`)) {
        return;
    }

    try {
        const response = await fetch(`/delete_access_policy/${accessId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification('Access policy deleted successfully');
            loadPolicies();  // Refresh the list
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        showNotification('Error deleting access policy: ' + error.message, 'error');
    }
}