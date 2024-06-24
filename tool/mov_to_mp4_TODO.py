import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

def convert_mov_to_mp4(mov_path, mp4_path):
    # 使用 GPU 加速并设置高质量的编码参数
    command = [
        "ffmpeg",
        "-i", mov_path,
        "-vcodec", "h264_nvenc",  # 使用 NVIDIA GPU 加速
        "-acodec", "aac",
        "-crf", "18",             # 设置 CRF 值，18 提供高质量
        "-preset", "slow",        # 设置编码速度与质量的平衡
        mp4_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Converted {mov_path} to {mp4_path}")

def process_directory(directory):
    files_to_convert = [
        (os.path.join(directory, filename), os.path.join(directory, filename[:-4] + ".mp4"))
        for filename in os.listdir(directory) if filename.endswith(".mov")
    ]

    # 使用 ThreadPoolExecutor 并行处理文件转换
    with ThreadPoolExecutor() as executor:
        executor.map(lambda p: convert_mov_to_mp4(*p), files_to_convert)

if __name__ == "__main__":
    directory = "/home/yan/Downloads"  # 替换为你的文件夹路径
    process_directory(directory)
