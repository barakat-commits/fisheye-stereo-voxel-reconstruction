#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

struct Vec3 {
    float x, y, z;
    
    Vec3() : x(0), y(0), z(0) {}
    Vec3(float x_, float y_, float z_) : x(x_), y(y_), z(z_) {}
    
    Vec3 operator+(const Vec3& other) const {
        return Vec3(x + other.x, y + other.y, z + other.z);
    }
    
    Vec3 operator-(const Vec3& other) const {
        return Vec3(x - other.x, y - other.y, z - other.z);
    }
    
    Vec3 operator*(float scalar) const {
        return Vec3(x * scalar, y * scalar, z * scalar);
    }
    
    float length() const {
        return std::sqrt(x * x + y * y + z * z);
    }
    
    Vec3 normalized() const {
        float len = length();
        if (len > 0) {
            return Vec3(x / len, y / len, z / len);
        }
        return Vec3(0, 0, 0);
    }
};

struct RayStep {
    int ix, iy, iz;
    float distance;
};

std::vector<RayStep> cast_ray_into_grid(
    Vec3 camera_pos, 
    Vec3 direction, 
    int N, 
    float voxel_size, 
    Vec3 grid_center
) {
    std::vector<RayStep> steps;
    
    // Normalize direction
    direction = direction.normalized();
    
    // Grid bounds
    float half_grid = (N * voxel_size) / 2.0f;
    Vec3 grid_min = Vec3(
        grid_center.x - half_grid,
        grid_center.y - half_grid,
        grid_center.z - half_grid
    );
    
    // DDA (Digital Differential Analyzer) algorithm
    Vec3 current_pos = camera_pos;
    float max_distance = N * voxel_size * 2.0f;
    float step_size = voxel_size * 0.5f;
    
    for (float t = 0; t < max_distance; t += step_size) {
        current_pos = camera_pos + direction * t;
        
        // Convert to grid coordinates
        int ix = static_cast<int>((current_pos.x - grid_min.x) / voxel_size);
        int iy = static_cast<int>((current_pos.y - grid_min.y) / voxel_size);
        int iz = static_cast<int>((current_pos.z - grid_min.z) / voxel_size);
        
        // Check bounds
        if (ix >= 0 && ix < N && iy >= 0 && iy < N && iz >= 0 && iz < N) {
            RayStep step;
            step.ix = ix;
            step.iy = iy;
            step.iz = iz;
            step.distance = t;
            steps.push_back(step);
        }
    }
    
    return steps;
}

py::array_t<float> process_image_to_voxel_grid(
    py::array_t<float> image,
    py::array_t<float> camera_position,
    py::array_t<float> camera_rotation,
    int grid_size,
    float voxel_size,
    py::array_t<float> grid_center_array,
    float attenuation_factor
) {
    auto img_buf = image.request();
    auto cam_pos_buf = camera_position.request();
    auto cam_rot_buf = camera_rotation.request();
    auto grid_center_buf = grid_center_array.request();
    
    if (img_buf.ndim != 2) {
        throw std::runtime_error("Image must be 2-dimensional");
    }
    
    int img_height = img_buf.shape[0];
    int img_width = img_buf.shape[1];
    
    float *img_ptr = static_cast<float *>(img_buf.ptr);
    float *cam_pos_ptr = static_cast<float *>(cam_pos_buf.ptr);
    float *grid_center_ptr = static_cast<float *>(grid_center_buf.ptr);
    
    Vec3 cam_pos(cam_pos_ptr[0], cam_pos_ptr[1], cam_pos_ptr[2]);
    Vec3 grid_center(grid_center_ptr[0], grid_center_ptr[1], grid_center_ptr[2]);
    
    // Initialize voxel grid
    int total_voxels = grid_size * grid_size * grid_size;
    std::vector<float> voxel_grid(total_voxels, 0.0f);
    
    // Process each pixel in parallel
    #pragma omp parallel for collapse(2)
    for (int py = 0; py < img_height; ++py) {
        for (int px = 0; px < img_width; ++px) {
            float pixel_value = img_ptr[py * img_width + px];
            
            if (pixel_value <= 0) continue;
            
            // Calculate ray direction (simplified pinhole camera model)
            float nx = (px - img_width / 2.0f) / (img_width / 2.0f);
            float ny = (py - img_height / 2.0f) / (img_height / 2.0f);
            
            Vec3 direction(nx, ny, 1.0f);
            
            // Cast ray
            std::vector<RayStep> steps = cast_ray_into_grid(
                cam_pos, direction, grid_size, voxel_size, grid_center
            );
            
            // Accumulate brightness in voxels
            for (const auto& step : steps) {
                float attenuation = std::exp(-attenuation_factor * step.distance);
                int idx = step.ix * grid_size * grid_size + step.iy * grid_size + step.iz;
                
                #pragma omp atomic
                voxel_grid[idx] += pixel_value * attenuation;
            }
        }
    }
    
    // Return as numpy array
    py::array_t<float> result({grid_size, grid_size, grid_size});
    auto result_buf = result.request();
    float *result_ptr = static_cast<float *>(result_buf.ptr);
    
    std::copy(voxel_grid.begin(), voxel_grid.end(), result_ptr);
    
    return result;
}

py::array_t<float> create_rotation_matrix(float roll, float pitch, float yaw) {
    py::array_t<float> result({3, 3});
    auto buf = result.request();
    float *ptr = static_cast<float *>(buf.ptr);
    
    // Rotation matrix from Euler angles (ZYX convention)
    float cr = std::cos(roll);
    float sr = std::sin(roll);
    float cp = std::cos(pitch);
    float sp = std::sin(pitch);
    float cy = std::cos(yaw);
    float sy = std::sin(yaw);
    
    ptr[0] = cy * cp;
    ptr[1] = cy * sp * sr - sy * cr;
    ptr[2] = cy * sp * cr + sy * sr;
    ptr[3] = sy * cp;
    ptr[4] = sy * sp * sr + cy * cr;
    ptr[5] = sy * sp * cr - cy * sr;
    ptr[6] = -sp;
    ptr[7] = cp * sr;
    ptr[8] = cp * cr;
    
    return result;
}

PYBIND11_MODULE(process_image_cpp, m) {
    m.doc() = "C++ module for efficient ray casting and voxel grid processing";
    
    m.def("process_image_to_voxel_grid", &process_image_to_voxel_grid,
          "Process an image into a voxel grid using ray casting",
          py::arg("image"),
          py::arg("camera_position"),
          py::arg("camera_rotation"),
          py::arg("grid_size"),
          py::arg("voxel_size"),
          py::arg("grid_center"),
          py::arg("attenuation_factor") = 0.01f
    );
    
    m.def("create_rotation_matrix", &create_rotation_matrix,
          "Create a 3x3 rotation matrix from Euler angles",
          py::arg("roll"),
          py::arg("pitch"),
          py::arg("yaw")
    );
}



