"""
Visualize Camera Ray Direction

Creates a 3D plot showing the center pixel ray and comparison rays.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Define rays
rays = {
    'Center (960,540)': np.array([0.024, -0.121, 0.992]),
    'Perfect Upward': np.array([0.0, 0.0, 1.0]),
    'Top-Left (0,0)': np.array([-0.7510, -0.5028, 0.4281]),
    'Top-Right (1920,0)': np.array([0.7605, -0.4921, 0.4237]),
}

# Calculate angles from vertical
up = np.array([0, 0, 1])
angles = {}
for name, ray in rays.items():
    if 'Perfect' not in name:
        angle = np.degrees(np.arccos(np.dot(ray, up)))
        angles[name] = angle

# Create 3D plot
fig = plt.figure(figsize=(14, 10))

# Plot 1: 3D Ray Visualization
ax1 = fig.add_subplot(221, projection='3d')
ax1.set_title('Camera Rays in 3D Space', fontsize=14, fontweight='bold')

colors = {
    'Center (960,540)': 'green',
    'Perfect Upward': 'blue',
    'Top-Left (0,0)': 'red',
    'Top-Right (1920,0)': 'orange',
}

# Camera position
camera_pos = np.array([0, 0, 0])
ax1.scatter(*camera_pos, color='black', s=200, marker='o', label='Camera', zorder=5)

# Draw rays
for name, ray in rays.items():
    end_point = camera_pos + ray * 0.5  # Scale for visibility
    
    ax1.quiver(camera_pos[0], camera_pos[1], camera_pos[2],
              ray[0], ray[1], ray[2],
              color=colors[name], arrow_length_ratio=0.15,
              linewidth=2.5 if 'Center' in name else 1.5,
              alpha=1.0 if 'Center' in name else 0.6,
              label=name)

ax1.set_xlabel('X (horizontal)', fontsize=10)
ax1.set_ylabel('Y (depth)', fontsize=10)
ax1.set_zlabel('Z (HEIGHT)', fontsize=10, fontweight='bold')
ax1.legend(loc='upper left', fontsize=8)
ax1.set_xlim(-0.5, 0.5)
ax1.set_ylim(-0.4, 0.2)
ax1.set_zlim(0, 0.6)
ax1.view_init(elev=20, azim=45)
ax1.grid(True, alpha=0.3)

# Plot 2: Component Breakdown (Center Ray)
ax2 = fig.add_subplot(222)
ax2.set_title('Center Ray Components [0.024, -0.121, 0.992]', 
              fontsize=12, fontweight='bold')

center_ray = rays['Center (960,540)']
components = ['X (right)', 'Y (back)', 'Z (UP)']
values = [center_ray[0], abs(center_ray[1]), center_ray[2]]
colors_bar = ['coral', 'lightblue', 'lime']

bars = ax2.bar(components, values, color=colors_bar, edgecolor='black', linewidth=1.5)
ax2.set_ylabel('Magnitude', fontsize=11)
ax2.set_ylim(0, 1.1)
ax2.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar, val in zip(bars, values):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
            f'{val:.3f}\n({val*100:.1f}%)',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='Perfect Vertical')

# Plot 3: Angle Comparison
ax3 = fig.add_subplot(223)
ax3.set_title('Angle from Vertical', fontsize=12, fontweight='bold')

ray_names = list(angles.keys())
angle_values = [angles[name] for name in ray_names]
colors_angle = [colors[name] for name in ray_names]

bars = ax3.barh(ray_names, angle_values, color=colors_angle, edgecolor='black', linewidth=1.5)
ax3.set_xlabel('Angle (degrees)', fontsize=11)
ax3.set_xlim(0, 70)
ax3.grid(axis='x', alpha=0.3)

# Add value labels
for bar, val in zip(bars, angle_values):
    width = bar.get_width()
    ax3.text(width + 1, bar.get_y() + bar.get_height()/2.,
            f'{val:.1f}°',
            ha='left', va='center', fontsize=10, fontweight='bold')

# Plot 4: Ray Paths at Different Heights
ax4 = fig.add_subplot(224)
ax4.set_title('Ray Path: Where Center Pixel Points', fontsize=12, fontweight='bold')

center_ray = rays['Center (960,540)']
heights = np.linspace(0, 0.5, 50)
x_positions = []
y_positions = []

for z in heights:
    t = z / center_ray[2]  # Solve for parameter t
    point = t * center_ray
    x_positions.append(point[0] * 100)  # Convert to cm
    y_positions.append(point[1] * 100)

ax4.plot(y_positions, heights * 100, 'g-', linewidth=3, label='Center Ray')
ax4.plot([0], [0], 'ko', markersize=10, label='Camera')
ax4.set_xlabel('Y Position (cm, backward ←)', fontsize=10)
ax4.set_ylabel('Z Height (cm, UP ↑)', fontsize=10, fontweight='bold')
ax4.grid(True, alpha=0.3)
ax4.legend(fontsize=9)
ax4.axhline(y=0, color='brown', linewidth=2, alpha=0.5, label='Ground')
ax4.axvline(x=0, color='gray', linestyle='--', alpha=0.5)

# Add annotations
ax4.annotate('At Z=30cm:\nY=-3.6cm back', 
            xy=(-3.6, 30), xytext=(-8, 35),
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
            fontsize=9, color='red', fontweight='bold')

plt.tight_layout()
plt.savefig('camera/ray_direction_visualization.png', dpi=150, bbox_inches='tight')
print("[OK] Saved: camera/ray_direction_visualization.png")
print("\nVisualization shows:")
print("  - Green ray (center): Mostly UP (99%)")
print("  - Red/orange rays (edges): More tilted (~65°)")
print("  - Center ray only 7.3° from vertical!")

plt.show()



