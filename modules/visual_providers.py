from __future__ import annotations

import os
import random
import time
from abc import ABC, abstractmethod
from typing import Optional

import replicate
import requests


class VisualProvider(ABC):
    @abstractmethod
    def generate_visual(self, prompt: str, duration: float) -> Optional[str]:
        raise NotImplementedError


class PexelsProvider(VisualProvider):
    def __init__(self, api_key: str, output_dir: str):
        if not api_key:
            raise ValueError("PEXELS_API_KEY is required for PexelsProvider")
        self.base_url = "https://api.pexels.com/videos/search"
        self.headers = {"Authorization": api_key}
        self.output_dir = output_dir

    def search_video(self, query: str, duration_min: int = 4) -> Optional[str]:
        params = {
            "query": query,
            "per_page": 5,
            "orientation": "portrait",
            "size": "medium",
        }

        response = requests.get(self.base_url, headers=self.headers, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        if not data.get("videos"):
            if " " in query:
                return self.search_video(query.split()[-1], duration_min=duration_min)
            return None

        valid_videos = [v for v in data["videos"] if v.get("duration", 0) >= duration_min] or data["videos"]
        selected_video = random.choice(valid_videos)
        video_files = selected_video.get("video_files", [])
        if not video_files:
            return None
        video_files.sort(key=lambda x: x.get("width", 0) * x.get("height", 0), reverse=True)
        return video_files[0].get("link")

    def download_video(self, url: str, filename: str) -> Optional[str]:
        save_path = os.path.join(self.output_dir, filename)
        if os.path.exists(save_path):
            return save_path

        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(save_path, "wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    file_handle.write(chunk)
        return save_path

    def generate_visual(self, prompt: str, duration: float) -> Optional[str]:
        url = self.search_video(prompt, duration_min=max(3, int(duration)))
        if not url:
            return None
        filename = f"pexels_{int(time.time() * 1000)}_{abs(hash(prompt)) % 10000}.mp4"
        return self.download_video(url, filename)


class StabilityAIProvider(VisualProvider):
    def __init__(self, api_key: str, output_dir: str):
        if not api_key:
            raise ValueError("STABILITY_API_KEY is required for StabilityAIProvider")
        self.api_key = api_key
        self.output_dir = output_dir
        self.endpoint = "https://api.stability.ai/v2beta/stable-image/generate/core"

    def generate_visual(self, prompt: str, duration: float) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*",
        }
        files = {"none": ""}
        data = {
            "prompt": prompt,
            "output_format": "jpeg",
            "aspect_ratio": "9:16",
        }

        response = requests.post(self.endpoint, headers=headers, files=files, data=data, timeout=60)
        response.raise_for_status()

        filename = f"stability_{int(time.time() * 1000)}_{abs(hash(prompt)) % 10000}.jpg"
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "wb") as file_handle:
            file_handle.write(response.content)
        return output_path


class ReplicateProvider(VisualProvider):
    def __init__(self, api_token: str, model: str, output_dir: str):
        if not api_token:
            raise ValueError("REPLICATE_API_TOKEN is required for ReplicateProvider")
        self.client = replicate.Client(api_token=api_token)
        self.model = model
        self.output_dir = output_dir

    def generate_visual(self, prompt: str, duration: float) -> Optional[str]:
        output = self.client.run(
            self.model,
            input={
                "prompt": prompt,
                "aspect_ratio": "9:16",
                "duration": min(max(duration, 3), 5),
            },
        )

        if isinstance(output, list) and output:
            media_url = str(output[0])
        else:
            media_url = str(output)

        if not media_url:
            return None

        response = requests.get(media_url, timeout=60)
        response.raise_for_status()
        extension = ".mp4" if "video" in response.headers.get("content-type", "") else ".jpg"
        filename = f"replicate_{int(time.time() * 1000)}_{abs(hash(prompt)) % 10000}{extension}"
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "wb") as file_handle:
            file_handle.write(response.content)
        return output_path
