from flask import Blueprint, render_template, request, flash, send_file, redirect, url_for
import os
import io
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
        
        file = None
        raw_data = None
        
        if "label" in request.files:
            file = request.files["label"]
        elif "label_pdf" in request.files:
            file = request.files["label_pdf"]
        elif len(request.files) == 1:
            file = next(iter(request.files.values()))
            
        if not file:
            # Check if it was sent as raw data (some Shortcuts configs do this by mistake)
            if request.data and len(request.data) > 100: # ensure it's not empty
                # We have raw data! We'll bypass the file object.
                raw_data = request.data
            else:
                error_msg = f"Error: No file part and no raw body in the request. Form keys sent: {list(request.form.keys())}. Files sent: {list(request.files.keys())}"
                return error_msg, 400
        
        if file:
            if file.filename == "":
                if request.accept_mimetypes.accept_html:
                    flash("No file selected.", "error")
                    return redirect(request.url)
                # Shortcuts might send files without a filename? 
                file.filename = "shortcut_upload.pdf"
                
            if not file.filename.lower().endswith(".pdf"):
                if request.accept_mimetypes.accept_html:
                    flash("Only PDF files are supported.", "error")
                    return redirect(request.url)
                return "Error: Only PDF files are supported.", 400
            
        try:
            unique_id = str(uuid.uuid4())[:8]
            
            if file:
                safe_name = secure_filename(file.filename)
                base_name = os.path.splitext(safe_name)[0]
                in_filename = f"{base_name}_{unique_id}.pdf"
            else:
                base_name = "raw_upload"
                in_filename = f"{base_name}_{unique_id}.pdf"
                
            out_filename = f"{base_name}_4x6_{unique_id}.pdf"
            
            in_path = settings.LABELS_INCOMING_DIR / in_filename
            out_path = settings.LABELS_PROCESSED_DIR / out_filename
            
            if file:
                file.save(in_path)
            elif raw_data:
                with open(in_path, "wb") as f:
                    f.write(raw_data)
            
            success = process_vinted_label(in_path, out_path)
            
            if success and os.path.exists(out_path):
                # Read the processed file into memory
                with open(out_path, "rb") as f:
                    file_data = io.BytesIO(f.read())
                
                # Delete the files from disk to save space and protect privacy
                try:
                    os.remove(in_path)
                    os.remove(out_path)
                except Exception as cleanup_err:
                    print(f"Warning: Failed to delete temporary label files: {cleanup_err}")
                
                # Return the processed file to the user from memory
                return send_file(
                    file_data,
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
