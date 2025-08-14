/* 
 * Modal fix script for student verification page
 * This script modifies Bootstrap's Modal handling to ensure modals never get stuck
 * Enhanced version with more aggressive fallback strategies
 */

// Add this script to the bottom of the page just before </body>
window.addEventListener('DOMContentLoaded', function() {
    console.log('Modal fix script loaded');
    
    // Monkey patch bootstrap modal to ensure it always closes
    if (window.bootstrap && window.bootstrap.Modal) {
        // Override the hide method
        const originalHide = bootstrap.Modal.prototype.hide;
        bootstrap.Modal.prototype.hide = function() {
            try {
                // Call original method
                originalHide.apply(this, arguments);
                
                // Additional clean-up
                setTimeout(() => {
                    try {
                        const modalElement = this._element;
                        if (modalElement && modalElement.classList.contains('show')) {
                            console.log('Modal still visible after hide() - forcing cleanup');
                            modalElement.classList.remove('show');
                            modalElement.style.display = 'none';
                            document.body.classList.remove('modal-open');
                            document.body.style.overflow = '';
                            document.body.style.paddingRight = '';
                            document.querySelectorAll('.modal-backdrop').forEach(el => {
                                try { el.remove(); } catch (e) { 
                                    if (el.parentNode) el.parentNode.removeChild(el); 
                                }
                            });
                        }
                    } catch (e) {
                        console.error('Error in modal cleanup:', e);
                    }
                }, 300);
            } catch (e) {
                console.error('Error in modal hide override:', e);
                
                // Emergency fallback
                try {
                    document.querySelectorAll('.modal-backdrop').forEach(el => {
                        try { el.remove(); } catch (e) { 
                            if (el.parentNode) el.parentNode.removeChild(el); 
                        }
                    });
                    
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                    
                    const modalElements = document.querySelectorAll('.modal.show');
                    modalElements.forEach(el => {
                        el.classList.remove('show');
                        el.style.display = 'none';
                    });
                } catch (err) {
                    console.error('Fatal error in modal cleanup:', err);
                }
            }
        };
        
        // Add global function to force close any modal
        window.forceCloseAllModals = function() {
            console.log('Force closing all modals');
            
            // Try to close all modals via Bootstrap API
            document.querySelectorAll('.modal.show').forEach(modal => {
                try {
                    const instance = bootstrap.Modal.getInstance(modal);
                    if (instance) instance.hide();
                } catch (e) {
                    console.warn('Error closing modal via Bootstrap:', e);
                }
            });
            
            // Brute force cleanup of all modal elements and classes
            try {
                // Remove backdrops
                document.querySelectorAll('.modal-backdrop').forEach(el => {
                    try { el.remove(); } catch (e) { 
                        if (el.parentNode) el.parentNode.removeChild(el); 
                    }
                });
                
                // Reset body classes and styles
                document.body.className = document.body.className.replace(/\bmodal-open\b/, '');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
                
                // Hide all modals
                document.querySelectorAll('.modal').forEach(modal => {
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                    modal.setAttribute('aria-hidden', 'true');
                });
            } catch (e) {
                console.error('Error in force close all:', e);
            }
        };
    }
    
    // Add safety listener for ESC key to force-close any modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && document.querySelector('.modal.show')) {
            console.log('ESC key pressed - attempting to force close any open modal');
            
            if (typeof window.forceCloseAllModals === 'function') {
                window.forceCloseAllModals();
            } else {
                // Fallback if global function not available
                document.querySelectorAll('.modal.show').forEach(modal => {
                    try {
                        const instance = bootstrap.Modal.getInstance(modal);
                        if (instance) instance.hide();
                    } catch (err) {
                        // Fallback cleanup
                        modal.classList.remove('show');
                        modal.style.display = 'none';
                    }
                });
                
                // Final cleanup
                document.querySelectorAll('.modal-backdrop').forEach(el => {
                    try { el.remove(); } catch (e) { 
                        if (el.parentNode) el.parentNode.removeChild(el); 
                    }
                });
                
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            }
        }
    });
    
    // Add observer to detect stuck modals
    const observerConfig = { attributes: true, childList: true, subtree: true };
    const observer = new MutationObserver((mutations) => {
        // Check if we have a verification in progress flag available
        const verificationInProgress = 
            typeof window.verificationInProgress !== 'undefined' ? 
            window.verificationInProgress : false;
            
        // Only auto-fix if verification is not in progress
        if (!verificationInProgress && 
            (document.body.classList.contains('modal-open') && 
             document.querySelectorAll('.modal-backdrop').length > 0 &&
             document.querySelectorAll('.modal.show').length === 0)) {
            
            console.warn('Detected stuck modal backdrop without visible modal - auto fixing');
            
            if (typeof window.forceCloseAllModals === 'function') {
                window.forceCloseAllModals();
            } else {
                // Remove backdrops and reset body
                document.querySelectorAll('.modal-backdrop').forEach(el => {
                    try { el.remove(); } catch (e) { 
                        if (el.parentNode) el.parentNode.removeChild(el); 
                    }
                });
                
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            }
        }
    });
    
    // Start observing the body for changes
    observer.observe(document.body, observerConfig);
});
