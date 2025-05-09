

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('uploadForm');
  const fileInput = document.getElementById('fileInput');
  const dropZone = document.getElementById('dropZone');
  const browseButton = document.getElementById('browseButton');
  const submitButton = document.getElementById('submitButton');
  const progressContainer = document.getElementById('progressContainer');
  const progressBar = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');
  const messageDisplay = document.getElementById('messageDisplay');
  const downloadOptions = document.getElementById('downloadOptions');
  const fileIcon = document.getElementById('fileIcon');
  const uploadText = document.getElementById('uploadText');

  let selectedFile = null;

  // Function to reset UI elements
  const resetUI = () => {
      selectedFile = null;
      fileInput.value = ''; // Clear the file input
      dropZone.classList.remove('border-emerald-400', 'bg-emerald-50', 'border-blue-500', 'bg-blue-50');
      dropZone.classList.add('border-slate-300', 'hover:border-blue-400');
      
      fileIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M12 12v6"/><path d="m15 15-3-3-3 3"/></svg>`;
      fileIcon.classList.remove('bg-emerald-100', 'text-emerald-600');
      fileIcon.classList.add('bg-blue-100', 'text-blue-600');
      
      uploadText.innerHTML = `
        <div class="space-y-1">
          <p class="text-sm font-medium text-slate-900">Upload your PDF statement</p>
          <p class="text-xs text-slate-500">Drag & drop your file here or click to browse</p>
        </div>
      `;
      
      browseButton.style.display = 'block'; // Show browse button again
      submitButton.disabled = true;
      submitButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        Upload & Convert
      `;
      submitButton.classList.add('bg-slate-200', 'text-slate-400', 'cursor-not-allowed');
      submitButton.classList.remove('bg-gradient-to-r', 'from-blue-600', 'to-indigo-600', 'text-white', 'shadow-md', 'hover:shadow-lg', 'hover:from-blue-700', 'hover:to-indigo-700', 'transform', 'hover:-translate-y-0.5');
      
      progressContainer.classList.add('hidden');
      progressBar.style.width = '0%';
      progressText.textContent = 'Processing... 0%';
      messageDisplay.classList.add('hidden');
      downloadOptions.classList.add('hidden');
      const downloadButtonsContainer = downloadOptions.querySelector('.grid');
      if(downloadButtonsContainer) downloadButtonsContainer.innerHTML = ''; // Clear old buttons
  };

  // Handle file selection
  const handleFileSelect = (file) => {
    // Always clear previous messages and download options when a new selection attempt is made
    messageDisplay.classList.add('hidden');
    downloadOptions.classList.add('hidden');

    if (file && file.type === 'application/pdf') {
      selectedFile = file;

      // Update UI for a successfully selected file
      dropZone.classList.remove('border-slate-300', 'hover:border-blue-400', 'border-blue-500', 'bg-blue-50');
      dropZone.classList.add('border-emerald-400', 'bg-emerald-50');
      
      fileIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>`; // PDF/File selected icon
      fileIcon.classList.remove('bg-blue-100', 'text-blue-600');
      fileIcon.classList.add('bg-emerald-100', 'text-emerald-600');
      
      uploadText.innerHTML = `
        <div class="space-y-1">
          <p class="text-sm font-medium text-slate-900">Selected file:</p>
          <p class="text-sm font-medium text-emerald-600" id="selectedFileName"></p>
        </div>
      `;
      const selectedFileNameP = uploadText.querySelector('#selectedFileName');
      if (selectedFileNameP) {
        selectedFileNameP.textContent = file.name;
      }
      
      browseButton.style.display = 'none';
      submitButton.disabled = false;
      // Ensure submit button has its original text and icon when enabled
      submitButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        Upload & Convert
      `;
      submitButton.classList.remove('bg-slate-200', 'text-slate-400', 'cursor-not-allowed');
      submitButton.classList.add('bg-gradient-to-r', 'from-blue-600', 'to-indigo-600', 'text-white', 'shadow-md', 'hover:shadow-lg', 'hover:from-blue-700', 'hover:to-indigo-700', 'transform', 'hover:-translate-y-0.5');
    } else {
      // Invalid file, no file selected, or non-PDF file
      if (file) { // A file was provided, but it's not a valid PDF
        showError('Please upload a valid PDF file.');
      }
      // Call resetUI to handle all aspects of resetting to the initial state
      // This will set selectedFile = null, disable submitButton, and reset UI elements.
      resetUI();
    }
  };

  // File input change handler
  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  });

  // Browse button click handler
  browseButton.addEventListener('click', () => {
    fileInput.click();
  });

  // Drag and drop handlers
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-slate-300', 'hover:border-blue-400');
    dropZone.classList.add('border-blue-500', 'bg-blue-50');
  });

  dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    if (!selectedFile) {
      dropZone.classList.remove('border-blue-500', 'bg-blue-50');
      dropZone.classList.add('border-slate-300', 'hover:border-blue-400');
    }
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    } else {
       dropZone.classList.remove('border-blue-500', 'bg-blue-50');
       dropZone.classList.add('border-slate-300', 'hover:border-blue-400');
    }
  });

  // Show error message
  const showError = (message) => {
    // Construct the error message display safely
    messageDisplay.innerHTML = `
      <div role="alert" class="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg shadow-md animate-appear">
        <div class="flex items-start">
          <svg class="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <div class="ml-3">
            <p class="text-sm font-medium text-red-800">Error:</p>
            <p class="text-sm text-red-700 mt-1" id="errorMessageText"></p>
          </div>
        </div>
      </div>
    `;
    const errorMessageTextP = messageDisplay.querySelector('#errorMessageText');
    if (errorMessageTextP) {
        errorMessageTextP.textContent = message;
    }
    messageDisplay.classList.remove('hidden');
    downloadOptions.classList.add('hidden'); // Hide download options on error
  };

  // Show success message
  const showSuccess = (message) => {
    // Construct the success message display safely
    // Note: If the success message needs to include HTML (like a link for GSheets),
    // that part is now handled by the Django template. This JS function will only handle plain text messages.
    messageDisplay.innerHTML = `
      <div role="alert" class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg shadow-md animate-appear">
        <div class="flex items-start">
          <svg class="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <div class="ml-3">
            <p class="text-sm text-blue-700" id="successMessageText"></p>
          </div>
        </div>
      </div>
    `;
    const successMessageTextP = messageDisplay.querySelector('#successMessageText');
    if (successMessageTextP) {
        successMessageTextP.textContent = message;
    }
    messageDisplay.classList.remove('hidden');
  };

  // Show download options - Updated to create actual links
  const showDownloadOptions = () => {
      const downloadButtonsContainer = downloadOptions.querySelector('.grid');
      if (!downloadButtonsContainer) return;

      // Retrieve URLs from data attributes stored on the #downloadOptions element
      const csvUrl = downloadOptions.dataset.csvUrl;
      const excelUrl = downloadOptions.dataset.excelUrl;
      const jsonUrl = downloadOptions.dataset.jsonUrl;
      const gsheetsUrl = downloadOptions.dataset.gsheetsUrl;

      downloadButtonsContainer.innerHTML = `
        <a href="${csvUrl}" download class="relative group flex flex-col items-center justify-center p-4 bg-white border border-slate-200 rounded-xl shadow-sm transition-all duration-300 hover:shadow-md hover:border-green-300 hover:bg-green-50/50 overflow-hidden">
          <div class="absolute inset-0 bg-gradient-to-br from-green-600 to-green-500 opacity-0 group-hover:opacity-5 transition-opacity duration-300"></div>
          <div class="w-12 h-12 mb-3 flex items-center justify-center rounded-full bg-gradient-to-br from-green-600 to-green-500 text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M8 13h2"/><path d="M8 17h2"/><path d="M14 13h2"/><path d="M14 17h2"/></svg>
          </div>
          <span class="font-medium text-slate-800 group-hover:text-green-700">CSV</span>
          <span class="text-xs text-slate-500 mt-1">Download as CSV file</span>
          <div class="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-green-500 to-transparent transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
        </a>

        <a href="${excelUrl}" download class="relative group flex flex-col items-center justify-center p-4 bg-white border border-slate-200 rounded-xl shadow-sm transition-all duration-300 hover:shadow-md hover:border-emerald-300 hover:bg-emerald-50/50 overflow-hidden">
          <div class="absolute inset-0 bg-gradient-to-br from-emerald-600 to-emerald-500 opacity-0 group-hover:opacity-5 transition-opacity duration-300"></div>
          <div class="w-12 h-12 mb-3 flex items-center justify-center rounded-full bg-gradient-to-br from-emerald-600 to-emerald-500 text-white">
             <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M12 18h-1v-2h1a1 1 0 0 0 1-1v-1a1 1 0 0 0-1-1H9v6h3"/><path d="m17 18-3-3 3-3"/><path d="m14 18 3-3-3-3"/></svg>
          </div>
          <span class="font-medium text-slate-800 group-hover:text-emerald-700">Excel</span>
          <span class="text-xs text-slate-500 mt-1">Download as Excel file</span>
          <div class="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-emerald-500 to-transparent transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
        </a>

        <a href="${jsonUrl}" download class="relative group flex flex-col items-center justify-center p-4 bg-white border border-slate-200 rounded-xl shadow-sm transition-all duration-300 hover:shadow-md hover:border-amber-300 hover:bg-amber-50/50 overflow-hidden">
           <div class="absolute inset-0 bg-gradient-to-br from-amber-600 to-amber-500 opacity-0 group-hover:opacity-5 transition-opacity duration-300"></div>
          <div class="w-12 h-12 mb-3 flex items-center justify-center rounded-full bg-gradient-to-br from-amber-600 to-amber-500 text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="m9 15 3 3 3-3"/></svg>
          </div>
          <span class="font-medium text-slate-800 group-hover:text-amber-700">JSON</span>
          <span class="text-xs text-slate-500 mt-1">Download as JSON file</span>
          <div class="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-amber-500 to-transparent transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
        </a>

        <a href="${gsheetsUrl}" id="googleSheetsButton" class="relative group flex flex-col items-center justify-center p-4 bg-white border border-slate-200 rounded-xl shadow-sm transition-all duration-300 hover:shadow-md hover:border-cyan-300 hover:bg-cyan-50/50 overflow-hidden">
           <div class="absolute inset-0 bg-gradient-to-br from-cyan-600 to-cyan-500 opacity-0 group-hover:opacity-5 transition-opacity duration-300"></div>
          <div class="w-12 h-12 mb-3 flex items-center justify-center rounded-full bg-gradient-to-br from-cyan-600 to-cyan-500 text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h14a2 2 0 0 0 2-2V7.5L14.5 2H6a2 2 0 0 0-2 2v4"/><polyline points="14 2 14 8 20 8"/><path d="M3 15h6"/><path d="M3 18h6"/><path d="M11 15h6"/><path d="M11 18h6"/></svg>
          </div>
          <span class="font-medium text-slate-800 group-hover:text-cyan-700">Google Sheets</span>
          <span class="text-xs text-slate-500 mt-1">Upload directly to Sheets</span>
           <div class="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-500 to-transparent transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
        </a>
      `;
      downloadOptions.classList.remove('hidden');
  };

   // Handle form submission with Fetch API
  if (form) { // Check if form element exists before adding listener
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

    if (!selectedFile) {
      console.error('No file selected, aborting submission.'); // New log
      showError('No file selected. Please choose a PDF file to upload.'); // User-facing message
      return;
    }

    // Reset previous messages/options
    messageDisplay.classList.add('hidden');
    downloadOptions.classList.add('hidden');
    progressContainer.classList.remove('hidden');
    progressBar.style.width = '0%';
    progressText.textContent = 'Uploading... 0%';
    submitButton.disabled = true;
    // Add loading indicator to submit button
    submitButton.innerHTML = `
      <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Processing...
    `;

    const formData = new FormData();
    formData.append('pdf_file', selectedFile);
    // Include CSRF token if not already handled by middleware/headers
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value; 

    try {
      // --- Progress Simulation ---
      progressBar.style.width = `10%`;
      progressText.textContent = `Uploading... 10%`;
      await new Promise(resolve => setTimeout(resolve, 150));
      progressBar.style.width = `30%`;
      progressText.textContent = `Uploading... 30%`;
      await new Promise(resolve => setTimeout(resolve, 250));
      // --- End Simulation ---

      const response = await fetch(form.action, { // Use form's action URL
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest', // Identify as AJAX request
        },
        body: formData,
      });

      progressText.textContent = 'Analyzing statement (this may take a moment)...';
      progressBar.style.width = `75%`; // Indicate analysis phase

      // Check if response is ok (status in the range 200-299)
      if (!response.ok) {
          // Try to get error message from JSON response if possible
          let errorMsg = `Server error: ${response.status} ${response.statusText}`;
          try {
              const errorResult = await response.json();
              if (errorResult && errorResult.errors && errorResult.errors.pdf_file && errorResult.errors.pdf_file[0] && errorResult.errors.pdf_file[0].message) {
                  errorMsg = `Error with PDF file: ${errorResult.errors.pdf_file[0].message}`;
              } else if (errorResult && errorResult.message) {
                  errorMsg = errorResult.message;
              }
          } catch (e) { /* Ignore if response is not JSON, keep original errorMsg */ }
          throw new Error(errorMsg);
      }

      const result = await response.json(); // Parse JSON response

      progressContainer.classList.add('hidden'); // Hide progress bar on completion

      if (result.status === 'success') {
        showSuccess(result.message); // Use message from server
        // Only show download options if results_ready is true in the response
        if (result.results_ready) {
            showDownloadOptions();
        } else {
             downloadOptions.classList.add('hidden'); // Ensure hidden if no results
        }
      } else {
        // Handle error status from JSON response
        let detailedErrorMsg = result.message || 'An unknown error occurred processing the file.';
        if (result.errors && result.errors.pdf_file && result.errors.pdf_file[0] && result.errors.pdf_file[0].message) {
            detailedErrorMsg = `Error with PDF file: ${result.errors.pdf_file[0].message}`;
        }
        showError(detailedErrorMsg);
      }

    } catch (error) { // Catch fetch errors or errors thrown above
      console.error('Upload error:', error);
      showError(`Upload failed: ${error.message}`);
      progressContainer.classList.add('hidden');
    } finally {
      // Restore submit button
      submitButton.disabled = false; // Re-enable after processing
       submitButton.innerHTML = `
         <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
         Upload & Convert
       `;
       // Don't reset the whole UI here, just the button state
    }
  });
  } else {
    console.error('script.js: Could not find form element with ID "uploadForm". Submit event listener NOT added.');
  }

  // Removed redundant diagnostic click listener for submitButton.
  // The primary 'submit' event listener on the form (around line 209) handles submission.

  // Note: Google Sheets upload still uses a direct link for auth,
  // actual upload logic would need another fetch call after auth.
  // The handleGoogleSheetsUpload function below is just a placeholder.
  window.handleGoogleSheetsUpload = () => {
     // This function is now mostly handled by the link's href pointing to the Django view
     // We could add a loading indicator here if desired before the redirect happens.
     // Optionally show a spinner briefly before the browser navigates
 };

 // Check if download options should be shown on page load (e.g., after redirect)
 if (downloadOptions && downloadOptions.dataset.showOnLoad === 'true') {
   showDownloadOptions();
   
   // Selectively reset form elements needed for a new upload,
   // without hiding the server-rendered message in messageDisplay.
   fileInput.value = ''; // Clear the file input if any was somehow selected
   selectedFile = null; // Ensure no file is considered selected by JS logic

   // Reset submit button to its initial disabled state
   submitButton.disabled = true;
   submitButton.innerHTML = `
     <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
     Upload & Convert
   `;
   submitButton.classList.add('bg-slate-200', 'text-slate-400', 'cursor-not-allowed');
   submitButton.classList.remove('bg-gradient-to-r', 'from-blue-600', 'to-indigo-600', 'text-white', 'shadow-md', 'hover:shadow-lg', 'hover:from-blue-700', 'hover:to-indigo-700', 'transform', 'hover:-translate-y-0.5');

   // Ensure browse button is visible
   browseButton.style.display = 'block';

   // Ensure dropzone is in its initial visual state (not success/error state from a previous JS interaction)
   dropZone.classList.remove('border-emerald-400', 'bg-emerald-50', 'border-blue-500', 'bg-blue-50');
   dropZone.classList.add('border-slate-300', 'hover:border-blue-400');
   fileIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M12 12v6"/><path d="m15 15-3-3-3 3"/></svg>`;
   fileIcon.classList.remove('bg-emerald-100', 'text-emerald-600');
   fileIcon.classList.add('bg-blue-100', 'text-blue-600');
   uploadText.innerHTML = `
     <div class="space-y-1">
       <p class="text-sm font-medium text-slate-900">Upload your PDF statement</p>
       <p class="text-xs text-slate-500">Drag & drop your file here or click to browse</p>
     </div>
   `;
   // Do NOT hide messageDisplay here, as it might contain a server-rendered message.
   // Do NOT hide downloadOptions as we just showed them.
 }
});