import os
import subprocess

def convert_mov_to_mp4(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".mov"):
            mov_path = os.path.join(directory, filename)
            mp4_path = os.path.join(directory, filename[:-4] + ".mp4")
            
            # 使用ffmpeg进行转换
            command = ["ffmpeg", "-i", mov_path, "-vcodec", "h264", "-acodec", "aac", mp4_path]
            subprocess.run(command)
            print(f"Converted {mov_path} to {mp4_path}")

if __name__ == "__main__":
    directory = "/home/yan/Downloads"  # 替换为你的文件夹路径
    convert_mov_to_mp4(directory)