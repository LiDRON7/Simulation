"""
CI sensor smoke tests.
Run inside drone-ci container after simulation starts.
Tests confirm all expected ROS 2 topics are publishing.
"""

import subprocess
import time

import pytest

REQUIRED_TOPICS = [
    ("/gps", "sensor_msgs/msg/NavSatFix"),
    ("/imu", "sensor_msgs/msg/Imu"),
    ("/lidar/points", "sensor_msgs/msg/PointCloud2"),
    ("/oakd/color/image", "sensor_msgs/msg/Image"),
    ("/oakd/depth", "sensor_msgs/msg/Image"),
    ("/model/hexacopter/odometry", "nav_msgs/msg/Odometry"),
]


def get_active_topics() -> dict:
    """Return dict of {topic: type} from ros2 topic list."""
    result = subprocess.run(
        ["ros2", "topic", "list", "-t"], capture_output=True, text=True, timeout=30
    )
    topics = {}
    for line in result.stdout.strip().splitlines():
        # Format: /topic_name [msg/type]
        parts = line.split(" ")
        if len(parts) == 2:
            topic = parts[0]
            msg_type = parts[1].strip("[]")
            topics[topic] = msg_type
    return topics


@pytest.fixture(scope="session", autouse=True)
def wait_for_simulation():
    """Give simulation time to start before running tests."""
    print("\n[TEST] Waiting 20s for simulation to initialize...")
    time.sleep(20)


@pytest.mark.parametrize("topic,expected_type", REQUIRED_TOPICS)
def test_topic_exists(topic, expected_type):
    """Verify each required sensor topic is active."""
    topics = get_active_topics()
    assert (
        topic in topics
    ), f"Topic '{topic}' not found. Active topics: {list(topics.keys())}"


@pytest.mark.parametrize("topic,expected_type", REQUIRED_TOPICS)
def test_topic_type(topic, expected_type):
    """Verify each topic publishes the correct message type."""
    topics = get_active_topics()
    if topic in topics:
        assert (
            topics[topic] == expected_type
        ), f"Topic '{topic}' has type '{topics[topic]}', expected '{expected_type}'"


def test_mavros_state():
    """Verify MAVROS is connected and FCU is reachable."""
    result = subprocess.run(
        ["ros2", "topic", "echo", "/mavros/state", "--once", "--timeout", "10"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, "MAVROS state topic not responding"
    assert (
        "connected: true" in result.stdout
    ), f"MAVROS not connected to FCU. Output: {result.stdout}"


def test_lidar_publishing():
    """Verify LiDAR is actively publishing point cloud data."""
    result = subprocess.run(
        ["ros2", "topic", "hz", "/lidar/points", "--window", "5"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    # Should report some Hz > 0
    assert (
        "average rate" in result.stdout
    ), "LiDAR not publishing. Check Velodyne Puck Lite sensor in SDF."
