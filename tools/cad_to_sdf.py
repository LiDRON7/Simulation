#!/usr/bin/env python3
"""Build the Gazebo models and PX4 airframe files for Widow and Huntsman from the CAD.

    python3 tools/cad_to_sdf.py                 # both drones, CAD repo next to this one
    python3 tools/cad_to_sdf.py --cad "/path/to/Drone-Construction/3D Models" --mesh --stl huntsman=/tmp/huntsman.stl

Reads <cad>/<Drone>/Full Drone/<drone>-checks.json, which the Fusion full-drone scripts write (every weight and
where it sits, the rotors, the sensors, the skids). Writes models/<drone>/ and config/airframes/<id>_gz_<drone>.
Rerun it after any CAD change; don't edit the generated files by hand.

--mesh also rebuilds models/<drone>/meshes/<drone>.stl from the CAD's full-drone STL, thinned to MESH_FACES
(needs: pip install numpy fast-simplification). Without it the mesh already in the repo is kept. Huntsman's full-drone
STL is too big to keep in the CAD repo (35 MB): export it from Fusion (File > Export, STL, low refinement) and pass
it with --stl huntsman=<file>.

What is real and what is a guess:
  from the CAD     weight, centre of mass, rotor and sensor positions, skids, the look
  estimated        moments of inertia (each part as a point at its place: good to maybe 20 %)
  EST, not measured  motor thrust and top speed. Put a motor on a thrust stand and fix MOTORS below.
Frames: model x forward, y left, z up, origin at the centre of mass. PX4 params are forward, right, down.
"""
import argparse, json, math, os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
G = 9.81
MESH_FACES = 40000
# max_rad_s: top loaded motor speed = KV x full battery volts x 0.8. max_thrust_n: EST from prop size, per motor.
# moment: torque per newton of thrust (m), EST, scaled from the x500's 0.016 for a 13 in prop.
MOTORS = {
    'widow':    dict(autostart=22001, max_rad_s=1330.0, max_thrust_n=8.0, moment=0.012, prop_g=8.0),      # M2208 1260 KV, 3S, 8045
    'huntsman': dict(autostart=22002, max_rad_s=802.0, max_thrust_n=18.6, moment=0.017, prop_g=30.0),     # Tarot 4108 380 KV, 6S, 1355
}
# PX4 "hexarotor x" motor order: where each motor sits (deg from forward, counter-clockwise seen from above) and its spin
HEXA_X = [(-90, 'cw'), (90, 'ccw'), (30, 'cw'), (-150, 'ccw'), (-30, 'ccw'), (150, 'cw')]
OAKD = dict(rgb_hfov=1.257, depth_hfov=1.396)     # OAK-D Pro: RGB 72 deg, stereo 80 deg (the CAD scripts use the same)


def load(cad, drone):
    d = json.load(open(os.path.join(cad, drone.capitalize(), 'Full Drone', f'{drone}-checks.json')))
    s = d['sim']
    items = [(n, g / 1000.0, [v / 1000.0 for v in c], r / 1000.0) for n, g, c, r in s['items']]
    m = sum(g for _, g, _, _ in items)
    table_cg = [sum(g * c[i] for _, g, c, _ in items) / m for i in range(3)]
    cg = [v / 1000.0 for v in d['cg_mm']]
    assert abs(m * 1000 - d['total_g']) < 0.01 * d['total_g'], f'{drone}: weight table {m * 1000:.0f} g, CAD says {d["total_g"]} g'
    assert max(abs(a - b) for a, b in zip(table_cg, cg)) < 0.006, f'{drone}: weight table centre {table_cg} is not the CAD centre {cg}'
    # inertia about the centre of mass: point masses, plus spread weights as rings of radius r round the z axis
    I = [0.0, 0.0, 0.0]
    for _, g, c, r in items:
        x, y, z = (c[i] - cg[i] for i in range(3))
        I[0] += g * (y * y + z * z + r * r / 2); I[1] += g * (x * x + z * z + r * r / 2); I[2] += g * (x * x + y * y + r * r)
    rel = lambda p: [p[i] / 1000.0 - cg[i] for i in range(3)]
    off = lambda p, ang: abs((math.degrees(math.atan2(p[1], p[0])) - ang + 180) % 360 - 180)
    rotors = []
    for ang, spin in HEXA_X:                      # put the CAD's rotors in PX4's order
        r = min(s['rotors'], key=lambda p: off(p, ang))
        assert off(r, ang) < 5, f'{drone}: no rotor at {ang} deg'
        rotors.append((rel(r), spin))
    assert len({tuple(r[0]) for r in rotors}) == 6, f'{drone}: need six different rotors'
    inradius = min(math.hypot(p[0], p[1]) for p in s['rotors']) / 1000.0 * math.cos(math.radians(30))
    assert math.hypot(cg[0], cg[1]) < 0.1 * inradius, f'{drone}: centre of mass far from the middle of the motors'
    skids = [[b[i] / 1000.0 - cg[i % 3] for i in range(6)] for b in s['skids']]
    return dict(name=drone, mass=m, cg=cg, inertia=I, rotors=rotors, prop_r=s['prop_d'] / 2000.0,
                imu=rel(s['imu']), gps=rel(s['gps']), camera=rel(s['camera']), tilt=math.radians(s['camera_tilt_deg']),
                lidar=rel(s['lidar']) if s['lidar'] else None, skids=skids, ground=min(b[2] for b in skids),
                **MOTORS[drone])


def box(name, b):    # collision box from x0, y0, z0, x1, y1, z1
    c = [(b[i] + b[i + 3]) / 2 for i in range(3)]; sz = [b[i + 3] - b[i] for i in range(3)]
    return f'''      <collision name="{name}">
        <pose>{c[0]:.4f} {c[1]:.4f} {c[2]:.4f} 0 0 0</pose>
        <geometry><box><size>{sz[0]:.4f} {sz[1]:.4f} {sz[2]:.4f}</size></box></geometry>
      </collision>
'''


def noise(sd, bias, corr):
    return ''.join(f'<{a}><noise type="gaussian"><mean>0</mean><stddev>{sd}</stddev><dynamic_bias_stddev>{bias}</dynamic_bias_stddev>'
                   f'<dynamic_bias_correlation_time>{corr}</dynamic_bias_correlation_time></noise></{a}>' for a in 'xyz')


def sdf(d, has_mesh):
    n, cg = d['name'], d['cg']
    k = d['max_thrust_n'] / d['max_rad_s'] ** 2                      # thrust = k x speed^2
    body_m = d['mass'] - 6 * d['prop_g'] / 1000.0
    out = f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated by tools/cad_to_sdf.py from the CAD. Do not edit: change the CAD or the tool and rerun it. -->
<sdf version='1.9'>
  <model name='{n}'>
    <pose>0 0 {-d['ground'] + 0.01:.4f} 0 0 0</pose>
    <self_collide>false</self_collide>
    <static>false</static>
    <link name="base_link">
      <inertial>
        <mass>{body_m:.4f}</mass>
        <inertia><ixx>{d['inertia'][0]:.5f}</ixx><ixy>0</ixy><ixz>0</ixz><iyy>{d['inertia'][1]:.5f}</iyy><iyz>0</iyz><izz>{d['inertia'][2]:.5f}</izz></inertia>
      </inertial>
      <gravity>true</gravity>
      <velocity_decay/>
'''
    if has_mesh:
        out += f'''      <visual name="body">
        <pose>{-cg[0]:.4f} {-cg[1]:.4f} {-cg[2]:.4f} 0 0 0</pose>
        <geometry><mesh><scale>0.001 0.001 0.001</scale><uri>model://{n}/meshes/{n}.stl</uri></mesh></geometry>
        <material><ambient>0.25 0.25 0.27 1</ambient><diffuse>0.25 0.25 0.27 1</diffuse></material>
      </visual>
'''
    arm = max(math.hypot(r[0][0], r[0][1]) for r in d['rotors']); rz = d['rotors'][0][0][2]
    out += box('body', [-arm * 0.45, -arm * 0.45, rz - 0.08, arm * 0.45, arm * 0.45, rz - 0.02])
    for i, b in enumerate(d['skids']):
        out += box(f'skid_{i}', b)
    out += f'''      <sensor name="air_pressure_sensor" type="air_pressure">
        <always_on>1</always_on>
        <update_rate>50</update_rate>
        <air_pressure><pressure><noise type="gaussian"><mean>0</mean><stddev>0.01</stddev></noise></pressure></air_pressure>
      </sensor>
      <sensor name="imu_sensor" type="imu">
        <pose>{d['imu'][0]:.4f} {d['imu'][1]:.4f} {d['imu'][2]:.4f} 0 0 0</pose>
        <always_on>1</always_on>
        <update_rate>250</update_rate>
        <imu>
          <angular_velocity>{noise(0.00018665, 3.8785e-05, 1000)}</angular_velocity>
          <linear_acceleration>{noise(0.00186, 0.006, 300)}</linear_acceleration>
        </imu>
      </sensor>
      <sensor name="navsat_sensor" type="navsat">
        <pose>{d['gps'][0]:.4f} {d['gps'][1]:.4f} {d['gps'][2]:.4f} 0 0 0</pose>
        <always_on>1</always_on>
        <update_rate>30</update_rate>
      </sensor>
    </link>
    <link name="camera_link">
      <pose relative_to="base_link">{d['camera'][0]:.4f} {d['camera'][1]:.4f} {d['camera'][2]:.4f} 0 {d['tilt']:.4f} 0</pose>
      <inertial><mass>0.001</mass><inertia><ixx>1e-6</ixx><iyy>1e-6</iyy><izz>1e-6</izz></inertia></inertial>
      <sensor name="oakd_rgb" type="camera">
        <camera>
          <horizontal_fov>{OAKD['rgb_hfov']}</horizontal_fov>
          <image><width>1280</width><height>720</height></image>
          <clip><near>0.1</near><far>100</far></clip>
        </camera>
        <always_on>1</always_on>
        <update_rate>30</update_rate>
        <topic>camera</topic>
      </sensor>
      <sensor name="oakd_depth" type="depth_camera">
        <camera>
          <horizontal_fov>{OAKD['depth_hfov']}</horizontal_fov>
          <image><width>640</width><height>480</height><format>R_FLOAT32</format></image>
          <clip><near>0.2</near><far>19.1</far></clip>
        </camera>
        <always_on>1</always_on>
        <update_rate>30</update_rate>
        <topic>depth_camera</topic>
      </sensor>
    </link>
    <joint name="camera_joint" type="fixed"><parent>base_link</parent><child>camera_link</child></joint>
'''
    if d['lidar']:
        # Puck LITE on its side: spin axis across the drone, top to the right, so the scan sweeps front to back through
        # the ground under the drone. Its 0 deg mark points down and back at 45 deg (Huntsman README). 16 beams, +-15 deg.
        out += f'''    <link name="lidar_link">
      <pose relative_to="base_link">{d['lidar'][0]:.4f} {d['lidar'][1]:.4f} {d['lidar'][2]:.4f} {math.pi / 2:.5f} {math.radians(135):.5f} 0</pose>
      <inertial><mass>0.001</mass><inertia><ixx>1e-6</ixx><iyy>1e-6</iyy><izz>1e-6</izz></inertia></inertial>
      <sensor name="lidar" type="gpu_lidar">
        <always_on>true</always_on>
        <update_rate>10</update_rate>
        <lidar>
          <scan>
            <horizontal><samples>1800</samples><min_angle>-3.14159</min_angle><max_angle>3.14159</max_angle></horizontal>
            <vertical><samples>16</samples><min_angle>-0.2618</min_angle><max_angle>0.2618</max_angle></vertical>
          </scan>
          <range><min>0.1</min><max>100.0</max></range>
        </lidar>
        <topic>/lidar</topic>
      </sensor>
    </link>
    <joint name="lidar_joint" type="fixed"><parent>base_link</parent><child>lidar_link</child></joint>
'''
    pm = d['prop_g'] / 1000.0; i_prop = pm * (2 * d['prop_r']) ** 2 / 12
    for i, (p, spin) in enumerate(d['rotors']):
        out += f'''    <link name="rotor_{i}">
      <gravity>true</gravity>
      <self_collide>false</self_collide>
      <velocity_decay/>
      <pose>{p[0]:.4f} {p[1]:.4f} {p[2]:.4f} 0 0 0</pose>
      <inertial>
        <mass>{pm:.4f}</mass>
        <inertia><ixx>{pm * 1e-4:.3e}</ixx><iyy>{i_prop:.3e}</iyy><izz>{i_prop:.3e}</izz></inertia>
      </inertial>
      <visual name="rotor_{i}_disc">
        <geometry><cylinder><radius>{d['prop_r']:.4f}</radius><length>0.003</length></cylinder></geometry>
        <material><ambient>0.1 0.1 0.1 0.3</ambient><diffuse>0.1 0.1 0.1 0.3</diffuse></material>
        <transparency>0.7</transparency>
      </visual>
    </link>
    <joint name="rotor_{i}_joint" type="revolute">
      <parent>base_link</parent>
      <child>rotor_{i}</child>
      <axis>
        <xyz>0 0 1</xyz>
        <limit><lower>-1e+16</lower><upper>1e+16</upper></limit>
        <dynamics><spring_reference>0</spring_reference><spring_stiffness>0</spring_stiffness></dynamics>
      </axis>
    </joint>
    <plugin filename="gz-sim-multicopter-motor-model-system" name="gz::sim::systems::MulticopterMotorModel">
      <jointName>rotor_{i}_joint</jointName>
      <linkName>rotor_{i}</linkName>
      <turningDirection>{spin}</turningDirection>
      <timeConstantUp>0.0125</timeConstantUp>
      <timeConstantDown>0.025</timeConstantDown>
      <maxRotVelocity>{d['max_rad_s']:.1f}</maxRotVelocity>
      <motorConstant>{k:.5e}</motorConstant>
      <momentConstant>{d['moment']}</momentConstant>
      <commandSubTopic>command/motor_speed</commandSubTopic>
      <motorNumber>{i}</motorNumber>
      <rotorDragCoefficient>8.06428e-05</rotorDragCoefficient>
      <rollingMomentCoefficient>1e-06</rollingMomentCoefficient>
      <rotorVelocitySlowdownSim>10</rotorVelocitySlowdownSim>
      <motorType>velocity</motorType>
    </plugin>
'''
    return out + '  </model>\n</sdf>\n'


def airframe(d):
    n = d['name']
    lo = round(0.12 * d['max_rad_s'])
    w_hover = math.sqrt(d['mass'] * G / 6 / (d['max_thrust_n'] / d['max_rad_s'] ** 2))
    hover = min(0.8, max(0.2, (w_hover - lo) / (d['max_rad_s'] - lo)))
    out = f'''#!/bin/sh
#
# @name Gazebo {n.capitalize()} (LiDRON)
#
# @type Hexarotor x
#
# Generated by Simulation/tools/cad_to_sdf.py from the CAD. Do not edit: rerun the tool.
# {d['mass'] * 1000:.0f} g, thrust to weight {6 * d['max_thrust_n'] / (d['mass'] * G):.2f} (EST: motor thrust is not measured).

. ${{R}}etc/init.d/rc.mc_defaults

PX4_SIMULATOR=${{PX4_SIMULATOR:=gz}}
PX4_GZ_WORLD=${{PX4_GZ_WORLD:=default}}
PX4_SIM_MODEL=${{PX4_SIM_MODEL:={n}}}

param set-default SIM_GZ_EN 1

param set-default SENS_EN_GPSSIM 1
param set-default SENS_EN_BAROSIM 0
param set-default SENS_EN_MAGSIM 1

param set-default CA_AIRFRAME 0
param set-default CA_ROTOR_COUNT 6
'''
    for i, (p, spin) in enumerate(d['rotors']):          # PX4: x forward, y right; + KM = counter-clockwise
        out += f'''
param set-default CA_ROTOR{i}_PX {p[0]:.3f}
param set-default CA_ROTOR{i}_PY {-p[1]:.3f}
param set-default CA_ROTOR{i}_KM {'0.05' if spin == 'ccw' else '-0.05'}
'''
    out += '\n' + ''.join(f'param set-default SIM_GZ_EC_FUNC{i + 1} {101 + i}\n' for i in range(6))
    out += '\n' + ''.join(f'param set-default SIM_GZ_EC_MIN{i + 1} {lo}\n' for i in range(6))
    out += '\n' + ''.join(f'param set-default SIM_GZ_EC_MAX{i + 1} {round(d["max_rad_s"])}\n' for i in range(6))
    out += f'''
param set-default MPC_THR_HOVER {hover:.2f}

# where the Pixhawk sits from the centre of mass (forward, right, down), as in the drone's README
param set-default EKF2_IMU_POS_X {d['imu'][0]:.3f}
param set-default EKF2_IMU_POS_Y {-d['imu'][1]:.3f}
param set-default EKF2_IMU_POS_Z {-d['imu'][2]:.3f}
'''
    return out, hover


def thin_mesh(src, dst):     # binary STL in, thinned binary STL out
    import numpy as np, fast_simplification
    raw = open(src, 'rb').read(); n = struct.unpack_from('<I', raw, 80)[0]
    assert len(raw) == 84 + 50 * n, 'not a binary STL'
    facet = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
    tri = np.frombuffer(raw, dtype=facet, count=n, offset=84)['v']
    pts, idx = np.unique(tri.reshape(-1, 3), axis=0, return_inverse=True)
    v, f = fast_simplification.simplify(pts.astype(np.float32), idx.reshape(-1, 3).astype(np.int32), target_count=MESH_FACES)
    out = np.zeros(len(f), dtype=facet); out['v'] = v[f]
    with open(dst, 'wb') as fh:
        fh.write(b'LiDRON'.ljust(80, b' ') + struct.pack('<I', len(f))); fh.write(out.tobytes())
    return n, len(f)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--cad', default=os.path.join(REPO, '..', 'Drone-Construction', '3D Models'))
    ap.add_argument('--mesh', action='store_true', help='rebuild the look from the CAD full-drone STL')
    ap.add_argument('--stl', action='append', default=[], metavar='DRONE=FILE', help='full-drone STL to use instead of the CAD repo\'s')
    a = ap.parse_args()
    stl = dict(x.split('=', 1) for x in a.stl)
    os.makedirs(os.path.join(REPO, 'config', 'airframes'), exist_ok=True)
    for drone in MOTORS:
        d = load(a.cad, drone)
        mdir = os.path.join(REPO, 'models', drone); os.makedirs(os.path.join(mdir, 'meshes'), exist_ok=True)
        mesh = os.path.join(mdir, 'meshes', f'{drone}.stl')
        if a.mesh:
            src = stl.get(drone) or os.path.join(a.cad, drone.capitalize(), 'Full Drone', f'{drone}-full-drone.stl')
            print(f'{drone}: mesh %d -> %d faces' % thin_mesh(src, mesh))
        open(os.path.join(mdir, 'model.sdf'), 'w').write(sdf(d, os.path.exists(mesh)))
        open(os.path.join(mdir, 'model.config'), 'w').write(f'''<?xml version="1.0"?>
<model>
  <name>{drone}</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>LiDRON {drone.capitalize()}, generated from the CAD by tools/cad_to_sdf.py</description>
</model>
''')
        text, hover = airframe(d)
        open(os.path.join(REPO, 'config', 'airframes', f'{d["autostart"]}_gz_{drone}'), 'w').write(text)
        r3 = lambda p: [round(v, 3) for v in p]
        print(f'{drone}: {d["mass"] * 1000:.0f} g, inertia {[round(v, 4) for v in d["inertia"]]} kg m2, hover throttle {hover:.2f}, '
              f'thrust/weight {6 * d["max_thrust_n"] / (d["mass"] * G):.2f} (EST), camera at {r3(d["camera"])}'
              + (f', lidar at {r3(d["lidar"])}' if d['lidar'] else ', no lidar') + f', skids {-d["ground"]:.3f} m under the centre of mass')
