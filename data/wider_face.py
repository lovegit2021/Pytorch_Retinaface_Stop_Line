import os
import os.path
import sys
import torch
import torch.utils.data as data
import cv2
import numpy as np

class WiderFaceDetection(data.Dataset):
    def __init__(self, txt_path, preproc=None):
        self.preproc = preproc
        self.imgs_path = []
        self.words = []
        f = open(txt_path,'r')
        lines = f.readlines()
        isFirst = True
        labels = []
        for line in lines:
            line = line.rstrip()
            if line.startswith('#'):
                if isFirst is True:
                    isFirst = False
                else:
                    labels_copy = labels.copy()
                    self.words.append(labels_copy)
                    labels.clear()
                path = line[2:]
                #path = txt_path.replace('label.txt','images/') + path
                #path = txt_path.replace('train_widerface.txt','images/') + path
                #path = txt_path.replace('train_widerface_color.txt','images_color/') + path
                path = txt_path.replace('train_widerface_shuffle.txt','images_color/') + path
                self.imgs_path.append(path)
            else:
                line = line.split(' ')
                label = [float(x) for x in line]
                labels.append(label)

        self.words.append(labels)

    def __len__(self):
        return len(self.imgs_path)

    def __getitem__(self, index):
        img = cv2.imread(self.imgs_path[index])
        height, width, _ = img.shape
        
        #ret = cv2.imread(self.imgs_path[index], cv2.IMREAD_GRAYSCALE)
        #height, width = ret.shape
        #img = np.empty((height, width, 3), dtype=np.uint8)
        #img[:, :, 0] = img[:, :, 1] = img[:, :, 2] = ret

        labels = self.words[index]
        #annotations = np.zeros((0, 15))
        annotations = np.zeros((0, 13))
        if len(labels) == 0:
            return annotations
        for idx, label in enumerate(labels):
            #annotation = np.zeros((1, 15))
            annotation = np.zeros((1, 13))
            #x y w h label0 x1 y1 x2 y2 x3 y3 x4 y4 label1
            #0 312 638 98 1 637 316 2 319 1 405 636 406 1
            # bbox
            annotation[0, 0] = label[0]  # x1
            annotation[0, 1] = label[1]  # y1
            annotation[0, 2] = label[0] + label[2]  # x2
            annotation[0, 3] = label[1] + label[3]  # y2
            #annotation[0, 2] = label[2]  # x2
            #annotation[0, 3] = label[3]  # y2

            #landmarks
            annotation[0, 4] = label[5]      # l0_x
            annotation[0, 5] = label[6]      # l0_y
            annotation[0, 6] = label[7]      # l1_x
            annotation[0, 7] = label[8]      # l1_y
            annotation[0, 8] = label[9]      # l2_x
            annotation[0, 9] = label[10]      # l2_y
            annotation[0, 10] = label[11]     # l3_x
            annotation[0, 11] = label[12]      # l3_y

            '''
            # landmarks
            annotation[0, 4] = label[4]    # l0_x
            annotation[0, 5] = label[5]    # l0_y
            annotation[0, 6] = label[7]    # l1_x
            annotation[0, 7] = label[8]    # l1_y
            annotation[0, 8] = label[10]   # l2_x
            annotation[0, 9] = label[11]   # l2_y
            annotation[0, 10] = label[13]  # l3_x
            annotation[0, 11] = label[14]  # l3_y
            annotation[0, 12] = label[16]  # l4_x
            annotation[0, 13] = label[17]  # l4_y
            '''

            '''
            annotation[0, 4] = -1.0      # l0_x
            annotation[0, 5] = -1.0      # l0_y
            annotation[0, 6] = -1.0      # l1_x
            annotation[0, 7] = -1.0      # l1_y
            annotation[0, 8] = -1.0      # l2_x
            annotation[0, 9] = -1.0      # l2_y
            annotation[0, 10] = -1.0     # l3_x
            annotation[0, 11] = -1.0     # l3_y
            annotation[0, 12] = -1.0     # l4_x
            annotation[0, 13] = -1.0     # l4_y
 
            if (annotation[0, 4]<0):
                annotation[0, 14] = -1
            else:
                annotation[0, 14] = 1
            '''
            
            # if (annotation[0, 4]<0):
            #     annotation[0, 12] = -1
            # else:
            #     annotation[0, 12] = 1

            annotation[0, 12] = label[13]  # cls [bg=0, face without mask=1, face with mask=2]
            if (label[13] > 2):
                print(self.imgs_path[index])
                

            annotations = np.append(annotations, annotation, axis=0)
        target = np.array(annotations)
        if self.preproc is not None:
            img, target = self.preproc(img, target)

        return torch.from_numpy(img), target

def detection_collate(batch):
    """Custom collate fn for dealing with batches of images that have a different
    number of associated object annotations (bounding boxes).

    Arguments:
        batch: (tuple) A tuple of tensor images and lists of annotations

    Return:
        A tuple containing:
            1) (tensor) batch of images stacked on their 0 dim
            2) (list of tensors) annotations for a given image are stacked on 0 dim
    """
    targets = []
    imgs = []
    for _, sample in enumerate(batch):
        for _, tup in enumerate(sample):
            if torch.is_tensor(tup):
                imgs.append(tup)
            elif isinstance(tup, type(np.empty(0))):
                annos = torch.from_numpy(tup).float()
                targets.append(annos)

    return (torch.stack(imgs, 0), targets)
