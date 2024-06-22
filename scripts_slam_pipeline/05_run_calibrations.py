"""
python /home/$(whoami)/Project_UMI/scripts_slam_pipeline/05_run_calibrations.py /home/$(whoami)/Project_UMI/example_demo_session

脚本的主要功能是运行一系列的校准任务，包括 SLAM 标签校准和夹持器范围校准。
"""

import sys
import os
import pathlib
import click
import subprocess

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
session_dir 会话目录, 这个项目默认是example_demo_session
'''
@click.command()
@click.argument('session_dir', nargs=-1)

def main(session_dir):
    '''
    脚本目录路径
    '''
    script_dir = pathlib.Path(__file__).parent.parent.joinpath('scripts')
    
    for session in session_dir:
        session = pathlib.Path(session)
        demos_dir = session.joinpath('demos')
        mapping_dir = demos_dir.joinpath('mapping')
        slam_tag_path = mapping_dir.joinpath('tx_slam_tag.json')
            
        '''
        运行 SLAM 标签校准
        '''
        script_path = script_dir.joinpath('calibrate_slam_tag.py')
        assert script_path.is_file()
        tag_path = mapping_dir.joinpath('tag_detection.pkl')
        assert tag_path.is_file()
        csv_path = mapping_dir.joinpath('camera_trajectory.csv')
        if not csv_path.is_file():
            csv_path = mapping_dir.joinpath('mapping_camera_trajectory.csv')
            print("camera_trajectory.csv not found! using mapping_camera_trajectory.csv")
        assert csv_path.is_file()
        
        cmd = [
            'python', str(script_path),
            '--tag_detection', str(tag_path),
            '--csv_trajectory', str(csv_path),
            '--output', str(slam_tag_path),
            '--keyframe_only'
        ]
        subprocess.run(cmd)
        
        '''
        运行夹持器范围校准
        '''
        script_path = script_dir.joinpath('calibrate_gripper_range.py')
        assert script_path.is_file()
        
        for gripper_dir in demos_dir.glob("gripper_calibration*"):
            gripper_range_path = gripper_dir.joinpath('gripper_range.json')
            tag_path = gripper_dir.joinpath('tag_detection.pkl')
            assert tag_path.is_file()
            cmd = [
                'python', str(script_path),
                '--input', str(tag_path),
                '--output', str(gripper_range_path)
            ]
            subprocess.run(cmd)


if __name__ == "__main__":
    main()