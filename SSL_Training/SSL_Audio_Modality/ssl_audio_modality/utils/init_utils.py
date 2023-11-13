import importlib
from typing import Any, Dict, Optional, Union

import torch
from torchvision import transforms
from pytorch_lightning import LightningModule


from ssl_audio_modality.utils.augmentations.compose_random_augmentations import compose_random_augmentations



def init_encoder(model_cfg: Dict[str, Any], ckpt_path: Optional[str] = None):
    """ Initialize (pre-trained) encoder from model configuration

    Parameters
    ----------
    model_cfg : dict
        configurations of the model: architecture and hyperparameters
    ckpt_path : str, optional
        path to the file with the pre-trained model, by default None

    Returns
    -------
    torch.nn.Module
        initialized encoder
    """
    module = importlib.import_module(f"{model_cfg['from_module']}")
    class_ = getattr(module, model_cfg['class_name'])
    return class_(**model_cfg['kwargs'], pretrained=ckpt_path)


# Transforms and augmentations
def init_transforms(transforms_cfg: Dict[str, Any]):
    """ Initialize transforms from the provided configs
    """
    train = []
    test = []
    if transforms_cfg is not None:
        for t in transforms_cfg:
            module = importlib.import_module(f"utils.{t['from_module']}")
            class_ = getattr(module, t['class_name'])

            if "kwargs" in t:
                transform = class_(**t['kwargs'])
            else:
                transform = class_()

            train.append(transform)
            if t['in_test']:
                test.append(transform)

            print(f"added {t['class_name']} transformation")

    composed_train_transform = transforms.Compose(train)
    composed_test_transform = transforms.Compose(test)

    return composed_train_transform, composed_test_transform


def init_augmentations(aug_dict: Dict[str, Any]):
    augmentations = None
    augmentations = compose_random_augmentations(aug_dict)
    augmentations = transforms.Compose(augmentations)
    return augmentations


def setup_ssl_model(
        encoder: Union[torch.nn.Module, LightningModule],
        model_cfg: Dict[str, Any]
):
    """ Initializes SSL model given encoder and configs

    Parameters
    ----------
    encoder : Union[torch.nn.Module, LightningModule]
    model_cfg : dict
        ssl model configurations dictionalry


    Returns
    -------
    (dict, pytorch_lightning.LightningModule)
        dictionary with encoders and the whole ssl model
    """
    # init ssl framework
    ssl_model = getattr(importlib.import_module(model_cfg['from_module']), model_cfg['ssl_framework'])(
        encoder,
        ssl_batch_size=model_cfg['batch_size'],
        **model_cfg['kwargs']
    )

    return ssl_model
