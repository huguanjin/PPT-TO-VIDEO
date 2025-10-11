import requests
from pathlib import Path
import os, sys
import time
from rich import print as rprint
# 新版本 moviepy 的导入方式
from moviepy.audio.io.AudioFileClip import AudioFileClip
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from core.config_utils import load_key

def fish_tts(text, save_path, character=None):
    fish_set = load_key("fish_tts")
    
    # 如果提供了character参数，使用它；否则使用配置文件中的默认值
    if character is not None:
        selected_character = character
    else:
        selected_character = fish_set["character"]
    
    if selected_character not in fish_set["character_id_dict"]:
        raise ValueError(f"Character <{selected_character}> not found in <character_id_dict>")
    id = fish_set["character_id_dict"][selected_character]
    url = "https://api.fish.audio/v1/tts"

    payload = {
        "text": text,
        "format": "mp3",
        "mp3_bitrate": 128,
        "normalize": True,
        "reference_id": id
    }
    headers = {
        "Authorization": f"Bearer {fish_set['api_key']}",
        "Content-Type": "application/json"
    }

    max_retries = 10  # 最大重试次数
    retry_delay = 15  # 重试间隔（秒）
    
    for attempt in range(max_retries):
        try:
            response = requests.request("POST", url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                wav_file_path = Path(save_path).with_suffix('.wav')
                wav_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Save the MP3 content to a temporary file
                temp_mp3_path = wav_file_path.with_suffix('.mp3')
                with open(temp_mp3_path, 'wb') as temp_file:
                    temp_file.write(response.content)

                # Convert mp3 to wav using moviepy
                audio_clip = AudioFileClip(str(temp_mp3_path))
                audio_clip.write_audiofile(str(wav_file_path))
                audio_clip.close()

                # Remove the temporary MP3 file
                os.remove(temp_mp3_path)

                rprint(f"[bold green]Converted audio saved to {wav_file_path}[/bold green]")
                return  # 成功后直接返回
            else:
                rprint(f"[bold red]Request failed, status code: {response.status_code}, retry attempt: {attempt + 1}/{max_retries}[/bold red]")
        except Exception as e:
            rprint(f"[bold red]Request exception: {e}, retry attempt: {attempt + 1}/{max_retries}[/bold red]")
        
        # 如果不是最后一次尝试，等待后重试
        if attempt < max_retries - 1:
            rprint(f"[yellow]Waiting {retry_delay} seconds before retry...[/yellow]")
            time.sleep(retry_delay)
        else:
            rprint("[bold red]Max retry attempts reached, operation failed.[/bold red]")
            raise Exception(f"Fish TTS failed after {max_retries} attempts")

if __name__ == '__main__':
    fish_tts("今天是个好日子！", "fish_tts.wav")
