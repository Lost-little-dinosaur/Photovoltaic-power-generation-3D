from Unet.net import *
from Unet.data import *




# _input = 'F:/other/BaoYan/zju/Project/src/Python/Photovoltaic-power-generation-3D/Unet/input.png'
# #
# img = keep_image_size_open_rgb(_input)
# img_data = transform(img).cuda()
# img_data = torch.unsqueeze(img_data, dim=0)
# net.eval()
# out = net(img_data)
# out = torch.argmax(out, dim=1)
# out = torch.squeeze(out, dim=0)
# out = out.unsqueeze(dim=0)
# print(set((out).reshape(-1).tolist()))
# out = (out).permute((1, 2, 0)).cpu().detach().numpy()
# cv2.imwrite('result/result.png', out)
# cv2.imshow('out', out * 255.0)
# cv2.waitKey(0)
# print()


def img2data(imgPath):
    net = UNet(2).cuda()

    weights = 'Unet/params/unet.pth'
    if os.path.exists(weights):
        net.load_state_dict(torch.load(weights))
        print('successfully loading')
    else:
        print('no loading')
    net.eval()
    return torch.squeeze(
        torch.argmax(net(torch.unsqueeze(transform(keep_image_size_open_rgb(imgPath)).cuda(), dim=0)), dim=1),
        dim=0).cpu().numpy()
