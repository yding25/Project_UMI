"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/01_extract_gopro_imu.py

脚本的主要功能是从 GoPro 视频文件中提取 IMU 数据，并使用 Docker 容器来执行这个任务。
"""

import sys
import os
import pathlib
import click
import subprocess
import multiprocessing
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
docker_image 指定要使用的 Docker 镜像
num_workers 指定并发任务数
no_docker_pull 用于控制是否从 Docker Hub 拉取最新的 Docker 镜像。
'''
@click.command()
@click.option('-d', '--docker_image', default="chicheng/openicc:latest")
@click.option('-n', '--num_workers', type=int, default=None)
@click.option('-np', '--no_docker_pull', is_flag=True, default=False, help="pull docker image from docker hub")

def main(docker_image, num_workers, no_docker_pull):
    session_dir = pathlib.Path("/home/{}/Project_UMI/example_demo_session".format(os.getenv('USER')))
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    '''
    检查 Docker 权限, 拉取 Docker 镜像
    '''
    try:
        subprocess.run(['docker', 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Permission denied: Make sure you have access to the Docker daemon.")
        exit(1)
    if not no_docker_pull:
        print(f"Pulling docker image {docker_image}")
        cmd = [
            'docker',
            'pull',
            docker_image
        ]
        p = subprocess.run(cmd)
        if p.returncode != 0:
            print("Docker pull failed!")
            exit(1)

    '''
    找到包含 raw_video.mp4 的目录
    '''
    input_dir = session_dir.joinpath('demos')
    input_video_dirs = [x.parent for x in input_dir.glob('*/raw_video.mp4')]
    print(f'Found {len(input_video_dirs)} video dirs')

    '''
    使用并发处理提取 IMU 数据
    '''
    with tqdm(total=len(input_video_dirs)) as pbar:
        # one chunk per thread, therefore no synchronization needed
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = set()
            for video_dir in tqdm(input_video_dirs):
                video_dir = video_dir.absolute()
                if video_dir.joinpath('imu_data.json').is_file():
                    print(f"imu_data.json already exists, skipping {video_dir.name}")
                    continue
                mount_target = pathlib.Path('/data')

                video_path = mount_target.joinpath('raw_video.mp4')
                json_path = mount_target.joinpath('imu_data.json')

                # run imu extractor
                cmd = [
                    'docker',
                    'run',
                    '--rm', # delete after finish
                    '--volume', str(video_dir) + ':' + '/data',
                    docker_image,
                    'node',
                    '/OpenImuCameraCalibrator/javascript/extract_metadata_single.js',
                    str(video_path),
                    str(json_path)
                ]

                stdout_path = video_dir.joinpath('extract_gopro_imu_stdout.txt')
                stderr_path = video_dir.joinpath('extract_gopro_imu_stderr.txt')

                if len(futures) >= num_workers:
                    # limit number of inflight tasks
                    completed, futures = concurrent.futures.wait(futures, 
                        return_when=concurrent.futures.FIRST_COMPLETED)
                    pbar.update(len(completed))

                futures.add(executor.submit(
                    lambda x, stdo, stde: subprocess.run(x, 
                        cwd=str(video_dir),
                        stdout=stdo.open('w'),
                        stderr=stde.open('w')), 
                    cmd, stdout_path, stderr_path))
                # print(' '.join(cmd))

            completed, futures = concurrent.futures.wait(futures)
            pbar.update(len(completed))

    print("Done! Result:")
    print([x.result() for x in completed])

if __name__ == "__main__":
    main()
