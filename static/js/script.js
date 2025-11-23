document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const uploadMessage = document.getElementById('uploadMessage');
    const fileInput = document.getElementById('fileInput');
    const tableNameInput = document.getElementById('tableName');
    const inputTypeRadios = document.getElementsByName('inputType');
    const textInput = document.getElementById('textInput');
    const speechButton = document.getElementById('speechButton');
    const textQuery = document.getElementById('textQuery');
    const submitQuery = document.getElementById('submitQuery');
    const resultsTable = document.getElementById('resultsTable');
    const tableHead = document.getElementById('tableHead');
    const tableBody = document.getElementById('tableBody');
    const sqlQueryDisplay = document.getElementById('sqlQuery');
    const errorMessage = document.getElementById('errorMessage');

    // Handle input type toggle
    inputTypeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'speech') {
                textInput.style.display = 'none';
                speechButton.style.display = 'block';
            } else {
                textInput.style.display = 'block';
                speechButton.style.display = 'none';
            }
        });
    });

    // File upload
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (data.error) {
                uploadMessage.textContent = data.error;
                uploadMessage.classList.add('text-danger');
            } else {
                uploadMessage.textContent = data.message;
                uploadMessage.classList.remove('text-danger');
                tableNameInput.value = data.table_name;
            }
        } catch (err) {
            uploadMessage.textContent = 'Upload failed';
            uploadMessage.classList.add('text-danger');
        }
    });

    // Speech recognition (Web Speech API)
    speechButton.addEventListener('click', () => {
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-US';
        recognition.start();
        speechButton.textContent = 'Listening...';
        recognition.onresult = (event) => {
            textQuery.value = event.results[0][0].transcript;
            speechButton.textContent = 'Start Speaking';
        };
        recognition.onend = () => {
            speechButton.textContent = 'Start Speaking';
        };
    });

    // Submit query
    submitQuery.addEventListener('click', async () => {
        const inputType = document.querySelector('input[name="inputType"]:checked').value;
        const tableName = tableNameInput.value;
        if (!tableName) {
            errorMessage.textContent = 'Please upload a CSV first';
            return;
        }

        const formData = new FormData();
        formData.append('input_type', inputType);
        formData.append('table_name', tableName);
        if (inputType === 'text') {
            formData.append('text_query', textQuery.value);
        }

        try {
            const response = await fetch('/query', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (data.error) {
                errorMessage.textContent = data.error;
                tableHead.innerHTML = '';
                tableBody.innerHTML = '';
                sqlQueryDisplay.textContent = '';
            } else {
                errorMessage.textContent = '';
                sqlQueryDisplay.textContent = `SQL Query: ${data.sql_query}`;
                
                // Render table
                tableHead.innerHTML = '<tr>' + data.columns.map(col => `<th>${col}</th>`).join('') + '</tr>';
                tableBody.innerHTML = data.results.map(row => 
                    '<tr>' + row.map(cell => `<td>${cell}</td>`).join('') + '</tr>'
                ).join('');
            }
        } catch (err) {
            errorMessage.textContent = 'Query failed';
        }
    });
});