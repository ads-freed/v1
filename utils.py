import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_file(file_storage):
    if file_storage and allowed_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file_storage.save(filepath)
        return unique_filename
    return None
