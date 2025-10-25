// Custom JavaScript for Pensieve Log

document.addEventListener('DOMContentLoaded', function() {
    
    // Copy API key to clipboard functionality
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const apiKey = this.getAttribute('data-api-key');
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            
            // Copy to clipboard
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(apiKey).then(() => {
                    showCopySuccess(button);
                    showToast();
                }).catch(err => {
                    console.error('Failed to copy:', err);
                    fallbackCopy(input, button);
                });
            } else {
                fallbackCopy(input, button);
            }
        });
    });
    
    // Fallback copy method for older browsers
    function fallbackCopy(input, button) {
        input.select();
        input.setSelectionRange(0, 99999); // For mobile devices
        
        try {
            document.execCommand('copy');
            showCopySuccess(button);
            showToast();
        } catch (err) {
            alert('Failed to copy API key. Please copy manually.');
        }
    }
    
    // Show visual feedback on copy button
    function showCopySuccess(button) {
        const originalHTML = button.innerHTML;
        const originalClass = button.className;
        
        button.innerHTML = '<i class="bi bi-check"></i>';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.className = originalClass;
        }, 2000);
    }
    
    // Show toast notification
    function showToast() {
        const toastEl = document.getElementById('copyToast');
        if (toastEl) {
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
        }
    }
    
    // Form validation for signup
    const signupForm = document.querySelector('form[action*="signup"]');
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password');
            const password2 = document.getElementById('password2');
            
            if (password && password2) {
                if (password.value !== password2.value) {
                    e.preventDefault();
                    alert('Passwords do not match!');
                    password2.focus();
                    return false;
                }
                
                if (password.value.length < 8) {
                    e.preventDefault();
                    alert('Password must be at least 8 characters long!');
                    password.focus();
                    return false;
                }
            }
        });
    }
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Confirm before regenerating API key
    const regenerateForms = document.querySelectorAll('form input[value="regenerate"]');
    regenerateForms.forEach(input => {
        const form = input.closest('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                if (!confirm('Are you sure you want to regenerate the API key? The old key will stop working immediately.')) {
                    e.preventDefault();
                    return false;
                }
            });
        }
    });
    
    // Confirm before deleting project
    const deleteForms = document.querySelectorAll('form input[value="delete"]');
    deleteForms.forEach(input => {
        const form = input.closest('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                if (!confirm('Are you sure you want to delete this project? All associated data will be permanently lost.')) {
                    e.preventDefault();
                    return false;
                }
            });
        }
    });
    
    // Project name validation
    const projectNameInput = document.getElementById('project_name');
    if (projectNameInput) {
        projectNameInput.addEventListener('input', function() {
            // Remove leading/trailing spaces and limit length
            this.value = this.value.trim();
            if (this.value.length > 200) {
                this.value = this.value.substring(0, 200);
            }
        });
    }
    
    // Auto-focus on modal open
    const createProjectModal = document.getElementById('createProjectModal');
    if (createProjectModal) {
        createProjectModal.addEventListener('shown.bs.modal', function () {
            const projectNameInput = document.getElementById('project_name');
            if (projectNameInput) {
                projectNameInput.focus();
            }
        });
    }
});
