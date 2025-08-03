#!/usr/bin/env python
from pathlib import Path
from pydantic import BaseModel
from crewai.flow import Flow, listen, start
from .submagic_project import upload_project, get_project, download_video

import time

class SubmagicState(BaseModel):
    project_id: str = ""
    file_name: str = ""
    download_url: str = ""
    folder_to_upload_path: str = "/Users/tylerreed/files_to_submagic"
    folder_from_submagic_path: str = "/Users/tylerreed/files_from_submagic"
    folder_processed_submagic_path: str = "/Users/tylerreed/files_processed"

class SubmagicFlow(Flow[SubmagicState]):

    @start()
    def upload_video_to_submagic(self):
        print("Uploading video to submagic")
        print("File information: ")
        print(f"File name: {self.state.file_name}")
        print(f"Folder to upload path: {self.state.folder_to_upload_path}")

    @listen(upload_video_to_submagic)
    def create_project(self):
        print("Creating project")
        full_file_path = self.state.folder_to_upload_path + "/" + self.state.file_name
        project = upload_project(full_file_path)
        self.state.project_id = project.get('id')

    @listen(create_project)
    def wait_for_project_to_finish(self):
        print("Waiting for project to finish")
        print(f"Project ID: {self.state.project_id}")
        project = get_project(self.state.project_id)
        
        while True:
            time.sleep(30)
            project = get_project(self.state.project_id)
            
            if project.get('status') == "completed" and 'downloadUrl' in project:
                self.state.download_url = project.get('downloadUrl')
                break
            elif project.get('status') == "processing":
                print("Project is still processing")
                continue
            elif project.get('status') == "failed":
                raise Exception("Project failed")
            
    @listen(wait_for_project_to_finish)
    def download_video(self):
        print("Downloading video")
        output_filename = self.state.folder_from_submagic_path + "/" + self.state.file_name
        downloaded_file = download_video(self.state.download_url, output_filename)
        
    @listen(download_video)
    def move_video_to_processed_folder(self):
        print("Moving video to processed folder")

        source = Path(self.state.folder_to_upload_path + "/" + self.state.file_name)

        processed_dir = Path(self.state.folder_processed_submagic_path)
        processed_dir.mkdir(exist_ok=True)

        destination = processed_dir / source.name
        source.rename(destination)

        print(f"File moved to: {destination}")

def kickoff(file_name):
    submagic_flow = SubmagicFlow()
    
    inputs = {
        "file_name": file_name
    }
    
    submagic_flow.kickoff(inputs=inputs)

if __name__ == "__main__":
    kickoff()
