// ==============================================================
// SweetAlert2 Toast & Alerts Configuration
// ==============================================================

const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3500,
    timerProgressBar: true,
    didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer);
        toast.addEventListener('mouseleave', Swal.resumeTimer);
    }
});

function showToast(icon, title) {
    Toast.fire({
        icon: icon,
        title: title
    });
}

function showAlert(icon, title, text) {
    Swal.fire({
        icon: icon,
        title: title,
        text: text,
        confirmButtonColor: '#2c3e50',
        confirmButtonText: 'ตกลง'
    });
}

// Confirmation helper for forms
function confirmAction(formId, title, text, confirmBtnText = 'ยืนยัน', icon = 'warning') {
    Swal.fire({
        title: title,
        text: text,
        icon: icon,
        showCancelButton: true,
        confirmButtonColor: '#e74c3c',
        cancelButtonColor: '#6c757d',
        confirmButtonText: confirmBtnText,
        cancelButtonText: 'ยกเลิก'
    }).then((result) => {
        if (result.isConfirmed) {
            document.getElementById(formId).submit();
        }
    });
}

// Image preview helper
function previewMultipleImages(input, previewContainerId) {
    const container = document.getElementById(previewContainerId);
    if (!container) return;
    container.innerHTML = '';

    if (input.files) {
        Array.from(input.files).forEach(file => {
            if (!file.type.match('image.*')) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                const col = document.createElement('div');
                col.className = 'col-4 col-md-3 mb-2';
                col.innerHTML = `
                    <div class="position-relative">
                        <img src="${e.target.result}" class="img-thumbnail" style="height: 90px; width: 100%; object-fit: cover; border-radius: 6px;">
                        <small class="text-truncate d-block mt-1 text-muted" style="font-size: 11px;">${file.name}</small>
                    </div>
                `;
                container.appendChild(col);
            };
            reader.readAsDataURL(file);
        });
    }
}

// Image Zoom Modal helper
function viewImageModal(src, title) {
    Swal.fire({
        title: title || 'รูปภาพประกอบ',
        imageUrl: src,
        imageAlt: title,
        showCloseButton: true,
        showConfirmButton: false,
        width: 'auto',
        customClass: {
            image: 'img-fluid rounded'
        }
    });
}
