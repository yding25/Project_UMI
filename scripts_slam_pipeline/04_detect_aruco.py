"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/04_detect_aruco.py \
-i /home/$(whoami)/Project_UMI/example_demo_session/demos \
-ci /home/$(whoami)/Project_UMI/example/calibration/gopro_intrinsics_2_7k.json \
-ac /home/$(whoami)/Project_UMI/example/calibration/aruco_config.yaml
"""

# %%
import sys
import os

ROOT_DIR = '/home/{}/Project_UMI'.format(os.getenv('USER'))
sys.path.append(ROOT_DIR)
os.chdir(ROOT_DIR)

# %%
import pathlib
import click
import multiprocessing
import subprocess
import concurrent.futures
from tqdm import tqdm

# %%
@click.command()
@click.option('-i', '--input_dir', required=True, help='Directory for demos folder')
@click.option('-ci', '--camera_intrinsics', required=True, help='Camera intrinsics json file (2.7k)')
@click.option('-ac', '--aruco_yaml', required=True, help='Aruco config yaml file')
@click.option('-n', '--num_workers', type=int, default=None)
def main(input_dir, camera_intrinsics, aruco_yaml, num_workers):
    input_dir = pathlib.Path(os.path.expanduser(input_dir)).absolute()
    input_video_dirs = [x.parent for x in input_dir.glob('*/raw_video.mp4')]
    print(f'Found {len(input_video_dirs)} video dirs')
    
    assert os.path.isfile(camera_intrinsics), f"Camera intrinsics file not found: {camera_intrinsics}"
    assert os.path.isfile(aruco_yaml), f"Aruco config file not found: {aruco_yaml}"

    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    script_path = pathlib.Path(ROOT_DIR).joinpath('scripts', 'detect_aruco.py')

    with tqdm(total=len(input_video_dirs)) as pbar:
        # one chunk per thread, therefore no synchronization needed
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = set()
            for video_dir in tqdm(input_video_dirs):
                video_dir = video_dir.absolute()
                video_path = video_dir.joinpath('raw_video.mp4')
                pkl_path = video_dir.joinpath('tag_detection.pkl')
                if pkl_path.is_file():
                    print(f"tag_detection.pkl already exists, skipping {video_dir.name}")
                    continue

                # run SLAM
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

# %%
if __name__ == "__main__":
    main()
