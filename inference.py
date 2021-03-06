#############
## Imports ##
#############

""" Global """
import cv2
import numpy as np
import argparse
from tqdm import tqdm
from tensorflow import keras

""" Local """
import Model
import constants

###############
## Functions ##
###############

def load_model(model_path, patch_size):
    model = Model.wsi_segmenter(patch_size)
    model.load_weights(model_path)
    return model

def inference(model, image, patch_size):
    mask = np.zeros(image.shape[:2])
    counter = np.zeros(image.shape[:2])
    stride = int(patch_size / 8)
    for i in tqdm(range(0, image.shape[0], stride)):
        for j in range(0, image.shape[1], stride):
            patch_img = image[i:i+patch_size, j:j+patch_size]
            patch_img_shape = patch_img.shape[:2]
            patch_img = cv2.resize(patch_img, (patch_size, patch_size))
            patch_mask = model.predict(np.array([patch_img]), verbose=0)[0, :, :, 0]
            mask[i:i+patch_img_shape[0], j:j+patch_img_shape[1]] += cv2.resize(patch_mask, patch_img_shape[::-1])
            counter[i:i+patch_img_shape[0], j:j+patch_img_shape[1]] += 1
    mask = (1. * mask / counter)
    return mask

##########
## MAIN ##
##########

def parse_args():
    parser = argparse.ArgumentParser(description="Arguments for training")
    parser.add_argument("-i", "--image_path", dest="image_path", help="Path to image", required=True)
    parser.add_argument("-m", "--model_path", dest="model_path", help="Path to the model weights", required=True)
    parser.add_argument("-o", "--output_path", dest="output_path", help="Path to save the predicted mask", required=True)
    parser.add_argument("-ps", "--patch_size", dest="patch_size", help="Patch size", default=constants.PATCH_SIZE, type=int)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    model = load_model(args.model_path, args.patch_size)
    image = cv2.imread(args.image_path)[:, :, ::-1] / 255.
    mask = inference(model, image, args.patch_size)
    mask = (mask * 255).astype(np.uint8)
    mask_th = ((mask > 128) * 255).astype(np.uint8)
    cv2.imwrite(args.output_path[:-4]+"-raw.jpg", mask)
    cv2.imwrite(args.output_path[:-4]+"-thresh.jpg", mask_th)
