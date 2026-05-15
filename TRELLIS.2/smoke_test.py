import os
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
os.environ["PY_SSIZE_T_CLEAN"] = "1"
import cv2
import imageio
from PIL import Image
import torch
from trellis2.pipelines import Trellis2ImageTo3DPipeline
from trellis2.utils import render_utils
from trellis2.renderers import EnvMap
import o_voxel

print(f"PyTorch: {torch.__version__}, CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}, VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# 1. Setup Environment Map
print("Loading environment map...")
envmap = EnvMap(torch.tensor(
    cv2.cvtColor(cv2.imread('assets/hdri/forest.exr', cv2.IMREAD_UNCHANGED), cv2.COLOR_BGR2RGB),
    dtype=torch.float32, device='cuda'
))

# 2. Load Pipeline from local weights
print("Loading pipeline from local weights...")
pipeline = Trellis2ImageTo3DPipeline.from_pretrained("TRELLIS.2-4B")
pipeline.cuda()
print("Pipeline loaded.")

# 3. Load Image & Run
print("Loading test image...")
image = Image.open("assets/example_image/T.png")
print(f"Image size: {image.size}, starting generation (512 resolution)...")

mesh = pipeline.run(image)[0]
mesh.simplify(16777216)
print("Generation complete.")

# 4. Render Video
print("Rendering preview video...")
video = render_utils.make_pbr_vis_frames(render_utils.render_video(mesh, envmap=envmap))
imageio.mimsave("/tmp/smoke_test.mp4", video, fps=15)
print("Video saved to /tmp/smoke_test.mp4")

# 5. Export to GLB
print("Exporting GLB...")
glb = o_voxel.postprocess.to_glb(
    vertices            =   mesh.vertices,
    faces               =   mesh.faces,
    attr_volume         =   mesh.attrs,
    coords              =   mesh.coords,
    attr_layout         =   mesh.layout,
    voxel_size          =   mesh.voxel_size,
    aabb                =   [[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
    decimation_target   =   300000,
    texture_size        =   2048,
    remesh              =   True,
    remesh_band         =   1,
    remesh_project      =   0,
    verbose             =   True
)
glb.export("/tmp/smoke_test.glb")
print("GLB saved to /tmp/smoke_test.glb")
print("Smoke test PASSED!")
