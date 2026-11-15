"""Runs inside lidron_autonomy while a scenario is recorded (record.sh copies it in).
python3 rec.py OUT_DIR: OUT_DIR/log.jsonl has grid, path, position, attitude and state with sim time;
OUT_DIR/depth/<t>.npy and OUT_DIR/lidar/<t>.npy hold the camera depth and the LiDAR cloud at 5 Hz, and
OUT_DIR/landing/<t>_{ground,obstacle}.npy what the landing check took as ground and as obstacles. Stop with SIGTERM."""
import json, os, signal, sys
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid, Path
from std_msgs.msg import String
from sensor_msgs.msg import Image, PointCloud2
from sensor_msgs_py import point_cloud2
from px4_msgs.msg import VehicleAttitude, VehicleLocalPosition

out = sys.argv[1]
for d in ('depth', 'lidar', 'landing'):
    os.makedirs(f'{out}/{d}', exist_ok=True)


class Rec(Node):
    def __init__(self):
        super().__init__('recorder', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.f = open(f'{out}/log.jsonl', 'w', buffering=1)
        self.last = {}
        px4 = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                         history=HistoryPolicy.KEEP_LAST, depth=1)
        self.create_subscription(OccupancyGrid, '/autonomy/occupancy_grid', self.grid, 10)
        self.create_subscription(Path, '/autonomy/path', self.path, 10)
        self.create_subscription(String, '/autonomy/state', self.state, 10)
        self.create_subscription(VehicleLocalPosition, '/fmu/out/vehicle_local_position', self.pos, px4)
        self.create_subscription(VehicleAttitude, '/fmu/out/vehicle_attitude', self.att, px4)
        self.create_subscription(Image, '/oakd/depth/image', self.depth, 2)
        self.create_subscription(PointCloud2, '/lidar/points', self.lidar, 2)
        self.create_subscription(String, '/landing/assessment', self.verdict, 10)
        self.create_subscription(PointCloud2, '/landing/ground_points', lambda m: self.landing(m, 'ground'), 2)
        self.create_subscription(PointCloud2, '/landing/non_ground_points', lambda m: self.landing(m, 'obstacle'), 2)

    def t(self):
        return self.get_clock().now().nanoseconds / 1e9

    def due(self, key, period):  # rate limit per stream, in sim seconds
        t = self.t()
        if t - self.last.get(key, -1e9) < period:
            return None
        self.last[key] = t
        return t

    def w(self, kind, data):
        self.f.write(json.dumps({'t': round(self.t(), 3), 'k': kind, 'd': data}) + '\n')

    def grid(self, m):
        r, n0, e0, w = m.info.resolution, m.info.origin.position.x, m.info.origin.position.y, m.info.width
        cells = [[round(n0 + (i % w + 0.5) * r, 2), round(e0 + (i // w + 0.5) * r, 2)] for i, v in enumerate(m.data) if v > 50]
        key = (n0, e0, len(cells), tuple(map(tuple, cells[:5])))
        if key != self.last.get('grid_key'):
            self.last['grid_key'] = key
            self.w('grid', {'r': r, 'cells': cells})

    def path(self, m):
        self.w('path', [[round(p.pose.position.x, 2), round(p.pose.position.y, 2)] for p in m.poses])

    def state(self, m):
        if m.data != self.last.get('state'):
            self.last['state'] = m.data
            self.w('state', m.data)

    def pos(self, m):
        if self.due('pos', 0.1) is not None:
            self.w('pos', [round(m.x, 3), round(m.y, 3), round(m.z, 3)])

    def att(self, m):
        if self.due('att', 0.1) is not None:
            self.w('att', [round(float(q), 5) for q in m.q])

    def depth(self, m):
        t = self.due('depth', 0.2)
        if t is not None and m.encoding.lower() in ('32fc1', '32fc'):
            img = np.frombuffer(m.data, np.float32)[:m.height * m.width].reshape(m.height, m.width)
            np.save(f'{out}/depth/{t:.3f}.npy', img[::2, ::2].astype(np.float16))

    def lidar(self, m):
        t = self.due('lidar', 0.2)
        if t is not None:
            p = point_cloud2.read_points_numpy(m, field_names=('x', 'y', 'z'))
            p = p[np.isfinite(p).all(axis=1)]
            np.save(f'{out}/lidar/{t:.3f}.npy', p.astype(np.float16))


    def verdict(self, m):
        if self.due('verdict', 0.2) is not None:
            self.w('land', json.loads(m.data))

    def landing(self, m, kind):
        t = self.due('landing_' + kind, 0.2)
        if t is not None:
            p = point_cloud2.read_points_numpy(m, field_names=('x', 'y', 'z')) if m.width * m.height else np.zeros((0, 3))
            np.save(f'{out}/landing/{t:.3f}_{kind}.npy', p.astype(np.float16))


rclpy.init()
node = Rec()
signal.signal(signal.SIGTERM, lambda *a: (_ for _ in ()).throw(KeyboardInterrupt))
try:
    rclpy.spin(node)
except KeyboardInterrupt:
    pass
