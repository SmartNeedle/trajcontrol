import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription
from launch.actions import LogInfo

import sys

from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch import LaunchDescription, actions
from launch.actions import DeclareLaunchArgument
from launch.substitutions import ThisLaunchFileDir


# Launch stage control in manual mode
# Remember to launch keypress node (trajcontrol package) in another terminal


def generate_launch_description():

    robot = Node(
        package="smart_template",
        executable="template",
    )  

    controller = Node(
        package="trajcontrol",
        executable="controller_manual",
    )   

    return LaunchDescription([
        controller,
        robot,
    ])
