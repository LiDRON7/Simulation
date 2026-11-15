"""render.py REC_DIR VIDEO_DIR OUT_DIR DRONE VIEWS
Puts a minimap (obstacle map, A* path, start A, goal B, drone, state) on every camera video, and draws the views
Gazebo can't film: 'depth' (the camera's depth image) and 'lidar-<chase|top|pad|tree|crate|wide>' (the LiDAR cloud)."""
import bisect, glob, json, math, os, re, subprocess, sys, tempfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from scene import FIXED, src as SIM

rec, vids, out, drone, views = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5].split(',')
os.makedirs(out, exist_ok=True)
ev = [json.loads(l) for l in open(f'{rec}/log.jsonl') if l.strip()]
S = {k: [(e['t'], e['d']) for e in ev if e['k'] == k] for k in ('grid', 'path', 'pos', 'att', 'state')}
T = {k: [x[0] for x in v] for k, v in S.items()}
t_end = ev[-1]['t']
# B: the destination the scenario sent (log.txt next to data/); else the end of the first planned path.
_log = os.path.join(os.path.dirname(os.path.abspath(rec)), 'log.txt')
_m = re.search(r'destination: N (-?[0-9.]+) E (-?[0-9.]+)', open(_log).read()) if os.path.exists(_log) else None
dn, de = (float(_m.group(1)), float(_m.group(2))) if _m else \
    (S['path'][0][1][-1] if S['path'] and S['path'][0][1] else (0.0, 0.0))


def at(k, t):
    i = bisect.bisect_right(T[k], t) - 1
    return S[k][i][1] if i >= 0 else None


COL = {'NAVIGATING': '#4dabf7', 'PLANNING': '#4dabf7', 'REPLANNING': '#ffa94d', 'HOLD': '#ff6b6b', 'ABORT': '#ff6b6b',
       'PILOT_OVERRIDE': '#b197fc', 'LANDING_CHECK': '#38d9a9', 'LANDING': '#94d82d', 'COMPLETE': '#94d82d'}
ns = [0, dn] + [p[1][0] for p in S['pos']]
es = [0, de] + [p[1][1] for p in S['pos']]
CN, CE = (max(ns) + min(ns)) / 2, (max(es) + min(es)) / 2
HALF = max(max(ns) - min(ns), max(es) - min(es)) / 2 + 4


def minimap(ax, t):
    """Top-down map in PX4's frame: north up, east right."""
    ax.set_facecolor('#1b1b1b')
    g = at('grid', t)
    if g:
        r = g['r']
        for n, e in g['cells']:
            ax.add_patch(plt.Rectangle((e - r / 2, n - r / 2), r, r, color='#868e96', lw=0))
    p = at('path', t)
    if p:
        ax.plot([q[1] for q in p], [q[0] for q in p], color='#4dabf7', lw=2)
    i = bisect.bisect_right(T['pos'], t)
    trail = [x[1] for x in S['pos'][max(0, i - 600):i]]
    if trail:
        ax.plot([q[1] for q in trail], [q[0] for q in trail], color='#ffd43b', lw=1.2, alpha=0.7)
        ax.plot(trail[-1][1], trail[-1][0], 'o', color='#ffd43b', ms=9, mec='#111111')
    ax.plot(0, 0, 's', color='#69db7c', ms=10); ax.text(0.7, 0.7, 'A', color='#69db7c', fontsize=12, weight='bold')
    ax.plot(de, dn, 'X', color='#ff6b6b', ms=11); ax.text(de + 0.7, dn + 0.7, 'B', color='#ff6b6b', fontsize=12, weight='bold')
    ax.set_xlim(CE - HALF, CE + HALF); ax.set_ylim(CN - HALF, CN + HALF); ax.set_aspect('equal')
    ax.tick_params(colors='#666666', labelsize=7)
    for s in ax.spines.values():
        s.set_color('#444444')
    st = at('state', t) or ''
    h = -trail[-1][2] if trail else 0.0
    ax.set_title(f'{st}   {h:.1f} m up', color=COL.get(st, '#dddddd'), fontsize=11, weight='bold', loc='left')


def ffmpeg(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)


def overlay(video, dst):
    """Camera video + minimap. The video's last frame lines up with the log's end (the sim stops with the recorder)."""
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                            'stream=r_frame_rate,nb_read_packets', '-of', 'csv=p=0', video], capture_output=True, text=True).stdout
    rate, frames = probe.strip().split(',')[:2]
    fps = eval(rate); frames = int(frames); t0 = t_end - frames / fps
    tmp = tempfile.mkdtemp()
    fig = plt.figure(figsize=(4, 4.2), dpi=100); fig.patch.set_facecolor('#111111')
    for k, t in enumerate(np.arange(t0, t_end, 1 / 12)):
        fig.clear(); minimap(fig.add_axes([0.08, 0.05, 0.88, 0.85]), t)
        fig.savefig(f'{tmp}/{k:05d}.png', facecolor=fig.get_facecolor())
    plt.close(fig)
    ffmpeg('-i', video, '-framerate', '12', '-i', f'{tmp}/%05d.png', '-filter_complex',
           f'[1]fps={fps:g},scale=380:-1[m];[0][m]overlay=W-w-16:16:shortest=1', '-c:v', 'libx264', '-crf', '20',
           '-pix_fmt', 'yuv420p', dst)


def quat(q):  # PX4 (w, x, y, z), body FRD to NED
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def rpy(r, p, y):  # SDF: fixed-axis roll, pitch, yaw
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]) @ np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]]) \
        @ np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])


def lidar_mount():
    sdf = open(f'{SIM}/models/{drone}/model.sdf').read()
    m = re.search(r'<link name="lidar_link">\s*<pose relative_to="base_link">([^<]+)</pose>', sdf)
    v = [float(x) for x in m.group(1).split()]
    return rpy(*v[3:]), np.array(v[:3])


def to_world(pts, t, R_mount, t_mount):
    """LiDAR frame -> Gazebo's east/north/up through the drone's PX4 pose."""
    pos, q = at('pos', t), at('att', t)
    if pos is None or q is None:
        return None, None, None
    flu = pts @ R_mount.T + t_mount
    frd = flu * np.array([1, -1, -1])
    ned = frd @ quat(q).T + np.array(pos)
    enu = np.stack([ned[:, 1], ned[:, 0], -ned[:, 2]], axis=1)
    yaw = math.atan2(2 * (q[0] * q[3] + q[1] * q[2]), 1 - 2 * (q[2] ** 2 + q[3] ** 2))  # NED yaw from north
    return enu, np.array([pos[1], pos[0], -pos[2]]), yaw


def project(P, eye, target, w=1280, h=720, fov=1.1):
    f = target - eye; f /= np.linalg.norm(f)
    hint = np.array([0, 1.0, 0]) if abs(f[2]) > 0.95 else np.array([0, 0, 1.0])
    r = np.cross(f, hint); r /= np.linalg.norm(r); u = np.cross(r, f)
    d = P - eye; z = d @ f; ok = z > 0.2
    fx = w / 2 / math.tan(fov / 2)
    return w / 2 + fx * (d @ r) / np.where(ok, z, 1), h / 2 - fx * (d @ u) / np.where(ok, z, 1), ok, z


def lidar_view(name, dst):
    files = sorted(glob.glob(f'{rec}/lidar/*.npy'), key=lambda p: float(os.path.basename(p)[:-4]))
    if not files:
        print(f'{name}: no LiDAR data ({drone} has no LiDAR?)'); return
    R_m, t_m = lidar_mount()
    gx, gy = np.meshgrid(np.arange(-40, 41, 2.0), np.arange(-40, 41, 2.0))
    grid = np.stack([gx.ravel(), gy.ravel(), np.zeros(gx.size)], axis=1)
    tmp = tempfile.mkdtemp()
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    k = 0
    for fpath in files:
        t = float(os.path.basename(fpath)[:-4])
        enu, me, yaw = to_world(np.load(fpath).astype(np.float32), t, R_m, t_m)
        if enu is None:
            continue
        head = np.array([math.sin(yaw), math.cos(yaw), 0])
        if name == 'chase':
            eye, target = me - 7 * head + [0, 0, 3.5], me + 3 * head
        elif name == 'top':
            eye, target = me + [0, -0.01, 30], me
        else:
            eye, target = np.array(FIXED[name][0], float), np.array(FIXED[name][1], float)
        fig.clear(); fig.patch.set_facecolor('#0d0d0d')
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1280); ax.set_ylim(720, 0); ax.axis('off'); ax.set_facecolor('#0d0d0d')
        gxp, gyp, ok, _ = project(grid, eye, target)
        ax.scatter(gxp[ok], gyp[ok], s=1, c='#333333')
        x, y, ok, z = project(enu, eye, target)
        ax.scatter(x[ok], y[ok], s=2, c=enu[ok, 2], cmap='turbo', vmin=-0.3, vmax=6, linewidths=0)
        dx, dy, dok, _ = project(me[None], eye, target)
        if dok[0]:
            ax.plot(dx, dy, 'o', ms=12, mfc='none', mec='#ffd43b', mew=2)
        ax.text(20, 40, f'{drone} · LiDAR · {name} view · coloured by height (0 to 6 m)', color='#dddddd', fontsize=14)
        minimap(fig.add_axes([0.72, 0.42, 0.26, 0.5]), t)
        fig.savefig(f'{tmp}/{k:05d}.png', facecolor=fig.get_facecolor()); k += 1
    plt.close(fig)
    ffmpeg('-framerate', '5', '-i', f'{tmp}/%05d.png', '-vf', 'fps=10,format=yuv420p', '-c:v', 'libx264', '-crf', '20', dst)


def depth_view(dst):
    files = sorted(glob.glob(f'{rec}/depth/*.npy'), key=lambda p: float(os.path.basename(p)[:-4]))
    tmp = tempfile.mkdtemp()
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    for k, fpath in enumerate(files):
        t = float(os.path.basename(fpath)[:-4])
        d = np.load(fpath).astype(np.float32)
        d[~np.isfinite(d) | (d <= 0)] = np.nan
        h, w = d.shape
        c = d[int(h * 0.3):int(h * 0.7), int(w * 0.3):int(w * 0.7)]
        close = np.nanmin(c) if np.isfinite(c).any() else float('inf')
        fig.clear(); fig.patch.set_facecolor('#0d0d0d')
        ax = fig.add_axes([0.01, 0.02, 0.68, 0.9])
        im = ax.imshow(d, cmap='turbo_r', vmin=0.2, vmax=12); ax.axis('off')
        ax.add_patch(plt.Rectangle((w * 0.3, h * 0.3), w * 0.4, h * 0.4, fill=False, ec='white', lw=1.5, ls='--'))
        cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.01); cb.ax.tick_params(colors='#aaaaaa'); cb.set_label('m', color='#aaaaaa')
        fig.text(0.01, 0.95, f'{drone} · OAK-D depth · closest in the centre box: {close:.1f} m', color='#dddddd', fontsize=14)
        minimap(fig.add_axes([0.73, 0.15, 0.25, 0.7]), t)
        fig.savefig(f'{tmp}/{k:05d}.png', facecolor=fig.get_facecolor())
    plt.close(fig)
    if files:
        ffmpeg('-framerate', '5', '-i', f'{tmp}/%05d.png', '-vf', 'fps=10,format=yuv420p', '-c:v', 'libx264', '-crf', '20', dst)


for v in views:
    if v == 'depth':
        depth_view(f'{out}/depth.mp4')
    elif v.startswith('lidar-'):
        lidar_view(v[6:], f'{out}/{v}.mp4')
    elif os.path.exists(f'{vids}/{v}.mp4'):
        overlay(f'{vids}/{v}.mp4', f'{out}/{v}.mp4')
    print('wrote' if os.path.exists(f'{out}/{v}.mp4') else 'skipped', f'{out}/{v}.mp4')
