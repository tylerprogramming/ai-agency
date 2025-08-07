#!/usr/bin/env python3
"""
Pydantic models for Google Drive responses
"""

from pydantic import BaseModel, Field

class GoogleDriveFolder(BaseModel):
    """Pydantic model for Google Drive folder response"""
    id: str = Field(..., description="Google Drive folder ID")
    name: str = Field(..., description="Folder name")
    url: str = Field(..., description="Web view URL for the folder")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1BxiMVs0XRA5nFMdKvBdBZjgm111111",
                "name": "My Folder",
                "url": "https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptl11111"
            }
        }


class GoogleDriveDocument(BaseModel):
    """Pydantic model for Google Drive document response"""
    id: str = Field(..., description="Google Drive document ID")
    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Web view URL for the document")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptl11111",
                "title": "My Document",
                "url": "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptl11111/edit"
            }
        }


class GoogleDriveFile(BaseModel):
    """Pydantic model for Google Drive file response"""
    id: str = Field(..., description="Google Drive file ID")
    title: str = Field(..., description="File title")
    url: str = Field(..., description="Web view URL for the file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptl11111",
                "title": "my_file.txt",
                "url": "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptl11111/view"
            }
        } 