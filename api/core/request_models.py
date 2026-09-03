from pydantic import BaseModel

class GCSPath(BaseModel):
    gcs_path : str