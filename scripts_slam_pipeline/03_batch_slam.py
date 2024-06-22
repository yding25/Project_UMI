"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/03_batch_slam.py --input_dir /home/$(whoami)/Project_UMI/example_demo_session/demos --map_path /home/$(whoami)/Project_UMI/example_demo_session/demos/mapping/map_atlas.osa

脚本的主要功能是批量处理多个视频文件，通过 ORB-SLAM3 算法从 GoPro 视频和 IMU 数据中提取相机轨迹，并生成相应的输出文件。它使用 Docker 容器来运行 SLAM 算法，并通过并行处理提高处理效率。
"""

import sys
import os
import pathlib
import click
import subprocess
import multiprocessing
import concurrent.futures
from tqdm import tqdm
import cv2
import av
import numpy as np
from umi.common.cv_util import draw_predefined_mask

'''
设置根目录 ROOT_DIR 为 /home/{USER}/Project_UMI。
将根目录添加到 Python 的路径中，并切换当前工作目录到根目录。
'''
ROOT_DIR = '/home/{}/Project_UMI'.format(os.getenv('USER'))
sys.path.append(ROOT_DIR)
os.chdir(ROOT_DIR)

'''
定义一个辅助函数 runner, 用于运行命令行命令并处理超时异常。
'''
def runner(cmd, cwd, stdout_path, stderr_path, timeout, **kwargs):
    try:
        return subprocess.run(cmd,                       
            cwd=str(cwd),
            stdout=stdout_path.open('w'),
            stderr=stderr_path.open('w'),
            timeout=timeout,
            **kwargs)
    except subprocess.TimeoutExpired as e:
        return e

'''
定义命令行参数
使用 click 库定义命令行参数
input_dir 指定了包含映射视频的目录
map_path 指定ORB_SLAM3生成的地图文件路径
docker_image 指定要使用的 Docker 镜像
num_workers 指定并发处理视频的工作线程数
max_lost_frames 指定ORB-SLAM3算法允许的最大丢帧数
timeout_multiple 指定超时的倍数，计算方式为 timeout_multiple 乘以视频的持续时间。这个值决定了处理每个视频的最大时间限制
no_docker_pull 如果设置了这个标志，脚本将不会从 Docker Hub 拉取 Docker 镜像
'''
@click.command()
@click.option('-i', '--input_dir', required=True, help='Directory for demos folder')
@click.option('-m', '--map_path', default=None, help='ORB_SLAM3 *.osa map atlas file')
@click.option('-d', '--docker_image', default="chicheng/orb_slam3:latest")
@click.option('-n', '--num_workers', type=int, default=None)
@click.option('-ml', '--max_lost_frames', type=int, default=60)
@click.option('-tm', '--timeout_multiple', type=float, default=16, help='timeout_multiple * duration = timeout')
@click.option('-np', '--no_docker_pull', is_flag=True, default=False, help="pull docker image from docker hub")

def main(input_dir, map_path, docker_image, num_workers, max_lost_frames, timeout_multiple, no_docker_pull):
    input_dir = pathlib.Path(os.path.expanduser(input_dir)).absolute()
    input_video_dirs = [x.parent for x in input_dir.glob('demo*/raw_video.mp4')]
    input_video_dirs += [x.parent for x in input_dir.glob('map*/raw_video.mp4')]
    print(f'Found {len(input_video_dirs)} video dirs')
    
    '''
    获取输入目录中的视频文件，并检查地图文件 map_path 是否存在
    '''
    if map_path is None:
        map_path = input_dir.joinpath('mapping', 'map_atlas.osa')
    else:
        map_path = pathlib.Path(os.path.expanduser(map_path)).absolute()
    assert map_path.is_file(), f"Map file not found: {map_path}"
    
    '''
    计算需要的工作线程数量
    '''
    if num_workers is None:
        num_workers = multiprocessing.cpu_count() // 2

    '''
    检查 Docker 权限, 拉取 Docker 镜像
    '''
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
    并行处理视频文件
    '''
    with tqdm(total=len(input_video_dirs)) as pbar:
        '''
        使用 concurrent.futures.ThreadPoolExecutor 实现并行处理。
        '''
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = set()
            for video_dir in tqdm(input_video_dirs):
                video_dir = video_dir.absolute()
                if video_dir.joinpath('camera_trajectory.csv').is_file():
                    print(f"camera_trajectory.csv already exists, skipping {video_dir.name}")
                    continue
                
                # softlink won't work in bind volume
                mount_target = pathlib.Path('/data')
                csv_path = mount_target.joinpath('camera_trajectory.csv')
                video_path = mount_target.joinpath('raw_video.mp4')
                json_path = mount_target.joinpath('imu_data.json')
                mask_path = mount_target.joinpath('slam_mask.png')
                mask_write_path = video_dir.joinpath('slam_mask.png')
                
                '''
                对每个视频目录，创建必要的文件路径并计算视频的持续时间。
                '''
                with av.open(str(video_dir.joinpath('raw_video.mp4').absolute())) as container:
                    video = container.streams.video[0]
                    duration_sec = float(video.duration * video.time_base)
                timeout = duration_sec * timeout_multiple
                
                '''
                生成遮罩文件
                '''
                slam_mask = np.zeros((2028, 2704), dtype=np.uint8)
                slam_mask = draw_predefined_mask(
                    slam_mask, color=255, mirror=True, gripper=False, finger=True)
                cv2.imwrite(str(mask_write_path.absolute()), slam_mask)

                map_mount_source = pathlib.Path(map_path)
                map_mount_target = pathlib.Path('/map').joinpath(map_mount_source.name)

                '''
                构建并运行 SLAM 命令。
                '''
                cmd = [
                    'docker',
                    'run',
                    '--rm', # delete after finish
                    '--volume', str(video_dir) + ':' + '/data',
                    '--volume', str(map_mount_source.parent) + ':' + str(map_mount_target.parent),
                    docker_image,
                    '/ORB_SLAM3/Examples/Monocular-Inertial/gopro_slam',
                    '--vocabulary', '/ORB_SLAM3/Vocabulary/ORBvoc.txt',
                    '--setting', '/ORB_SLAM3/Examples/Monocular-Inertial/gopro10_maxlens_fisheye_setting_v1_720.yaml',
                    '--input_video', str(video_path),
                    '--input_imu_json', str(json_path),
                    '--output_trajectory_csv', str(csv_path),
                    '--load_map', str(map_mount_target),
                    '--mask_img', str(mask_path),
                    '--max_lost_frames', str(max_lost_frames)
                ]

                stdout_path = video_dir.joinpath('slam_stdout.txt')
                stderr_path = video_dir.joinpath('slam_stderr.txt')

                print(f"Running command: {' '.join(cmd)}")
                print(f"stdout: {stdout_path}")
                print(f"stderr: {stderr_path}")

                if len(futures) >= num_workers:
                    # limit number of inflight tasks
                    completed, futures = concurrent.futures.wait(futures, 
                        return_when=concurrent.futures.FIRST_COMPLETED)
                    pbar.update(len(completed))

                futures.add(executor.submit(runner,
                    cmd, str(video_dir), stdout_path, stderr_path, timeout))
                # print(' '.join(cmd))

            completed, futures = concurrent.futures.wait(futures)
            pbar.update(len(completed))

    print("Done! Result:")
    print([x.result() for x in completed])

# %%
if __name__ == "__main__":
    main()
