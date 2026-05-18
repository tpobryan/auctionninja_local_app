from flask import Blueprint, render_template, request, flash, send_file, redirect, url_for
import os
import uuid
from werkzeug.utils import secure_filename
from ..config import settings
from ..services.label_processor import process_vinted_label

labels_bp = Blueprint("labels", __name__, url_prefix="/")

# Ensure directories exist
os.makedirs(settings.LABELS_INCOMING_DIR, exist_ok=True)
os.makedirs(settings.LABELS_PROCESSED_DIR, exist_ok=True)

@labels_bp.route("/upload-label", methods=["GET", "POST"])
def upload_label():
    if request.method == "POST":
        print(f"Content-Type: {request.content_type}")
        print(f"Request Form Keys: {list(request.form.keys())}")
        print(f"Request Files Keys: {list(request.files.keys())}")
        
        if "label" in request.files:
            file = request.files["label"]
        elif "label_pdf" in request.files:
            file = request.files["label_pdf"]
        else:
            # Check if it was sent as raw data
            if request.content_length and request.content_type == "application/pdf":
                return "Error: File sent as raw body, but expected multipart/form-data 'label' field.", 400
            if request.accept_mimetypes.accept_html:
                flash("No file part in the request.", "error")
                return redirect(request.url)
            return "Error: No file part in the request. Keys found: " + str(list(request.files.keys())), 400
        
        if file.filename == "":
            if request.accept_mimetypes.accept_html:
                flash("No file selected.", "error")
                return redirect(request.url)
            # Shortcuts might send files without a filename? 
            # If so, let's just assign a fake filename so it proceeds!
            file.filename = "shortcut_upload.pdf"
            
        if not file.filename.lower().endswith(".pdf"):
            if request.accept_mimetypes.accept_html:
                flash("Only PDF files are supported.", "error")
                return redirect(request.url)
            return "Error: Only PDF files are supported.", 400
            
        try:
            # Secure filename and add uuid to avoid collisions
            safe_name = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())[:8]
            base_name = os.path.splitext(safe_name)[0]
            
            in_filename = f"{base_name}_{unique_id}.pdf"
            out_filename = f"{base_name}_4x6_{unique_id}.pdf"
            
            in_path = settings.LABELS_INCOMING_DIR / in_filename
            out_path = settings.LABELS_PROCESSED_DIR / out_filename
            
            file.save(in_path)
            
            success = process_vinted_label(in_path, out_path)
            
            if success and os.path.exists(out_path):
                # Return the processed file to the user
                return send_file(
                    out_path,
                    as_attachment=True,
                    download_name=f"{base_name}_4x6.pdf",
                    mimetype="application/pdf"
                )
            else:
                if request.accept_mimetypes.accept_html:
                    flash("Failed to process the label. Please ensure it is a valid PDF.", "error")
                    return redirect(request.url)
                return "Error: Failed to process the label. Please ensure it is a valid PDF.", 400
                
        except Exception as e:
            if request.accept_mimetypes.accept_html:
                flash(f"An error occurred: {str(e)}", "error")
                return redirect(request.url)
            return f"Error: An exception occurred: {str(e)}", 500
            
    return render_template("upload_label.html")
