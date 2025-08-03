import requests
from dotenv import load_dotenv
import os

load_dotenv()

def create_project(file_id):
    url = 'https://api.submagic.co/v1/projects'
    headers = {
        'x-api-key': os.getenv('SUBMAGIC_API_KEY'),
        'Content-Type': 'application/json'
    }
    data = {
        'title': 'A simple video test4',
        'language': 'en',
        'videoUrl': f'https://drive.google.com/uc?export=download&id={file_id}',
        'templateName': 'Hormozi 2',
        'dictionary': ['Submagic', 'AI-powered', 'captions'],
        'magicZooms': False,
        'magicBrolls': True,
        'magicBrollsPercentage': 50
    }

    response = requests.post(url, headers=headers, json=data)
    project = response.json()
    return project

def upload_project(file_path):
    url = 'https://api.submagic.co/v1/projects/upload'
    headers = {
        'x-api-key': os.getenv('SUBMAGIC_API_KEY')
    }

    with open(file_path, 'rb') as video_file:
        files = {
            'file': video_file
        }
        data = {
            'title': 'My Uploaded Video',
            'language': 'en',
            'templateName': 'Ella',
            'dictionary': '["Submagic", "AI-powered", "captions"]',
            'magicZooms': 'false',
            'magicBrolls': 'true',
            'magicBrollsPercentage': '50'
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        project = response.json()

        print(f"Project uploaded: {project.get('id')}")
        return project

def get_project(project_id):
    url = f'https://api.submagic.co/v1/projects/{project_id}'
    headers = {
        'x-api-key': os.getenv('SUBMAGIC_API_KEY')
    }

    response = requests.get(url, headers=headers)

    return response.json()

def download_video(download_url, output_filename='downloaded_video.mp4'):
    """
    Download a video from the given URL and save it to the specified filename.
    """
    try:
        print(f"Downloading video from: {download_url}")
        
        # Download the video
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        # Save the video to file
        with open(output_filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"Video downloaded successfully as: {output_filename}")
        return output_filename
        
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None