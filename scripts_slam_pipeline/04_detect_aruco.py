"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/04_detect_aruco.py \
-i /home/$(whoami)/Project_UMI/example_demo_session/demos \
-ci /home/$(whoami)/Project_UMI/example/calibration/gopro_intrinsics_2_7k.json \
-ac /home/$(whoami)/Project_UMI/example/calibration/aruco_config.yaml

脚本的主要功能是从指定目录中的视频文件中检测 ArUco 标签，并将检测结果保存为 pickle 文件。
"""

import sys
import os
import pathlib
import click
import multiprocessing
import subprocess
import concurrent.futures
from tqdm import tqdm

'''
设置根目录 ROOT_DIR 为 /home/{USER}/Project_UMI。
将根目录添加到 Python 的路径中，并切换当前工作目录到根目录。
'''
ROOT_DIR = '/home/{}/Project_UMI'.format(os.getenv('USER'))
sys.path.append(ROOT_DIR)
os.chdir(ROOT_DIR)

'''
定义命令行参数
使用 click 库定义命令行参数
input_dir 指定包含演示视频文件的目录
camera_intrinsics 指定相机内参文件的路径,JSON 文件, 分辨率为(2704x2028)
aruco_yaml 指定 ArUco 配置文件的路径，该文件是一个包含 ArUco 标签配置的 YAML 文件
num_workers 指定并行处理视频文件的工作线程数
'''
@click.command()
@click.option('-i', '--input_dir', required=True, help='Directory for demos folder')
@click.option('-ci', '--camera_intrinsics', required=True, help='Camera intrinsics json file (2.7k)')
@click.option('-ac', '--aruco_yaml', required=True, help='Aruco config yaml file')
@click.option('-n', '--num_workers', type=int, default=None)

def main(input_dir, camera_intrinsics, aruco_yaml, num_workers):
    input_dir = pathlib.Path(os.path.expanduser(input_dir)).absolute()
    
    '''
    使用 glob 方法查找所有名为 raw_video.mp4 的文件，并获取其所在目录。
    '''
    input_video_dirs = [x.parent for x in input_dir.glob('*/raw_video.mp4')]
    print(f'Found {len(input_video_dirs)} video dirs')

    '''
    确保相机内参文件和 ArUco 配置文件存在
    '''    
    assert os.path.isfile(camera_intrinsics), f"Camera intrinsics file not found: {camera_intrinsics}"
    assert os.path.isfile(aruco_yaml), f"Aruco config file not found: {aruco_yaml}"

    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    '''
    定义 detect_aruco.py 脚本的路径，该脚本负责实际的 ArUco 标签检测工作。
    '''
    script_path = pathlib.Path(ROOT_DIR).joinpath('scripts', 'detect_aruco.py')

    '''
    使用 tqdm 显示处理进度条，总数为找到的视频目录数量。
    '''
    with tqdm(total=len(input_video_dirs)) as pbar:
        
        '''
        使用 concurrent.futures.ThreadPoolExecutor 创建线程池来并行处理视频文件。
        '''
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = set()
            for video_dir in tqdm(input_video_dirs):
                video_dir = video_dir.absolute()
                video_path = video_dir.joinpath('raw_video.mp4')
                pkl_path = video_dir.joinpath('tag_detection.pkl')
                if pkl_path.is_file():
                    print(f"tag_detection.pkl already exists, skipping {video_dir.name}")
                    continue

                '''
                构建运行 detect_aruco.py 脚本的命令
                '''
                cmd = [
                    'python', str(script_path),
                    '--input', str(video_path),
                    '--output', str(pkl_path),
                    '--intrinsics_json', str(camera_intrinsics),
                    '--aruco_yaml', str(aruco_yaml),
                    '--num_workers', '1'
                ]

                if len(futures) >= num_workers:
                    # limit number of inflight tasks
                    completed, futures = concurrent.futures.wait(futures, 
                        return_when=concurrent.futures.FIRST_COMPLETED)
                    pbar.update(len(completed))

                futures.add(executor.submit(
                    lambda x: subprocess.run(x, 
                        capture_output=True), 
                    cmd))
                # futures.add(executor.submit(lambda x: print(' '.join(x)), cmd))

            completed, futures = concurrent.futures.wait(futures)            
            pbar.update(len(completed))

    print("Done! Result:")
    print([x.result() for x in completed])

if __name__ == "__main__":
    main()
