import os

import numpy as np
import torch
from torch.utils.data import Dataset
from Unet.utils import *
from torchvision import transforms

transform = transforms.Compose([
    transforms.ToTensor()
])


class MyDataset(Dataset):
    def __init__(self, path):
        self.path = path
        self.name = os.listdir(os.path.join(path, 'SegmentationGrayClass'))

    def __len__(self):
        return len(self.name)

    def __getitem__(self, index):
        segment_name = self.name[index]  # xx.png
        segment_path = os.path.join(self.path, 'SegmentationGrayClass', segment_name)
        image_path = os.path.join(self.path, 'PNGImages', segment_name)
        segment_image = keep_image_size_open(segment_path)
        image = keep_image_size_open_rgb(image_path)
        return transform(image), torch.Tensor(np.array(segment_image))


if __name__ == '__main__':
    from torch.nn.functional import one_hot
    data = MyDataset('data')
    print(data[0][0].shape)
    print(data[0][1].shape)
    out=one_hot(data[0][1].long())
    print(out.shape)

# !ls "/content/drive/My Drive/Colab Notebooks/pytorch-UNet/AIRS数据集/SegmentationGrayClass (2)"
# !mv "/content/drive/My Drive/Colab Notebooks/pytorch-UNet/AIRS数据集/SegmentationGrayClass (2)" "/content/drive/My Drive/Colab Notebooks/pytorch-UNet/AIRS数据集/SegmentationGrayClass" # 重命名文件夹