"""Compute depth maps for images in the input folder."""

import os

import cv2
import numpy as np
import torch
from model_loader import default_models, load_model

import utils

first_execution = True

first_execution = True


def process(device, model, model_type, image, input_size, target_size, optimize, use_camera):
    """
    Run the inference and interpolate.

    Args:
        device (torch.device): the torch device used
        model: the model used for inference
        model_type: the type of the model
        image: the image fed into the neural network
        input_size: the size (width, height) of the neural network input (for OpenVINO)
        target_size: the size (width, height) the neural network output is interpolated to
        optimize: optimize the model to half-floats on CUDA?
        use_camera: is the camera used?

    Returns:
        the prediction
    """
    global first_execution

    if "openvino" in model_type:
        if first_execution or not use_camera:
            print(
                f"    Input resized to {input_size[0]}x{input_size[1]} before entering the encoder"
            )
            first_execution = False

        sample = [np.reshape(image, (1, 3, *input_size))]
        prediction = model(sample)[model.output(0)][0]
        prediction = cv2.resize(prediction, dsize=target_size, interpolation=cv2.INTER_CUBIC)
    else:
        sample = torch.from_numpy(image).to(device).unsqueeze(0)

        if optimize and device == torch.device("cuda"):
            if first_execution:
                print(
                    "  Optimization to half-floats activated. Use with caution, because models like Swin require\n"
                    "  float precision to work properly and may yield non-finite depth values to some extent for\n"
                    "  half-floats."
                )
            sample = sample.to(memory_format=torch.channels_last)
            sample = sample.half()

        if first_execution or not use_camera:
            height, width = sample.shape[2:]
            print(f"    Input resized to {width}x{height} before entering the encoder")
            first_execution = False

        prediction = model.forward(sample)
        prediction = (
            torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=target_size[::-1],
                mode="bicubic",
                align_corners=False,
            )
            .squeeze()
            .cpu()
            .numpy()
        )

    return prediction


def create_side_by_side(image, depth, grayscale):
    """
    Take an RGB image and depth map and place them side by side. This includes a proper normalization of the depth map
    for better visibility.

    Args:
        image: the RGB image
        depth: the depth map
        grayscale: use a grayscale colormap?

    Returns:
        the image and depth map place side by side
    """
    depth_min = depth.min()
    depth_max = depth.max()
    normalized_depth = 255 * (depth - depth_min) / (depth_max - depth_min)
    normalized_depth *= 3

    right_side = np.repeat(np.expand_dims(normalized_depth, 2), 3, axis=2) / 3
    if not grayscale:
        right_side = cv2.applyColorMap(np.uint8(right_side), cv2.COLORMAP_INFERNO)

    if image is None:
        return right_side
    else:
        return np.concatenate((image, right_side), axis=1)


def run(img_sources, model_path = None, model_type="dpt_swin2_large_384", optimize=False, height=None,
        square=False, grayscale=False):
    """ img_sources: list of image URLs"""
    print("Initialize")

    if model_path is None:
        model_path = default_models[model_type]
        print("  Using default model for %s: %s" % (model_type, model_path))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device: %s" % device)

    model, transform, net_w, net_h = load_model(device, model_path, model_type, optimize, height, square)

    # get input
    num_images = len(img_sources)
    print("Start processing")
    results = []

    for index, url in enumerate(img_sources):

        # input
        original_image_rgb = utils.load_image_from_url(url)  # in [0, 1]
        image = transform({"image": original_image_rgb})["image"]

        # compute
        with torch.no_grad():
            prediction = process(device, model, model_type, image, (net_w, net_h), original_image_rgb.shape[1::-1],
                                optimize, False)
        results.append(prediction.astype(np.float32))
    
    return results

if __name__ == "__main__":
    input_path = ["https://lh3.googleusercontent.com/place-photos/AEkURDx03-8vfQPvYg11_8scYfRtdK8213AArtwFtbT84UMSkW6W3kFRfeBeY_-IkPETwspgDMXtamZR6_6xDFTpwXGlpGr1YEx36Sl1fscuG_nV8nBYQYXkD4V9-GM7pE7MVdWdv3qhlxsx9vKetIPfy2ASjA=s1600-w400"]
    output_path = "\\output"
    model_path = "midas_v21_small_256.pt"
    results = run(input_path, model_path, model_type="midas_v21_small_256", optimize=True, height=None,
        square=False, grayscale=False)

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    i = 0
    for res in results:
        i += 1
        output_file = os.path.join(output_path, str(i))
        utils.write_pfm(output_file + ".pfm", res)
        
