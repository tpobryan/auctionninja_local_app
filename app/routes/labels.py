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
        if "label_pdf" not in request.files:
            flash("No file part in the request.", "error")
            return redirect(request.url)
            
        file = request.files["label_pdf"]
        
        if file.filename == "":
            flash("No file selected.", "error")
            return redirect(request.url)
            
        if not file.filename.lower().endswith(".pdf"):
            flash("Only PDF files are supported.", "error")
            return redirect(request.url)
            
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
                flash("Failed to process the label. Please ensure it is a valid PDF.", "error")
                return redirect(request.url)
                
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(request.url)
            
    return render_template("upload_label.html")
